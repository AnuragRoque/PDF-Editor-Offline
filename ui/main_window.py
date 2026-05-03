"""
Master Main Window for Local Precision PDF Editor desktop application.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFileDialog,
    QToolBar, QStatusBar, QMessageBox, QLabel, QPushButton, QComboBox, QSpinBox,
    QProgressBar
)
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from pathlib import Path
import fitz
import traceback
from typing import Optional

from app.core.models import DocumentModel, TextSpan, EditSpec, ValidationReport, StrategyType
from app.pdf.analyzer import analyze_pdf_document
from app.pdf.loader import open_pdf_document
from app.editing.history import EditHistory
from app.editing.planner import plan_and_execute_edit
from app.ui.pdf_viewer import PDFViewerCanvas
from app.ui.text_panel import TextPanel
from app.ui.properties_panel import PropertiesPanel
from app.ui.comparison_view import ComparisonView
from app.ui.widgets.zoom_control import ZoomControl
from app.ui.dialogs import FontSubstitutionDialog, OverflowWarningDialog, TechnicalInspectorDialog
from app.core.logging import logger

class LoadDocumentWorker(QThread):
    finished_signal = pyqtSignal(bool, object, str)  # success, doc_model, error_msg

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            logger.info(f"Background thread parsing document: '{self.file_path}'")
            doc_model = analyze_pdf_document(self.file_path)
            self.finished_signal.emit(True, doc_model, "")
        except Exception as e:
            err_msg = f"Failed to analyze PDF '{self.file_path}': {e}\n{traceback.format_exc()}"
            logger.error(err_msg)
            self.finished_signal.emit(False, None, str(e))

class EditWorker(QThread):
    finished_signal = pyqtSignal(bool, str, object, object)

    def __init__(self, current_pdf: str, spec: EditSpec, preferred_strat=None):
        super().__init__()
        self.current_pdf = current_pdf
        self.spec = spec
        self.preferred_strat = preferred_strat

    def run(self):
        try:
            success, out_path, report, strat = plan_and_execute_edit(
                self.current_pdf, self.spec, self.preferred_strat
            )
            self.finished_signal.emit(success, out_path, report, strat)
        except Exception as e:
            logger.error(f"Background edit thread exception: {e}\n{traceback.format_exc()}")
            self.finished_signal.emit(False, self.current_pdf, ValidationReport(is_valid=False, overall_status="FAILED"), StrategyType.STRATEGY_2_PYMUPDF_REDACT_INSERT)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local Precision PDF Editor — Surgical Text Editing")
        self.resize(1280, 800)

        self.current_pdf_path: str = ""
        self.original_pdf_path: str = ""
        self.doc_model: Optional[DocumentModel] = None
        self.doc_fitz: Optional[fitz.Document] = None
        self.current_page_num: int = 0
        self.history: Optional[EditHistory] = None

        self._init_actions()
        self._init_menu()
        self._init_toolbar()
        self._init_ui()
        self._init_statusbar()

    def _init_actions(self):
        self.act_open = QAction("Open PDF...", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self._on_open_pdf)

        self.act_save_as = QAction("Save PDF As...", self)
        self.act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.act_save_as.triggered.connect(self._on_save_as)

        self.act_undo = QAction("Undo", self)
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.act_undo.setEnabled(False)
        self.act_undo.triggered.connect(self._on_undo)

        self.act_redo = QAction("Redo", self)
        self.act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.act_redo.setEnabled(False)
        self.act_redo.triggered.connect(self._on_redo)

        self.act_inspect = QAction("Technical Stream Inspector", self)
        self.act_inspect.triggered.connect(self._on_inspect_technical)

    def _init_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.act_open)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()

        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction(self.act_undo)
        edit_menu.addAction(self.act_redo)

        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction(self.act_inspect)

    def _init_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        toolbar.addAction(self.act_open)
        toolbar.addAction(self.act_save_as)
        toolbar.addSeparator()
        toolbar.addAction(self.act_undo)
        toolbar.addAction(self.act_redo)
        toolbar.addSeparator()

        # Page navigation
        toolbar.addWidget(QLabel(" Page: "))
        self.spin_page = QSpinBox()
        self.spin_page.setRange(1, 1)
        self.spin_page.valueChanged.connect(self._on_page_changed)
        toolbar.addWidget(self.spin_page)

        self.lbl_page_count = QLabel(" / 0 ")
        toolbar.addWidget(self.lbl_page_count)

        toolbar.addSeparator()
        # Zoom control
        self.zoom_ctrl = ZoomControl()
        self.zoom_ctrl.zoom_changed.connect(self._on_zoom_changed)
        toolbar.addWidget(self.zoom_ctrl)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Panel: Text List & Search
        self.text_panel = TextPanel()
        self.text_panel.span_selected.connect(self._on_span_selected_from_panel)
        splitter.addWidget(self.text_panel)

        # Center Panel: Canvas Viewer
        self.canvas = PDFViewerCanvas()
        self.canvas.span_clicked.connect(self._on_span_clicked_on_canvas)
        splitter.addWidget(self.canvas)

        # Right Panel: Properties Inspector
        self.prop_panel = PropertiesPanel()
        self.prop_panel.edit_requested.connect(self._on_edit_requested)
        splitter.addWidget(self.prop_panel)

        splitter.setSizes([300, 680, 300])
        main_layout.addWidget(splitter)

    def _init_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(140)
        self.progress_bar.setMaximum(0)  # Indeterminate mode
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)

        self.statusbar.showMessage("Ready. Open a PDF document to begin precision editing.")

    def _on_open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Text-Based PDF", "", "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        self._load_pdf_file(file_path)

    def _load_pdf_file(self, file_path: str):
        self.statusbar.showMessage(f"Analyzing PDF document baseline on background thread...")
        self.progress_bar.setVisible(True)

        self.load_worker = LoadDocumentWorker(file_path)
        self.load_worker.finished_signal.connect(lambda ok, model, err, fp=file_path: self._on_load_finished(ok, model, err, fp))
        self.load_worker.start()

    def _on_load_finished(self, success: bool, doc_model: Optional[DocumentModel], error_msg: str, file_path: str):
        self.progress_bar.setVisible(False)
        if hasattr(self, 'load_worker') and self.load_worker.isRunning():
            self.load_worker.wait()

        if not success or not doc_model:
            QMessageBox.critical(self, "Error Loading PDF", f"Failed to parse PDF document:\n{error_msg}")
            self.statusbar.showMessage("Error loading PDF document.")
            return

        if not doc_model.is_text_based:
            QMessageBox.warning(
                self,
                "Scanned PDF Warning",
                "This PDF does not contain reliable editable text. Scanned-PDF editing is not enabled for this project."
            )
            self.statusbar.showMessage("Image-only scanned PDF detected.")
            return

        try:
            self.original_pdf_path = file_path
            self.current_pdf_path = file_path
            self.doc_model = doc_model
            self.doc_fitz = open_pdf_document(file_path)
            self.history = EditHistory(file_path)

            self.spin_page.setMaximum(self.doc_model.page_count)
            self.lbl_page_count.setText(f" / {self.doc_model.page_count}")
            
            self.text_panel.load_document_model(self.doc_model)
            self._render_current_page()
            self._update_undo_redo_state()

            self.statusbar.showMessage(f"Loaded '{Path(file_path).name}' ({self.doc_model.page_count} pages, {sum(len(p.spans) for p in doc_model.pages)} text elements).")
        except Exception as e:
            logger.error(f"Error finalizing PDF load UI setup: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Error Displaying PDF", f"Failed to render document:\n{e}")

    def _render_current_page(self):
        if not self.doc_fitz or not self.doc_model:
            return

        page_idx = self.current_page_num
        spans = self.doc_model.pages[page_idx].spans if page_idx < len(self.doc_model.pages) else []
        self.canvas.load_page(self.doc_fitz, page_idx, spans)

    def _on_page_changed(self, value: int):
        self.current_page_num = value - 1
        self._render_current_page()

    def _on_zoom_changed(self, value: int):
        self.canvas.set_zoom(value)

    def _on_span_selected_from_panel(self, span: TextSpan):
        if span.page_num != self.current_page_num:
            self.spin_page.setValue(span.page_num + 1)
        self.canvas.highlight_span(span)
        self.prop_panel.load_span(span)

    def _on_span_clicked_on_canvas(self, span: TextSpan):
        self.text_panel.select_span(span)
        self.prop_panel.load_span(span)

    def _on_edit_requested(self, spec: EditSpec):
        if not self.current_pdf_path:
            return

        self.statusbar.showMessage(f"Executing surgical edit on Page {spec.page_num + 1}...")
        self.progress_bar.setVisible(True)

        # Launch Edit Worker thread
        self.edit_worker = EditWorker(self.current_pdf_path, spec)
        self.edit_worker.finished_signal.connect(self._on_edit_finished)
        self.edit_worker.start()

    def _on_edit_finished(self, success: bool, output_pdf_path: str, report: ValidationReport, strat: StrategyType):
        self.progress_bar.setVisible(False)
        if hasattr(self, 'edit_worker') and self.edit_worker.isRunning():
            self.edit_worker.wait()

        if success and report.is_valid:
            # Commit edit to history
            self.history.push_command(self.edit_worker.sender() if hasattr(self.edit_worker, 'sender') else None, output_pdf_path)
            self.current_pdf_path = output_pdf_path
            self.doc_fitz = fitz.open(output_pdf_path)
            
            # Reload doc_model asynchronously
            self._load_pdf_file(output_pdf_path)

            msg = (
                f"PDF EDITED\n\n"
                f"Validation:\n"
                f"  Structural   PASS\n"
                f"  Content      PASS\n"
                f"  Typography   PASS\n"
                f"  Geometry     PASS\n"
                f"  Visual       PASS\n\n"
                f"Unexpected differences: {report.unexpected_diff_pixels}"
            )
            QMessageBox.information(self, "Edit Passed Validation", msg)
            self.statusbar.showMessage(f"Edit committed via strategy '{strat.value}'. Unexpected diffs: {report.unexpected_diff_pixels}.")
        else:
            QMessageBox.warning(self, "Validation Failure", f"Edit failed validation layers.\nRolling back to last good source state.")
            self.statusbar.showMessage("Edit rolled back due to validation failure.")

    def _on_undo(self):
        if self.history and self.history.can_undo():
            prev_path = self.history.undo()
            if prev_path:
                self.current_pdf_path = prev_path
                self.doc_fitz = fitz.open(prev_path)
                self._load_pdf_file(prev_path)
                self.statusbar.showMessage("Undid last edit operation.")

    def _on_redo(self):
        if self.history and self.history.can_redo():
            next_path = self.history.redo()
            if next_path:
                self.current_pdf_path = next_path
                self.doc_fitz = fitz.open(next_path)
                self._load_pdf_file(next_path)
                self.statusbar.showMessage("Redid edit operation.")

    def _update_undo_redo_state(self):
        if self.history:
            self.act_undo.setEnabled(self.history.can_undo())
            self.act_redo.setEnabled(self.history.can_redo())

    def _on_save_as(self):
        if not self.current_pdf_path:
            return
        dest_path, _ = QFileDialog.getSaveFileName(self, "Save Edited PDF As", "", "PDF Files (*.pdf)")
        if dest_path:
            from app.pdf.writer import save_pdf_atomically
            if save_pdf_atomically(self.current_pdf_path, dest_path):
                QMessageBox.information(self, "Saved Successfully", f"PDF saved to:\n{dest_path}")

    def _on_inspect_technical(self):
        if not self.doc_model:
            return
        details = (
            f"Document Path: {self.current_pdf_path}\n"
            f"Page Count: {self.doc_model.page_count}\n"
            f"Text Spans: {sum(len(p.spans) for p in self.doc_model.pages)}\n"
            f"Fonts Catalog: {[f.name for f in self.doc_model.fonts]}\n"
        )
        dlg = TechnicalInspectorDialog(details, self)
        dlg.exec()
