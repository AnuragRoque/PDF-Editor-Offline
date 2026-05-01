"""
Layer 5: Visual Validation comparing rendered pages under controlled DPI.
"""

import fitz
import os
from typing import Optional
from app.core.models import EditSpec, ValidationLayerResult
from app.core.config import config
from app.pdf.renderer import renderer
from app.validation.diff import compute_visual_diff
from app.pdf.writer import create_temp_pdf_path

def validate_visual(
    orig_pdf_path: str,
    edited_pdf_path: str,
    spec: EditSpec
) -> ValidationLayerResult:
    """
    Renders before and after pages at visual_diff_dpi, applies expected_bbox mask,
    and counts unexpected pixel differences.
    """
    try:
        doc_orig = fitz.open(orig_pdf_path)
        doc_edited = fitz.open(edited_pdf_path)

        p_num = spec.page_num
        if p_num >= doc_orig.page_count or p_num >= doc_edited.page_count:
            doc_orig.close()
            doc_edited.close()
            return ValidationLayerResult("Visual", False, ["Page number out of bounds."], {})

        img_orig = renderer.render_page_to_pil(doc_orig, p_num, config.visual_diff_dpi)
        img_edited = renderer.render_page_to_pil(doc_edited, p_num, config.visual_diff_dpi)

        doc_orig.close()
        doc_edited.close()

        unexpected_pixels, diff_img = compute_visual_diff(
            img_orig,
            img_edited,
            expected_bbox=spec.target_bbox,
            dpi=config.visual_diff_dpi
        )

        # Save diff heatmap to temp file
        diff_path = create_temp_pdf_path(prefix="diff_").replace(".pdf", ".png")
        diff_img.save(diff_path)

        passed = unexpected_pixels <= config.visual_max_unexpected_pixels
        errors = []
        if not passed:
            errors.append(f"Visual validation failed: {unexpected_pixels} unexpected diff pixels found outside target bounding box!")

        return ValidationLayerResult(
            layer_name="Visual",
            passed=passed,
            errors=errors,
            warnings=[],
            details={
                "unexpected_pixels": unexpected_pixels,
                "diff_image_path": diff_path
            }
        )
    except Exception as e:
        return ValidationLayerResult("Visual", False, [f"Visual validation exception: {e}"], {})
