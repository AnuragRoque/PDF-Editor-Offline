"""
Text insertion module with nearby typography style inference.
"""

import fitz
from typing import Tuple, Optional, Dict, Any
from app.core.models import EditSpec, TextSpan, ColorInfo, BBox
from app.pdf.fonts import get_fitz_font_name
from app.pdf.text_detector import extract_page_text_spans
from app.core.logging import logger

def infer_nearby_style(spans: list, target_x: float, target_y: float) -> Dict[str, Any]:
    """Infers font, size, and color from the closest text span on page."""
    if not spans:
        return {
            "font_name": "Helvetica",
            "font_size": 12.0,
            "color": ColorInfo(0.0, 0.0, 0.0)
        }

    closest_span = spans[0]
    min_dist = float('inf')

    for span in spans:
        # Distance to bbox center
        cx = (span.bbox.x0 + span.bbox.x1) / 2.0
        cy = (span.bbox.y0 + span.bbox.y1) / 2.0
        dist = ((cx - target_x) ** 2 + (cy - target_y) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            closest_span = span

    return {
        "font_name": closest_span.font_name,
        "font_size": closest_span.font_size,
        "color": closest_span.color
    }

def execute_add_text(
    input_pdf_path: str,
    output_pdf_path: str,
    spec: EditSpec
) -> Tuple[bool, str]:
    """Inserts new text onto target page at specified origin coordinates."""
    try:
        doc = fitz.open(input_pdf_path)
        if spec.page_num < 0 or spec.page_num >= doc.page_count:
            doc.close()
            return (False, f"Invalid page number {spec.page_num}.")

        page = doc[spec.page_num]

        # Use origin or bbox x0, y1
        x = spec.origin[0] if spec.origin else (spec.target_bbox.x0 if spec.target_bbox else 72.0)
        y = spec.origin[1] if spec.origin else (spec.target_bbox.y1 if spec.target_bbox else 72.0)

        fitz_font = get_fitz_font_name(spec.font_name)
        color_tuple = (spec.color.r, spec.color.g, spec.color.b) if spec.color else (0.0, 0.0, 0.0)
        font_size = spec.manual_font_size or spec.font_size

        page.insert_text(
            fitz.Point(x, y),
            spec.replacement_text,
            fontname=fitz_font,
            fontsize=font_size,
            color=color_tuple,
            overlay=True
        )

        doc.save(output_pdf_path)
        doc.close()
        return (True, "Text added successfully.")

    except Exception as e:
        logger.error(f"Failed to add text: {e}")
        return (False, f"Error adding text: {e}")
