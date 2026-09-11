"""
Application Entry Point for Local Precision PDF Editor.
"""

import sys
import os
import traceback
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt

# Ensure root package is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ui.main_window import MainWindow
from app.core.config import config
from app.core.logging import logger

def setup_app_style(app: QApplication):
    app.setStyle("Fusion")

    # Dark modern palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(32, 33, 36))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.Base, QColor(24, 25, 27))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(32, 33, 36))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 46, 50))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(0, 122, 204))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 122, 204))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(palette)

    # Clean UI font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

def main():
    try:
        logger.info(f"Starting {config.app_name} v{config.app_version}...")
        app = QApplication(sys.argv)
        app.setApplicationName(config.app_name)
        app.setApplicationVersion(config.app_version)

        setup_app_style(app)

        window = MainWindow()
        
        # Auto-load PDF if provided via CLI
        if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
            pdf_path = sys.argv[1]
            logger.info(f"Opening CLI PDF argument: {pdf_path}")
            window._load_pdf_file(pdf_path)

        window.show()
        window.raise_()
        window.activateWindow()

        logger.info("Application window displayed successfully.")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Fatal error starting application: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
    
