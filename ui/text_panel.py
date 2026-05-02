"""
Text Panel displaying searchable document text items and selection tree.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import List, Dict
from app.core.models import DocumentModel, TextSpan, PageModel

class TextPanel(QWidget):
    span_selected = pyqtSignal(object)  # Emits TextSpan when item clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.doc_model: Optional[DocumentModel] = None

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        lbl_title = QLabel("<b>Detected Text Elements</b>")
        layout.addWidget(lbl_title)

        # Search bar
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search text on pages...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_box.addWidget(self.search_input)
        layout.addLayout(search_box)

        # Match count label
        self.lbl_matches = QLabel("0 elements")
        layout.addWidget(self.lbl_matches)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Page / Text", "Font", "Size"])
        self.tree.setColumnWidth(0, 160)
        self.tree.setColumnWidth(1, 100)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

    def load_document_model(self, doc_model: DocumentModel):
        self.doc_model = doc_model
        self.search_input.clear()
        self.populate_tree()

    def populate_tree(self, filter_text: str = ""):
        self.tree.clear()
        if not self.doc_model:
            return

        total_count = 0
        filter_lower = filter_text.lower().strip()

        for page in self.doc_model.pages:
            page_item = QTreeWidgetItem([f"Page {page.page_num + 1} ({len(page.spans)} items)"])
            page_item.setExpanded(True)
            
            matching_spans = 0
            for span in page.spans:
                if filter_lower and filter_lower not in span.text.lower():
                    continue

                span_item = QTreeWidgetItem([
                    span.text,
                    span.font_name,
                    f"{span.font_size:.1f} pt"
                ])
                span_item.setData(0, Qt.ItemDataRole.UserRole, span)
                page_item.addChild(span_item)
                matching_spans += 1
                total_count += 1

            if matching_spans > 0:
                self.tree.addTopLevelItem(page_item)

        self.lbl_matches.setText(f"{total_count} matching elements")

    def _on_search_changed(self, text: str):
        self.populate_tree(text)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        span = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(span, TextSpan):
            self.span_selected.emit(span)

    def select_span(self, span: TextSpan):
        """Programmatically selects span in tree."""
        for i in range(self.tree.topLevelItemCount()):
            page_item = self.tree.topLevelItem(i)
            for j in range(page_item.childCount()):
                child = page_item.child(j)
                if child.data(0, Qt.ItemDataRole.UserRole) == span:
                    self.tree.setCurrentItem(child)
                    return
