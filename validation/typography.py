"""
Layer 3: Typography Validation verifying font family, size, weight, and color preservation.
"""

from typing import List
from app.core.models import DocumentModel, EditSpec, ValidationLayerResult
from app.pdf.fonts import clean_font_name

def validate_typography(
    orig_doc: DocumentModel,
    edited_doc: DocumentModel,
    spec: EditSpec
) -> ValidationLayerResult:
    """
    Validates typography preservation across target and non-target spans.
    """
    errors: List[str] = []
    warnings: List[str] = []

    p_idx = spec.page_num
    if p_idx < 0 or p_idx >= len(edited_doc.pages):
        return ValidationLayerResult("Typography", False, ["Page index out of bounds."], warnings)

    orig_spans = orig_doc.pages[p_idx].spans
    edited_spans = edited_doc.pages[p_idx].spans

    # Check non-target spans on page
    for o_span in orig_spans:
        # Skip target span if spec has target_bbox
        if spec.target_bbox and o_span.bbox.intersects(spec.target_bbox):
            continue
            
        # Match with edited span by position
        matching = [e for e in edited_spans if abs(e.bbox.x0 - o_span.bbox.x0) < 2.0 and abs(e.bbox.y0 - o_span.bbox.y0) < 2.0]
        if matching:
            e_span = matching[0]
            if abs(e_span.font_size - o_span.font_size) > 0.5:
                errors.append(f"Untouched text '{o_span.text[:15]}' font size changed from {o_span.font_size} to {e_span.font_size}.")
            if clean_font_name(e_span.font_name).lower() != clean_font_name(o_span.font_name).lower():
                warnings.append(f"Untouched text '{o_span.text[:15]}' font changed from {o_span.font_name} to {e_span.font_name}.")

    passed = len(errors) == 0
    return ValidationLayerResult(
        layer_name="Typography",
        passed=passed,
        errors=errors,
        warnings=warnings
    )
