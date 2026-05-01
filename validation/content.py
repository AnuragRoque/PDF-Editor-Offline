"""
Layer 2: Content Validation verifying expected edits and untouched text content.
"""

from typing import List
from app.core.models import DocumentModel, EditSpec, ValidationLayerResult, EditOperation

def validate_content(
    orig_doc: DocumentModel,
    edited_doc: DocumentModel,
    spec: EditSpec
) -> ValidationLayerResult:
    """
    Validates that:
    1. The requested edit (replacement, addition, removal) is present in target region.
    2. Non-target text spans on the target page and untouched pages remain 100% intact.
    """
    errors: List[str] = []
    warnings: List[str] = []

    p_idx = spec.page_num
    if p_idx < 0 or p_idx >= len(edited_doc.pages):
        errors.append(f"Target page {p_idx+1} does not exist in edited document.")
        return ValidationLayerResult("Content", False, errors, warnings)

    orig_page = orig_doc.pages[p_idx]
    edited_page = edited_doc.pages[p_idx]

    # 1. Verify requested edit on target page
    all_edited_text = " ".join([s.text for s in edited_page.spans])

    if spec.operation == EditOperation.REPLACE:
        if spec.replacement_text not in all_edited_text:
            errors.append(f"Replacement text '{spec.replacement_text}' was not found on page {p_idx+1}.")
            
    elif spec.operation == EditOperation.ADD:
        if spec.replacement_text not in all_edited_text:
            errors.append(f"Added text '{spec.replacement_text}' was not found on page {p_idx+1}.")
            
    elif spec.operation == EditOperation.REMOVE:
        if spec.target_text in all_edited_text:
            errors.append(f"Target text '{spec.target_text}' still exists on page {p_idx+1} after removal.")

    # 2. Check non-target spans on the SAME target page (Protection against accidental redaction deletion)
    if spec.target_bbox:
        for o_span in orig_page.spans:
            # Skip target span being edited
            if o_span.bbox.intersects(spec.target_bbox):
                continue

            # Ensure non-target span text (len > 2) is still present on page
            if len(o_span.text) > 2 and o_span.text not in all_edited_text:
                errors.append(f"Untouched line '{o_span.text[:30]}' on Page {p_idx+1} was accidentally destroyed!")

    # 3. Check untouched pages
    for page_num in range(orig_doc.page_count):
        if page_num == p_idx:
            continue
        orig_text = " ".join([s.text for s in orig_doc.pages[page_num].spans])
        edited_text = " ".join([s.text for s in edited_doc.pages[page_num].spans])
        if orig_text != edited_text:
            errors.append(f"Untouched page {page_num+1} text content was accidentally modified!")

    passed = len(errors) == 0
    return ValidationLayerResult(
        layer_name="Content",
        passed=passed,
        errors=errors,
        warnings=warnings
    )
