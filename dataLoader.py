import logging

import h5py
import numpy as np
from PyQt5 import QtCore


class DataWorker(QtCore.QThread):
    loaded = QtCore.pyqtSignal(object)
    statusChanged = QtCore.pyqtSignal(str)
    failed = QtCore.pyqtSignal(str)

    def run(self):
        try:
            data = self.load()
            if not self.isInterruptionRequested():
                self.loaded.emit(data)
        except (OSError, KeyError, ValueError, TypeError, IndexError, MemoryError) as error:
            logging.exception('Data preparation failed')
            self.failed.emit('Data preparation failed: {}'.format(error))


class TestDataGenerator(DataWorker):
    def load(self):
        self.statusChanged.emit('Generating test data')
        n = 14000
        k = 300
        genomes = np.random.randint(2, size=(k, 2, n), dtype=np.int8)
        rf = 0.1 * np.random.random(n - 1)
        effects = np.random.uniform(0, 100, size=n)
        gebvs = np.array([
            np.sum((genome[0] + genome[1]) * effects) for genome in genomes
        ])
        self.statusChanged.emit('Finished generating test data')
        return {
            'Geno': genomes, 'RF': rf, 'Eft': effects, 'Gebvs': gebvs,
            'Potentials': np.array([13494.078388, 12369035.6329792]),
        }


class DataFileLoader(DataWorker):
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.filename = filename

    def load(self):
        self.statusChanged.emit('Loading {}'.format(self.filename))
        with h5py.File(self.filename, 'r') as source:
            data = {
                'Geno': np.array(source['Geno'][()], dtype=np.int8),
                'RF': np.asarray(source['RF'][()]).reshape(-1),
                'Eft': np.asarray(source['eft'][()]).reshape(-1),
                'Gebvs': np.asarray(source['gebvs'][()]).reshape(-1),
                'Potentials': np.asarray(source['potentials'][()]).reshape(-1),
            }
        genomes = data['Geno']
        if genomes.ndim != 3 or genomes.shape[1] != 2:
            raise ValueError('Geno must have shape (population, 2, loci).')
        n = genomes.shape[2]
        if (data['RF'].size != n - 1 or data['Eft'].size != n
                or data['Gebvs'].size != genomes.shape[0] or data['Potentials'].size != 2):
            raise ValueError('The data arrays have incompatible shapes.')
        self.statusChanged.emit('Finished loading data')
        return data
