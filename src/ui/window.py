from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QSlider, QProgressBar,
    QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from .liveplot import LivePlot
from src.core.ballot import theoretical_prob, run_single_sequence

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bertrand Ballot Visualizer")
        self.resize(950, 620)

        # Set stylesheet
        self.setStyleSheet("""
            QWidget {
                font-size: 12px;
                background: #ffffff;
            }
            QLabel {
                color: #222;
            }
            QPushButton {
                padding: 6px 12px;
                background-color: #0084FF;
                color: white;
                border-radius: 6px;
            }
            QPushButton:disabled {
                background-color: #aacfff;
            }
            QGroupBox {
                margin-top: 10px;
                padding: 10px;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                font-weight: bold;
                color: #333;
            }
            QProgressBar {
                height: 20px;
                border-radius: 4px;
                background: #e6e6e6;
            }
            QProgressBar::chunk {
                background-color: #0084FF;
                border-radius: 4px;
            }
        """)

        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        ctrl = QHBoxLayout()
        ctrl.setSpacing(12)
        layout.addLayout(ctrl)

        ctrl.addWidget(QLabel("A votes:"))
        self.spin_a = QSpinBox()
        self.spin_a.setRange(1, 1000)
        self.spin_a.setValue(7)
        ctrl.addWidget(self.spin_a)

        ctrl.addSpacing(10)

        ctrl.addWidget(QLabel("B votes:"))
        self.spin_b = QSpinBox()
        self.spin_b.setRange(0, 999)
        self.spin_b.setValue(3)
        ctrl.addWidget(self.spin_b)

        ctrl.addSpacing(15)

        ctrl.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.setFixedWidth(150)
        ctrl.addWidget(self.speed_slider)

        self.speed_label = QLabel("50%")
        ctrl.addWidget(self.speed_label)

        ctrl.addStretch(1)

        self.btn_run_one = QPushButton("Run")
        ctrl.addWidget(self.btn_run_one)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        ctrl.addWidget(self.btn_stop)

        # Probability 
        self.lbl_theo = QLabel("P = ")
        layout.addWidget(self.lbl_theo)

        # Counts of A/B
        grp = QGroupBox("Counts")
        gbox = QVBoxLayout(grp)
        gbox.setSpacing(6)
        layout.addWidget(grp)

        # A
        self.lbl_a_count = QLabel("A: 0")
        gbox.addWidget(self.lbl_a_count)

        self.bar_a = QProgressBar()
        self.bar_a.setFixedHeight(20)
        gbox.addWidget(self.bar_a)

        # B
        self.lbl_b_count = QLabel("B: 0")
        gbox.addWidget(self.lbl_b_count)

        self.bar_b = QProgressBar()
        self.bar_b.setFixedHeight(20)
        gbox.addWidget(self.bar_b)

        # Plot
        self.plot = LivePlot(self, width=6, height=4)
        layout.addWidget(self.plot, stretch=1)
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_step)
        self.btn_run_one.clicked.connect(self.start_single_run)
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v}%")
        )
        self.btn_stop.clicked.connect(self.stop_animation)
        self.current_votes = []
        self.idx = 0
        self.a_count = 0
        self.b_count = 0

    def update_theory_label(self):
        a = self.spin_a.value()
        b = self.spin_b.value()
        p = theoretical_prob(a, b)
        self.lbl_theo.setText(f"P = {p:.2f}")

    def start_single_run(self):
        a = self.spin_a.value()
        b = self.spin_b.value()
        self.update_theory_label()
        self.current_votes = run_single_sequence(a, b)
        self.n_steps = len(self.current_votes)
        self.idx = 0
        self.a_count = 0
        self.b_count = 0
        self.bar_a.setRange(0, self.n_steps)
        self.bar_b.setRange(0, self.n_steps)
        self.bar_a.setValue(0)
        self.bar_b.setValue(0)
        self.lbl_a_count.setText("A: 0")
        self.lbl_b_count.setText("B: 0")
        self.plot.reset(self.n_steps)
        
        speed_percent = self.speed_slider.value()
        max_delay = 200
        interval_ms = max_delay - int((speed_percent / 100) * (max_delay - 1))
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