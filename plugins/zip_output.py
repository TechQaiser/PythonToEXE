"""
Zip Output Plugin

A post-build plugin that creates a ZIP archive of the build output.
This serves as an example plugin demonstrating the plugin system.
"""

import zipfile
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Import plugin base classes from the main app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.plugin_loader import PostBuildPlugin


class ZipOutputPlugin(PostBuildPlugin):
    """Plugin that zips the build output folder."""

    NAME = "Zip Output"
    DESCRIPTION = "Creates a ZIP archive of the build output folder"
    VERSION = "1.0.0"
    AUTHOR = "PyInstaller Builder"
    PLUGIN_TYPE = "post_build"

    def execute(self, context: Dict[str, Any]) -> bool:
        """
        Create a ZIP archive of the build output.

        Args:
            context: Dictionary containing:
                - 'build_config': BuildConfig instance
                - 'output_path': Path to build output
                - 'build_result': BuildResult instance
                - 'app_config': AppConfig instance

        Returns:
            True if ZIP was created successfully, False otherwise.
        """
        try:
            output_path = context.get('output_path')
            if not output_path or not Path(output_path).exists():
                self.logger.warning("Zip Output: No valid output path found")
                return False

            output_path = Path(output_path)

            # Generate ZIP filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            build_config = context.get('build_config')
            app_name = build_config.app_name if build_config else "build"
            app_name = app_name or "build"

            zip_filename = f"{app_name}_{timestamp}.zip"
            zip_path = output_path.parent / zip_filename

            self.logger.info(f"Zip Output: Creating archive at {zip_path}")

            # Create ZIP archive
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # If output_path is a directory, add all its contents
                if output_path.is_dir():
                    for file_path in output_path.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(output_path.parent)
                            zipf.write(file_path, arcname)
                            self.logger.debug(f"  Added: {arcname}")
                else:
                    # If it's a single file, just add it
                    zipf.write(output_path, output_path.name)

            self.logger.success(f"Zip Output: Archive created successfully: {zip_path}")
            return True

        except Exception as e:
            self.logger.error(f"Zip Output: Failed to create archive: {str(e)}")
            return False


class CleanBuildPlugin(PostBuildPlugin):
    """Plugin that cleans up build artifacts after successful build."""

    NAME = "Clean Build Artifacts"
    DESCRIPTION = "Removes temporary build files (.spec, build folder) after successful build"
    VERSION = "1.0.0"
    AUTHOR = "PyInstaller Builder"
    PLUGIN_TYPE = "post_build"

    def execute(self, context: Dict[str, Any]) -> bool:
        """
        Clean up build artifacts.

        Args:
            context: Build context dictionary

        Returns:
            True if cleanup was successful, False otherwise.
        """
        try:
            build_config = context.get('build_config')
            if not build_config or not build_config.script_path:
                return False

            script_path = Path(build_config.script_path)
            script_dir = script_path.parent

            # Clean up .spec file
            spec_file = script_dir / f"{script_path.stem}.spec"
            if spec_file.exists():
                spec_file.unlink()
                self.logger.info(f"Clean Build: Removed {spec_file.name}")

            # Clean up build folder
            build_folder = script_dir / "build"
            if build_folder.exists():
                import shutil
                shutil.rmtree(build_folder)
                self.logger.info("Clean Build: Removed build folder")

            self.logger.success("Clean Build: Cleanup completed")
            return True

        except Exception as e:
            self.logger.error(f"Clean Build: Cleanup failed: {str(e)}")
            return False
