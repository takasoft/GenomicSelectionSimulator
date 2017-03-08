from PyQt5 import QtCore, QtGui, QtWidgets # GUI
import design # design.py file (Design of gui)
import numpy as np # fast c++ calculation module
from dataLoader import TestDataGenerator, DataFileLoader
from simulation import Simulator
import sys

class GenomicSelectionApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
	"""
	This is a class to control the GUI written in design.py
	I made design.py from design.ui by using pyuic5
	pyuic5 design.ui -o design.py
	"""

	def __init__(self):
		"""
		Constructor
		"""

		super(self.__class__, self).__init__()

		''' instance variables '''
		# dictionary that contains nessesary data for the simulation
		self.data = {'Geno': None, 'RF': None, 'Eft': None, 'Gebvs': None, 'Potentials': None}
		# list of original populations
		self.orgPopulations = ['test data 1', 'test data 2', 'test data 3']
		# list of selection approaches
		self.selectionApproaches = ['GEBV', 'HV', 'OHV']
		# file name of the data file
		self.filename = None
		# simulator object
		self.simulator = None

		# sets up layout and widgets that are defined
		self.setupUi(self) 

		# move the window to the upper left for test purpose
		self.move(1, 0)

		# set up connections of gui elements
		self.setupConnections()

		# display original populations and selection approaches
		self.dispItems()

		# change the current status
		self.changeStatus("Please load the data. (File->Open Data File)")

	def setupConnections(self):
		"""
		Set up connections of the GUI elements
		"""

		## When the start button is clicked
		self.btnStartPause.clicked.connect(self.btnStartPauseClicked)
		## When the stop button is clicked
		self.btnStop.clicked.connect(self.btnStopClicked)
		## when open data option is clicked
		self.actionOpenData.triggered.connect(self.loadData)
		## when the generate test data option is clicked
		self.actionGenerateTestData.triggered.connect(self.generateTestData)

	def btnStartPauseClicked(self):
		"""
		Start/Pause button is clicked
		"""

		if self.data['Geno'] is None:
			# data not loaded yet
			print('Data not loaded yet')
			self.changeStatus('Please load the data first.')
		else:
			# start simulation

			if self.simulator is None:
				# if it is the first time to start the simulation

				self.simulator = Simulator(self.data, self.gridLayout, self.canvas, self.listStatus, self.listSimStatus)
				self.simulator.start() 
				self.btnStartPause.setText('Pause')
			else:
				if self.simulator.isSimStopped():
					self.simulator.restart()
				else:
					if self.simulator.isSimPaused():
						self.simulator.resume()
						self.btnStartPause.setText('Pause')
					else:
						self.simulator.pause()
						self.btnStartPause.setText('Resume')

	def btnStopClicked(self):
		"""
		Stop button is clicked
		"""
		if self.simulator is None:
			# data not loaded yet
			print('Start the simulation first')
			self.changeStatus('Please start the simulation first.')
		else:
			self.simulator.stop()
			self.btnStartPause.setText('Start')
		
	def generateTestData(self):
		"""
		generate test data using a different thread 
		"""
		self.testDataGenerator = TestDataGenerator(self.data, self.listStatus)
		self.testDataGenerator.start()
		
	def loadData(self):
		"""
		load data using a different thread
		"""

		self.fileDialog = QtWidgets.QFileDialog(self)
		selectedfile = self.fileDialog.getOpenFileName(self, 'Open File', './', 'Data (*.mat *.csv *.xlsx)')
		self.filename = selectedfile[0]
		
		print('{} is selected'.format(self.filename))

		if self.filename is not None:
			self.dataFileLoader = DataFileLoader(self.data, self.filename, self.listStatus)
			self.dataFileLoader.start()

	def dispItems(self):
		"""
		displays the original Populations and selection approaches
		"""

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

	def changeStatus(self, text):
		self.listStatus.insertItem(0, text)



	def closeEvent(self, event):
		""" 
		shows a exit prompt and exit the app
		"""

		quit_msg = "Are you sure you want to exit the program?"
		
		reply = QtWidgets.QMessageBox.question(self, 'Message', 
					 quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

		if reply == QtWidgets.QMessageBox.Yes:
			event.accept()
			if self.simulator is not None:
				self.simulator.exit()
		else:
			event.ignore()

# main function
if __name__=="__main__":
	app = QtWidgets.QApplication(sys.argv) 
	form = GenomicSelectionApp()       
	form.show()  # show the form  
	sys.exit(app.exec_())
	