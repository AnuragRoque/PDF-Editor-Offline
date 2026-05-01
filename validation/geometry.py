"""
Layer 4: Geometry Validation checking coordinate drift of untouched page objects.
"""

from typing import List
from app.core.models import DocumentModel, EditSpec, ValidationLayerResult

def validate_geometry(
    orig_doc: DocumentModel,
    edited_doc: DocumentModel,
    spec: EditSpec
) -> ValidationLayerResult:
    """
    Validates that no unexpected coordinate shifts or object drift occurred on non-target elements.
    """
    errors: List[str] = []
    warnings: List[str] = []

    p_idx = spec.page_num
    if p_idx >= len(orig_doc.pages) or p_idx >= len(edited_doc.pages):
        return ValidationLayerResult("Geometry", False, ["Page index out of bounds."], warnings)

    orig_page = orig_doc.pages[p_idx]
    edited_page = edited_doc.pages[p_idx]

    # Compare image bboxes
    if len(orig_page.images) == len(edited_page.images):
        for idx in range(len(orig_page.images)):
            o_img = orig_page.images[idx]
            e_img = edited_page.images[idx]
            if abs(o_img.bbox.x0 - e_img.bbox.x0) > 1.0 or abs(o_img.bbox.y0 - e_img.bbox.y0) > 1.0:
                errors.append(f"Image {idx+1} moved from {o_img.bbox.tuple} to {e_img.bbox.tuple}.")

    passed = len(errors) == 0
    return ValidationLayerResult(
        layer_name="Geometry",
        passed=passed,
        errors=errors,
        warnings=warnings
    )
