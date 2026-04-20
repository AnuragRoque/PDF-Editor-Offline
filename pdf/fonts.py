"""
Font resolution, analysis, mapping, and substitution utilities.
"""

import re
from typing import Dict, List, Tuple, Optional
from app.core.models import FontInfo
from app.core.logging import logger

STANDARD_PDF_FONTS = {
    "helvetica": "helv",
    "helvetica-bold": "hebo",
    "helvetica-oblique": "heit",
    "helvetica-boldoblique": "hebi",
    "times-roman": "tiro",
    "times-bold": "tibo",
    "times-italic": "tiit",
    "times-bolditalic": "tibi",
    "courier": "cour",
    "courier-bold": "cobo",
    "courier-oblique": "coit",
    "courier-boldoblique": "cobi",
    "symbol": "symb",
    "zapfdingbats": "zadb",
}

DEFAULT_FONT_SUBSTITUTIONS = {
    "arial": "Helvetica",
    "arial-bold": "Helvetica-Bold",
    "arial-italic": "Helvetica-Oblique",
    "calibri": "Helvetica",
    "aptos": "Helvetica",
    "segoe ui": "Helvetica",
    "times new roman": "Times-Roman",
    "georgia": "Times-Roman",
    "courier new": "Courier",
}

def clean_font_name(font_name: str) -> str:
    """Removes PDF subset tag prefixes like 'ABCDEF+' from font names."""
    if not font_name:
        return "Helvetica"
    clean = re.sub(r'^[A-Z]{6}\+', '', font_name)
    return clean.strip()

def analyze_font_metadata(raw_name: str, size: float, flags: int = 0) -> FontInfo:
    """Analyzes raw PDF font name and flags to build a structured FontInfo."""
    cleaned = clean_font_name(raw_name)
    is_subset = bool(re.match(r'^[A-Z]{6}\+', raw_name))
    
    name_lower = cleaned.lower()
    is_bold = bool(flags & 2) or "bold" in name_lower or "black" in name_lower or "heavy" in name_lower
    is_italic = bool(flags & 1) or "italic" in name_lower or "oblique" in name_lower

    weight = "bold" if is_bold else "normal"
    style = "italic" if is_italic else "normal"

    return FontInfo(
        name=cleaned,
        family=cleaned.split('-')[0],
        weight=weight,
        style=style,
        size=size,
        is_embedded=True,
        is_subset=is_subset,
        encoding="Standard"
    )

def get_fitz_font_name(font_name: str, is_bold: bool = False, is_italic: bool = False) -> str:
    """
    Maps a generic font name or target font specification to a PyMuPDF built-in font identifier or standard name.
    """
    cleaned = clean_font_name(font_name)
    lower = cleaned.lower()

    if lower in STANDARD_PDF_FONTS:
        return STANDARD_PDF_FONTS[lower]

    # Map common fonts to standard 14 equivalents if necessary
    if "times" in lower or "georgia" in lower or "serif" in lower:
        if is_bold and is_italic:
            return "tibi"
        elif is_bold:
            return "tibo"
        elif is_italic:
            return "tiit"
        else:
            return "tiro"
            
    if "courier" in lower or "mono" in lower or "code" in lower:
        if is_bold and is_italic:
            return "cobi"
        elif is_bold:
            return "cobo"
        elif is_italic:
            return "coit"
        else:
            return "cour"

    # Default to Helvetica family
    if is_bold and is_italic:
        return "hebi"
    elif is_bold:
        return "hebo"
    elif is_italic:
        return "heit"
    else:
        return "helv"

def find_font_candidates(target_font_name: str) -> List[Tuple[str, float]]:
    """
    Generates closest font candidates with confidence score percentage (0-100%).
    Used when exact target font is unavailable or subset.
    """
    cleaned = clean_font_name(target_font_name)
    lower = cleaned.lower()

    candidates = []
    
    # Check exact match in sub
    if lower in DEFAULT_FONT_SUBSTITUTIONS:
        candidates.append((DEFAULT_FONT_SUBSTITUTIONS[lower], 95.0))
        
    if "helvetica" in lower or "arial" in lower or "sans" in lower:
        candidates.append(("Helvetica", 96.0))
        candidates.append(("Arial", 90.0))
    elif "times" in lower or "serif" in lower:
        candidates.append(("Times-Roman", 96.0))
        candidates.append(("Times New Roman", 90.0))
    elif "courier" in lower or "mono" in lower:
        candidates.append(("Courier", 96.0))
        candidates.append(("Courier New", 90.0))
    else:
        candidates.append(("Helvetica", 85.0))

    return candidates
