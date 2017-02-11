import sys

from PyQt5 import QtCore, QtWidgets

import design
from dataLoader import TestDataGenerator, DataFileLoader
from simulation import Simulator


class GenomicSelectionApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.data = {'Geno': None, 'RF': None, 'Eft': None, 'Gebvs': None, 'Potentials': None}
        self.orgPopulations = ['test data 1', 'test data 2', 'test data 3']
        self.selectionApproaches = ['GEBV', 'HV', 'OHV']
        self.filename = None
        self.simulator = None
        self.loader = None
        self._closing = False
        self.setupUi(self)
        self.move(1, 0)
        self.btnStartPause.clicked.connect(self.btnStartPauseClicked)
        self.btnStop.clicked.connect(self.btnStopClicked)
        self.actionOpenData.triggered.connect(self.loadData)
        self.actionGenerateTestData.triggered.connect(self.generateTestData)
        self.listWidgetOrgPopulation.addItems(self.orgPopulations)
        self.listWidgetSelectionApproach.addItems(self.selectionApproaches)
        self.listWidgetOrgPopulation.setCurrentRow(0)
        self.listWidgetSelectionApproach.setCurrentRow(0)
        self._updateControls()
        self.changeStatus('Please load the data. (File->Open Data File)')

    def _simulating(self):
        return self.simulator is not None and self.simulator.isRunning()

    def _loading(self):
        return self.loader is not None and self.loader.isRunning()

    def _updateControls(self):
        simulating = self._simulating()
        loading = self._loading()
        stopping = simulating and self.simulator.isSimStopped()
        self.btnStartPause.setEnabled(not (loading or stopping or self._closing))
        self.btnStop.setEnabled(simulating and not (stopping or self._closing))
        self.actionOpenData.setEnabled(not (simulating or loading or self._closing))
        self.actionGenerateTestData.setEnabled(not (simulating or loading or self._closing))
        if not simulating:
            self.btnStartPause.setText('Start')
        elif self.simulator.isSimPaused():
            self.btnStartPause.setText('Resume')
        else:
            self.btnStartPause.setText('Pause')

    def btnStartPauseClicked(self):
        if self.data['Geno'] is None:
            self.changeStatus('Please load the data first.')
            return
        if self.simulator is None:
            self.simulator = Simulator(
                self.data, self.gridLayout, self.canvas, self.listStatus, self.listSimStatus
            )
            self.canvas = self.simulator.canvas
            self.simulator.finished.connect(self._workerFinished)
            self.simulator.start()
        elif self.simulator.isSimStopped():
            self.simulator.restart()
        elif self.simulator.isSimPaused():
            self.simulator.resume()
        else:
            self.simulator.pause()
        self._updateControls()

    def btnStopClicked(self):
        if self.simulator is not None:
            self.simulator.stop()
        self._updateControls()

    def _startLoader(self, loader):
        if self.loader is not None:
            self.loader.deleteLater()
        self.loader = loader
        loader.statusChanged.connect(self.changeStatus)
        loader.failed.connect(self.changeStatus)
        loader.loaded.connect(self._dataLoaded)
        loader.finished.connect(self._workerFinished)
        loader.start()
        self._updateControls()

    def generateTestData(self):
        if self._simulating() or self._loading():
            self.changeStatus('Please stop the current operation before generating data.')
            return
        self._startLoader(TestDataGenerator(self))

    def loadData(self):
        if self._simulating() or self._loading():
            self.changeStatus('Please stop the current operation before loading data.')
            return
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open File', './', 'MATLAB HDF5 data (*.mat)'
        )
        if filename:
            self.filename = filename
            self._startLoader(DataFileLoader(filename, self))

    @QtCore.pyqtSlot(object)
    def _dataLoaded(self, data):
        if self._closing:
            return
        if self.simulator is not None:
            self.simulator.deleteLater()
            self.simulator = None
        self.data = data

    @QtCore.pyqtSlot()
    def _workerFinished(self):
        self._updateControls()
        if self._closing and not (self._simulating() or self._loading()):
            QtCore.QTimer.singleShot(0, self.close)

    @QtCore.pyqtSlot(str)
    def changeStatus(self, text):
        self.listStatus.insertItem(0, text)

    def closeEvent(self, event):
        if not self._closing:
            reply = QtWidgets.QMessageBox.question(
                self, 'Message', 'Are you sure you want to exit the program?',
                QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No,
            )
            if reply != QtWidgets.QMessageBox.Yes:
                event.ignore()
                return
            self._closing = True
        if self._simulating() or self._loading():
            if self._simulating():
                self.simulator.exit()
            if self._loading():
                self.loader.requestInterruption()
            self.changeStatus('Waiting for the current operation to stop.')
            self._updateControls()
            event.ignore()
            return
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = GenomicSelectionApp()
    form.show()
    sys.exit(app.exec_())
