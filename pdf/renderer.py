"""
High-resolution page rendering to PIL Image and QImage with caching support.
"""

import fitz
from PIL import Image, ImageDraw
import io
from typing import Tuple, Dict, Optional
from PyQt6.QtGui import QImage
from app.core.config import config
from app.core.models import BBox, ColorInfo
from app.core.logging import logger

class PDFRenderer:
    def __init__(self):
        self._cache: Dict[str, Image.Image] = {}

    def render_page_to_pil(
        self,
        doc: fitz.Document,
        page_num: int,
        dpi: int = config.render_dpi
    ) -> Image.Image:
        """Renders page_num (0-indexed) to PIL Image at given DPI."""
        cache_key = f"{doc.name}_{page_num}_{dpi}"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        if page_num < 0 or page_num >= doc.page_count:
            raise ValueError(f"Invalid page number {page_num} for document with {doc.page_count} pages.")

        page = doc[page_num]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Cache management
        if len(self._cache) > config.cache_max_pages:
            self._cache.clear()
        self._cache[cache_key] = img.copy()

        return img

    def render_page_to_qimage(
        self,
        doc: fitz.Document,
        page_num: int,
        dpi: int = config.render_dpi
    ) -> QImage:
        """Renders page_num to a safe, memory-independent PyQt6 QImage."""
        if page_num < 0 or page_num >= doc.page_count:
            return QImage()

        page = doc[page_num]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        return qimg.copy()  # Deep copy prevents dangling C++ pointer segfaults

    def draw_bbox_highlights(
        self,
        base_img: Image.Image,
        bboxes: list,
        color: str = "#007acc",
        width: int = 2,
        dpi: int = config.render_dpi
    ) -> Image.Image:
        """Overlays bounding box rectangles onto rendered image at correct scale."""
        img = base_img.copy().convert("RGBA")
        draw = ImageDraw.Draw(img)
        scale = dpi / 72.0

        for bbox in bboxes:
            if isinstance(bbox, BBox):
                bx0, by0, bx1, by1 = bbox.tuple
            else:
                bx0, by0, bx1, by1 = bbox

            x0 = bx0 * scale
            y0 = by0 * scale
            x1 = bx1 * scale
            y1 = by1 * scale

            # Draw semi-transparent fill + border line
            draw.rectangle([x0, y0, x1, y1], outline=color, width=width)

        return img.convert("RGB")

renderer = PDFRenderer()
