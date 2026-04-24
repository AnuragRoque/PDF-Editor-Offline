"""
Atomic PDF Writer and Transaction temporary file handling.
"""

import os
import shutil
import tempfile
from pathlib import Path
from app.core.config import config
from app.core.logging import logger

def create_temp_pdf_path(prefix: str = "trans_") -> str:
    """Creates a temporary file path inside application temp directory."""
    fd, path = tempfile.mkstemp(suffix=".pdf", prefix=prefix, dir=str(config.temp_dir))
    os.close(fd)
    return path

def save_pdf_atomically(src_path: str, dest_path: str) -> bool:
    """Safely writes output to dest_path via atomic replacement without overwriting source directly."""
    temp_target = dest_path + ".tmp"
    try:
        shutil.copy2(src_path, temp_target)
        if os.path.exists(dest_path):
            os.replace(temp_target, dest_path)
        else:
            os.rename(temp_target, dest_path)
        logger.info(f"PDF saved atomically to '{dest_path}'.")
        return True
    except Exception as e:
        logger.error(f"Failed to save PDF atomically to '{dest_path}': {e}")
        if os.path.exists(temp_target):
            os.remove(temp_target)
        return False
