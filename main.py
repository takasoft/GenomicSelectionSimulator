from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal
import sys
import design # design.py file
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np # fast c++ calculation module
import h5py # for loading .mat data
from GenericLinkage import cross2


# this class inherits from qthread
# thus this will use another thread
# to read data from file
class ThreadLoadMatData(QtCore.QThread):
	# signal when loading is finished
	#startedLoading = pyqtSignal()
	#update = pyqtSignal()
	dataLoaded = pyqtSignal(object)
	
	def __init__(self, filename):
		QtCore.QThread.__init__(self)
		self.filename = filename
 
	def run(self):
		#self.startedLoading.emit()

		with h5py.File(self.filename, 'r') as f:
			print("Loading {} ".format(self.filename))
			#f = h5py.File(filename,'r')
			variables = f.items()

			# extract all data
			for name, data in variables:
				# If DataSet pull the associated Data
				if type(data) is h5py.Dataset:
					#self.update.emit()
					value = data.value
					if(name == "Geno"):
						genomes = value
					if(name == "RF"):
						rf = value
					if(name == "eft"):
						eft = value
					if(name == "gebvs"):
						gebvs = value
					if(name == "potentials"):
						potentials = value
			print("finished loading")

		# make gebvs row based
		gebvs = gebvs[:,0]
		# convert 1 by 1406756 matrix to 1D array
		rf = rf[0]
		eft = eft[0]


		data = [genomes, rf, eft, gebvs, potentials]

		self.dataLoaded.emit(data)


# a thread to generate another data
class ThreadGenerateTestData(QtCore.QThread):
	dataLoaded = pyqtSignal(object)
	
	def __init__(self):
		QtCore.QThread.__init__(self)
 
	def run(self):
		n = 14000
		genomes = np.random.randint(2, size=(600,n))
		genomes = np.reshape(genomes, (300, 2, n), order='C')
		rf = 0.1*np.random.random(n-1)
		eft = 700*np.random.random(n)
		#gebvs = np.random.uniform(low=4000000, high=6000000, size=(300,))
		gebvs = np.random.normal(5000000, 500000, 300)
		potentials = np.array([13494.078388, 12369035.6329792])

		data = [genomes, rf, eft, gebvs, potentials]

		self.dataLoaded.emit(data)


