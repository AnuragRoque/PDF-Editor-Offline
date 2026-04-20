"""
Master document analyzer constructing complete DocumentModel baseline.
"""

import fitz
from typing import Optional
from app.core.models import DocumentModel, PageModel, FontInfo
from app.core.exceptions import NonEditablePDFError
from app.pdf.loader import open_pdf_document
from app.pdf.metadata import (
    extract_document_metadata,
    extract_page_boxes,
    extract_page_annotations,
    extract_page_links
)
from app.pdf.text_detector import extract_page_text_spans
from app.pdf.object_analyzer import extract_page_images
from app.pdf.fonts import analyze_font_metadata
from app.core.logging import logger

def analyze_pdf_document(file_path: str, password: str = "") -> DocumentModel:
    """
    Analyzes PDF document and constructs internal DocumentModel baseline.
    Raises NonEditablePDFError if document has no editable text (scanned PDF).
    """
    logger.info(f"Analyzing PDF document baseline: '{file_path}'")
    doc = open_pdf_document(file_path, password)
    meta = extract_document_metadata(doc)

    pages: list = []
    font_catalog: dict = {}
    total_spans = 0

    for page_num in range(doc.page_count):
        try:
            page = doc[page_num]
            boxes = extract_page_boxes(page)
            spans = extract_page_text_spans(page, page_num)
            total_spans += len(spans)
            
            images = extract_page_images(page, page_num)
            annots = extract_page_annotations(page, page_num)
            links = extract_page_links(page, page_num)

            # Collect fonts
            for span in spans:
                if span.font_name not in font_catalog:
                    try:
                        font_info = analyze_font_metadata(span.font_name, span.font_size, span.font_flags)
                        font_catalog[span.font_name] = font_info
                    except Exception as fe:
                        logger.debug(f"Font analysis warning for '{span.font_name}': {fe}")

            page_model = PageModel(
                page_num=page_num,
                width=page.rect.width,
                height=page.rect.height,
                rotation=page.rotation,
                mediabox=tuple(boxes["mediabox"]),
                cropbox=tuple(boxes["cropbox"]),
                spans=spans,
                images=images,
                annotations=annots,
                links=links
            )
            pages.append(page_model)
            logger.info(f"Page {page_num+1}/{doc.page_count} analyzed: {len(spans)} text spans, {len(images)} images.")
        except Exception as pe:
            logger.error(f"Error analyzing page {page_num+1}: {pe}")

    doc.close()

    is_text_based = total_spans > 0
    if not is_text_based:
        logger.warning(f"PDF document '{file_path}' contains 0 text spans. Scanned / image-only PDF detected.")

    logger.info(f"Document analysis completed: {len(pages)} pages, {total_spans} total spans, {len(font_catalog)} unique fonts.")

    return DocumentModel(
        file_path=file_path,
        page_count=len(pages),
        metadata=meta,
        pages=pages,
        is_encrypted=meta.get("encryption", False),
        is_text_based=is_text_based,
        fonts=list(font_catalog.values())
    )
