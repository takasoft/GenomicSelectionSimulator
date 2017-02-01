#!/usr/bin/python

from PyQt5 import QtCore, QtGui, QtWidgets
import sys 
import design # design.py file
import random
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import h5py
from GenericLinkage import cross2

class GenomicSelectionApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
	def __init__(self):
		super(self.__class__, self).__init__()
		# sets up layout and widgets that are defined
		self.setupUi(self) 


		
		# set up the private variables for options 
		# in questions and original populations lists
		self.questions = []
		self.orgPopulations = []

		# current generation number
		self.currentGen = 0
		# number of progenies to produce for every 2 genomes
		self.numProgenies = 20
		# number of genomes to pick from 300 genome pool
		self.numChosenGenomes =30
		# number of rows in a genome
		self.numRows = 0

		# genome data
		self.genomes = None
		self.rf = None
		self.eft = None
		self.gebvs = None
		self.potentials = None

		# When the start button is pressed
		self.btnStart.clicked.connect(self.bntStartPressed) 
		self.actionExit.triggered.connect(self.actionExitTriggered)

		# setup graph
		## set up the canvas to display the graph
		self.fig = plt.figure()
		self.canvas = FigureCanvas(self.fig)
		self.gridLayout.addWidget(self.canvas, 2, 0, 1, 3)
		## setup figure
		self.fig.subplots_adjust(top=0.85, bottom=0.22, left=0.2, right=0.95)
		self.fig.suptitle('Simulation Results', fontsize=10)
		## setup axis and plot
		self.ax = self.fig.add_subplot(111)
		### discards the old graph
		#self.ax.hold(False) 
		### set up the axis
		self.refreshAxis()


	# read from mat file
	def readData(self, fileName):
		with h5py.File(fileName, 'r') as f:
			print("Loading {} ".format(fileName))
			#f = h5py.File(fileName,'r')
			variables = f.items()

			# extract all data
			for name, data in variables:
				# If DataSet pull the associated Data
				if type(data) is h5py.Dataset:
					value = data.value
					#values.append(value)
					if(name == "Geno"):
						self.genomes = value
					if(name == "RF"):
						self.rf = value
					if(name == "eft"):
						self.eft = value
					if(name == "gebvs"):
						self.gebvs = value
					if(name == "potentials"):
						self.potentials = value
			print("finished loading")

		# make gebvs row based
		self.gebvs = self.gebvs[:,0]
		# get a number of rows in genome matrix
		self.numRows = self.genomes.shape[2]
		# convert 1 by 1406756 matrix to 1D array
		self.rf = self.rf[0]
		self.eft = self.eft[0]
		#print(self.eft.shape)



	# setup axis
	def refreshAxis(self):
		## set up axis names
		self.ax.set_xlabel("Generation Number", fontsize=10)
		self.ax.set_ylabel('GEBV', fontsize=10)
		## make a grid
		self.ax.grid(True)
		## fix the axis
		self.ax.set_xlim([0,10])
		self.ax.set_ylim([0,12000000])
		self.ax.set_xticks(np.arange(0, 11, 1))   
		#self.ax.set_ylim([0,2])
		## use scientific notation
		self.ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))


	# plot results
	def plot(self):
		print("plotting generation {}".format(self.currentGen))
		# process the self.gebvs to make a histogram
		hist, bins = np.histogram(self.gebvs, bins=10)
		width = (bins[1] - bins[0])
		center = (bins[:-1] + bins[1:]) / 2
		## make the height of the histogram lower
		hist = hist/np.amax(hist)*0.5

		## make a histogram
		self.ax.barh(center, hist, width, self.currentGen, color='blue')
		# refresh the axis after plot
		self.refreshAxis()
		# refresh canvas
		self.canvas.draw()

		# gives gui time to process and refresh canvas
		QtWidgets.QApplication.processEvents()



	# display the original Populations and selection approaches
	def dispItems(self):
		#print("display items")
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

		# start plotting the first generation
		self.plot()
		self.currentGen += 1


	# check the options
	def startSimulation(self):
		#print("check options")
		# currently selected choice
		idxOrgPopulation = self.listWidgetOrgPopulation.currentRow()
		idxSelectionApproach = self.listWidgetSelectionApproach.currentRow()
		
		# user has not chosen answer
		if (idxOrgPopulation < 0 or idxSelectionApproach < 0):
			print("  not chosen yet")

		#print(idxOrgPopulation)
		#print(idxSelectionApproach)

		#self.reproduce()
		#self.plot()
		#self.currentGen += 1
		

		while(self.currentGen < 10):
			self.reproduce()
			self.plot()
			self.currentGen += 1


	# picks 30 best genomes
	# produces 20 progenies from every 2 genomes
	# calculates the GEBVs for the 300 progenies
	def reproduce(self):
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
		print(self.gebvs.shape)
		print(np.amax(self.gebvs))

					
	# when the start button is pressed
	def bntStartPressed(self):
		print("start button pressed")
		self.startSimulation()


	# exit action is triggered
	def actionExitTriggered(self):
		print("exit")
		QtGui.QApplication.quit()

			
	# set orgPopulations, selectionApproaches
	def setData(self, orgPopulations, selectionApproaches):
		self.orgPopulations = orgPopulations
		self.selectionApproaches = selectionApproaches


	# run the GUI
	def run(self):
		print("start app")
		self.readData("GenomicSelectionData.mat")
		self.dispItems()                      


def main():
	orgPopulations = ["tree1", "tree2", "tree3"]
	selectionApproaches = ["approach1", "approach2", "approach3"]

	app = QtWidgets.QApplication(sys.argv) 
	# set the form to be our ExampleApp (design) 
	form = GenomicSelectionApp()   
	form.setData(orgPopulations, selectionApproaches)
	form.run()
	# show the form              
	form.show()                         
	app.exec_() 


if __name__ == '__main__':  
	main()                              
