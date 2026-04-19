"""
PDF Loading and validation of document files.
"""

import fitz
import pikepdf
from pathlib import Path
from typing import Tuple
from app.core.exceptions import PDFEditorError

def open_pdf_document(file_path: str, password: str = "") -> fitz.Document:
    """
    Opens PDF file using PyMuPDF (fitz).
    Raises PDFEditorError if file is corrupt or password protected.
    """
    path = Path(file_path)
    if not path.exists():
        raise PDFEditorError(f"PDF file does not exist: {file_path}")

    try:
        doc = fitz.open(file_path)
        if doc.is_encrypted:
            if not password or not doc.authenticate(password):
                raise PDFEditorError("PDF is password protected or authentication failed.")
        return doc
    except Exception as e:
        raise PDFEditorError(f"Failed to open PDF document: {e}")

def open_pikepdf_document(file_path: str, password: str = "") -> pikepdf.Pdf:
    """
    Opens PDF file using pikepdf for low-level object stream analysis.
    """
    try:
        if password:
            return pikepdf.open(file_path, password=password)
        return pikepdf.open(file_path)
    except Exception as e:
        raise PDFEditorError(f"Failed to open PDF with pikepdf: {e}")
