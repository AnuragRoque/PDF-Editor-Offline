"""
Properties Panel for inspecting selected text properties and applying surgical edits.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton, QGroupBox, QDoubleSpinBox, QComboBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Optional
from app.core.models import TextSpan, EditSpec, EditOperation
from app.pdf.fonts import get_fitz_font_name

class PropertiesPanel(QWidget):
    edit_requested = pyqtSignal(object)  # Emits EditSpec when Apply Edit is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_span: Optional[TextSpan] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        grp_spec = QGroupBox("Target Text Element Properties")
        form = QFormLayout(grp_spec)

        self.lbl_orig_text = QLineEdit()
        self.lbl_orig_text.setReadOnly(True)
        form.addRow("Original Text:", self.lbl_orig_text)

        self.txt_replacement = QLineEdit()
        self.txt_replacement.setPlaceholderText("Enter surgical replacement text...")
        form.addRow("Replacement Text:", self.txt_replacement)

        self.lbl_font = QLabel("-")
        form.addRow("Font Name:", self.lbl_font)

        self.lbl_size = QLabel("-")
        form.addRow("Font Size:", self.lbl_size)

        self.lbl_color = QLabel("-")
        form.addRow("Color:", self.lbl_color)

        self.lbl_bbox = QLabel("-")
        form.addRow("Bounding Box:", self.lbl_bbox)

        layout.addWidget(grp_spec)

        # Mode Selection
        grp_mode = QGroupBox("Edit Operation Mode")
        mode_layout = QHBoxLayout(grp_mode)
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["REPLACE", "ADD", "REMOVE"])
        mode_layout.addWidget(self.combo_mode)
        layout.addWidget(grp_mode)

        # Optional fit override controls
        grp_fit = QGroupBox("Manual Typography Fit Controls (Optional)")
        fit_form = QFormLayout(grp_fit)
        
        self.spin_font_size = QDoubleSpinBox()
        self.spin_font_size.setRange(1.0, 200.0)
        self.spin_font_size.setValue(12.0)
        fit_form.addRow("Override Font Size:", self.spin_font_size)

        self.spin_hscale = QDoubleSpinBox()
        self.spin_hscale.setRange(10.0, 300.0)
        self.spin_hscale.setValue(100.0)
        fit_form.addRow("Horizontal Scale (%):", self.spin_hscale)

        layout.addWidget(grp_fit)

        # Action Buttons
        self.btn_apply = QPushButton("Apply Surgical Edit")
        self.btn_apply.setStyleSheet("background-color: #007acc; color: white; font-weight: bold; padding: 8px;")
        self.btn_apply.clicked.connect(self._on_apply)
        layout.addWidget(self.btn_apply)

        layout.addStretch()

    def load_span(self, span: TextSpan):
        self.selected_span = span
        self.lbl_orig_text.setText(span.text)
        self.txt_replacement.setText(span.text)
        self.lbl_font.setText(span.font_name)
        self.lbl_size.setText(f"{span.font_size:.1f} pt")
        self.lbl_color.setText(span.color.hex_color)
        self.lbl_bbox.setText(f"({span.bbox.x0:.1f}, {span.bbox.y0:.1f}, {span.bbox.x1:.1f}, {span.bbox.y1:.1f})")
        self.spin_font_size.setValue(span.font_size)

    def _on_apply(self):
        if not self.selected_span:
            return

        mode_str = self.combo_mode.currentText()
        if mode_str == "REPLACE":
            op = EditOperation.REPLACE
        elif mode_str == "ADD":
            op = EditOperation.ADD
        else:
            op = EditOperation.REMOVE

        spec = EditSpec(
            page_num=self.selected_span.page_num,
            operation=op,
            target_span=self.selected_span,
            target_text=self.selected_span.text,
            replacement_text=self.txt_replacement.text(),
            target_bbox=self.selected_span.bbox,
            font_name=self.selected_span.font_name,
            font_size=self.selected_span.font_size,
            color=self.selected_span.color,
            origin=self.selected_span.origin,
            manual_font_size=self.spin_font_size.value() if abs(self.spin_font_size.value() - self.selected_span.font_size) > 0.1 else None,
            manual_hscale=self.spin_hscale.value()
        )

        self.edit_requested.emit(spec)
