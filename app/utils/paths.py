"""Path utilities for PyInstaller Advanced Builder."""

import os
import sys
from pathlib import Path
from typing import Optional


def get_app_root() -> Path:
    """Get the application root directory."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent


def get_config_dir() -> Path:
    """Get the configuration directory."""
    config_dir = Path.home() / ".pyinstaller_builder"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_plugins_dir() -> Path:
    """Get the plugins directory."""
    return get_app_root() / "plugins"


def get_assets_dir() -> Path:
    """Get the assets directory."""
    return get_app_root() / "assets"


def get_icons_dir() -> Path:
    """Get the icons directory."""
    return get_assets_dir() / "icons"


def get_default_output_dir() -> Path:
    """Get the default output directory for builds."""
    output_dir = Path.home() / "PyInstallerBuilds"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_path(path: str) -> str:
    """Normalize a path string for the current OS."""
    return os.path.normpath(path)


def get_relative_path(path: Path, base: Optional[Path] = None) -> Path:
    """Get relative path from base directory."""
    if base is None:
        base = get_app_root()
    try:
        return path.relative_to(base)
    except ValueError:
        return path
