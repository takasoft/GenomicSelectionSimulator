import logging
import threading
from dataclasses import dataclass

import numpy as np
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mtick

from genetic_linkage import cross2


@dataclass(frozen=True)
class PlotFrame:
    run_id: int
    generation: int
    centers: np.ndarray
    heights: np.ndarray
    width: float
    average: float
    minimum: float
    maximum: float
    high: float
    low: float


class Simulator(QtCore.QThread):
    statusChanged = QtCore.pyqtSignal(str)
    progressChanged = QtCore.pyqtSignal(str)
    frameReady = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, data, layout, canvas, listStatus, listSimStatus):
        super().__init__(layout.parentWidget())
        self.data = data
        self.layout = layout
        self.listStatus = listStatus
        self.listSimStatus = listSimStatus
        self.bakGeno = data['Geno'].copy()
        self.bakGebvs = data['Gebvs'].copy()
        self.numProgeny = 20
        self.currGen = 0
        self._cancel = threading.Event()
        self._running = threading.Event()
        self._running.set()
        self._run_id = 0
        self._previous_frame = None
        self._accept_frames = True

        self.statusChanged.connect(self.changeStatus, QtCore.Qt.QueuedConnection)
        self.progressChanged.connect(self.changeSimStatus, QtCore.Qt.QueuedConnection)
        self.frameReady.connect(self.renderPlot, QtCore.Qt.QueuedConnection)
        self.failed.connect(self.changeStatus, QtCore.Qt.QueuedConnection)

        index = layout.indexOf(canvas)
        position = layout.getItemPosition(index)
        layout.removeWidget(canvas)
        canvas.hide()
        canvas.deleteLater()
        self.fig = Figure()
        self.fig.subplots_adjust(top=0.85, bottom=0.22, left=0.2, right=0.95)
        self.fig.suptitle('Simulation Results', fontsize=10)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        layout.addWidget(self.canvas, *position)
        self.refreshAxis()

    def start(self):
        if self.isRunning():
            self.changeStatus('Please wait for the simulation to stop.')
            return
        self._cancel.clear()
        self._running.set()
        self._run_id += 1
        self._accept_frames = True
        self._previous_frame = None
        self.currGen = 0
        self.ax.clear()
        self.refreshAxis()
        self.canvas.draw_idle()
        super().start()

    def run(self):
        try:
            self.data['Geno'] = self.bakGeno.copy()
            self.data['Gebvs'] = self.bakGebvs.copy()
            self.numGenoToSelect = self.data['Geno'].shape[0] // 10
            self.numGenoRows = self.data['Geno'].shape[2]
            if self.numGenoToSelect < 2 or self.numGenoToSelect % 2:
                raise ValueError('The selected top 10% must contain an even number of at least two genomes.')
            self.statusChanged.emit('Starting simulation')
            self.plot()
            for generation in range(1, 11):
                if not self._checkpoint() or not self.calcGen():
                    return
                if not self._checkpoint():
                    return
                self.currGen = generation
                self.plot()
                if self._cancel.wait(0.2):
                    return
            self.statusChanged.emit('Simulation completed')
        except (ValueError, TypeError, IndexError, MemoryError, ArithmeticError) as error:
            logging.exception('Simulation failed')
            self.failed.emit('Simulation failed: {}'.format(error))

    def _checkpoint(self):
        self._running.wait()
        return not self._cancel.is_set()

    def stop(self):
        self._accept_frames = False
        self._cancel.set()
        self._running.set()
        self.changeStatus('Simulation stopped')

    def pause(self):
        self._running.clear()
        self.changeStatus('Simulation paused')

    def resume(self):
        self._running.set()
        self.changeStatus('Simulation resumed')

    def restart(self):
        self.start()

    def exit(self):
        self.stop()

    def isSimStopped(self):
        return not self.isRunning() or self._cancel.is_set()

    def isSimPaused(self):
        return not self._running.is_set()

    def calcGen(self):
        self.progressChanged.emit('Calculating generation {}'.format(self.currGen + 1))
        best_indices = np.argsort(self.data['Gebvs'])[::-1][:self.numGenoToSelect]
        best_genomes = self.data['Geno'][best_indices]
        progeny = []
        for i in range(0, self.numGenoToSelect, 2):
            if not self._checkpoint():
                return False
            progeny.append(cross2(
                best_genomes[i], best_genomes[i + 1], self.data['RF'], self.numProgeny
            ))
        genomes = np.concatenate(progeny, axis=0)
        gebvs = np.empty(genomes.shape[0])
        for i, genome in enumerate(genomes):
            if not self._checkpoint():
                return False
            gebvs[i] = np.sum((genome[0] + genome[1]) * self.data['Eft'])
        self.data['Geno'] = genomes
        self.data['Gebvs'] = gebvs
        return True

    def plot(self):
        """Prepare small plot summaries in the worker, never touch Qt here."""
        gebvs = self.data['Gebvs']
        genomes = self.data['Geno']
        hist, bins = np.histogram(gebvs, bins=10)
        frame = PlotFrame(
            self._run_id, self.currGen, (bins[:-1] + bins[1:]) / 2,
            hist / np.amax(hist) * 0.5, float(bins[1] - bins[0]),
            float(np.mean(gebvs)), float(np.min(gebvs)), float(np.max(gebvs)),
            float(2 * np.sum(np.any(genomes, axis=(0, 1)) * self.data['Eft'])),
            float(2 * np.sum(np.all(genomes, axis=(0, 1)) * self.data['Eft'])),
        )
        self.frameReady.emit(frame)

    @QtCore.pyqtSlot(object)
    def renderPlot(self, frame):
        if not self._accept_frames or frame.run_id != self._run_id:
            return
        self.changeSimStatus('Plotting generation {}'.format(frame.generation))
        self.ax.barh(frame.centers, frame.heights, frame.width, frame.generation, color='blue')
        previous = self._previous_frame
        if previous is not None:
            x = [previous.generation, frame.generation]
            self.ax.plot(x, [previous.average, frame.average], linewidth=0.3, color='red')
            self.ax.fill_between(
                x, [previous.minimum, frame.minimum], [previous.maximum, frame.maximum],
                facecolor='blue', alpha=0.2,
            )
            self.ax.fill_between(
                x, [previous.high, frame.high], [self.data['Potentials'][1]] * 2,
                facecolor='grey', alpha=0.7,
            )
            self.ax.fill_between(
                x, [0, 0], [previous.low, frame.low], facecolor='grey', alpha=0.7,
            )
        self._previous_frame = frame
        # Qt coalesces queued redraws instead of blocking the simulation worker.
        self.canvas.draw_idle()

    def refreshAxis(self):
        self.ax.set_xlabel('Generation Number', fontsize=10)
        self.ax.set_ylabel('GEBV', fontsize=10)
        self.ax.grid(True)
        self.ax.set_xlim([0, 10])
        self.ax.set_ylim([0, self.data['Potentials'][1]])
        self.ax.set_xticks(np.arange(0, 11, 1))
        self.ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))

    @QtCore.pyqtSlot(str)
    def changeSimStatus(self, text):
        self.listSimStatus.insertItem(0, text)

    @QtCore.pyqtSlot(str)
    def changeStatus(self, text):
        self.listStatus.insertItem(0, text)
