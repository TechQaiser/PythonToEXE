<h1 align="center">PyInstaller Advanced Builder</h1>

<p align="center">
  A .py to .exe converter using a modern graphical interface and <a href="https://pyinstaller.org/">PyInstaller</a> in Python.
</p>

<p align="center">
  <img src="imgs/main.png" alt="PyInstaller Advanced Builder" width="700">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/platform-windows-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/PyQt5-5.15+-blueviolet" alt="PyQt5">
  <img src="https://img.shields.io/badge/PyInstaller-6.0+-orange" alt="PyInstaller">
</p>

---

## Why This Tool?

PyInstaller is powerful but the command-line workflow gets repetitive. This tool wraps it in a clean interface with:

- Visual options instead of remembering flags
- Real-time build output with error highlighting
- Save/load build presets for different projects
- Plugin system for custom post-build tasks
- Dark and light themes

---

## Quick Start

```bash
git clone https://github.com/AIMasterRace/PythonToEXE.git
cd PythonToEXE
pip install -r requirements.txt
python run.py
```

That's it. The window opens, you're ready to build.

---

## Screenshots

<details>
<summary><b>Basic Settings</b> — Configure script, output, icon, build mode</summary>
<br>
<img src="imgs/main.png" alt="Main Tab" width="650">
</details>

<details>
<summary><b>Advanced Options</b> — Hidden imports, exclude modules, data files</summary>
<br>
<img src="imgs/advance_tab.png" alt="Advanced Tab" width="650">
</details>

<details>
<summary><b>Installer Setup</b> — NSIS / Inno Setup configuration</summary>
<br>
<img src="imgs/installer_tab.png" alt="Installer Tab" width="650">
</details>

<details>
<summary><b>Plugins</b> — Extend with custom post-build tasks</summary>
<br>
<img src="imgs/plugins_tab.png" alt="Plugins Tab" width="650">
</details>

---

## Features

| Feature | Description |
|---------|-------------|
| One-File / One-Dir | Choose between single exe or folder output |
| Console Toggle | Hide console window for GUI apps |
| Icon Support | Custom `.ico` file for your executable |
| Hidden Imports | Add modules PyInstaller misses |
| Exclude Modules | Remove unwanted modules (reduce size) |
| Data Files | Bundle assets, configs, etc. |
| Clean Build | Auto-cleanup previous build cache |
| Real-time Logs | Watch build progress live |
| Presets | Save and load build configurations |
| Themes | Dark and light mode |
| Plugins | Run custom tasks after build |

---

## Build Options Explained

**One File** — Packs everything into a single `.exe`. Slower startup but easy to distribute.

**One Directory** — Creates a folder with `.exe` + dependencies. Faster startup.

**Console Window** — Keep checked for CLI apps. Uncheck for GUI apps (no black window).

**Clean Build** — Removes old build cache. Recommended to avoid stale file issues.

**Exclude Modules** — Comma-separated list. Example: `tkinter, unittest, pydoc`

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `F5` | Start Build |
| `Ctrl+N` | New Project |
| `Ctrl+O` | Open Script |
| `Ctrl+S` | Save Preset |
| `Ctrl+L` | Load Preset |
| `Ctrl+T` | Toggle Theme |
| `Ctrl+Shift+C` | Clear Logs |

---

## Plugins

The tool supports plugins for post-build automation. Two examples included:

- **Zip Output** — Creates a `.zip` archive of the build
- **Clean Build Artifacts** — Removes `.spec` and `build/` folder

Want to create your own? **[See the Plugin Guide →](plugins/README.md)**

---

## Project Structure

```
PythonToEXE/
├── app/
│   ├── main.py                 # Entry point
│   ├── core/
│   │   ├── builder.py          # PyInstaller wrapper
│   │   ├── config_manager.py   # Settings persistence
│   │   ├── logger.py           # Log system
│   │   ├── plugin_loader.py    # Plugin loader
│   │   └── venv_manager.py     # Virtualenv support
│   ├── utils/                  # Helper modules
│   └── windows/                # UI components
├── plugins/                    # Drop plugins here
├── imgs/                       # Screenshots
├── requirements.txt
└── run.py
```

---

## Requirements

- Python 3.8 or higher
- PyQt5
- PyInstaller 6.0+

```bash
pip install -r requirements.txt
```

---

## Configuration Storage

Settings save automatically to:

```
~/.pyinstaller_builder/
├── config.json      # App settings
└── presets/         # Saved build presets
```

---

## Roadmap

- [ ] Multiple Python interpreter support
- [ ] PyInstaller version selector
- [ ] NSIS/Inno Setup full integration
- [ ] Spec file editor
- [ ] Dependency size analyzer
- [ ] Build queue for batch processing

---

## Contributing

Found a bug? Have an idea? Open an issue or submit a PR.

---

## License

MIT License — use it, modify it, ship it.

---

<p align="center">
  Made with PyQt5 and PyInstaller
</p>
