import sys
import traceback
import threading
from pathlib import Path
from queue import Queue

import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtWidgets

from last2 import Ui_MainWindow


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEDULERS_DIR = PROJECT_ROOT / "schedulers_simulator"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCHEDULERS_DIR) not in sys.path:
    sys.path.insert(0, str(SCHEDULERS_DIR))

from schedulers_simulator.FCFS import FCFS
from schedulers_simulator.Non_preemptive_priority import Non_preemptive_priority
from schedulers_simulator.Process import Process
from schedulers_simulator.SJF import sjf_preemptive
from schedulers_simulator.SJF_NF import sjf
from schedulers_simulator.gantt_chart import draw_gantt, redraw_gantt
from schedulers_simulator.preemptive_priority import preemptive_priority_scheduler
from schedulers_simulator.round_robin import RoundRobinScheduler


ALGO_LABEL_TO_KEY = {
    "First Come First Serve": "FCFS",
    "Shortest Job First(SJF) Preemptive": "SJF (Preemptive)",
    "Shortest Job First(SJF) Non Preemptive": "SJF (Non-Preemptive)",
    "Priority Scheduling Preemptive": "Priority (Preemptive)",
    "Priority Scheduling Non Preemptive": "Priority (Non-Preemptive)",
    "Round Robin": "Round Robin",
}


class SchedulerWorker(QtCore.QObject):
    progress = QtCore.pyqtSignal(object, int)
    finished = QtCore.pyqtSignal(object, int, float, float)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, run_fn, processes, new_process_queue, live_sim, pause_event):
        super().__init__()
        self.run_fn = run_fn
        self.processes = processes
        self.new_process_queue = new_process_queue
        self.live_sim = live_sim
        self.pause_event = pause_event

    @QtCore.pyqtSlot()
    def run(self):
        try:
            def on_progress(history, time_counter):
                self.progress.emit(list(history), int(time_counter))

            history, time_counter, att, awt = self.run_fn(
                self.processes,
                self.new_process_queue,
                live_sim=self.live_sim,
                pause_event=self.pause_event,
                fig=None,
                ax=None,
                on_progress=on_progress,
            )

            self.finished.emit(history, int(time_counter), float(att), float(awt))
        except Exception:
            self.failed.emit(traceback.format_exc())


class SchedulerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.pending_processes = []
        self.original_bursts = {}
        self.pid_to_row = {}
        self.current_pid = 0

        self.is_running = False
        self.live_sim = False
        self.new_process_queue = Queue()
        self.pause_event = threading.Event()
        self.pause_event.set()

        self.last_history = None
        self.last_time_counter = 0
        self.last_att = 0.0
        self.last_awt = 0.0

        self.live_history = []
        self.live_time_counter = 0
        self.live_fig = None
        self.live_ax = None

        self.worker_thread = None
        self.worker = None

        self._configure_widgets()
        self._connect_signals()
        self._update_algo_specific_inputs()
        self._set_running_state(False)

    def _configure_widgets(self):
        self.ui.arrival_input.setMinimum(0)
        self.ui.arrival_input.setMaximum(100000)
        self.ui.burst_input.setMinimum(1)
        self.ui.burst_input.setMaximum(100000)
        self.ui.priority_input.setMinimum(0)
        self.ui.priority_input.setMaximum(100000)
        self.ui.quantum_input.setMinimum(1)
        self.ui.quantum_input.setMaximum(100000)
        self.ui.quantum_input.setValue(4)

    def _connect_signals(self):
        self.ui.dropdown_menu.currentTextChanged.connect(self._update_algo_specific_inputs)
        self.ui.addButton.clicked.connect(self._on_add_clicked)
        self.ui.runButton.clicked.connect(self._on_run_clicked)
        self.ui.pauseButton.clicked.connect(self._on_pause_clicked)
        self.ui.resumeButton.clicked.connect(self._on_resume_clicked)
        self.ui.resetButton.clicked.connect(self._on_reset_clicked)
        self.ui.saveButton.clicked.connect(self._on_display_clicked)

    def _selected_algo_key(self):
        selected_label = self.ui.dropdown_menu.currentText()
        return ALGO_LABEL_TO_KEY[selected_label]

    def _resolve_run_function(self, selected_algo):
        if selected_algo == "Round Robin":
            quantum = self.ui.quantum_input.value()
            if quantum <= 0:
                raise ValueError("Quantum must be greater than 0.")
            return RoundRobinScheduler(quantum).runRoundRobin

        scheduler_functions = {
            "FCFS": FCFS().run,
            "SJF (Non-Preemptive)": sjf,
            "SJF (Preemptive)": sjf_preemptive,
            "Priority (Non-Preemptive)": Non_preemptive_priority,
            "Priority (Preemptive)": preemptive_priority_scheduler,
        }
        return scheduler_functions[selected_algo]

    def _copy_processes_for_run(self):
        copied = []
        for process in self.pending_processes:
            copied.append(
                Process(
                    process.num,
                    process.arrival_time,
                    process.burst_time,
                    process.priority,
                )
            )
        return copied

    def _append_log(self, message):
        self.ui.textEdit.append(message)

    def _append_table_row(self, pid, burst, finish="-"):
        row = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row)
        self.ui.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(str(pid)))
        self.ui.tableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(str(burst)))
        self.ui.tableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(str(finish)))
        self.pid_to_row[pid] = row

    def _live_window_exists(self):
        fig = self.live_fig
        if fig is None:
            return False
        figure_number = getattr(fig, "number", None)
        if figure_number is None:
            return False
        return plt.fignum_exists(figure_number)

    def _ensure_live_window(self):
        if self._live_window_exists():
            return

        plt.ion()
        self.live_fig, self.live_ax = plt.subplots(figsize=(12, 3))
        try:
            manager = getattr(self.live_fig.canvas, "manager", None)
            if manager is not None and hasattr(manager, "set_window_title"):
                manager.set_window_title("Live Gantt")
        except Exception:
            pass
        self.live_fig.show()

    def _redraw_live_window(self):
        fig = self.live_fig
        ax = self.live_ax
        if fig is None or ax is None:
            return

        figure_number = getattr(fig, "number", None)
        if figure_number is None or not plt.fignum_exists(figure_number):
            return

        redraw_gantt(ax, self.live_history)
        ax.set_xlim(0, max(self.live_time_counter, 1))
        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        plt.pause(0.001)

    def _close_live_window(self):
        if self._live_window_exists():
            plt.close(self.live_fig)
        self.live_fig = None
        self.live_ax = None

    def _set_running_state(self, running):
        self.is_running = running

        self.ui.runButton.setEnabled(not running)
        self.ui.resetButton.setEnabled(not running)
        self.ui.dropdown_menu.setEnabled(not running)
        self.ui.checkBox.setEnabled(not running)

        self.ui.pauseButton.setEnabled(running and self.live_sim and self.pause_event.is_set())
        self.ui.resumeButton.setEnabled(running and self.live_sim and not self.pause_event.is_set())
        if running and self.live_sim:
            self.ui.saveButton.setEnabled(True)
            self.ui.saveButton.setText("live gantt")
        else:
            self.ui.saveButton.setEnabled((not running) and (self.last_history is not None))
            self.ui.saveButton.setText("display")

        if not running:
            self.ui.addButton.setEnabled(True)
        else:
            # Dynamic add is only allowed when paused.
            self.ui.addButton.setEnabled(self.live_sim and not self.pause_event.is_set())

    def _update_algo_specific_inputs(self):
        algo = self._selected_algo_key()
        needs_priority = "Priority" in algo
        needs_quantum = algo == "Round Robin"

        self.ui.priority_label.setVisible(needs_priority)
        self.ui.priority_input.setVisible(needs_priority)
        self.ui.quantum_label.setVisible(needs_quantum)
        self.ui.quantum_input.setVisible(needs_quantum)

    def _build_process_from_inputs(self, pid):
        algo = self._selected_algo_key()
        arrival = self.ui.arrival_input.value()
        burst = self.ui.burst_input.value()
        if burst <= 0:
            raise ValueError("Burst time must be greater than 0.")

        priority = self.ui.priority_input.value() if "Priority" in algo else None
        return Process(pid, arrival, burst, priority)

    def _on_add_clicked(self):
        try:
            pid = self.current_pid + 1
            process = self._build_process_from_inputs(pid)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", str(exc))
            return

        if self.is_running:
            if not self.live_sim:
                QtWidgets.QMessageBox.information(
                    self,
                    "Unavailable",
                    "Adding a process while running is only available in live simulation mode.",
                )
                return

            if self.pause_event.is_set():
                QtWidgets.QMessageBox.information(
                    self,
                    "Pause Required",
                    "Pause the simulation first, then add a process.",
                )
                return

            self.current_pid = pid
            self.new_process_queue.put(process)
            self.original_bursts[process.num] = process.burst_time
            self._append_table_row(process.num, process.burst_time)
            self._append_log(f"P{process.num} queued for dynamic insertion.")
            return

        self.current_pid = pid
        self.pending_processes.append(process)
        self.original_bursts[process.num] = process.burst_time
        self._append_table_row(process.num, process.burst_time)
        self._append_log(f"P{process.num} added to pending list.")

    def _on_run_clicked(self):
        if self.is_running:
            return

        if not self.pending_processes:
            QtWidgets.QMessageBox.information(
                self,
                "No Processes",
                "Add at least one process before running the simulation.",
            )
            return

        selected_algo = self._selected_algo_key()
        try:
            run_fn = self._resolve_run_function(selected_algo)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Invalid Configuration", str(exc))
            return

        self.live_sim = self.ui.checkBox.isChecked()
        self.new_process_queue = Queue()
        self.pause_event = threading.Event()
        self.pause_event.set()

        processes_for_run = self._copy_processes_for_run()

        self.last_history = None
        self.last_time_counter = 0
        self.last_att = 0.0
        self.last_awt = 0.0

        self.live_history = []
        self.live_time_counter = 0
        if self.live_sim:
            self._ensure_live_window()
            self._redraw_live_window()

        self.worker_thread = QtCore.QThread(self)
        self.worker = SchedulerWorker(
            run_fn,
            processes_for_run,
            self.new_process_queue,
            self.live_sim,
            self.pause_event,
        )
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_scheduler_progress)
        self.worker.finished.connect(self._on_scheduler_finished)
        self.worker.failed.connect(self._on_scheduler_failed)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.failed.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()
        self._set_running_state(True)
        self._append_log(f"Running {selected_algo}...")

    def _on_pause_clicked(self):
        if not self.is_running or not self.live_sim:
            return
        if not self.pause_event.is_set():
            return

        self.pause_event.clear()
        self._set_running_state(True)
        self._append_log("Simulation paused.")

    def _on_resume_clicked(self):
        if not self.is_running or not self.live_sim:
            return
        if self.pause_event.is_set():
            return

        self.pause_event.set()
        self._set_running_state(True)
        self._append_log("Simulation resumed.")

    def _build_finish_map(self, history):
        finish_map = {}
        for entry in history:
            process_num, _start, end = entry
            if isinstance(process_num, int) and process_num > 0:
                finish_map[process_num] = max(finish_map.get(process_num, 0), int(end))
        return finish_map

    def _update_finish_column(self, finish_map):
        for pid, row in self.pid_to_row.items():
            finish_value = finish_map.get(pid)
            text = "-" if finish_value is None else str(finish_value)
            self.ui.tableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(text))

    def _on_scheduler_progress(self, history, time_counter):
        self.live_history = list(history)
        self.live_time_counter = int(time_counter)
        if self.live_sim:
            self._redraw_live_window()

    def _on_scheduler_finished(self, history, time_counter, att, awt):
        self.last_history = list(history)
        self.last_time_counter = int(time_counter)
        self.last_att = float(att)
        self.last_awt = float(awt)

        self.live_history = list(history)
        self.live_time_counter = int(time_counter)
        if self.live_sim:
            self._redraw_live_window()

        finish_map = self._build_finish_map(history)
        self._update_finish_column(finish_map)

        self._append_log(f"Average Turnaround Time: {self.last_att:.2f} sec")
        self._append_log(f"Average Waiting Time: {self.last_awt:.2f} sec")
        self._append_log("Simulation completed.")

        if not self.pause_event.is_set():
            self.pause_event.set()

        self._set_running_state(False)
        self.worker = None
        self.worker_thread = None

    def _on_scheduler_failed(self, trace_text):
        self._set_running_state(False)
        self.worker = None
        self.worker_thread = None
        QtWidgets.QMessageBox.critical(self, "Simulation Error", "The scheduler failed. See details in the log.")
        self._append_log("Scheduler execution failed:")
        self._append_log(trace_text)

    def _on_display_clicked(self):
        if self.is_running:
            if self.live_sim:
                self._ensure_live_window()
                self._redraw_live_window()
                self._append_log("Opened live Gantt window.")
            else:
                QtWidgets.QMessageBox.information(
                    self,
                    "Unavailable",
                    "Live Gantt is only available while a live simulation is running.",
                )
            return

        if not self.last_history:
            QtWidgets.QMessageBox.information(
                self,
                "No Result",
                "Run a simulation first to display the Gantt chart.",
            )
            return

        final_fig, final_ax = plt.subplots(figsize=(12, 3))
        draw_gantt(final_ax, self.last_history, self.last_time_counter)
        plt.show()
        self._append_log("Displayed final Gantt chart and saved image as gantt.png.")

    def _on_reset_clicked(self):
        if self.is_running:
            QtWidgets.QMessageBox.information(
                self,
                "Simulation Running",
                "Wait until the simulation finishes before resetting.",
            )
            return

        self.pending_processes.clear()
        self.original_bursts.clear()
        self.pid_to_row.clear()
        self.current_pid = 0
        self.new_process_queue = Queue()

        self.last_history = None
        self.last_time_counter = 0
        self.last_att = 0.0
        self.last_awt = 0.0

        self.live_history = []
        self.live_time_counter = 0
        self._close_live_window()

        self.pause_event = threading.Event()
        self.pause_event.set()

        self.ui.tableWidget.setRowCount(0)
        self.ui.textEdit.clear()
        self._set_running_state(False)
        self._append_log("State reset.")

    def closeEvent(self, event):
        if self.is_running:
            QtWidgets.QMessageBox.warning(
                self,
                "Simulation Running",
                "Please wait for the simulation to finish before closing the window.",
            )
            event.ignore()
            return

        self._close_live_window()
        super().closeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = SchedulerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()