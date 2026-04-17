import sys
import traceback
import threading
from pathlib import Path
from queue import Queue

import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtWidgets, QtGui

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

## ── Button stylesheets ──────────────────────────────────────────────────────

STYLE_PAUSE_ACTIVE = """
    QPushButton {
        background-color: #E9C46A;
        color: #1a1a2e;
        border-radius: 6px;
        font-weight: bold;
        padding: 6px 12px;
    }
    QPushButton:hover { background-color: #f4d03f; }
    QPushButton:pressed { background-color: #d4a017; }
"""

STYLE_PAUSE_INACTIVE = """
    QPushButton {
        background-color: #3a3a5c;
        color: #888;
        border-radius: 6px;
        font-weight: bold;
        padding: 6px 12px;
    }
"""

STYLE_RESUME_ACTIVE = """
    QPushButton {
        background-color: #2DC653;
        color: #1a1a2e;
        border-radius: 6px;
        font-weight: bold;
        padding: 6px 12px;
    }
    QPushButton:hover { background-color: #27ae60; }
    QPushButton:pressed { background-color: #1e8449; }
"""

STYLE_RESUME_INACTIVE = """
    QPushButton {
        background-color: #3a3a5c;
        color: #888;
        border-radius: 6px;
        font-weight: bold;
        padding: 6px 12px;
    }
"""

STYLE_RUN_ACTIVE = """
    QPushButton {
        background-color: #457B9D;
        color: white;
        border-radius: 6px;
        font-weight: bold;
        padding: 6px 12px;
    }
    QPushButton:hover { background-color: #5a9dbf; }
    QPushButton:pressed { background-color: #2c5f7a; }
    QPushButton:disabled { background-color: #3a3a5c; color: #888; }
"""

STYLE_RESET = """
    QPushButton {
        background-color: #E63946;
        color: white;
        border-radius: 6px;
        font-weight: bold;
        padding: 6px 12px;
    }
    QPushButton:hover { background-color: #ff4d5a; }
    QPushButton:pressed { background-color: #c0392b; }
    QPushButton:disabled { background-color: #3a3a5c; color: #888; }
"""

## ── Worker ──────────────────────────────────────────────────────────────────

class SchedulerWorker(QtCore.QObject):
    progress = QtCore.pyqtSignal(object, int)
    finished = QtCore.pyqtSignal(object, int, float, float)
    failed   = QtCore.pyqtSignal(str)

    def __init__(self, run_fn, processes, new_process_queue, live_sim, pause_event):
        super().__init__()
        self.run_fn            = run_fn
        self.processes         = processes
        self.new_process_queue = new_process_queue
        self.live_sim          = live_sim
        self.pause_event       = pause_event

    @QtCore.pyqtSlot()
    def run(self):
        try:
            def on_progress(history, time_counter):
                self.progress.emit(list(history), int(time_counter))

            history, time_counter, att, awt = self.run_fn(
                self.processes,
                self.new_process_queue,
                live_sim    = self.live_sim,
                pause_event = self.pause_event,
                fig         = None,
                ax          = None,
                on_progress = on_progress,
            )
            self.finished.emit(history, int(time_counter), float(att), float(awt))
        except Exception:
            self.failed.emit(traceback.format_exc())


## ── Main Window ─────────────────────────────────────────────────────────────

class SchedulerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.pending_processes = []
        self.original_bursts   = {}
        self.pid_to_row        = {}
        self.current_pid       = 0

        # ── tracks remaining burst per pid for live update ──
        self.remaining_bursts  = {}

        self.is_running        = False
        self.live_sim          = False
        self.new_process_queue = Queue()
        self.pause_event       = threading.Event()
        self.pause_event.set()

        self.last_history      = None
        self.last_time_counter = 0
        self.last_att          = 0.0
        self.last_awt          = 0.0

        self.live_history      = []
        self.live_time_counter = 0
        self.live_fig          = None
        self.live_ax           = None

        self.worker_thread     = None
        self.worker            = None

        self._configure_widgets()
        self._connect_signals()
        self._update_algo_specific_inputs()
        self._set_running_state(False)

    # ── Widget setup ────────────────────────────────────────────────────────

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

        # Table: 4 columns — PID | Original Burst | Remaining | Finish
        self.ui.tableWidget.setColumnCount(4)
        self.ui.tableWidget.setHorizontalHeaderLabels(["PID", "Burst", "Remaining", "Finish"])
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.ui.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget.setAlternatingRowColors(False)

        # Apply button styles
        self.ui.runButton.setStyleSheet(STYLE_RUN_ACTIVE)
        self.ui.resetButton.setStyleSheet(STYLE_RESET)

    def _connect_signals(self):
        self.ui.dropdown_menu.currentTextChanged.connect(self._update_algo_specific_inputs)
        self.ui.addButton.clicked.connect(self._on_add_clicked)
        self.ui.runButton.clicked.connect(self._on_run_clicked)
        self.ui.pauseButton.clicked.connect(self._on_pause_clicked)
        self.ui.resumeButton.clicked.connect(self._on_resume_clicked)
        self.ui.resetButton.clicked.connect(self._on_reset_clicked)
        self.ui.saveButton.clicked.connect(self._on_display_clicked)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _selected_algo_key(self):
        return ALGO_LABEL_TO_KEY[self.ui.dropdown_menu.currentText()]

    def _resolve_run_function(self, selected_algo):
        if selected_algo == "Round Robin":
            quantum = self.ui.quantum_input.value()
            if quantum <= 0:
                raise ValueError("Quantum must be greater than 0.")
            return RoundRobinScheduler(quantum).runRoundRobin

        return {
            "FCFS":                      FCFS().run,
            "SJF (Non-Preemptive)":      sjf,
            "SJF (Preemptive)":          sjf_preemptive,
            "Priority (Non-Preemptive)": Non_preemptive_priority,
            "Priority (Preemptive)":     preemptive_priority_scheduler,
        }[selected_algo]

    def _copy_processes_for_run(self):
        return [
            Process(p.num, p.arrival_time, p.burst_time, p.priority)
            for p in self.pending_processes
        ]

    def _append_log(self, message):
        self.ui.textEdit.append(message)

    def _append_table_row(self, pid, burst, finish="-"):
        row = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row)

        for col, value in enumerate([str(pid), str(burst), str(burst), str(finish)]):
            item = QtWidgets.QTableWidgetItem(value)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.ui.tableWidget.setItem(row, col, item)

        self.pid_to_row[pid]       = row
        self.remaining_bursts[pid] = burst   # ← track remaining burst

    def _update_remaining_burst(self, pid, remaining):
        """Update the Remaining column for a given pid."""
        row = self.pid_to_row.get(pid)
        if row is None:
            return
        item = QtWidgets.QTableWidgetItem(str(max(remaining, 0)))
        item.setTextAlignment(QtCore.Qt.AlignCenter)

        # Highlight the currently running process in yellow
        if remaining > 0:
            item.setForeground(QtGui.QColor("#E9C46A"))
        else:
            item.setForeground(QtGui.QColor("#2DC653"))   # green when done

        self.ui.tableWidget.setItem(row, 2, item)

    # ── Pause / Resume button highlighting ──────────────────────────────────

    def _update_pause_resume_style(self):
        """Highlight the correct button based on current pause state."""
        paused = not self.pause_event.is_set()

        if self.is_running and self.live_sim:
            # Pause button: yellow when clickable (not yet paused)
            self.ui.pauseButton.setStyleSheet(
                STYLE_PAUSE_INACTIVE if paused else STYLE_PAUSE_ACTIVE
            )
            self.ui.pauseButton.setEnabled(not paused)

            # Resume button: green when clickable (currently paused)
            self.ui.resumeButton.setStyleSheet(
                STYLE_RESUME_ACTIVE if paused else STYLE_RESUME_INACTIVE
            )
            self.ui.resumeButton.setEnabled(paused)
        else:
            self.ui.pauseButton.setStyleSheet(STYLE_PAUSE_INACTIVE)
            self.ui.pauseButton.setEnabled(False)
            self.ui.resumeButton.setStyleSheet(STYLE_RESUME_INACTIVE)
            self.ui.resumeButton.setEnabled(False)

        self.ui.addButton.setEnabled((not self.is_running) or (self.is_running and self.live_sim and paused))
    # ── Live window ─────────────────────────────────────────────────────────

    def _live_window_exists(self):
        fig = self.live_fig
        if fig is None:
            return False
        num = getattr(fig, "number", None)
        return num is not None and plt.fignum_exists(num)

    def _ensure_live_window(self):
        if self._live_window_exists():
            return
        plt.ion()
        self.live_fig, self.live_ax = plt.subplots(figsize=(12, 3))
        try:
            mgr = getattr(self.live_fig.canvas, "manager", None)
            if mgr and hasattr(mgr, "set_window_title"):
                mgr.set_window_title("Live Gantt")
        except Exception:
            pass
        self.live_fig.show()

    def _redraw_live_window(self):
        fig, ax = self.live_fig, self.live_ax
        if fig is None or ax is None:
            return
        num = getattr(fig, "number", None)
        if num is None or not plt.fignum_exists(num):
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
        self.live_ax  = None

    # ── Running state ────────────────────────────────────────────────────────

    def _set_running_state(self, running):
        self.is_running = running

        self.ui.runButton.setEnabled(not running)
        self.ui.resetButton.setEnabled(not running)
        self.ui.dropdown_menu.setEnabled(not running)
        self.ui.checkBox.setEnabled(not running)

        if running and self.live_sim:
            self.ui.saveButton.setEnabled(True)
            self.ui.saveButton.setText("Live Gantt")
        else:
            self.ui.saveButton.setEnabled((not running) and (self.last_history is not None))
            self.ui.saveButton.setText("Display")

        self.ui.addButton.setEnabled(
            (not running) or (running and self.live_sim and not self.pause_event.is_set())
        )

        # Always sync button highlight after state change
        self._update_pause_resume_style()

    def _update_algo_specific_inputs(self):
        algo = self._selected_algo_key()
        self.ui.priority_label.setVisible("Priority" in algo)
        self.ui.priority_input.setVisible("Priority" in algo)
        self.ui.quantum_label.setVisible(algo == "Round Robin")
        self.ui.quantum_input.setVisible(algo == "Round Robin")

    # ── Button handlers ──────────────────────────────────────────────────────

    def _build_process_from_inputs(self, pid):
        algo    = self._selected_algo_key()
        arrival = self.ui.arrival_input.value()
        burst   = self.ui.burst_input.value()
        if burst <= 0:
            raise ValueError("Burst time must be greater than 0.")
        priority = self.ui.priority_input.value() if "Priority" in algo else None
        return Process(pid, arrival, burst, priority)

    def _on_add_clicked(self):
        try:
            pid     = self.current_pid + 1
            process = self._build_process_from_inputs(pid)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", str(exc))
            return

        if self.is_running:
            if not self.live_sim:
                QtWidgets.QMessageBox.information(
                    self, "Unavailable",
                    "Adding a process while running is only available in live simulation mode."
                )
                return
            if self.pause_event.is_set():
                QtWidgets.QMessageBox.information(
                    self, "Pause Required",
                    "Pause the simulation first, then add a process."
                )
                return
            self.current_pid = pid
            self.new_process_queue.put(process)
            self.original_bursts[process.num] = process.burst_time
            self._append_table_row(process.num, process.burst_time)
            self._append_log(f"⚡ P{process.num} queued for dynamic insertion.")
            return

        self.current_pid = pid
        self.pending_processes.append(process)
        self.original_bursts[process.num] = process.burst_time
        self._append_table_row(process.num, process.burst_time)
        self._append_log(f"✔ P{process.num} added (arrival={process.arrival_time}, burst={process.burst_time}).")

    def _on_run_clicked(self):
        if self.is_running:
            return
        if not self.pending_processes:
            QtWidgets.QMessageBox.information(
                self, "No Processes",
                "Add at least one process before running the simulation."
            )
            return

        selected_algo = self._selected_algo_key()
        try:
            run_fn = self._resolve_run_function(selected_algo)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Invalid Configuration", str(exc))
            return

        self.live_sim          = self.ui.checkBox.isChecked()
        self.new_process_queue = Queue()
        self.pause_event       = threading.Event()
        self.pause_event.set()

        processes_for_run = self._copy_processes_for_run()

        self.last_history      = None
        self.last_time_counter = 0
        self.last_att          = 0.0
        self.last_awt          = 0.0
        self.live_history      = []
        self.live_time_counter = 0

        # Reset remaining bursts to original
        for pid, burst in self.original_bursts.items():
            self.remaining_bursts[pid] = burst
            row = self.pid_to_row.get(pid)
            if row is not None:
                item = QtWidgets.QTableWidgetItem(str(burst))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.ui.tableWidget.setItem(row, 2, item)

        if self.live_sim:
            self._ensure_live_window()
            self._redraw_live_window()

        self.worker_thread = QtCore.QThread(self)
        self.worker        = SchedulerWorker(
            run_fn, processes_for_run,
            self.new_process_queue, self.live_sim, self.pause_event
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
        self._append_log(f"▶ Running {selected_algo}...")

    def _on_pause_clicked(self):
        if not self.is_running or not self.live_sim:
            return
        if not self.pause_event.is_set():
            return
        self.pause_event.clear()
        self._update_pause_resume_style()          # ← update highlight immediately
        self._append_log("⏸ Simulation paused.")

    def _on_resume_clicked(self):
        if not self.is_running or not self.live_sim:
            return
        if self.pause_event.is_set():
            return
        self.pause_event.set()
        self._update_pause_resume_style()          # ← update highlight immediately
        self._append_log("▶ Simulation resumed.")

    # ── Scheduler signal handlers ────────────────────────────────────────────

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
            item = QtWidgets.QTableWidgetItem(text)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            if finish_value is not None:
                item.setForeground(QtGui.QColor("#2DC653"))
            self.ui.tableWidget.setItem(row, 3, item)

    def _on_scheduler_progress(self, history, time_counter):
        """Called every tick — update Gantt and remaining burst times."""
        self.live_history      = list(history)
        self.live_time_counter = int(time_counter)

        # ── Compute remaining burst from history ──
        # Sum how long each process has already run
        time_run = {}
        for (pnum, start, end) in history:
            time_run[pnum] = time_run.get(pnum, 0) + (end - start)

        for pid, original in self.original_bursts.items():
            ran       = time_run.get(pid, 0)
            remaining = original - ran
            self._update_remaining_burst(pid, remaining)

        if self.live_sim:
            self._redraw_live_window()

    def _on_scheduler_finished(self, history, time_counter, att, awt):
        self.last_history      = list(history)
        self.last_time_counter = int(time_counter)
        self.last_att          = float(att)
        self.last_awt          = float(awt)
        self.live_history      = list(history)
        self.live_time_counter = int(time_counter)

        if self.live_sim:
            self._redraw_live_window()

        # Set all remaining bursts to 0
        for pid in self.pid_to_row:
            self._update_remaining_burst(pid, 0)

        finish_map = self._build_finish_map(history)
        self._update_finish_column(finish_map)

        self._append_log(f"✔ Average Turnaround Time : {self.last_att:.2f} sec")
        self._append_log(f"✔ Average Waiting Time    : {self.last_awt:.2f} sec")
        self._append_log("🏁 Simulation completed.")

        if not self.pause_event.is_set():
            self.pause_event.set()

        self._set_running_state(False)
        self.worker       = None
        self.worker_thread = None

    def _on_scheduler_failed(self, trace_text):
        self._set_running_state(False)
        self.worker        = None
        self.worker_thread = None
        QtWidgets.QMessageBox.critical(
            self, "Simulation Error",
            "The scheduler failed. See details in the log."
        )
        self._append_log("❌ Scheduler execution failed:")
        self._append_log(trace_text)

    def _on_display_clicked(self):
        if self.is_running:
            if self.live_sim:
                self._ensure_live_window()
                self._redraw_live_window()
                self._append_log("Opened live Gantt window.")
            else:
                QtWidgets.QMessageBox.information(
                    self, "Unavailable",
                    "Live Gantt is only available while a live simulation is running."
                )
            return

        if not self.last_history:
            QtWidgets.QMessageBox.information(
                self, "No Result",
                "Run a simulation first to display the Gantt chart."
            )
            return

        final_fig, final_ax = plt.subplots(figsize=(12, 3))
        draw_gantt(final_ax, self.last_history, self.last_time_counter)
        plt.show()
        self._append_log("📊 Displayed final Gantt chart.")

    def _on_reset_clicked(self):
        if self.is_running:
            QtWidgets.QMessageBox.information(
                self, "Simulation Running",
                "Wait until the simulation finishes before resetting."
            )
            return

        self.pending_processes.clear()
        self.original_bursts.clear()
        self.remaining_bursts.clear()
        self.pid_to_row.clear()
        self.current_pid       = 0
        self.new_process_queue = Queue()
        self.last_history      = None
        self.last_time_counter = 0
        self.last_att          = 0.0
        self.last_awt          = 0.0
        self.live_history      = []
        self.live_time_counter = 0
        self._close_live_window()
        self.pause_event = threading.Event()
        self.pause_event.set()

        self.ui.tableWidget.setRowCount(0)
        self.ui.textEdit.clear()
        self._set_running_state(False)
        self._append_log("🔄 State reset.")

    def closeEvent(self, event):
        if self.is_running:
            QtWidgets.QMessageBox.warning(
                self, "Simulation Running",
                "Please wait for the simulation to finish before closing."
            )
            event.ignore()
            return
        self._close_live_window()
        super().closeEvent(event)


## ── Entry point ─────────────────────────────────────────────────────────────

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = SchedulerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()