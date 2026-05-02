"""
PyQt6 PDF Canvas Viewer with mouse text selection overlays and zoom support.
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PyQt6.QtGui import QPixmap, QImage, QPen, QColor, QBrush, QMouseEvent, QPainter
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
import fitz
from typing import List, Optional
from app.core.models import TextSpan, BBox
from app.pdf.renderer import renderer
from app.core.config import config
from app.core.logging import logger

class PDFViewerCanvas(QGraphicsView):
    span_clicked = pyqtSignal(object)  # Emits TextSpan when clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.doc: Optional[fitz.Document] = None
        self.current_page_num: int = 0
        self.spans: List[TextSpan] = []
        self.selected_span: Optional[TextSpan] = None
        self.zoom_factor: float = 1.0

        self.pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.rect_items: List[QGraphicsRectItem] = []
        self.selected_rect_item: Optional[QGraphicsRectItem] = None

    def load_page(self, doc: fitz.Document, page_num: int, spans: List[TextSpan]):
        """Loads and renders target page onto QGraphicsScene."""
        self.doc = doc
        self.current_page_num = page_num
        self.spans = spans
        self.selected_span = None

        self.scene.clear()
        self.rect_items.clear()
        self.selected_rect_item = None

        if not self.doc or page_num < 0 or page_num >= doc.page_count:
            return

        try:
            qimg = renderer.render_page_to_qimage(self.doc, page_num, config.render_dpi)
            pixmap = QPixmap.fromImage(qimg)
            self.pixmap_item = self.scene.addPixmap(pixmap)

            # Add text bounding box overlays
            scale = config.render_dpi / 72.0
            pen = QPen(QColor(0, 122, 204, 160), 1.5)
            brush = QBrush(QColor(0, 122, 204, 25))

            for span in spans:
                bx0, by0, bx1, by1 = span.bbox.tuple
                rect_f = QRectF(bx0 * scale, by0 * scale, span.bbox.width * scale, span.bbox.height * scale)
                r_item = self.scene.addRect(rect_f, pen, brush)
                r_item.setData(0, span)
                self.rect_items.append(r_item)
        except Exception as e:
            logger.error(f"Error loading page {page_num+1} onto canvas: {e}")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.pixmap_item:
            scene_pos = self.mapToScene(event.pos())
            scale = config.render_dpi / 72.0
            doc_x = scene_pos.x() / scale
            doc_y = scene_pos.y() / scale

            # Find matching text span
            clicked_span = None
            for span in self.spans:
                if span.bbox.x0 <= doc_x <= span.bbox.x1 and span.bbox.y0 <= doc_y <= span.bbox.y1:
                    clicked_span = span
                    break

            if clicked_span:
                self.highlight_span(clicked_span)
                self.span_clicked.emit(clicked_span)

        super().mousePressEvent(event)

    def highlight_span(self, span: TextSpan):
        """Highlights selected span with a distinct yellow/orange border."""
        self.selected_span = span
        scale = config.render_dpi / 72.0

        if self.selected_rect_item:
            self.scene.removeItem(self.selected_rect_item)
            self.selected_rect_item = None

        bx0, by0, bx1, by1 = span.bbox.tuple
        rect_f = QRectF(bx0 * scale - 2, by0 * scale - 2, span.bbox.width * scale + 4, span.bbox.height * scale + 4)
        
        pen = QPen(QColor(255, 140, 0, 255), 2.5)
        brush = QBrush(QColor(255, 200, 0, 60))
        self.selected_rect_item = self.scene.addRect(rect_f, pen, brush)

    def set_zoom(self, zoom_percent: int):
        factor = zoom_percent / 100.0
        self.resetTransform()
        self.scale(factor, factor)
        self.zoom_factor = factor
