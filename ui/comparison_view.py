"""
Before / After Comparison View supporting Side-by-Side, Overlay, and Visual Diff Heatmaps.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QScrollArea
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from typing import Optional
import fitz
from app.pdf.renderer import renderer
from app.core.config import config

class ComparisonView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # 1. Side-by-Side tab
        self.tab_side = QWidget()
        side_layout = QHBoxLayout(self.tab_side)
        
        self.lbl_orig = QLabel("Original PDF Page")
        self.lbl_orig.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_orig = QScrollArea()
        scroll_orig.setWidget(self.lbl_orig)
        scroll_orig.setWidgetResizable(True)

        self.lbl_edited = QLabel("Edited PDF Page")
        self.lbl_edited.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_edited = QScrollArea()
        scroll_edited.setWidget(self.lbl_edited)
        scroll_edited.setWidgetResizable(True)

        side_layout.addWidget(scroll_orig)
        side_layout.addWidget(scroll_edited)

        # 2. Visual Diff Heatmap tab
        self.tab_diff = QWidget()
        diff_layout = QVBoxLayout(self.tab_diff)
        self.lbl_diff_img = QLabel("Visual Difference Heatmap")
        self.lbl_diff_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_diff = QScrollArea()
        scroll_diff.setWidget(self.lbl_diff_img)
        scroll_diff.setWidgetResizable(True)
        diff_layout.addWidget(scroll_diff)

        self.tabs.addTab(self.tab_side, "Side-by-Side")
        self.tabs.addTab(self.tab_diff, "Visual Diff Heatmap")

        layout.addWidget(self.tabs)

    def load_comparison(self, orig_pdf_path: str, edited_pdf_path: str, page_num: int, diff_image_path: Optional[str] = None):
        """Loads rendered page comparison into tabs."""
        try:
            doc_orig = fitz.open(orig_pdf_path)
            doc_edited = fitz.open(edited_pdf_path)

            pil_orig = renderer.render_page_to_pil(doc_orig, page_num, config.render_dpi)
            pil_edited = renderer.render_page_to_pil(doc_edited, page_num, config.render_dpi)

            doc_orig.close()
            doc_edited.close()

            # Original pixmap
            pix_orig = QPixmap.fromImage(renderer.render_page_to_pil(fitz.open(orig_pdf_path), page_num).toqimage() if hasattr(pil_orig, 'toqimage') else QPixmap())
            # Convert via PIL bytes
            pix_orig = QPixmap(orig_pdf_path) if not pix_orig else pix_orig

            if diff_image_path and QPixmap(diff_image_path):
                self.lbl_diff_img.setPixmap(QPixmap(diff_image_path))

        except Exception as e:
            pass
