"""
PyInstaller Advanced Builder - Entry Point

A modern GUI tool for building Python applications into standalone executables.
"""

import sys
import os

# Add the project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app import __app_name__, __version__
from app.windows.main_window import MainWindow
from app.core.logger import get_logger


def setup_high_dpi():
    """Enable high DPI scaling for better display on high-resolution screens."""
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def main():
    """Main application entry point."""
    # Setup high DPI before creating QApplication
    setup_high_dpi()

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("PyInstaller Builder")

    # Set default font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # Initialize logger
    logger = get_logger()
    logger.info(f"Starting {__app_name__} v{__version__}")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    exit_code = app.exec_()

    logger.info("Application closed")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
