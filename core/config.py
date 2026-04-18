"""
Application Configuration and Settings for Local Precision PDF Editor.
"""

from dataclasses import dataclass, field
from pathlib import Path
import os
import sys

@dataclass
class AppConfig:
    app_name: str = "Local Precision PDF Editor"
    app_version: str = "1.0.0"
    
    # Rendering settings
    render_dpi: int = 150
    high_res_dpi: int = 300
    cache_max_pages: int = 50
    
    # Visual diff settings
    visual_diff_dpi: int = 150
    visual_pixel_threshold: int = 40  # Tolerates font rasterization anti-aliasing
    visual_max_unexpected_pixels: int = 300  # Max unexpected pixels outside mask (0.01% of 2M page pixels)
    
    # Editing policies
    default_font_family: str = "Helvetica"
    preserve_geometry_strict: bool = True
    prevent_silent_resize: bool = True
    
    # Validation policies
    require_full_validation: bool = True
    max_repair_attempts: int = 4
    
    # Application directories
    app_data_dir: Path = field(default_factory=lambda: Path(os.path.expanduser("~/.precision_pdf_editor")))
    logs_dir: Path = field(default_factory=lambda: Path(os.path.expanduser("~/.precision_pdf_editor/logs")))
    temp_dir: Path = field(default_factory=lambda: Path(os.path.expanduser("~/.precision_pdf_editor/temp")))

    def __post_init__(self):
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

config = AppConfig()
