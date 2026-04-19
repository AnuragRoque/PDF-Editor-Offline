"""
PDF Document Metadata, Catalog, Bookmarks, and Page Box extraction.
"""

import fitz
from typing import Dict, Any, List, Optional
from app.core.models import BBox, AnnotationInfo, LinkInfo

def extract_document_metadata(doc: fitz.Document) -> Dict[str, Any]:
    """Extracts raw metadata from fitz Document object."""
    meta = doc.metadata or {}
    toc = doc.get_toc()
    return {
        "format": doc.name,
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "subject": meta.get("subject", ""),
        "keywords": meta.get("keywords", ""),
        "creator": meta.get("creator", ""),
        "producer": meta.get("producer", ""),
        "creationDate": meta.get("creationDate", ""),
        "modDate": meta.get("modDate", ""),
        "encryption": doc.is_encrypted,
        "page_count": doc.page_count,
        "toc": toc
    }

def extract_page_boxes(page: fitz.Page) -> Dict[str, List[float]]:
    """Extracts page box dimensions (MediaBox, CropBox, BleedBox, TrimBox, ArtBox)."""
    return {
        "mediabox": list(page.rect),
        "cropbox": list(page.cropbox),
        "rotation": page.rotation
    }

def extract_page_annotations(page: fitz.Page, page_num: int) -> List[AnnotationInfo]:
    """Extracts page annotations."""
    annots = []
    annot = page.first_annot
    idx = 0
    while annot:
        rect = annot.rect
        annots.append(AnnotationInfo(
            id=f"annot_{page_num}_{idx}",
            page_num=page_num,
            type_name=annot.type[1] if annot.type else "Unknown",
            bbox=BBox(rect.x0, rect.y0, rect.x1, rect.y1),
            content=annot.info.get("content", "")
        ))
        annot = annot.next
        idx += 1
    return annots

def extract_page_links(page: fitz.Page, page_num: int) -> List[LinkInfo]:
    """Extracts hyperlinks on page."""
    links = []
    link_list = page.get_links()
    for idx, link in enumerate(link_list):
        rect = link.get("from", fitz.Rect(0, 0, 0, 0))
        links.append(LinkInfo(
            id=f"link_{page_num}_{idx}",
            page_num=page_num,
            bbox=BBox(rect.x0, rect.y0, rect.x1, rect.y1),
            uri=link.get("uri", ""),
            dest_page=link.get("page", None)
        ))
    return links
