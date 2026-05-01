"""
Master Multi-Layer Validation Pipeline Orchestrator.
"""

from typing import Optional
import fitz
import pikepdf
from app.core.models import EditSpec, ValidationReport, ValidationLayerResult
from app.pdf.analyzer import analyze_pdf_document
from app.validation.structural import validate_structural
from app.validation.content import validate_content
from app.validation.typography import validate_typography
from app.validation.geometry import validate_geometry
from app.validation.visual import validate_visual
from app.core.logging import logger

def validate_pdf_edit(
    orig_pdf_path: str,
    edited_pdf_path: str,
    spec: EditSpec
) -> ValidationReport:
    """
    Executes complete 6-layer validation pipeline on generated PDF output.
    Layer 1: Structural
    Layer 2: Content
    Layer 3: Typography
    Layer 4: Geometry
    Layer 5: Visual
    Layer 6: Integrity (re-open verification)
    """
    layers = {}

    # Layer 6: Integrity check (file reopening)
    integrity_result = ValidationLayerResult("Integrity", True)
    try:
        doc_test = fitz.open(edited_pdf_path)
        page_cnt = doc_test.page_count
        doc_test.close()
        
        pike_test = pikepdf.open(edited_pdf_path)
        pike_test.close()
    except Exception as e:
        integrity_result.passed = False
        integrity_result.errors.append(f"Integrity check failed: Output PDF file is corrupt or cannot be opened ({e}).")

    layers["Integrity"] = integrity_result
    if not integrity_result.passed:
        return ValidationReport(is_valid=False, layers=layers, overall_status="FAILED")

    # Analyze documents
    orig_doc = analyze_pdf_document(orig_pdf_path)
    edited_doc = analyze_pdf_document(edited_pdf_path)

    # Layer 1: Structural
    layers["Structural"] = validate_structural(orig_doc, edited_doc)

    # Layer 2: Content
    layers["Content"] = validate_content(orig_doc, edited_doc, spec)

    # Layer 3: Typography
    layers["Typography"] = validate_typography(orig_doc, edited_doc, spec)

    # Layer 4: Geometry
    layers["Geometry"] = validate_geometry(orig_doc, edited_doc, spec)

    # Layer 5: Visual
    visual_res = validate_visual(orig_pdf_path, edited_pdf_path, spec)
    layers["Visual"] = visual_res

    # Overall validity check
    all_passed = all(l.passed for l in layers.values())
    status = "PASS" if all_passed else "FAILED"

    unexpected_pixels = visual_res.details.get("unexpected_pixels", 0)
    diff_path = visual_res.details.get("diff_image_path", None)

    report = ValidationReport(
        is_valid=all_passed,
        layers=layers,
        unexpected_diff_pixels=unexpected_pixels,
        diff_image_path=diff_path,
        overall_status=status
    )

    logger.info(f"Validation finished. Overall status: {status}. Unexpected diff pixels: {unexpected_pixels}.")
    return report
