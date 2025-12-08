# bernard_ballot_ui.py
# Requires: PyQt6, matplotlib
# pip install PyQt6 matplotlib

import sys
import random
from functools import partial

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QSlider, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


def theoretical_prob(a: int, b: int) -> float:
    if a <= b:
        return 0.0
    return (a - b) / (a + b)


def run_single_sequence(a: int, b: int):
    votes = ['A'] * a + ['B'] * b
    random.shuffle(votes)
    return votes


def run_many_simulations(a: int, b: int, trials: int):
    if a <= b:
        return 0.0
    success = 0
    for _ in range(trials):
        votes = run_single_sequence(a, b)
        a_count = 0
        b_count = 0
        ok = True
        for v in votes:
            if v == 'A':
                a_count += 1
            else:
                b_count += 1
            if a_count <= b_count:
                ok = False
                break
        if ok:
            success += 1
    return success / trials


class LivePlot(FigureCanvas):
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel("Ballots counted")
        self.ax.set_ylabel("Lead (A - B)")
        self.line, = self.ax.plot([], [], marker='o')
        self.ax.axhline(0, color='gray', linewidth=0.8)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(-1, 1)
        self.fig = fig

    def reset(self, n_steps):
        self.xdata = []
        self.ydata = []
        self.line.set_data([], [])
        self.ax.set_xlim(0, max(1, n_steps))
        # dynamic y limits will be set as we go
        self.ax.set_ylim(-max(1, n_steps//2), max(1, n_steps//2))
        self.draw()

    def add_point(self, step, lead):
        self.xdata.append(step)
        self.ydata.append(lead)
        self.line.set_data(self.xdata, self.ydata)
        # adjust y-limits if needed
        ymin, ymax = self.ax.get_ylim()
        if lead <= ymin + 1 or lead >= ymax - 1:
            rng = max(1, int(max(abs(lead), abs(ymin), abs(ymax)) * 1.2))
            self.ax.set_ylim(-rng, rng)
        self.ax.set_xlim(0, max(10, step + 1))
        self.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bertrand Ballot Visualizer")
        self.resize(900, 600)

        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout()
        main.setLayout(layout)

        # Top control panel
        ctrl = QHBoxLayout()
        layout.addLayout(ctrl)

        ctrl.addWidget(QLabel("A votes:"))
        self.spin_a = QSpinBox()
        self.spin_a.setRange(1, 1000)
        self.spin_a.setValue(7)
        ctrl.addWidget(self.spin_a)

        ctrl.addWidget(QLabel("B votes:"))
        self.spin_b = QSpinBox()
        self.spin_b.setRange(0, 999)
        self.spin_b.setValue(3)
        ctrl.addWidget(self.spin_b)

        self.btn_run_one = QPushButton("Run Single (Animate)")
        ctrl.addWidget(self.btn_run_one)

        self.btn_run_many = QPushButton("Run Many (Monte Carlo)")
        ctrl.addWidget(self.btn_run_many)

        ctrl.addWidget(QLabel("Trials:"))
        self.spin_trials = QSpinBox()
        self.spin_trials.setRange(100, 2000000)
        self.spin_trials.setValue(10000)
        ctrl.addWidget(self.spin_trials)

        ctrl.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 200)  # smaller -> faster
        self.speed_slider.setValue(60)
        ctrl.addWidget(self.speed_slider)

        # Stats labels
        stats = QHBoxLayout()
        layout.addLayout(stats)
        self.lbl_theo = QLabel("Theoretical P = -")
        stats.addWidget(self.lbl_theo)
        self.lbl_emp = QLabel("Empirical P = -")
        stats.addWidget(self.lbl_emp)
        self.lbl_status = QLabel("Status: Idle")
        stats.addWidget(self.lbl_status)

        # Bars and counts
        bars = QHBoxLayout()
        layout.addLayout(bars)
        left = QVBoxLayout()
        right = QVBoxLayout()
        bars.addLayout(left, stretch=1)
        bars.addLayout(right, stretch=3)

        self.lbl_a_count = QLabel("A: 0")
        left.addWidget(self.lbl_a_count)
        self.bar_a = QProgressBar()
        self.bar_a.setRange(0, 100)
        left.addWidget(self.bar_a)

        self.lbl_b_count = QLabel("B: 0")
        left.addWidget(self.lbl_b_count)
        self.bar_b = QProgressBar()
        self.bar_b.setRange(0, 100)
        left.addWidget(self.bar_b)

        # Plot
        self.plot = LivePlot(self, width=6, height=4)
        right.addWidget(self.plot)

        # Connections
        self.btn_run_one.clicked.connect(self.start_single_run)
        self.btn_run_many.clicked.connect(self.start_many_runs)

        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_step)
        self.current_votes = []
        self.idx = 0
        self.a_count = 0
        self.b_count = 0
        self.n_steps = 0
        self.failed_at = None

    def update_theory_label(self):
        a = self.spin_a.value()
        b = self.spin_b.value()
        p = theoretical_prob(a, b)
        self.lbl_theo.setText(f"Theoretical P = {p:.6f}  ( (a-b)/(a+b) )")

    def start_single_run(self):
        a = self.spin_a.value()
        b = self.spin_b.value()
        if a <= b:
            QMessageBox.warning(self, "Invalid", "Require a > b for positive probability.")
            return
        self.update_theory_label()

        self.current_votes = run_single_sequence(a, b)
        self.n_steps = len(self.current_votes)
        self.idx = 0
        self.a_count = 0
        self.b_count = 0
        self.failed_at = None

        # setup bars
        self.bar_a.setRange(0, self.n_steps)
        self.bar_b.setRange(0, self.n_steps)
        self.bar_a.setValue(0)
        self.bar_b.setValue(0)
        self.lbl_a_count.setText("A: 0")
        self.lbl_b_count.setText("B: 0")
        self.plot.reset(self.n_steps)
        self.lbl_status.setText("Status: Running (animate)...")

        # start timer
        sp = max(1, 201 - self.speed_slider.value())  # invert speed slider to ms interval
        self.timer.start(sp)

        # disable buttons while animating
        self.btn_run_one.setEnabled(False)
        self.btn_run_many.setEnabled(False)

    def animate_step(self):
        if self.idx >= self.n_steps:
            self.finish_animation()
            return
        v = self.current_votes[self.idx]
        if v == 'A':
            self.a_count += 1
        else:
            self.b_count += 1

        lead = self.a_count - self.b_count
        step_num = self.idx + 1
        self.plot.add_point(step_num, lead)
        self.bar_a.setValue(self.a_count)
        self.bar_b.setValue(self.b_count)
        self.lbl_a_count.setText(f"A: {self.a_count}")
        self.lbl_b_count.setText(f"B: {self.b_count}")

        # check fail condition: A must be strictly greater than B at all times
        if lead <= 0 and self.failed_at is None:
            self.failed_at = step_num
            # highlight and stop or continue to show path (we'll continue but mark)
            self.lbl_status.setText(f"Status: FAILED at step {self.failed_at} (A not leading)")
            # Optionally stop immediately:
            # self.timer.stop()
            # self.finish_animation()
            # return

        self.idx += 1

    def finish_animation(self):
        self.timer.stop()
        if self.failed_at is None:
            self.lbl_status.setText("Status: SUCCESS — A always led during count")
        # re-enable buttons
        self.btn_run_one.setEnabled(True)
        self.btn_run_many.setEnabled(True)

    def start_many_runs(self):
        a = self.spin_a.value()
        b = self.spin_b.value()
        trials = self.spin_trials.value()
        if a <= b:
            QMessageBox.warning(self, "Invalid", "Require a > b for positive probability.")
            return
        self.update_theory_label()
        self.lbl_status.setText("Status: Running Monte Carlo ...")
        QApplication.processEvents()

        emp = run_many_simulations(a, b, trials)
        self.lbl_emp.setText(f"Empirical P (trials={trials}) = {emp:.6f}")
        theo = theoretical_prob(a, b)
        self.lbl_status.setText(f"Done. Theoretical={theo:.6f}, Empirical={emp:.6f}")

        # quick popup with result
        QMessageBox.information(self, "Monte Carlo result",
                                f"Trials: {trials}\nTheoretical P = {theo:.6f}\nEmpirical P = {emp:.6f}")

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
