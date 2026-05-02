"""
Zoom Control Widget for PDF Viewer.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt6.QtCore import Qt, pyqtSignal

class ZoomControl(QWidget):
    zoom_changed = pyqtSignal(int)  # Emits percentage e.g. 100

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.btn_out = QPushButton("-")
        self.btn_out.setFixedWidth(28)
        self.btn_out.clicked.connect(self._zoom_out)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(25, 400)
        self.slider.setValue(100)
        self.slider.setFixedWidth(120)
        self.slider.valueChanged.connect(self._on_slider_change)

        self.btn_in = QPushButton("+")
        self.btn_in.setFixedWidth(28)
        self.btn_in.clicked.connect(self._zoom_in)

        self.lbl_val = QLabel("100%")
        self.lbl_val.setFixedWidth(45)

        layout.addWidget(self.btn_out)
        layout.addWidget(self.slider)
        layout.addWidget(self.btn_in)
        layout.addWidget(self.lbl_val)

    def _zoom_in(self):
        val = min(400, self.slider.value() + 25)
        self.slider.setValue(val)

    def _zoom_out(self):
        val = max(25, self.slider.value() - 25)
        self.slider.setValue(val)

    def _on_slider_change(self, value: int):
        self.lbl_val.setText(f"{value}%")
        self.zoom_changed.emit(value)

    def set_zoom(self, value: int):
        self.slider.setValue(max(25, min(400, value)))
