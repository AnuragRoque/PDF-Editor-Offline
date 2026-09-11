"""
Font resolution, analysis, mapping, and substitution utilities.
"""

import re
import os
import glob
import threading
from typing import Dict, List, Tuple, Optional
import fitz
from app.core.models import FontInfo, EditSpec, FONT_FLAG_BOLD, FONT_FLAG_ITALIC
from app.core.logging import logger

# System font search locations (Windows first, then common cross-platform dirs).
SYSTEM_FONT_DIRS = [
    os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/.fonts"),
    "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
]

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
    is_bold = bool(flags & FONT_FLAG_BOLD) or "bold" in name_lower or "black" in name_lower or "heavy" in name_lower
    is_italic = bool(flags & FONT_FLAG_ITALIC) or "italic" in name_lower or "oblique" in name_lower

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


# ---------------------------------------------------------------------------
# Font-face preservation helpers
#
# The goal is to keep the *original* font face when re-inserting edited text,
# instead of collapsing everything to a base-14 substitute. Preference order:
#   1. Reuse the font program already embedded in the PDF (exact face).
#   2. Load a matching system font of the same family from disk.
#   3. Fall back to a base-14 standard font (get_fitz_font_name).
# ---------------------------------------------------------------------------

def extract_embedded_font(doc: "fitz.Document", page: "fitz.Page", target_font_name: str) -> Tuple[Optional[bytes], str]:
    """
    Extracts the embedded font program for `target_font_name` from the page.
    Returns (font_buffer_bytes, ext) or (None, "") when no embedded program is found.
    """
    target_clean = clean_font_name(target_font_name).lower()
    try:
        font_list = page.get_fonts(full=True)
    except Exception:
        try:
            font_list = doc.get_page_fonts(page.number, full=True)
        except Exception:
            return None, ""

    # Prefer an exact (subset-stripped) basefont match, then a substring match.
    exact_match = None
    loose_match = None
    for finfo in font_list:
        xref = finfo[0]
        basefont = finfo[3] if len(finfo) > 3 else ""
        base_clean = clean_font_name(basefont).lower()
        if not base_clean:
            continue
        if base_clean == target_clean:
            exact_match = xref
            break
        if base_clean in target_clean or target_clean in base_clean:
            loose_match = loose_match or xref

    xref = exact_match if exact_match is not None else loose_match
    if xref is None:
        return None, ""

    try:
        _name, ext, _ftype, buffer = doc.extract_font(xref)
        if buffer and len(buffer) > 0 and ext and ext not in ("n/a",):
            return bytes(buffer), ext
    except Exception as e:
        logger.debug(f"extract_font failed for xref {xref}: {e}")
    return None, ""


def font_buffer_covers_text(buffer: bytes, text: str) -> bool:
    """Returns True if the font program in `buffer` has glyphs for every non-space char in `text`."""
    try:
        font = fitz.Font(fontbuffer=buffer)
    except Exception as e:
        logger.debug(f"Could not load font buffer for glyph coverage check: {e}")
        return False
    return _font_covers(font, text)


def font_file_covers_text(font_path: str, text: str) -> bool:
    """Returns True if the font file at `font_path` has glyphs for every non-space char in `text`."""
    try:
        font = fitz.Font(fontfile=font_path)
    except Exception as e:
        logger.debug(f"Could not load font file '{font_path}' for glyph coverage check: {e}")
        return False
    return _font_covers(font, text)


def _font_covers(font: "fitz.Font", text: str) -> bool:
    for ch in text:
        if ch.isspace():
            continue
        try:
            if font.has_glyph(ord(ch)) == 0:
                return False
        except Exception:
            return False
    return True


# Style words stripped when deriving a font's family key from its full name.
_STYLE_WORDS = frozenset({
    "bold", "italic", "oblique", "regular", "book", "roman", "normal",
    "light", "medium", "semibold", "demibold", "demi", "semi", "black",
    "heavy", "thin", "extralight", "ultralight", "extrabold", "ultrabold",
    "condensed", "narrow", "wide", "expanded", "mt", "ps",
})

_FONT_INDEX: Optional[List[Dict]] = None
_FONT_INDEX_LOCK = threading.Lock()


def _family_key(name: str) -> str:
    """Reduces a font name to a comparable family key by dropping style/weight words."""
    n = re.sub(r'[^a-z0-9 ]', ' ', (name or "").lower())
    tokens = [t for t in n.split() if t and t not in _STYLE_WORDS]
    return "".join(tokens)


