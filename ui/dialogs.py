"""
UI Dialogs for Font Substitutions, Overflow Warnings, and Technical Stream Inspection.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QRadioButton, QButtonGroup, QTextEdit
)
from PyQt6.QtCore import Qt
from typing import List, Tuple, Optional

class FontSubstitutionDialog(QDialog):
    def __init__(self, original_font: str, candidates: List[Tuple[str, float]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Font Substitution Approval")
        self.setMinimumWidth(420)
        self.selected_font = candidates[0][0] if candidates else "Helvetica"
        self._init_ui(original_font, candidates)

    def _init_ui(self, original_font: str, candidates: List[Tuple[str, float]]):
        layout = QVBoxLayout(self)

        lbl_info = QLabel(
            f"<b>Original Font:</b> {original_font}<br>"
            "<b>Exact Local Font:</b> Not found / Subset embedded<br><br>"
            "Please select an approved replacement font candidate:"
        )
        layout.addWidget(lbl_info)

        self.list_widget = QListWidget()
        for cand_name, confidence in candidates:
            item_text = f"{cand_name} (Confidence: {confidence:.1f}%)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, cand_name)
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

        layout.addWidget(self.list_widget)

        btn_box = QHBoxLayout()
        btn_ok = QPushButton("Approve Font")
        btn_ok.clicked.connect(self._on_approve)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def _on_approve(self):
        curr_item = self.list_widget.currentItem()
        if curr_item:
            self.selected_font = curr_item.data(Qt.ItemDataRole.UserRole)
        self.accept()

class OverflowWarningDialog(QDialog):
    def __init__(self, target_width: float, est_width: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Text Overflow Warning")
        self.setMinimumWidth(440)
        self.action = "keep_size"
        self._init_ui(target_width, est_width)

    def _init_ui(self, target_width: float, est_width: float):
        layout = QVBoxLayout(self)

        lbl = QLabel(
            f"<b>OVERFLOW WARNING:</b> Replacement text exceeds original bounds.<br><br>"
            f"Target BBox Width: <b>{target_width:.1f} pt</b><br>"
            f"Estimated Text Width: <b>{est_width:.1f} pt</b><br><br>"
            "Select manual resolution strategy:"
        )
        layout.addWidget(lbl)

        self.btn_group = QButtonGroup(self)
        
        self.rb1 = QRadioButton("Keep Original Size & Bounds (Allow Overflow)")
        self.rb2 = QRadioButton("Manually Adjust Font Size to Fit")
        self.rb3 = QRadioButton("Cancel Edit")

        self.rb1.setChecked(True)

        self.btn_group.addButton(self.rb1, 1)
        self.btn_group.addButton(self.rb2, 2)
        self.btn_group.addButton(self.rb3, 3)

        layout.addWidget(self.rb1)
        layout.addWidget(self.rb2)
        layout.addWidget(self.rb3)

        btn_box = QHBoxLayout()
        btn_ok = QPushButton("Proceed")
        btn_ok.clicked.connect(self._on_ok)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)

    def _on_ok(self):
        sel_id = self.btn_group.checkedId()
        if sel_id == 1:
            self.action = "keep_size"
            self.accept()
        elif sel_id == 2:
            self.action = "manual_fit"
            self.accept()
        else:
            self.reject()

class TechnicalInspectorDialog(QDialog):
    def __init__(self, details_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PDF Technical Operator Inspector")
        self.resize(600, 450)

        layout = QVBoxLayout(self)
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setFontFamily("Consolas")
        self.txt.setText(details_text)
        layout.addWidget(self.txt)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
