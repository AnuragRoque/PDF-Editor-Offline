"""
Visual Difference Image Generator and Anti-Aliasing Resilient Masking using OpenCV/NumPy.
"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional
from app.core.models import BBox
from app.core.config import config
from app.core.logging import logger

def compute_visual_diff(
    img_orig: Image.Image,
    img_edited: Image.Image,
    expected_bbox: Optional[BBox] = None,
    dpi: int = config.visual_diff_dpi,
    threshold: int = 40
) -> Tuple[int, Image.Image]:
    """
    Computes visual pixel difference between original and edited images.
    Applies expected_bbox mask and anti-aliasing morphological noise filtering.
    Returns (unexpected_diff_pixel_count, diff_heatmap_image).
    """
    # Ensure identical dimensions
    if img_orig.size != img_edited.size:
        img_edited = img_edited.resize(img_orig.size)

    arr_orig = np.array(img_orig.convert("RGB"))
    arr_edited = np.array(img_edited.convert("RGB"))

    # Channel-wise absolute difference
    diff = np.abs(arr_orig.astype(np.int16) - arr_edited.astype(np.int16))
    max_diff = np.max(diff, axis=2)

    # Initial binary threshold mask
    diff_binary = (max_diff > threshold).astype(np.uint8)

    # 1. Zero out target edit region (expected bbox + 25pt buffer)
    scale = dpi / 72.0
    if expected_bbox:
        padded_bbox = expected_bbox.pad(25.0)
        x0 = max(0, int(padded_bbox.x0 * scale))
        y0 = max(0, int(padded_bbox.y0 * scale))
        x1 = min(img_orig.width, int(padded_bbox.x1 * scale))
        y1 = min(img_orig.height, int(padded_bbox.y1 * scale))

        diff_binary[y0:y1, x0:x1] = 0

    # 2. Filter out anti-aliasing edge noise around existing text glyphs
    # Morphological opening (remove 1-2 pixel isolated anti-aliasing lines)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    clean_diff = cv2.morphologyEx(diff_binary, cv2.MORPH_OPEN, kernel)

    # 3. Filter out small noise blobs (keep only true structural diffs > 15 pixels)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(clean_diff)
    filtered_diff = np.zeros_like(clean_diff)
    
    for i in range(1, num_labels):  # Skip background (index 0)
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= 15:  # True visual diff blob
            filtered_diff[labels == i] = 1

    unexpected_pixel_count = int(np.sum(filtered_diff))

    # 4. Generate red visual diff heatmap
    diff_heatmap_arr = arr_orig.copy()
    # Highlight unexpected diffs in bright red
    diff_heatmap_arr[filtered_diff > 0] = [255, 0, 0]
    
    diff_img = Image.fromarray(diff_heatmap_arr)

    return (unexpected_pixel_count, diff_img)
