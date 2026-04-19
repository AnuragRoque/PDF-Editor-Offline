"""
Geometry utilities, bounding box math, transform matrices, and text overflow calculations.
"""

import math
from typing import Tuple, Dict, Any, Optional
from app.core.models import BBox

def transform_point(x: float, y: float, matrix: Tuple[float, float, float, float, float, float]) -> Tuple[float, float]:
    """Applies a 2x3 affine matrix (a, b, c, d, e, f) to point (x, y)."""
    a, b, c, d, e, f = matrix
    tx = a * x + c * y + e
    ty = b * x + d * y + f
    return (tx, ty)

def bbox_from_points(points: list) -> BBox:
    """Calculates axis-aligned bounding box covering all points [(x0,y0), (x1,y1), ...]."""
    if not points:
        return BBox(0.0, 0.0, 0.0, 0.0)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return BBox(min(xs), min(ys), max(xs), max(ys))

def calculate_text_width_estimate(text: str, font_size: float, font_name: str = "Helvetica") -> float:
    """
    Estimates width of text string given font name and font size.
    Uses glyph average metrics for common PDF standard fonts.
    """
    if not text:
        return 0.0

    font_lower = font_name.lower()
    # Monospace estimate
    if any(k in font_lower for k in ["courier", "mono"]):
        return len(text) * font_size * 0.60
    
    # Narrow / Condensed estimate
    if any(k in font_lower for k in ["narrow", "condensed"]):
        avg_char_width = 0.42
    # Bold / Wide estimate
    elif any(k in font_lower for k in ["bold", "heavy", "black"]):
        avg_char_width = 0.55
    else:
        avg_char_width = 0.48

    # Specific char width tweaks
    total_factor = 0.0
    for char in text:
        if char in "i1lI|!,.;:'":
            total_factor += 0.28
        elif char in "wWM@":
            total_factor += 0.85
        elif char.isupper():
            total_factor += 0.62
        elif char == ' ':
            total_factor += 0.25
        else:
            total_factor += avg_char_width

    return total_factor * font_size

def check_text_overflow(
    replacement_text: str,
    target_bbox: BBox,
    font_size: float,
    font_name: str = "Helvetica",
    tolerance_ratio: float = 1.05
) -> Tuple[bool, float, float]:
    """
    Checks if replacement text overflows target bounding box width.
    Returns (overflows, estimated_width, max_allowed_width).
    """
    max_allowed_width = target_bbox.width * tolerance_ratio
    # If target_bbox has zero width (e.g. point insertion), max_allowed is infinite/unrestricted
    if target_bbox.width <= 1.0:
        return (False, 0.0, max_allowed_width)
        
    estimated_width = calculate_text_width_estimate(replacement_text, font_size, font_name)
    overflows = estimated_width > max_allowed_width
    return (overflows, estimated_width, max_allowed_width)

def calculate_fit_font_size(
    text: str,
    target_bbox: BBox,
    font_size: float,
    font_name: str = "Helvetica"
) -> float:
    """Calculates the exact font size required to fit text inside target_bbox without overflow."""
    if not text or target_bbox.width <= 1.0:
        return font_size
    estimated_width = calculate_text_width_estimate(text, font_size, font_name)
    if estimated_width <= target_bbox.width:
        return font_size
    scale_factor = target_bbox.width / max(1.0, estimated_width)
    return round(font_size * scale_factor, 2)
