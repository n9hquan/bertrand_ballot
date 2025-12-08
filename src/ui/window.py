from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QSlider, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

from .liveplot import LivePlot
from src.core.ballot import theoretical_prob, run_single_sequence


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bertrand Ballot Visualizer")
        self.resize(900, 600)

        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout()
        main.setLayout(layout)

        # Controls row
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

        self.btn_run_one = QPushButton("Run Animation")
        ctrl.addWidget(self.btn_run_one)

        ctrl.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(50)
        ctrl.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("50%")
        self.speed_label.setMinimumWidth(35)
        ctrl.addWidget(self.speed_label)
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v}%")
        )
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        ctrl.addWidget(self.btn_stop)

        # Single label: theoretical probability
        stats = QHBoxLayout()
        layout.addLayout(stats)
        self.lbl_theo = QLabel("Theoretical P = -")
        stats.addWidget(self.lbl_theo)

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
        left.addWidget(self.bar_a)

        self.lbl_b_count = QLabel("B: 0")
        left.addWidget(self.lbl_b_count)
        self.bar_b = QProgressBar()
        left.addWidget(self.bar_b)

        # Plot area
        self.plot = LivePlot(self, width=6, height=4)
        right.addWidget(self.plot)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_step)

        # Button connection
        self.btn_run_one.clicked.connect(self.start_single_run)

        # State
        self.current_votes = []
        self.idx = 0
        self.a_count = 0
        self.b_count = 0
        self.n_steps = 0
        
        self.btn_stop.clicked.connect(self.stop_animation)

    def update_theory_label(self):
        a = self.spin_a.value()
        b = self.spin_b.value()
        p = theoretical_prob(a, b)
        self.lbl_theo.setText(f"Theoretical P = {p:.6f}")

    def start_single_run(self):
        a = self.spin_a.value()
        b = self.spin_b.value()
        if a <= b:
            QMessageBox.warning(self, "Invalid", "Require a > b.")
            return

        self.update_theory_label()

        self.current_votes = run_single_sequence(a, b)
        self.n_steps = len(self.current_votes)
        self.idx = 0
        self.a_count = 0
        self.b_count = 0

        # Bars
        self.bar_a.setRange(0, self.n_steps)
        self.bar_b.setRange(0, self.n_steps)
        self.bar_a.setValue(0)
        self.bar_b.setValue(0)

        self.lbl_a_count.setText("A: 0")
        self.lbl_b_count.setText("B: 0")

        self.plot.reset(self.n_steps)

        # compute delay: slider 1-100%, where 100% = fastest
        speed_percent = self.speed_slider.value()
        max_delay = 200
        interval_ms = max_delay - int((speed_percent / 100) * (max_delay - 1))

        # IMPORTANT: stop old timer before starting new
        if self.timer.isActive():
            self.timer.stop()

        self.timer.start(interval_ms)

        self.btn_run_one.setEnabled(False)
        self.btn_stop.setEnabled(True)

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

        self.idx += 1

    def finish_animation(self):
        if self.timer.isActive():
            self.timer.stop()

        self.btn_run_one.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
    def stop_animation(self):
        if self.timer.isActive():
            self.timer.stop()

        self.btn_run_one.setEnabled(True)
        self.btn_stop.setEnabled(False)