# this class inherits from qthread
# thus this will use another thread
# to calculate graph of each generation
class ThreadCalculateGen(QtCore.QThread):
	graphCalculated = pyqtSignal(object)
	
	def __init__(self, currentGen, data):
		QtCore.QThread.__init__(self)

		self.currentGen = currentGen

		self.genomes = data[0]
		self.rf = data[1]
		self.eft = data[2]
		self.gebvs = data[3]
		self.potentials = data[4]

		self.numProgenies = 20
		self.numChosenGenomes = 30
		self.numRows = self.genomes.shape[2]


	# picks 30 best genomes
	# produces 20 progenies from every 2 genomes
	# calculates the GEBVs for the 300 progenies
	def run(self):
		print("reproducing generation {}".format(self.currentGen))

		# save the indexes of chosen genomes
		# by descending order
		chosenGenomeIdx = np.argsort(self.gebvs)[::-1]

		# pick 30 best genomes
		## add the first one
		chosenGenomes = self.genomes[chosenGenomeIdx[0]]
		## make a 2*30 by 1406757 matrix
		for i in range(1, self.numChosenGenomes):
			chosenGenomes = np.concatenate((chosenGenomes, self.genomes[chosenGenomeIdx[i]]), axis=0)
		#print(chosenGenomes.shape)
		chosenGenomes = np.reshape(chosenGenomes, (self.numChosenGenomes, 2, self.numRows), order='C')
		#print(chosenGenomes.shape)

		# produces 20 progenies from every 2 genomes
		# we are going to make a 2*20*15 by 1406757 matrix
		# and reshape it to 300 by 2 by 1406757 matrix
		## add the first one
		print("current genome pair: 1")
		L1 = chosenGenomes[0]
		L2 = chosenGenomes[1]
		#print(L2.shape)
		self.genomes = np.empty([0, 0, 0])
		self.genomes = cross2(L1, L2, self.rf, self.numProgenies)
		#print(self.genomes.shape)
		## repeat adding 
		for i in range(1, self.numChosenGenomes//2):
			#print(i)
			print("current genome pair: {}".format(i+1))
			L1 = chosenGenomes[2*i]
			L2 = chosenGenomes[2*i+1]
			self.genomes = np.concatenate((self.genomes, cross2(L1, L2, self.rf, self.numProgenies)), axis=0)

		# update the current genomes
		#self.genomes = self.genomes	

		# calculate the GEBVs 
		print("Calculating GEBVs")
		for i in range(self.numChosenGenomes*self.numProgenies//2):
			#print(i)
			
			gebv = np.sum((self.genomes[i][0]+self.genomes[i][1])*self.eft)
			#print(gebv)
			self.gebvs[i] = gebv

		self.graphCalculated.emit([self.genomes, self.rf, self.eft, self.gebvs, self.potentials])


# widget to draw the graph
# wrapper class of FigureCanvas
class WidgetGraph():
	def __init__(self):
		# data
		self.genomes = None # this value will be updated every generation
		self.rf = None
		self.eft = None
		self.gebvs = None # this value will be updated every generation
		self.potentials = None

		# for graph
		self.canvas = None
		self.fig = None
		self.ax = None

		# current generation 
		self.currentGen = 0

		self.setupGraph()
		self.refreshAxis()

		self.threadCalc = None

		self.averageGEBVs = []
		self.maxGEBV = []
		self.minGEBV = []
		self.high = []
		self.low = []

		self.layout = None
		self.labelStatus = None

	# sets genome, recombination frequency, 
	# GEBV, and potentials
	def setData(self, data):
		self.genomes = data[0]
		self.rf = data[1]
		self.eft = data[2]
		self.gebvs = data[3]
		self.potentials = data[4]
		#print(self.potentials)

	# returns the data
	def getData(self):
		return [self.genome, self.rf, self.eft, self.gebvs, self.potentials]

	# setup graph
	def setupGraph(self):
		# set up the canvas to display the graph
		self.fig = plt.figure()
		self.canvas = FigureCanvas(self.fig)
		# setup figure
		self.fig.subplots_adjust(top=0.85, bottom=0.22, left=0.2, right=0.95)
		self.fig.suptitle('Simulation Results', fontsize=10)
		# setup axis and plot
		self.ax = self.fig.add_subplot(111)


	# refresh the axis
	# needs to call this after plotting
	def refreshAxis(self):
		## set up axis names
		self.ax.set_xlabel("Generation Number", fontsize=10)
		self.ax.set_ylabel('GEBV', fontsize=10)
		## make a grid
		self.ax.grid(True)
		## fix the axis
		self.ax.set_xlim([0,10])
		self.ax.set_ylim([0,12369035.6329792])
		self.ax.set_xticks(np.arange(0, 11, 1))   
		self.ax.set_yticks([0,2000000,4000000,6000000,8000000,10000000,12000000])   
		## use scientific notation
		self.ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))

	# adds this widget to the current layout
	def addToLayout(self, layout, a, b, c, d):
		layout.addWidget(self.canvas, a, b, c, d)

	def setLabelStatus(self, label):
		self.labelStatus = label

	def changeStatus(self, text):
		self.labelStatus.setText(text)

	def plotAverage(self):
		average = np.mean(self.gebvs)
		self.averageGEBVs.append(average)
		#print(self.averageGEBVs)
		#print(len(self.averageGEBVs))
		if(self.currentGen > 0):
			#self.ax.set_color('red')
			self.ax.plot([self.currentGen-1, self.currentGen], self.averageGEBVs, linewidth=0.3, color='red')
			self.averageGEBVs.pop(0)


	def fillMaxMinGEBV(self):
		self.maxGEBV.append(np.max(self.gebvs))
		self.minGEBV.append(np.min(self.gebvs))
		if(self.currentGen > 0):
			self.ax.fill_between([self.currentGen-1, self.currentGen], self.minGEBV, self.maxGEBV, facecolor='blue', alpha=0.2)
			#self.ax.fill([self.currentGen-1, self.currentGen], self.maxGEBV, color='black')
			#self.ax.plot([self.currentGen-1, self.currentGen], self.minGEBV, color='black')
			self.maxGEBV.pop(0)
			self.minGEBV.pop(0)

	def fillHighLow(self):
		#h = genomes
		self.high.append(h)
		self.low.append(l)
		if(self.currentGen > 0):
			self.ax.plot([self.currentGen-1, self.currentGen], self.high, linewidth=1, color='red')
			#self.ax.fill([self.currentGen-1, self.currentGen], self.maxGEBV, color='black')
			#self.ax.plot([self.currentGen-1, self.currentGen], self.minGEBV, color='black')
			self.high.pop(0)
			self.low.pop(0)

	# plot results
	def plot(self):
		print("plotting generation {}".format(self.currentGen))
		self.changeStatus("Plotting generation {}".format(self.currentGen))
		# process the self.gebvs to make a histogram
		hist, bins = np.histogram(self.gebvs, bins=10)
		width = (bins[1] - bins[0])
		center = (bins[:-1] + bins[1:]) / 2
		## make the height of the histogram lower
		hist = hist/np.amax(hist)*0.5

		## make a histogram
		self.ax.barh(center, hist, width, self.currentGen, color='blue')
		self.plotAverage()
		self.fillMaxMinGEBV()
		# refresh the axis after plot
		self.refreshAxis()
		# refresh canvas
		self.canvas.draw()

		# gives gui time to process and refresh canvas
		QtWidgets.QApplication.processEvents()


	def reproduce(self):	
		self.currentGen += 1
		self.changeStatus("Calculating Generation: {}".format(self.currentGen))
		self.threadCalc = ThreadCalculateGen(self.currentGen, [self.genomes, self.rf, self.eft, self.gebvs, self.potentials])
		self.threadCalc.graphCalculated.connect(self.finishedCalcGen)
		self.threadCalc.start()
		self.threadCalc.wait()

	def finishedCalcGen(self, data):
		

		self.genomes = data[0]
		self.rf = data[1]
		self.eft = data[2]
		self.gebvs = data[3]
		self.potentials = data[4]

		self.plot()


	def startSimulation(self):
		#self.plot()
		i = 0
		while(i < 10):
			self.reproduce()
			QtWidgets.QApplication.processEvents()
			i += 1

		self.changeStatus("Finished Simulation")


class GenomicSelectionApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
	def __init__(self):
		super(self.__class__, self).__init__()
		# sets up layout and widgets that are defined
		self.setupUi(self) 

		# move the window to the upper left for test purpose
		self.move(1, 0)

		self.setupConnections()

		# set up the private variables for options 
		# in questions and original populations lists
		self.orgPopulations = ["tree1", "tree2", "tree3"]
		self.selectionApproaches = ["approach1", "approach2", "approach3"]
		self.dispItems()

		# graph plotter
		self.widgetGraph = None
		self.setupWidgetGraph()

		# set the current status
		self.labelStatus.setText("Please load the data.")

	# set up the widget to display the graph
	def setupWidgetGraph(self):
		print("setting up graph widget")
		# replace the placeholder with the graph widget
		idx = self.gridLayout.indexOf(self.canvas)
		graphLocation = self.gridLayout.getItemPosition(idx)
		#print("POS {}".format(graphLocation))
		self.gridLayout.removeWidget(self.canvas)
		self.widgetGraph = WidgetGraph()
		self.widgetGraph.setLabelStatus(self.labelStatus)
		self.widgetGraph.addToLayout(self.gridLayout, graphLocation[0], graphLocation[1], graphLocation[2], graphLocation[3])

	# connect signals
	def setupConnections(self):
		## When the start button is clicked
		self.btnStart.clicked.connect(self.bntStartPressed)
		## when exit option is pressed 
		self.actionExit.triggered.connect(self.close)
		## when open data option is pressed
		self.actionOpenData.triggered.connect(self.loadData)
		## when load data button is clicked
		self.btnLoadData.clicked.connect(self.loadData)

		self.btnGenerateData.clicked.connect(self.generateData)

	# when the start button is pressed
	def bntStartPressed(self):
		print("start button pressed")

		
		self.widgetGraph.startSimulation()
		
	# load data using a different thread
	def generateData(self):
		print("loading data")
		# update stats
		self.gridLayout
		self.labelStatus.setText("Loading data...")

		self.thread = ThreadGenerateTestData()
		self.thread.dataLoaded.connect(self.onDataReady)
		self.thread.start()

	# load data using a different thread
	def loadData(self):
		print("loading data")
		# update stats
		self.labelStatus.setText("Loading data...")

		self.thread = ThreadLoadMatData("GenomicSelectionData.mat")
		self.thread.dataLoaded.connect(self.onDataReady)
		self.thread.start()

	# when the data is fully loaded
	def onDataReady(self, data):
		#print(data)

		self.widgetGraph.setData(data)
		self.widgetGraph.plot()

		print("data loaded")
		self.labelStatus.setText("Data successfully loaded.")

	# display the original Populations and selection approaches
	def dispItems(self):
		print("displaying items")
		# clear the list first
		self.listWidgetOrgPopulation.clear()
		if self.orgPopulations:
			for choice in self.orgPopulations:
				self.listWidgetOrgPopulation.addItem(choice) 

		self.listWidgetSelectionApproach.clear()
		if self.selectionApproaches:
			for choice in self.selectionApproaches:
				self.listWidgetSelectionApproach.addItem(choice) 

		self.listWidgetOrgPopulation.setCurrentRow(0)
		self.listWidgetSelectionApproach.setCurrentRow(0)


if __name__=="__main__":
	app = QtWidgets.QApplication(sys.argv) 
	form = GenomicSelectionApp()       
	form.show()  # show the form  
	sys.exit(app.exec_())
