import h5py # for loading .mat data
import numpy as np # fast c++ calculation module
import threading
from PyQt5 import QtCore, QtGui, QtWidgets # GUI

class TestDataGenerator:
	"""
	Makes gausian distribution data
	"""

	def __init__(self, data, listStatus):
		""" constructor """

		self.data = data
		self.listStatus = listStatus

	def generate(self):
		"""
		generates test data
		"""

		print("Generating test data")
		self.listStatus.insertItem(0, "Generating test data")

		n = 14000
		k = 300
		self.data['Geno'] = np.random.randint(2, size=(2*k,n), dtype=np.int8)
		self.data['Geno'] = np.reshape(self.data['Geno'], (k, 2, n), order='C')
		#print(self.data['Geno'])
		self.data['RF'] = 0.1*np.random.random(n-1)
		#self.data['Eft'] = 700*np.random.random(n)
		self.data['Eft'] = np.random.uniform(0, 100, size=n)
		#print(self.data['Eft'])
		self.data['Potentials'] = np.array([13494.078388, 12369035.6329792])

		self.data['Gebvs'] = np.zeros(k)
		for i in range(k):
			self.data['Gebvs'][i] = np.sum((self.data['Geno'][i][0]+self.data['Geno'][i][1])*self.data['Eft'])	

		#print(self.data['Gebvs'])	

		print('Finished generating test data')
		self.listStatus.insertItem(0, 'Finished generating test data')

	def start(self):
		""" 
		Generate test data using another thread
		"""

		self.threadGenData = threading.Thread(target=self.generate)
		self.threadGenData.start()   



class DataFileLoader:
	""" 
	loads data from .mat file 
	"""

	def __init__(self, data, filename, listStatus):
		""" constructor """

		self.data = data
		self.filename = filename
		self.listStatus = listStatus
 
	def loadMat(self):
		""" load .mat data file """

		print("Loading {} ".format(self.filename))
		self.listStatus.insertItem(0, "Loading {} ".format(self.filename))
		QtWidgets.QApplication.processEvents()

		with h5py.File(self.filename, 'r') as f:
			variables = f.items()

			# extract all data
			for name, vdata in variables:
				# If DataSet pull the associated Data
				if type(vdata) is h5py.Dataset:
					#self.update.emit()
					value = vdata.value
					if(name == "Geno"):
						# convert it to a bool array
						self.data['Geno'] = np.array(value, dtype=np.int8)
					if(name == "RF"):
						self.data['RF'] = value
					if(name == "eft"):
						self.data['Eft'] = value
					if(name == "gebvs"):
						self.data['Gebvs'] = value
					if(name == "potentials"):
						self.data['Potentials'] = value

		# make gebvs row based
		self.data['Gebvs'] = self.data['Gebvs'][:,0]
		# convert 1 by 1406756 matrix to 1D array
		self.data['RF'] = self.data['RF'][0]
		self.data['Eft'] = self.data['Eft'][0]

		#print(self.data['Geno'])

		print('Finished loading data')
		self.listStatus.insertItem(0, 'Finished loading data')
		QtWidgets.QApplication.processEvents()


	def start(self):
		""" 
		Load file data
		"""

		

		self.threadLoadData = threading.Thread(target=self.loadMat)
		self.threadLoadData.start()   
