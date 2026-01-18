"""Dialog windows for PyInstaller Advanced Builder."""

from pathlib import Path
from typing import Optional, List

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QFileDialog,
    QComboBox, QListWidget, QListWidgetItem, QCheckBox,
    QGroupBox, QTextEdit, QDialogButtonBox, QMessageBox,
    QTabWidget, QWidget, QSpinBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app.core.config_manager import BuildConfig, InstallerConfig


class HiddenImportsDialog(QDialog):
    """Dialog for managing hidden imports."""

    def __init__(self, hidden_imports: List[str], parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.hidden_imports = hidden_imports.copy()
        self.setWindowTitle("Hidden Imports")
        self.setMinimumSize(400, 300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        info_label = QLabel(
            "Add module names that PyInstaller fails to detect automatically.\n"
            "Example: sklearn.utils._cython_blas"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # List widget
        self.list_widget = QListWidget()
        for item in self.hidden_imports:
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        # Input row
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter module name...")
        self.input_field.returnPressed.connect(self._add_import)
        input_layout.addWidget(self.input_field)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_import)
        input_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_import)
        input_layout.addWidget(remove_btn)

        layout.addLayout(input_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_import(self):
        text = self.input_field.text().strip()
        if text and text not in self.hidden_imports:
            self.hidden_imports.append(text)
            self.list_widget.addItem(text)
            self.input_field.clear()

    def _remove_import(self):
        current = self.list_widget.currentItem()
        if current:
            self.hidden_imports.remove(current.text())
            self.list_widget.takeItem(self.list_widget.row(current))

    def get_imports(self) -> List[str]:
        return self.hidden_imports


class DataFilesDialog(QDialog):
    """Dialog for managing data files to include."""

    def __init__(self, data_files: List[str], parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.data_files = data_files.copy()
        self.setWindowTitle("Data Files")
        self.setMinimumSize(500, 350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        info_label = QLabel(
            "Add data files to include in the build.\n"
            "Format: source_path;destination_folder\n"
            "Example: assets/icon.png;assets"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # List widget
        self.list_widget = QListWidget()
        for item in self.data_files:
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        # Input row
        input_layout = QHBoxLayout()

        self.source_field = QLineEdit()
        self.source_field.setPlaceholderText("Source path...")
        input_layout.addWidget(self.source_field, 2)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_source)
        input_layout.addWidget(browse_btn)

        self.dest_field = QLineEdit()
        self.dest_field.setPlaceholderText("Destination folder...")
        input_layout.addWidget(self.dest_field, 1)

        layout.addLayout(input_layout)

        # Action buttons
        action_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_file)
        action_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_file)
        action_layout.addWidget(remove_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_source(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "", "All Files (*)"
        )
        if path:
            self.source_field.setText(path)

    def _add_file(self):
        source = self.source_field.text().strip()
        dest = self.dest_field.text().strip() or "."

        if source:
            entry = f"{source};{dest}"
            if entry not in self.data_files:
                self.data_files.append(entry)
                self.list_widget.addItem(entry)
                self.source_field.clear()
                self.dest_field.clear()

    def _remove_file(self):
        current = self.list_widget.currentItem()
        if current:
            self.data_files.remove(current.text())
            self.list_widget.takeItem(self.list_widget.row(current))

    def get_data_files(self) -> List[str]:
        return self.data_files


class InstallerSettingsDialog(QDialog):
    """Dialog for installer configuration."""

    def __init__(self, config: InstallerConfig, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.config = InstallerConfig(
            enabled=config.enabled,
            company_name=config.company_name,
            app_name=config.app_name,
            version=config.version,
            setup_icon=config.setup_icon,
            license_file=config.license_file,
            installer_type=config.installer_type
        )
        self.setWindowTitle("Installer Settings")
        self.setMinimumSize(450, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Enable checkbox
        self.enable_check = QCheckBox("Enable installer creation")
        self.enable_check.setChecked(self.config.enabled)
        self.enable_check.stateChanged.connect(self._toggle_enabled)
        layout.addWidget(self.enable_check)

        # Settings group
        self.settings_group = QGroupBox("Installer Settings")
        form_layout = QFormLayout(self.settings_group)

        # Installer type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["NSIS", "Inno Setup"])
        self.type_combo.setCurrentText(
            "NSIS" if self.config.installer_type == "nsis" else "Inno Setup"
        )
        form_layout.addRow("Installer Type:", self.type_combo)

        # Company name
        self.company_edit = QLineEdit(self.config.company_name)
        self.company_edit.setPlaceholderText("Your Company Name")
        form_layout.addRow("Company Name:", self.company_edit)

        # App name
        self.app_name_edit = QLineEdit(self.config.app_name)
        self.app_name_edit.setPlaceholderText("Application Name")
        form_layout.addRow("Application Name:", self.app_name_edit)

        # Version
        self.version_edit = QLineEdit(self.config.version)
        self.version_edit.setPlaceholderText("1.0.0")
        form_layout.addRow("Version:", self.version_edit)

        # Setup icon
        icon_layout = QHBoxLayout()
        self.icon_edit = QLineEdit(self.config.setup_icon)
        self.icon_edit.setPlaceholderText("Path to setup icon (.ico)")
        icon_layout.addWidget(self.icon_edit)
        icon_btn = QPushButton("Browse")
        icon_btn.clicked.connect(self._browse_icon)
        icon_layout.addWidget(icon_btn)
        form_layout.addRow("Setup Icon:", icon_layout)

        # License file
        license_layout = QHBoxLayout()
        self.license_edit = QLineEdit(self.config.license_file)
        self.license_edit.setPlaceholderText("Path to license file (.txt, .rtf)")
        license_layout.addWidget(self.license_edit)
        license_btn = QPushButton("Browse")
        license_btn.clicked.connect(self._browse_license)
        license_layout.addWidget(license_btn)
        form_layout.addRow("License File:", license_layout)

        layout.addWidget(self.settings_group)
        self._toggle_enabled(self.config.enabled)

        # Note
        note_label = QLabel(
            "Note: NSIS or Inno Setup must be installed on your system\n"
            "for installer creation to work."
        )
        note_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(note_label)

        layout.addStretch()

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _toggle_enabled(self, state):
        self.settings_group.setEnabled(bool(state))

    def _browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon", "", "Icon Files (*.ico)"
        )
        if path:
            self.icon_edit.setText(path)

    def _browse_license(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select License File", "", "Text Files (*.txt *.rtf)"
        )
        if path:
            self.license_edit.setText(path)

    def get_config(self) -> InstallerConfig:
        return InstallerConfig(
            enabled=self.enable_check.isChecked(),
            company_name=self.company_edit.text().strip(),
            app_name=self.app_name_edit.text().strip(),
            version=self.version_edit.text().strip(),
            setup_icon=self.icon_edit.text().strip(),
            license_file=self.license_edit.text().strip(),
            installer_type="nsis" if self.type_combo.currentText() == "NSIS" else "inno"
        )


class PresetsDialog(QDialog):
    """Dialog for managing build presets."""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.config_manager = config_manager
        self.selected_preset = None
        self.setWindowTitle("Build Presets")
        self.setMinimumSize(400, 300)
        self._setup_ui()
        self._load_presets()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Presets list
        self.presets_list = QListWidget()
        self.presets_list.itemDoubleClicked.connect(self._load_preset)
        layout.addWidget(self.presets_list)

        # Buttons
        btn_layout = QHBoxLayout()

        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._load_preset)
        btn_layout.addWidget(load_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_preset)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_presets(self):
        self.presets_list.clear()
        presets = self.config_manager.list_presets()
        for preset in presets:
            self.presets_list.addItem(preset)

    def _load_preset(self):
        current = self.presets_list.currentItem()
        if current:
            self.selected_preset = current.text()
            self.accept()

    def _delete_preset(self):
        current = self.presets_list.currentItem()
        if current:
            preset_name = current.text()
            reply = QMessageBox.question(
                self, "Delete Preset",
                f"Delete preset '{preset_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                preset_file = self.config_manager.config_dir / "presets" / f"{preset_name}.json"
                if preset_file.exists():
                    preset_file.unlink()
                self._load_presets()

    def get_selected_preset(self) -> Optional[str]:
        return self.selected_preset


class AboutDialog(QDialog):
    """About dialog showing application information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("About")
        self.setFixedSize(600, 360)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)

        # Title
        title = QLabel("PyInstaller Advanced Builder")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        # Version
        version = QLabel("v1.0.0")
        version.setStyleSheet("color: #888888; font-size: 10pt;")
        version.setAlignment(Qt.AlignLeft)
        layout.addWidget(version)

        layout.addSpacing(6)

        # Description
        desc = QLabel(
            "A modern, feature-rich GUI tool for building Python applications "
            "into standalone executables using PyInstaller. Supports themes, "
            "plugins, and advanced build configurations."
        )
        desc.setStyleSheet("font-size: 11pt;")
        desc.setAlignment(Qt.AlignLeft)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(10)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #444444;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        layout.addSpacing(10)

        # Footer - Copyright & License
        copyright_label = QLabel("© 2025 PythonToEXE  —  MIT License")
        copyright_label.setStyleSheet("color: #888888; font-size: 10pt;")
        copyright_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(copyright_label)

        # GitHub link
        github_label = QLabel(
            'GitHub: <a href="https://github.com/AIMasterRace/PythonToEXE" '
            'style="color: #4da6ff;">github.com/AIMasterRace/PythonToEXE</a>'
        )
        github_label.setStyleSheet("font-size: 10pt;")
        github_label.setAlignment(Qt.AlignLeft)
        github_label.setOpenExternalLinks(True)
        layout.addWidget(github_label)

        layout.addStretch()

        # Close button - bottom right, outline style
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedSize(90, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #aaaaaa;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #666666;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
