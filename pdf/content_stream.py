"""
PDF Content Stream parsing and direct operator string patching.
"""

import pikepdf
import re
from typing import Optional, Tuple
from app.core.logging import logger

def patch_content_stream_text(
    pdf_path: str,
    output_path: str,
    page_num: int,
    target_text: str,
    replacement_text: str
) -> bool:
    """
    Attempts Strategy 1: Direct Content Stream Text Replacement using pikepdf.
    Validates that target_text is inside a valid text operator (Tj or TJ) before replacing.
    """
    if len(target_text) < 2:
        return False

    try:
        pdf = pikepdf.open(pdf_path)
        if page_num < 0 or page_num >= len(pdf.pages):
            pdf.close()
            return False

        page = pdf.pages[page_num]
        
        contents = page.Contents
        if isinstance(contents, pikepdf.Array):
            stream_list = contents
        else:
            stream_list = [contents]

        modified = False
        target_bytes = target_text.encode('latin1', errors='ignore')
        replacement_bytes = replacement_text.encode('latin1', errors='ignore')

        target_pattern = b'(' + target_bytes + b')'
        replacement_pattern = b'(' + replacement_bytes + b')'

        for stream in stream_list:
            if not hasattr(stream, 'read_bytes'):
                continue
            data = stream.read_bytes()
            
            # Require (target_text) to be followed by Tj, TJ, ', or " text operator
            # e.g. (target) Tj or [(target)] TJ
            tj_pattern = re.compile(re.escape(target_pattern) + rb'\s*(?:Tj|TJ|\'|")')
            
            if tj_pattern.search(data):
                new_data = tj_pattern.sub(replacement_pattern + b' Tj', data, count=1)
                stream.write_bytes(new_data)
                modified = True
                logger.info(f"Strategy 1: Replaced '{target_text}' -> '{replacement_text}' in text stream operator.")

        if modified:
            pdf.save(output_path)
            pdf.close()
            return True

        pdf.close()
        return False
    except Exception as e:
        logger.debug(f"Content stream patching skipped/failed: {e}")
        return False
