"""Input validation utilities."""

import os
import re
from pathlib import Path
from typing import Tuple, Optional


def validate_python_script(path: str) -> Tuple[bool, str]:
    """Validate that a path points to a valid Python script."""
    if not path:
        return False, "No script path provided"

    file_path = Path(path)

    if not file_path.exists():
        return False, f"File does not exist: {path}"

    if not file_path.is_file():
        return False, f"Path is not a file: {path}"

    if file_path.suffix.lower() != '.py':
        return False, "File must have .py extension"

    return True, "Valid Python script"


def validate_requirements_file(path: str) -> Tuple[bool, str]:
    """Validate that a path points to a valid requirements.txt file."""
    if not path:
        return True, "No requirements file (optional)"

    file_path = Path(path)

    if not file_path.exists():
        return False, f"File does not exist: {path}"

    if not file_path.is_file():
        return False, f"Path is not a file: {path}"

    return True, "Valid requirements file"


def validate_icon_file(path: str) -> Tuple[bool, str]:
    """Validate that a path points to a valid icon file."""
    if not path:
        return True, "No icon file (optional)"

    file_path = Path(path)

    if not file_path.exists():
        return False, f"Icon file does not exist: {path}"

    if not file_path.is_file():
        return False, f"Path is not a file: {path}"

    if file_path.suffix.lower() != '.ico':
        return False, "Icon file must have .ico extension for Windows"

    return True, "Valid icon file"


def validate_output_directory(path: str) -> Tuple[bool, str]:
    """Validate output directory path."""
    if not path:
        return False, "No output directory provided"

    dir_path = Path(path)

    # Check if path can be created
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True, "Valid output directory"
    except PermissionError:
        return False, f"Permission denied: {path}"
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def validate_app_name(name: str) -> Tuple[bool, str]:
    """Validate application name for build."""
    if not name:
        return False, "Application name is required"

    # Check for invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        if char in name:
            return False, f"Name contains invalid character: {char}"

    if len(name) > 100:
        return False, "Name is too long (max 100 characters)"

    return True, "Valid application name"


def validate_version_string(version: str) -> Tuple[bool, str]:
    """Validate version string format."""
    if not version:
        return True, "No version (optional)"

    # Simple version pattern: major.minor.patch
    pattern = r'^\d+\.\d+\.\d+$'
    if not re.match(pattern, version):
        return False, "Version must be in format: X.Y.Z (e.g., 1.0.0)"

    return True, "Valid version string"


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe as a filename."""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')

    # Remove leading/trailing spaces and dots
    name = name.strip(' .')

    # Limit length
    if len(name) > 100:
        name = name[:100]

    return name or "unnamed"
