import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QSlider,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

from logic.probability import theoretical_prob
from logic.simulation import run_single_sequence, run_many_simulations
from ui.liveplot import LivePlot


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bertrand Ballot Visualizer")
        self.resize(900, 600)

        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)

        # Top controls
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
        self.spin_trials.setRange(100, 2_000_000)
        self.spin_trials.setValue(10_000)
        ctrl.addWidget(self.spin_trials)

        ctrl.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 200)
        self.speed_slider.setValue(60)
        ctrl.addWidget(self.speed_slider)

        # Stats row
        stats = QHBoxLayout()
        layout.addLayout(stats)
        self.lbl_theo = QLabel("Theoretical P = -")
        self.lbl_emp = QLabel("Empirical P = -")
        self.lbl_status = QLabel("Status: Idle")
        stats.addWidget(self.lbl_theo)
        stats.addWidget(self.lbl_emp)
        stats.addWidget(self.lbl_status)

        # Vote counters
        bars = QHBoxLayout()
        layout.addLayout(bars)
        left = QVBoxLayout()
        right = QVBoxLayout()
        bars.addLayout(left, 1)
        bars.addLayout(right, 3)

        self.lbl_a_count = QLabel("A: 0")
        left.addWidget(self.lbl_a_count)
        self.bar_a = QProgressBar()
        left.addWidget(self.bar_a)

        self.lbl_b_count = QLabel("B: 0")
        left.addWidget(self.lbl_b_count)
        self.bar_b = QProgressBar()
        left.addWidget(self.bar_b)

        # Plot
        self.plot = LivePlot(self, width=6, height=4)
        right.addWidget(self.plot)

        # Signals
        self.btn_run_one.clicked.connect(self.start_single_run)
        self.btn_run_many.clicked.connect(self.start_many_runs)

        # Timer
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
        self.lbl_theo.setText(f"Theoretical P = {p:.6f}")

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

        self.bar_a.setRange(0, self.n_steps)
        self.bar_b.setRange(0, self.n_steps)
        self.bar_a.setValue(0)
        self.bar_b.setValue(0)
        self.lbl_a_count.setText("A: 0")
        self.lbl_b_count.setText("B: 0")

        self.plot.reset(self.n_steps)
        self.lbl_status.setText("Status: Running (animate)...")

        speed = max(1, 201 - self.speed_slider.value())
        self.timer.start(speed)

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
        step = self.idx + 1

        self.plot.add_point(step, lead)

        self.bar_a.setValue(self.a_count)
        self.bar_b.setValue(self.b_count)
        self.lbl_a_count.setText(f"A: {self.a_count}")
        self.lbl_b_count.setText(f"B: {self.b_count}")

        if lead <= 0 and self.failed_at is None:
            self.failed_at = step
            self.lbl_status.setText(f"FAILED at step {step}")

        self.idx += 1

    def finish_animation(self):
        self.timer.stop()

        if self.failed_at is None:
            self.lbl_status.setText("SUCCESS — A always led")

        self.btn_run_one.setEnabled(True)
        self.btn_run_many.setEnabled(True)

    def start_many_runs(self):
        a = self.spin_a.value()
        b = self.spin_b.value()
        trials = self.spin_trials.value()

        if a <= b:
            QMessageBox.warning(self, "Invalid", "Require a > b.")
            return

        self.update_theory_label()
        self.lbl_status.setText("Running Monte Carlo...")
        p_emp = run_many_simulations(a, b, trials)

        self.lbl_emp.setText(f"Empirical P = {p_emp:.6f}")

        p_theo = theoretical_prob(a, b)
        self.lbl_status.setText(f"Done. Theoretical={p_theo:.6f}, Empirical={p_emp:.6f}")

        QMessageBox.information(
            self, "Monte Carlo result",
            f"Trials: {trials}\nTheoretical P = {p_theo:.6f}\nEmpirical P = {p_emp:.6f}"
        )
