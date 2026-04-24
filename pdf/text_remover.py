"""
Surgical text removal module.
"""

import fitz
from typing import Tuple
from app.core.models import EditSpec, BBox
from app.core.logging import logger

def execute_remove_text(
    input_pdf_path: str,
    output_pdf_path: str,
    spec: EditSpec
) -> Tuple[bool, str]:
    """Removes text span specified in spec without painting broad white rectangles."""
    if not spec.target_bbox:
        return (False, "Target bounding box is required for text removal.")

    try:
        doc = fitz.open(input_pdf_path)
        if spec.page_num < 0 or spec.page_num >= doc.page_count:
            doc.close()
            return (False, f"Invalid page number {spec.page_num}.")

        page = doc[spec.page_num]
        rect = fitz.Rect(spec.target_bbox.tuple)

        # Redact the exact target bbox without painting white fill
        page.add_redact_annot(rect, fill=False)
        if hasattr(page, "apply_redactions"):
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        elif hasattr(page, "apply_redact_annot"):
            page.apply_redact_annot(images=fitz.PDF_REDACT_IMAGE_NONE)

        doc.save(output_pdf_path)
        doc.close()
        return (True, "Text removed surgically.")

    except Exception as e:
        logger.error(f"Failed to remove text: {e}")
        return (False, f"Error removing text: {e}")
