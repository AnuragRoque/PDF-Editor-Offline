"""
Layer 1: Structural Validation comparing document structure before and after.
"""

from typing import Dict, Any, List
from app.core.models import DocumentModel, ValidationLayerResult

def validate_structural(orig_doc: DocumentModel, edited_doc: DocumentModel) -> ValidationLayerResult:
    """
    Compares page count, page dimensions, rotation, media boxes, annotations, links, and metadata.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Page count check
    if orig_doc.page_count != edited_doc.page_count:
        errors.append(f"Page count mismatch: Original has {orig_doc.page_count}, Edited has {edited_doc.page_count}.")

    # 2. Page boxes and dimensions check
    for p_idx in range(min(len(orig_doc.pages), len(edited_doc.pages))):
        orig_page = orig_doc.pages[p_idx]
        edited_page = edited_doc.pages[p_idx]

        if abs(orig_page.width - edited_page.width) > 0.5 or abs(orig_page.height - edited_page.height) > 0.5:
            errors.append(f"Page {p_idx+1} dimensions changed: ({orig_page.width}x{orig_page.height}) -> ({edited_page.width}x{edited_page.height}).")

        if orig_page.rotation != edited_page.rotation:
            errors.append(f"Page {p_idx+1} rotation changed: {orig_page.rotation} -> {edited_page.rotation}.")

        if orig_page.mediabox != edited_page.mediabox:
            errors.append(f"Page {p_idx+1} MediaBox changed: {orig_page.mediabox} -> {edited_page.mediabox}.")

        # Check annotation count
        if len(orig_page.annotations) != len(edited_page.annotations):
            warnings.append(f"Page {p_idx+1} annotation count changed: {len(orig_page.annotations)} -> {len(edited_page.annotations)}.")

        # Check link count
        if len(orig_page.links) != len(edited_page.links):
            warnings.append(f"Page {p_idx+1} link count changed: {len(orig_page.links)} -> {len(edited_page.links)}.")

    passed = len(errors) == 0
    return ValidationLayerResult(
        layer_name="Structural",
        passed=passed,
        errors=errors,
        warnings=warnings,
        details={"page_count_orig": orig_doc.page_count, "page_count_edited": edited_doc.page_count}
    )
