"""Configuration management with JSON persistence."""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict

from app.utils.paths import get_config_dir


@dataclass
class BuildConfig:
    """Build configuration settings."""
    script_path: str = ""
    requirements_path: str = ""
    output_dir: str = ""
    icon_path: str = ""
    app_name: str = ""
    one_file: bool = True
    console_mode: bool = True
    clean_build: bool = True
    hidden_imports: list = field(default_factory=list)
    exclude_modules: list = field(default_factory=list)
    data_files: list = field(default_factory=list)
    additional_args: str = ""


@dataclass
class InstallerConfig:
    """Installer configuration settings."""
    enabled: bool = False
    company_name: str = ""
    app_name: str = ""
    version: str = "1.0.0"
    setup_icon: str = ""
    license_file: str = ""
    installer_type: str = "nsis"  # nsis or inno


@dataclass
class AppConfig:
    """Main application configuration."""
    theme: str = "dark"
    last_script_dir: str = ""
    last_output_dir: str = ""
    python_interpreter: str = ""
    auto_open_output: bool = True
    save_logs: bool = True
    build_config: BuildConfig = field(default_factory=BuildConfig)
    installer_config: InstallerConfig = field(default_factory=InstallerConfig)
    recent_projects: list = field(default_factory=list)


class ConfigManager:
    """Manages application configuration persistence."""

    CONFIG_FILE = "config.json"
    MAX_RECENT_PROJECTS = 10

    def __init__(self):
        self.config_dir = get_config_dir()
        self.config_file = self.config_dir / self.CONFIG_FILE
        self.config = self._load_config()

    def _load_config(self) -> AppConfig:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return self._dict_to_config(data)
            except (json.JSONDecodeError, KeyError, TypeError):
                return AppConfig()
        return AppConfig()

    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig."""
        build_data = data.get('build_config', {})
        installer_data = data.get('installer_config', {})

        return AppConfig(
            theme=data.get('theme', 'dark'),
            last_script_dir=data.get('last_script_dir', ''),
            last_output_dir=data.get('last_output_dir', ''),
            python_interpreter=data.get('python_interpreter', ''),
            auto_open_output=data.get('auto_open_output', True),
            save_logs=data.get('save_logs', True),
            build_config=BuildConfig(**build_data) if build_data else BuildConfig(),
            installer_config=InstallerConfig(**installer_data) if installer_data else InstallerConfig(),
            recent_projects=data.get('recent_projects', [])
        )

    def save(self):
        """Save configuration to file."""
        data = {
            'theme': self.config.theme,
            'last_script_dir': self.config.last_script_dir,
            'last_output_dir': self.config.last_output_dir,
            'python_interpreter': self.config.python_interpreter,
            'auto_open_output': self.config.auto_open_output,
            'save_logs': self.config.save_logs,
            'build_config': asdict(self.config.build_config),
            'installer_config': asdict(self.config.installer_config),
            'recent_projects': self.config.recent_projects
        }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            self.save()

    def add_recent_project(self, path: str):
        """Add a project to recent projects list."""
        if path in self.config.recent_projects:
            self.config.recent_projects.remove(path)
        self.config.recent_projects.insert(0, path)
        self.config.recent_projects = self.config.recent_projects[:self.MAX_RECENT_PROJECTS]
        self.save()

    def save_preset(self, name: str, build_config: BuildConfig) -> Path:
        """Save a build preset."""
        presets_dir = self.config_dir / "presets"
        presets_dir.mkdir(exist_ok=True)

        preset_file = presets_dir / f"{name}.json"
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(build_config), f, indent=2)

        return preset_file

    def load_preset(self, name: str) -> Optional[BuildConfig]:
        """Load a build preset."""
        preset_file = self.config_dir / "presets" / f"{name}.json"
        if preset_file.exists():
            with open(preset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return BuildConfig(**data)
        return None

    def list_presets(self) -> list:
        """List available presets."""
        presets_dir = self.config_dir / "presets"
        if presets_dir.exists():
            return [f.stem for f in presets_dir.glob("*.json")]
        return []


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get or create the global config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
