"""Plugin system for extensible build processors and post-build tasks."""

import importlib.util
import inspect
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Type
from dataclasses import dataclass

from app.utils.paths import get_plugins_dir
from app.core.logger import get_logger


@dataclass
class PluginInfo:
    """Information about a loaded plugin."""
    name: str
    description: str
    version: str
    author: str
    plugin_type: str  # 'build_processor' or 'post_build'
    enabled: bool = True


class PluginBase(ABC):
    """Base class for all plugins."""

    # Plugin metadata - subclasses should override these
    NAME = "Base Plugin"
    DESCRIPTION = "Base plugin description"
    VERSION = "1.0.0"
    AUTHOR = "Unknown"
    PLUGIN_TYPE = "post_build"  # 'build_processor' or 'post_build'

    def __init__(self):
        self.logger = get_logger()

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> bool:
        """
        Execute the plugin.

        Args:
            context: Dictionary containing:
                - 'build_config': BuildConfig instance
                - 'output_path': Path to build output
                - 'build_result': BuildResult instance
                - 'app_config': AppConfig instance

        Returns:
            True if execution was successful, False otherwise.
        """
        pass

    def get_info(self) -> PluginInfo:
        """Get plugin information."""
        return PluginInfo(
            name=self.NAME,
            description=self.DESCRIPTION,
            version=self.VERSION,
            author=self.AUTHOR,
            plugin_type=self.PLUGIN_TYPE
        )


class BuildProcessorPlugin(PluginBase):
    """Base class for build processor plugins that modify the build process."""

    PLUGIN_TYPE = "build_processor"

    @abstractmethod
    def pre_build(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called before the build starts. Can modify the build configuration.

        Args:
            context: Build context dictionary

        Returns:
            Modified context dictionary
        """
        pass

    @abstractmethod
    def post_build(self, context: Dict[str, Any]) -> bool:
        """
        Called after the build completes.

        Args:
            context: Build context dictionary

        Returns:
            True if successful
        """
        pass

    def execute(self, context: Dict[str, Any]) -> bool:
        """Default execute runs post_build."""
        return self.post_build(context)


class PostBuildPlugin(PluginBase):
    """Base class for post-build task plugins."""

    PLUGIN_TYPE = "post_build"


class PluginLoader:
    """Loads and manages plugins."""

    def __init__(self, plugins_dir: Optional[Path] = None):
        self.plugins_dir = plugins_dir or get_plugins_dir()
        self.logger = get_logger()
        self.plugins: Dict[str, PluginBase] = {}
        self._load_plugins()

    def _load_plugins(self):
        """Load all plugins from the plugins directory."""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created plugins directory: {self.plugins_dir}")
            return

        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            try:
                self._load_plugin_file(plugin_file)
            except Exception as e:
                self.logger.error(f"Failed to load plugin {plugin_file.name}: {str(e)}")

    def _load_plugin_file(self, file_path: Path):
        """Load a single plugin file."""
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec is None or spec.loader is None:
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find plugin classes in the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, PluginBase) and
                obj not in (PluginBase, BuildProcessorPlugin, PostBuildPlugin)):
                try:
                    plugin_instance = obj()
                    self.plugins[plugin_instance.NAME] = plugin_instance
                    self.logger.info(f"Loaded plugin: {plugin_instance.NAME}")
                except Exception as e:
                    self.logger.error(f"Failed to instantiate plugin {name}: {str(e)}")

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def get_all_plugins(self) -> List[PluginBase]:
        """Get all loaded plugins."""
        return list(self.plugins.values())

    def get_plugins_by_type(self, plugin_type: str) -> List[PluginBase]:
        """Get plugins of a specific type."""
        return [p for p in self.plugins.values() if p.PLUGIN_TYPE == plugin_type]

    def get_build_processors(self) -> List[BuildProcessorPlugin]:
        """Get all build processor plugins."""
        return [p for p in self.plugins.values() if isinstance(p, BuildProcessorPlugin)]

    def get_post_build_plugins(self) -> List[PostBuildPlugin]:
        """Get all post-build plugins."""
        return [p for p in self.plugins.values() if isinstance(p, PostBuildPlugin)]

    def execute_plugin(self, name: str, context: Dict[str, Any]) -> bool:
        """Execute a plugin by name."""
        plugin = self.get_plugin(name)
        if plugin:
            try:
                return plugin.execute(context)
            except Exception as e:
                self.logger.error(f"Plugin {name} execution failed: {str(e)}")
                return False
        return False

    def execute_post_build_plugins(self, context: Dict[str, Any]) -> Dict[str, bool]:
        """Execute all enabled post-build plugins."""
        results = {}
        for plugin in self.get_post_build_plugins():
            info = plugin.get_info()
            if info.enabled:
                results[plugin.NAME] = self.execute_plugin(plugin.NAME, context)
        return results

    def reload_plugins(self):
        """Reload all plugins from disk."""
        self.plugins.clear()
        self._load_plugins()


# Global plugin loader instance
_plugin_loader: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    """Get or create the global plugin loader."""
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader()
    return _plugin_loader
