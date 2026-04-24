"""
Multi-strategy surgical text replacement engine with tight baseline redaction.
"""

import fitz
import pikepdf
from typing import Tuple, Optional
from app.core.models import EditSpec, StrategyType, BBox, ColorInfo
from app.core.exceptions import PDFEditorError, FontError
from app.pdf.content_stream import patch_content_stream_text
from app.pdf.fonts import get_fitz_font_name, clean_font_name
from app.pdf.geometry import check_text_overflow, calculate_fit_font_size
from app.core.logging import logger

def compute_tight_redact_rect(spec: EditSpec) -> fitz.Rect:
    """
    Computes a tight baseline redaction rectangle around target_bbox.
    Shrinks vertical top/bottom bounds to prevent touching ascenders/descenders of lines above or below.
    """
    bbox = spec.target_bbox
    if not bbox:
        return fitz.Rect(0, 0, 0, 0)

    # Use baseline origin if available
    if spec.origin and spec.font_size > 0:
        origin_y = spec.origin[1]
        top_y = max(bbox.y0 + 0.5, origin_y - (spec.font_size * 0.78))
        bottom_y = min(bbox.y1 - 0.5, origin_y + (spec.font_size * 0.18))
        return fitz.Rect(bbox.x0 + 0.2, top_y, bbox.x1 - 0.2, bottom_y)

    # Fallback tight crop (inset vertical by 1.2pt)
    top_y = bbox.y0 + 1.2 if bbox.height > 6.0 else bbox.y0
    bottom_y = bbox.y1 - 1.2 if bbox.height > 6.0 else bbox.y1
    return fitz.Rect(bbox.x0 + 0.2, top_y, bbox.x1 - 0.2, bottom_y)

def execute_replace_strategy(
    input_pdf_path: str,
    output_pdf_path: str,
    spec: EditSpec,
    strategy: StrategyType = StrategyType.STRATEGY_2_PYMUPDF_REDACT_INSERT
) -> Tuple[bool, StrategyType, str]:
    """
    Executes surgical text replacement using specified strategy.
    Returns (success, strategy_used, message).
    """
    if not spec.target_bbox:
        return (False, strategy, "Target bounding box is required for text replacement.")

    # Check Strategy 1: Direct Content Stream Patching
    if strategy == StrategyType.STRATEGY_1_STREAM_PATCH:
        success = patch_content_stream_text(
            input_pdf_path,
            output_pdf_path,
            spec.page_num,
            spec.target_text,
            spec.replacement_text
        )
        if success:
            return (True, StrategyType.STRATEGY_1_STREAM_PATCH, "Direct content stream patch successful.")
        # Fallback to Strategy 2
        strategy = StrategyType.STRATEGY_2_PYMUPDF_REDACT_INSERT

    # Strategy 2 / 4: Redaction & Re-insertion
    try:
        doc = fitz.open(input_pdf_path)
        if spec.page_num < 0 or spec.page_num >= doc.page_count:
            doc.close()
            return (False, strategy, f"Invalid page number {spec.page_num}.")

        page = doc[spec.page_num]
        
        # Calculate tight baseline redaction rect to avoid destroying adjacent lines
        rect = compute_tight_redact_rect(spec)

        # Redact only the exact target bbox baseline
        page.add_redact_annot(rect, fill=False)  # Transparent fill retains background
        if hasattr(page, "apply_redactions"):
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        elif hasattr(page, "apply_redact_annot"):
            page.apply_redact_annot(images=fitz.PDF_REDACT_IMAGE_NONE)

        # Infer bold & italic font flags
        is_bold = False
        is_italic = False
        if spec.target_span:
            is_bold = spec.target_span.is_bold
            is_italic = spec.target_span.is_italic
        else:
            font_lower = spec.font_name.lower()
            is_bold = "bold" in font_lower or "black" in font_lower or "heavy" in font_lower
            is_italic = "italic" in font_lower or "oblique" in font_lower

        font_size = spec.manual_font_size or spec.font_size
        fitz_font = get_fitz_font_name(spec.font_name, is_bold=is_bold, is_italic=is_italic)

        # Color
        color_tuple = (0, 0, 0)
        if spec.color:
            color_tuple = (spec.color.r, spec.color.g, spec.color.b)

        # Text insertion point (baseline origin)
        if spec.origin:
            origin_pt = fitz.Point(spec.origin[0] + spec.manual_offset_x, spec.origin[1] + spec.manual_offset_y)
        else:
            origin_pt = fitz.Point(spec.target_bbox.x0 + spec.manual_offset_x, spec.target_bbox.y1 - 2.0 + spec.manual_offset_y)

        # Insert replacement text span
        page.insert_text(
            origin_pt,
            spec.replacement_text,
            fontname=fitz_font,
            fontsize=font_size,
            color=color_tuple,
            overlay=True
        )

        doc.save(output_pdf_path)
        doc.close()

        return (True, strategy, f"Text replaced successfully using {strategy.value}.")

    except Exception as e:
        logger.error(f"Text replacement failed using strategy {strategy.value}: {e}")
        return (False, strategy, f"Strategy execution error: {e}")
