import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import h5py
import numpy as np
from PyQt5 import QtCore, QtTest, QtWidgets

import main
import simulation
from dataLoader import DataFileLoader, DataWorker


def sample_data():
    rng = np.random.RandomState(42)
    genomes = rng.randint(2, size=(40, 2, 8)).astype(np.int8)
    effects = np.arange(1, 9, dtype=float)
    return {
        'Geno': genomes, 'RF': np.full(7, 0.05), 'Eft': effects,
        'Gebvs': np.sum(genomes.sum(axis=1) * effects, axis=1),
        'Potentials': np.array([0, 2 * effects.sum()]),
    }


class RecordingSimulator(simulation.Simulator):
    def __init__(self, *args):
        self.render_threads = []
        self.status_threads = []
        self.frames = []
        super().__init__(*args)

    @QtCore.pyqtSlot(object)
    def renderPlot(self, frame):
        self.render_threads.append(threading.current_thread())
        self.frames.append(frame)
        super().renderPlot(frame)

    @QtCore.pyqtSlot(str)
    def changeStatus(self, text):
        self.status_threads.append(threading.current_thread())
        super().changeStatus(text)

    @QtCore.pyqtSlot(str)
    def changeSimStatus(self, text):
        self.status_threads.append(threading.current_thread())
        super().changeSimStatus(text)


