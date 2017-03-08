import threading
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from GenericLinkage import cross2
import numpy as np # fast c++ calculation module
import time


class Simulator(threading.Thread):
	"""
	Thread to simulates genomic selection
	usage: simulator = Simulator(layout, canvas)
	"""

	def __init__(self, data, layout, canvas, listStatus, listSimStatus):
		""" constructor """

		threading.Thread.__init__(self) # inheritance of threading module
		
		# private variables for displaying graph
		self.layout = layout # layout of the GUI
		self.canvas = canvas
		self.fig = None
		self.ax = None
		self.listStatus = listStatus # list of status change
		self.listSimStatus = listSimStatus # list of simulation status change

		# private variables for calculation
		self.data = data
		self.bakGeno = np.copy(self.data['Geno']) # backup of the initial geno
		self.bakGebvs = np.copy(self.data['Gebvs']) # backup of the initial Gebvs
		self.currGen = 0 # current generation
		self.numGenoToSelect = self.data['Geno'].shape[0]//10 # number of genomes to select
		self.numGenoRows = self.data['Geno'].shape[2] # number of rows of genome
		self.numProgeny = 20 # number of progeny each pair produces
		self.averageGEBVs = []
		self.maxGEBV = []
		self.minGEBV = []
		self.high = []
		self.low = []


		# private variables for controling the calculation
		self.isStopped = False
		self.isPaused = False
		self.isDone = False

		# set up the graph widget
		self.setupGraph()

	def run(self):
		""" 
		This is the start point of a python thread
		"""

		while not self.isDone:
			print("Starting calculation")
			self.changeStatus("Starting simulation")
			self.calculate()
			print("Exiting calculation")

			while self.isStopped:
				# wait until restarted
				time.sleep(0.5)		

			# reset the data
			self.data['Geno'] = self.bakGeno
			self.data['Gebvs'] = self.bakGebvs
			self.currGen = 0
			self.averageGEBVs = []
			self.maxGEBV = []
			self.minGEBV = []
			self.high = []
			self.low = []

			# reset the status
			self.isStopped = False
			self.isPaused = False
			
	def calculate(self):
		"""
		do the simulatio calculation
		"""

		# plot the first generation
		self.plot()

		while not self.isStopped or not self.isDone:
			if self.currGen >= 10:
				self.isStopped = True
				return

			if self.isStopped:
				return

			while self.isPaused:
				# pause until simulation is resumed
				time.sleep(0.5)

			
			self.calcGen()
			if self.isStopped:
				return
			self.currGen += 1
			self.plot()


			time.sleep(0.2)

	def stop(self):
		"""
		Stop the calculation
		This resets the calculated data
		"""

		print("stopped")
		self.changeStatus("Simulation stopped")
		self.isStopped = True
		self.isPaused = False

	def pause(self):
		"""
		Puase the calculation
		This doesn't reset the calculated data
		"""

		print("paused")
		self.changeStatus("Simulation paused")
		self.isPaused = True

	def resume(self):
		"""
		Resume from paused calculation
		"""

		print("resumed")
		self.changeStatus("Simulation resumed")
		self.isPaused = False

	def restart(self):
		"""
		restart the calculation
		"""

		print("restarting")
		self.changeStatus("Simulation restarting")
		if self.isStopped == True:
			self.isStopped = False
		else:
			self.isStopped = True
			time.sleep(0.5)
			self.isStopped = False
			self.isPaused = False

		self.ax.clear()

	def exit(self):
		""" 
		exit the calculation entirely
		making this thread unusable
		call this method only when you exit the entire simulation
		"""

		self.isDone = True
		self.isPaused = False


	def isSimStopped(self):
		""" 
		return if the simulation is stopped
		""" 
		return self.isStopped

	def isSimPaused(self):
		""" 
		return if the simulation is stopped
		""" 

		return self.isPaused

	def setupGraph(self):
		""" 
		setup the graph
		"""

		# delelte the place holder and
		idx = self.layout.indexOf(self.canvas)
		pos = self.layout.getItemPosition(idx)
		self.layout.removeWidget(self.canvas)

		# initialize the figure
		self.fig = plt.figure()
		# initialize the pyqt canvas of the figure
		self.canvas = FigureCanvas(self.fig)
		# setup the figure
		self.fig.subplots_adjust(top=0.85, bottom=0.22, left=0.2, right=0.95)
		self.fig.suptitle('Simulation Results', fontsize=10)
		# setup the axis and plot
		self.ax = self.fig.add_subplot(111)

		# adds this widget to the current layout
		self.layout.addWidget(self.canvas, pos[0], pos[1], pos[2], pos[3])


	def calcGen(self):
		""" 
		calculate each generation
		"""

		print("Calculating generation {}".format(self.currGen+1))
		self.changeSimStatus("Calculating generation {}".format(self.currGen+1))

		# save the indexes of best genomes
		# by descending order
		bestGenomeIdx = np.argsort(self.data['Gebvs'])[::-1]

		''' pick 30 best genomes '''
		## add the first one
		bestGenomes = self.data['Geno'][bestGenomeIdx[0]]

		## make a 2*30 by 1406757 matrix
		for i in range(1, self.numGenoToSelect):
			bestGenomes = np.concatenate((bestGenomes, self.data['Geno'][bestGenomeIdx[i]]), axis=0)

		bestGenomes = np.reshape(bestGenomes, (self.numGenoToSelect, 2, self.numGenoRows), order='C')

		# empty the current genomes
		self.data['Geno'] = None

		# produces 20 progeny from every 2 genomes
		# we are going to make a 2*20*15 by 1406757 matrix
		# and reshape it to 300 by 2 by 1406757 matrix
		## add the first one
		print("current genome pair: 1")
		L1 = bestGenomes[0]
		L2 = bestGenomes[1]
		#print(L2)
		
		self.data['Geno'] = cross2(L1, L2, self.data['RF'], self.numProgeny)
		#print(self.genomes.shape)
		
		for i in range(1, self.numGenoToSelect//2):
			## repeat producing new generation

			print("current genome pair: {}".format(i+1))
			L1 = bestGenomes[2*i]
			L2 = bestGenomes[2*i+1]
			self.data['Geno'] = np.concatenate((self.data['Geno'], cross2(L1, L2, self.data['RF'], self.numProgeny)), axis=0)

			if self.isStopped or self.isDone:
				return

			while(self.isPaused):
				# pause until simulation is resumed
				time.sleep(0.5)

				if self.isStopped or self.isDone:
					return

		#print(self.data['Geno'])

		# calculate the GEBVs 
		print("Calculating GEBVs")
		for i in range(self.numGenoToSelect*self.numProgeny//2):

			if self.isStopped or self.isDone:
				return

			self.data['Gebvs'][i] = np.sum((self.data['Geno'][i][0]+self.data['Geno'][i][1])*self.data['Eft'])
	
	def refreshAxis(self):
		"""
		refresh the axis
		needs to call this after plotting
		"""

		## set up axis names
		self.ax.set_xlabel("Generation Number", fontsize=10)
		self.ax.set_ylabel('GEBV', fontsize=10)
		## make a grid
		self.ax.grid(True)
		## fix the axis
		self.ax.set_xlim([0,10])
		self.ax.set_ylim([0,self.data['Potentials'][1]])
		self.ax.set_xticks(np.arange(0, 11, 1))   
		self.ax.set_yticks([0,2000000,4000000,6000000,8000000,10000000,12000000])   
		## use scientific notation
		self.ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))

	def plotAverage(self):
		average = np.mean(self.data['Gebvs'])
		self.averageGEBVs.append(average)
		#print(self.averageGEBVs)
		#print(len(self.averageGEBVs))
		if(self.currGen > 0):
			#self.ax.set_color('red')
			self.ax.plot([self.currGen-1, self.currGen], self.averageGEBVs, linewidth=0.3, color='red')
			self.averageGEBVs.pop(0)

		# fill between max gebv and min gebv
	def fillMaxMinGEBV(self):
		self.maxGEBV.append(np.max(self.data['Gebvs']))
		self.minGEBV.append(np.min(self.data['Gebvs']))
		if(self.currGen > 0):
			self.ax.fill_between([self.currGen-1, self.currGen], self.minGEBV, self.maxGEBV, facecolor='blue', alpha=0.2)
			self.maxGEBV.pop(0)
			self.minGEBV.pop(0)

	# fill between ylim and highest potential
	# and  between 0 and lowest potential
	def fillHighLow(self):
		#Y = np.reshape(self.genomes, (2*self.numProgenies*self.numChosenGenomes, self.numRows), order='C')
		Y = np.reshape(self.data['Geno'], (600, self.numGenoRows), order='C')
		sumYcolumn = np.sum(Y, axis=0, dtype=np.bool)
		prodYcolumn = np.prod(Y, axis=0, dtype=np.bool)
		h = 2*np.sum(sumYcolumn*self.data['Eft'])
		l = 2*np.sum(prodYcolumn*self.data['Eft'])
		#print(h)
		#print(l)
		
		self.high.append(h)
		self.low.append(l)
		if(self.currGen > 0):
			self.ax.fill_between([self.currGen-1, self.currGen], self.high, [12369035.6329792, 12369035.6329792], facecolor='grey', alpha=0.7)
			self.ax.fill_between([self.currGen-1, self.currGen], [0,0], self.low, facecolor='grey', alpha=0.7)
			self.high.pop(0)
			self.low.pop(0)

	def plot(self):
		""" 
		plot histogram of each generation
		"""

		print("plotting generation {}".format(self.currGen))
		self.changeSimStatus("plotting generation {}".format(self.currGen))

		#self.changeStatus("Plotting generation {}".format(self.currentGen))
		# process the self.gebvs to make a histogram
		hist, bins = np.histogram(self.data['Gebvs'], bins=10)
		width = (bins[1] - bins[0])
		center = (bins[:-1] + bins[1:]) / 2
		## make the height of the histogram lower
		hist = hist/np.amax(hist)*0.5

		## make a histogram
		self.ax.barh(center, hist, width, self.currGen, color='blue')
		self.plotAverage()
		self.fillMaxMinGEBV()
		self.fillHighLow()
		# refresh the axis after plot
		self.refreshAxis()
		# refresh canvas
		self.canvas.draw()

	def changeSimStatus(self, text):
		self.listSimStatus.insertItem(0, text)

	def changeStatus(self, text):
		self.listStatus.insertItem(0, text)




class ThreadTestCalculation(threading.Thread):
	""" 
	calculation for test purposes only
	"""

	def __init__(self):
		threading.Thread.__init__(self)
		self.num = 0
		self.isStopped = False
		self.isPaused = False
		self.calcID = 0

	def run(self):
		while True:
			print("Starting calculation {}".format(self.calcID))
			self.calculate()
			print("Exiting calculation {}".format(self.calcID))
			self.num = 0
			self.isStopped = False
			self.isPaused = False
			self.calcID += 1
			while self.isStopped:
				time.sleep(0.5)

	def calculate(self):
		while not self.isStopped:
			while(self.isPaused):
				time.sleep(0.5)

			self.num += 1
			time.sleep(0.2)

	def show(self):
		return self.num

	def stop(self):
		print("stopped")
		self.isStopped = True

	def pause(self):
		print("paused")
		self.isPaused = True

	def resume(self):
		print("resumed")
		self.isPaused = False

	def restart(self):
		print("restarting")
		self.isStopped = True
		time.sleep(0.5)
		self.isStopped = False
		self.isPaused = False

	def isSimStopped(self):
		return isStopped


