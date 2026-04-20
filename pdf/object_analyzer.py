"""
Detection and extraction of non-text PDF page objects (Images, Vectors, Forms).
"""

import fitz
from typing import List, Dict, Any
from app.core.models import BBox, ImageInfo
from app.core.logging import logger

def extract_page_images(page: fitz.Page, page_num: int) -> List[ImageInfo]:
    """Extracts image object info and bounding boxes on page safely."""
    images = []
    try:
        image_list = page.get_images(full=True)
        for idx, img_info in enumerate(image_list):
            try:
                xref = img_info[0]
                if xref <= 0:
                    continue
                base_image = page.parent.extract_image(xref)
                if not base_image:
                    continue
                    
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)
                ext = base_image.get("ext", "png")

                # Get image bounding box on page
                bbox_list = page.get_image_rects(xref)
                for b_idx, rect in enumerate(bbox_list):
                    images.append(ImageInfo(
                        id=f"img_p{page_num}_x{xref}_{b_idx}",
                        page_num=page_num,
                        bbox=BBox(rect.x0, rect.y0, rect.x1, rect.y1),
                        width=width,
                        height=height,
                        ext=ext
                    ))
            except Exception as e:
                logger.debug(f"Failed to extract image xref {img_info[0]} on page {page_num+1}: {e}")
    except Exception as e:
        logger.warning(f"Error enumerating page images on page {page_num+1}: {e}")

    return images

def count_page_drawings(page: fitz.Page) -> int:
    """Counts vector path drawings (lines, rectangles, curves) on page."""
    try:
        drawings = page.get_drawings()
        return len(drawings)
    except Exception:
        return 0