def _build_font_index() -> List[Dict]:
    """
    Indexes installed fonts using each font program's *real* metadata (family,
    bold, italic) as reported by fitz.Font — not filename heuristics, which are
    unreliable for compact names like cambriab/cambriai/cambriaz.
    """
    index: List[Dict] = []
    seen_paths = set()
    for d in SYSTEM_FONT_DIRS:
        if not d or not os.path.isdir(d):
            continue
        for pattern in ("*.ttf", "*.otf", "*.ttc"):
            for path in glob.glob(os.path.join(d, pattern)):
                if path in seen_paths:
                    continue
                seen_paths.add(path)
                try:
                    fo = fitz.Font(fontfile=path)
                    flags = fo.flags or {}
                    name = fo.name or os.path.splitext(os.path.basename(path))[0]
                except Exception:
                    continue
                index.append({
                    "path": path,
                    "name": name,
                    "family": _family_key(name),
                    "bold": bool(flags.get("bold")),
                    "italic": bool(flags.get("italic")),
                })
    return index


def get_font_index() -> List[Dict]:
    """Returns the cached system-font index, building it lazily on first use."""
    global _FONT_INDEX
    if _FONT_INDEX is None:
        with _FONT_INDEX_LOCK:
            if _FONT_INDEX is None:
                _FONT_INDEX = _build_font_index()
                logger.info(f"Indexed {len(_FONT_INDEX)} system fonts by real metadata.")
    return _FONT_INDEX


def find_system_font_file(family: str, is_bold: bool = False, is_italic: bool = False) -> Optional[str]:
    """
    Finds the best system font file for `family` and the requested bold/italic
    style, matching on each font's real metadata. Returns the path or None.
    """
    fam_key = _family_key(family)
    if not fam_key:
        return None

    index = get_font_index()

    # Prefer exact family-key matches; fall back to substring overlap.
    candidates = [f for f in index if f["family"] == fam_key]
    if not candidates:
        candidates = [f for f in index if fam_key in f["family"] or f["family"] in fam_key]
    if not candidates:
        return None

    def score(f: Dict) -> tuple:
        return (
            2 * int(f["bold"] == is_bold) + 2 * int(f["italic"] == is_italic),
            int(f["family"] == fam_key),
            -len(f["family"]),  # prefer the tightest family name on ties
        )

    best = max(candidates, key=score)
    logger.info(
        f"Matched system font for '{family}' (bold={is_bold}, italic={is_italic}): "
        f"{best['name']} -> {best['path']}"
    )
    return best["path"]


def resolve_insertion_font(
    doc: "fitz.Document",
    page: "fitz.Page",
    spec: EditSpec,
    is_bold: bool = False,
    is_italic: bool = False,
    embedded_buffer: Optional[bytes] = None,
) -> str:
    """
    Resolves the font to use for (re)inserting text, preserving the original face
    wherever possible. Registers the chosen font on `page` when needed and returns
    the fontname to pass to page.insert_text().

    `embedded_buffer` should be the original embedded font program, extracted
    *before* any redaction (apply_redactions can strip the font from page
    resources). When None, it is extracted here from `spec`'s font name.

    Preference order:
      1. Reuse the original embedded font program (exact face).
      2. Load a matching system font of the same family (covers new glyphs).
      3. Fall back to a base-14 standard font.
    """
    orig_font_name = spec.target_span.font_name if spec.target_span else spec.font_name
    replacement = spec.replacement_text or ""

    # 1) Reuse the embedded font program if it covers the replacement glyphs.
    try:
        buffer = embedded_buffer
        if buffer is None:
            buffer, _ext = extract_embedded_font(doc, page, orig_font_name)
        if buffer and font_buffer_covers_text(buffer, replacement):
            fontname = "F_" + (re.sub(r'\W', '', clean_font_name(orig_font_name))[:24] or "embed")
            page.insert_font(fontname=fontname, fontbuffer=buffer)
            logger.info(f"Preserving original embedded font '{clean_font_name(orig_font_name)}' for insertion.")
            return fontname
    except Exception as e:
        logger.warning(f"Embedded font reuse failed, trying system font: {e}")

    # 2) Match a system font of the same family (handles subset glyph gaps).
    try:
        family = clean_font_name(orig_font_name).split('-')[0]
        sys_path = find_system_font_file(family, is_bold=is_bold, is_italic=is_italic)
        if sys_path and font_file_covers_text(sys_path, replacement):
            fontname = "F_sys_" + (re.sub(r'\W', '', family.lower())[:20] or "match")
            page.insert_font(fontname=fontname, fontfile=sys_path)
            logger.info(f"Preserving font family '{family}' via system font: {sys_path}")
            return fontname
    except Exception as e:
        logger.warning(f"System font match failed, falling back to base-14: {e}")

    # 3) Base-14 fallback (may change the visible face).
    fallback = get_fitz_font_name(orig_font_name, is_bold=is_bold, is_italic=is_italic)
    logger.warning(f"Could not preserve font '{clean_font_name(orig_font_name)}'; falling back to base-14 '{fallback}'.")
    return fallback