class RecordingWindow(main.GenomicSelectionApp):
    def __init__(self):
        self.loaded_threads = []
        self.status_threads = []
        super().__init__()

    @QtCore.pyqtSlot(object)
    def _dataLoaded(self, data):
        self.loaded_threads.append(threading.current_thread())
        super()._dataLoaded(data)

    @QtCore.pyqtSlot(str)
    def changeStatus(self, text):
        self.status_threads.append(threading.current_thread())
        super().changeStatus(text)


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        replacement = patch.object(main, 'Simulator', RecordingSimulator)
        replacement.start()
        self.addCleanup(replacement.stop)
        self.window = RecordingWindow()
        self.window.data = sample_data()
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window._closing = True
        self.window.close()
        self.wait_until(lambda: not (self.window._simulating() or self.window._loading()))
        self.window.close()
        self.window.deleteLater()
        self.app.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)

    def wait_until(self, predicate, timeout=8):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            QtTest.QTest.qWait(10)
        self.app.processEvents()
        self.assertTrue(predicate(), 'Timed out while waiting for Qt work to complete')

    def start_simulation(self):
        self.window.btnStartPause.click()
        simulator = self.window.simulator
        self.wait_until(lambda: bool(simulator.frames))
        return simulator

    def test_plotting_and_status_stay_on_gui_thread_with_live_heartbeat(self):
        calculation_threads = []
        original_cross = simulation.cross2

        def record_cross(*args):
            calculation_threads.append(threading.current_thread())
            return original_cross(*args)

        ticks = []
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: ticks.append(time.monotonic()))
        timer.start(5)
        self.addCleanup(timer.stop)
        with patch.object(simulation, 'cross2', side_effect=record_cross):
            simulator = self.start_simulation()
            draw_threads = []
            simulator.canvas.mpl_connect(
                'draw_event', lambda event: draw_threads.append(threading.current_thread())
            )
            self.wait_until(lambda: not simulator.isRunning())
        self.assertEqual([frame.generation for frame in simulator.frames], list(range(11)))
        self.assertTrue(calculation_threads)
        self.assertTrue(all(t is not threading.main_thread() for t in calculation_threads))
        self.assertGreaterEqual(len(draw_threads), 3)
        self.assertTrue(all(t is threading.main_thread() for t in draw_threads))
        self.assertTrue(all(t is threading.main_thread() for t in simulator.render_threads))
        self.assertTrue(all(t is threading.main_thread() for t in simulator.status_threads))
        self.assertGreater(len(ticks), 20)
        self.assertLess(max(b - a for a, b in zip(ticks, ticks[1:])), 1.0)
        self.assertEqual(self.window.btnStartPause.text(), 'Start')
        self.assertTrue(self.window.actionOpenData.isEnabled())
        self.assertEqual(self.window.data['Geno'].shape, (40, 2, 8))
        np.testing.assert_array_equal(
            self.window.data['Gebvs'],
            np.sum(self.window.data['Geno'].sum(axis=1) * self.window.data['Eft'], axis=1),
        )

    def test_pause_resume_stop_and_restart(self):
        simulator = self.start_simulation()
        self.window.btnStartPause.click()
        self.assertTrue(simulator.isSimPaused())
        self.assertEqual(self.window.btnStartPause.text(), 'Resume')
        generation = simulator.currGen
        QtTest.QTest.qWait(300)
        self.assertEqual(simulator.currGen, generation)
        self.window.btnStartPause.click()
        self.assertFalse(simulator.isSimPaused())
        self.wait_until(lambda: simulator.currGen > generation)
        self.window.btnStartPause.click()
        started = time.monotonic()
        self.window.btnStop.click()
        self.wait_until(lambda: not simulator.isRunning(), timeout=1)
        self.assertLess(time.monotonic() - started, 1)
        self.assertEqual(self.window.btnStartPause.text(), 'Start')
        previous_run = simulator._run_id
        self.window.btnStartPause.click()
        self.wait_until(lambda: simulator.frames[-1].run_id != previous_run)
        initial = next(frame for frame in simulator.frames if frame.run_id != previous_run)
        self.assertEqual(initial.generation, 0)
        self.assertEqual(initial.average, simulator.frames[0].average)
        self.assertEqual(self.window.btnStartPause.text(), 'Pause')

    def test_close_while_paused_releases_worker_without_blocking(self):
        simulator = self.start_simulation()
        self.window.btnStartPause.click()
        with patch.object(QtWidgets.QMessageBox, 'question', return_value=QtWidgets.QMessageBox.Yes):
            started = time.monotonic()
            self.window.close()
            self.assertLess(time.monotonic() - started, 0.25)
        self.wait_until(lambda: not simulator.isRunning() and not self.window.isVisible(), timeout=1)

    def test_stale_frames_after_stop_or_restart_are_ignored(self):
        simulator = self.start_simulation()
        old_frame = simulator.frames[0]
        self.window.btnStop.click()
        self.wait_until(lambda: not simulator.isRunning())
        previous = simulator._previous_frame
        simulator.renderPlot(old_frame)
        self.assertIs(simulator._previous_frame, previous)
        simulator.restart()
        simulator.renderPlot(old_frame)
        self.assertIsNone(simulator._previous_frame)
        self.wait_until(lambda: simulator._previous_frame is not None)

    def test_calculation_errors_are_visible_and_controls_recover(self):
        with self.assertLogs(level='ERROR'):
            with patch.object(simulation, 'cross2', side_effect=ValueError('invalid genome data')):
                simulator = self.start_simulation()
                self.wait_until(lambda: not simulator.isRunning())
        messages = [
            self.window.listStatus.item(i).text()
            for i in range(self.window.listStatus.count())
        ]
        self.assertTrue(any('Simulation failed: invalid genome data' in text for text in messages))
        self.assertTrue(self.window.btnStartPause.isEnabled())
        self.assertEqual(self.window.btnStartPause.text(), 'Start')

    def test_generated_data_is_delivered_on_gui_thread(self):
        self.window.generateTestData()
        self.wait_until(lambda: not self.window._loading())
        self.assertEqual(self.window.data['Geno'].shape, (300, 2, 14000))
        self.assertEqual(self.window.loaded_threads, [threading.main_thread()])
        self.assertTrue(all(t is threading.main_thread() for t in self.window.status_threads))
        self.assertTrue(self.window.btnStartPause.isEnabled())

    def test_default_population_plots_without_starving_qt_events(self):
        self.window.generateTestData()
        self.wait_until(lambda: not self.window._loading())
        ticks = []
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: ticks.append(time.monotonic()))
        timer.start(5)
        self.addCleanup(timer.stop)
        simulator = self.start_simulation()
        self.wait_until(lambda: simulator._previous_frame.generation >= 2)
        self.assertGreater(len(ticks), 10)
        self.assertLess(max(b - a for a, b in zip(ticks, ticks[1:])), 1.0)
        self.window.btnStop.click()
        self.wait_until(lambda: not simulator.isRunning(), timeout=2)
        self.assertTrue(self.window.btnStartPause.isEnabled())

    def test_mat_file_load_is_atomic_and_delivered_on_gui_thread(self):
        expected = sample_data()
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / 'sample.mat'
            with h5py.File(filename, 'w') as source:
                for key, name in [('Geno', 'Geno'), ('RF', 'RF'), ('Eft', 'eft'),
                                  ('Gebvs', 'gebvs'), ('Potentials', 'potentials')]:
                    source[name] = expected[key]
            with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(filename), '')):
                self.window.loadData()
            self.wait_until(lambda: not self.window._loading())
        for name, value in expected.items():
            np.testing.assert_array_equal(self.window.data[name], value)
        self.assertEqual(self.window.loaded_threads, [threading.main_thread()])

    def test_cancelled_file_dialog_does_not_start_loading(self):
        with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=('', '')):
            self.window.loadData()
        self.assertIsNone(self.window.loader)

    def test_load_failure_preserves_data_and_notifies_user(self):
        original = self.window.data
        with tempfile.TemporaryDirectory() as directory:
            missing = str(Path(directory) / 'missing.mat')
            with self.assertLogs(level='ERROR'):
                self.window._startLoader(DataFileLoader(missing, self.window))
                self.wait_until(lambda: not self.window._loading())
        self.assertIs(self.window.data, original)
        self.assertTrue(self.window.listStatus.item(0).text().startswith('Data preparation failed:'))
        self.assertTrue(self.window.actionOpenData.isEnabled())

    def test_close_during_loading_keeps_event_loop_alive(self):
        class SlowLoader(DataWorker):
            def load(self):
                time.sleep(0.3)
                return sample_data()

        self.window._startLoader(SlowLoader(self.window))
        self.assertFalse(self.window.btnStartPause.isEnabled())
        self.assertFalse(self.window.actionGenerateTestData.isEnabled())
        ticks = []
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: ticks.append(True))
        timer.start(5)
        self.addCleanup(timer.stop)
        with patch.object(QtWidgets.QMessageBox, 'question', return_value=QtWidgets.QMessageBox.Yes):
            started = time.monotonic()
            self.window.close()
            self.assertLess(time.monotonic() - started, 0.25)
        self.wait_until(lambda: not self.window._loading() and not self.window.isVisible(), timeout=2)
        self.assertGreater(len(ticks), 5)
        self.assertFalse(self.window.loaded_threads)


if __name__ == '__main__':
    unittest.main()
