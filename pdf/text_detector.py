"""
Text detection and span extraction per page using PyMuPDF dict text API.
"""

import fitz
from typing import List, Dict, Any, Tuple
from app.core.models import TextSpan, BBox, ColorInfo
from app.pdf.fonts import clean_font_name
from app.core.logging import logger

def parse_color(color_val: Any) -> ColorInfo:
    """Safely converts color representation (int, tuple, list) to ColorInfo."""
    if color_val is None:
        return ColorInfo(0.0, 0.0, 0.0)
    try:
        if isinstance(color_val, int):
            r = ((color_val >> 16) & 255) / 255.0
            g = ((color_val >> 8) & 255) / 255.0
            b = (color_val & 255) / 255.0
            return ColorInfo(r, g, b)
        elif isinstance(color_val, (list, tuple)):
            if len(color_val) == 3:
                return ColorInfo(float(color_val[0]), float(color_val[1]), float(color_val[2]))
            elif len(color_val) == 4:
                # Convert CMYK (c, m, y, k) to RGB estimate
                c, m, y, k = [float(x) for x in color_val]
                r = (1.0 - c) * (1.0 - k)
                g = (1.0 - m) * (1.0 - k)
                b = (1.0 - y) * (1.0 - k)
                return ColorInfo(r, g, b)
    except Exception:
        pass
    return ColorInfo(0.0, 0.0, 0.0)

def extract_page_text_spans(page: fitz.Page, page_num: int) -> List[TextSpan]:
    """
    Extracts all text spans from page using PyMuPDF get_text("dict").
    Produces fully populated TextSpan models with origin, font, color, matrix, and bboxes.
    """
    spans: List[TextSpan] = []
    try:
        text_page = page.get_text("dict")
    except Exception as e:
        logger.error(f"Failed to get_text('dict') on page {page_num+1}: {e}")
        return spans
    
    for b_idx, block in enumerate(text_page.get("blocks", [])):
        if block.get("type") != 0:  # 0 is text block
            continue

        for l_idx, line in enumerate(block.get("lines", [])):
            line_dir = line.get("dir", (1.0, 0.0))
            for s_idx, span in enumerate(line.get("spans", [])):
                try:
                    text = span.get("text", "")
                    if not text and "chars" in span:
                        text = "".join([c.get("c", "") for c in span.get("chars", [])])

                    text = text.strip()
                    if not text:
                        continue

                    bbox_raw = span.get("bbox", (0, 0, 0, 0))
                    bbox = BBox(bbox_raw[0], bbox_raw[1], bbox_raw[2], bbox_raw[3])
                    
                    font_name = span.get("font", "Helvetica")
                    font_size = float(span.get("size", 12.0))
                    flags = int(span.get("flags", 0))
                    
                    color = parse_color(span.get("color", 0))
                    origin = span.get("origin", (bbox.x0, bbox.y1))
                    
                    # Matrix (a, b, c, d, e, f)
                    matrix = (line_dir[0], line_dir[1], -line_dir[1], line_dir[0], origin[0], origin[1])

                    span_id = f"span_p{page_num}_b{b_idx}_l{l_idx}_s{s_idx}"

                    spans.append(TextSpan(
                        id=span_id,
                        page_num=page_num,
                        text=text,
                        bbox=bbox,
                        font_name=font_name,
                        font_size=font_size,
                        font_flags=flags,
                        color=color,
                        origin=origin,
                        matrix=matrix,
                        rotation=page.rotation,
                        block_idx=b_idx,
                        line_idx=l_idx,
                        span_idx=s_idx
                    ))
                except Exception as e:
                    logger.debug(f"Error parsing span on page {page_num+1}, block {b_idx}: {e}")

    return spans

def search_text_spans(spans: List[TextSpan], query: str, case_sensitive: bool = False) -> List[TextSpan]:
    """Searches extracted spans for query string."""
    if not query:
        return []
        
    results = []
    target = query if case_sensitive else query.lower()
    
    for span in spans:
        span_text = span.text if case_sensitive else span.text.lower()
        if target in span_text:
            results.append(span)
            
    return results
