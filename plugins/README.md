# Plugin Development Guide

This guide explains how to create plugins for PyInstaller Advanced Builder.

Plugins run automatically after a successful build. Use them for tasks like:

- Creating zip archives
- Uploading builds to a server
- Running post-build scripts
- Cleaning up temporary files
- Sending notifications

---

## Quick Example

Create a file in the `plugins/` folder:

```python
# plugins/my_plugin.py

from app.core.plugin_loader import PostBuildPlugin

class MyPlugin(PostBuildPlugin):
    NAME = "My Plugin"
    DESCRIPTION = "Does something after build"
    VERSION = "1.0.0"
    AUTHOR = "Your Name"

    def execute(self, context):
        output_path = context.get('output_path')
        self.logger.info(f"Build output: {output_path}")

        # your logic here

        return True  # return False if something failed
```

Drop the file in `plugins/` and restart the app. It shows up in the Plugins tab.

---

## Plugin Types

### PostBuildPlugin

Runs after build completes. Most common type.

```python
from app.core.plugin_loader import PostBuildPlugin

class MyPostPlugin(PostBuildPlugin):
    NAME = "My Post Plugin"
    DESCRIPTION = "Runs after build"
    VERSION = "1.0.0"
    AUTHOR = "You"

    def execute(self, context):
        # context contains build info
        return True
```

### BuildProcessorPlugin

Has hooks for both pre-build and post-build. Use when you need to modify build settings.

```python
from app.core.plugin_loader import BuildProcessorPlugin

class MyProcessor(BuildProcessorPlugin):
    NAME = "My Processor"
    DESCRIPTION = "Modifies build process"
    VERSION = "1.0.0"
    AUTHOR = "You"

    def pre_build(self, context):
        # modify context before build starts
        return context

    def post_build(self, context):
        # runs after build
        return True

    def execute(self, context):
        return self.post_build(context)
```

---

## Context Object

The `context` dictionary passed to plugins contains:

| Key | Type | Description |
|-----|------|-------------|
| `build_config` | `BuildConfig` | Script path, output dir, options |
| `output_path` | `Path` | Where the build was saved |
| `build_result` | `BuildResult` | Status, build time, errors |
| `app_config` | `AppConfig` | App settings, theme, etc. |

### Accessing context data

```python
def execute(self, context):
    # Build configuration
    config = context.get('build_config')
    script = config.script_path
    output = config.output_dir
    app_name = config.app_name

    # Build result
    result = context.get('build_result')
    if result.status.value == 'success':
        self.logger.info("Build succeeded!")

    # Output path
    output_path = context.get('output_path')

    return True
```

---

## Logging

Use `self.logger` for output. Messages appear in the build console.

```python
def execute(self, context):
    self.logger.debug("Debug message")      # gray
    self.logger.info("Info message")        # white
    self.logger.warning("Warning message")  # orange
    self.logger.error("Error message")      # red
    self.logger.success("Success message")  # green
    return True
```

---

## Plugin Metadata

Every plugin needs these class attributes:

```python
NAME = "Plugin Name"           # shown in UI
DESCRIPTION = "What it does"   # shown in UI
VERSION = "1.0.0"              # version string
AUTHOR = "Your Name"           # credit
PLUGIN_TYPE = "post_build"     # or "build_processor"
```

---

## Included Plugins

### Zip Output

Creates a timestamped zip archive of the build output.

```
my_app_20250118_143052.zip
```

### Clean Build Artifacts

Removes PyInstaller's temporary files:

- `*.spec` file
- `build/` folder

Keeps your project directory clean.

---

## File Structure

```
plugins/
├── __init__.py          # empty, required
├── README.md            # this file
├── zip_output.py        # example: zip + clean plugins
└── your_plugin.py       # your custom plugins
```

---

## Tips

1. **Return value matters** — Return `True` for success, `False` for failure. Failed plugins are logged.

2. **Don't block** — Plugins run on the main thread. Keep them fast or use threading for heavy tasks.

3. **Handle errors** — Wrap risky code in try/except. Log errors with `self.logger.error()`.

4. **Test separately** — Test your plugin logic in a standalone script first.

5. **Check paths exist** — Always verify `output_path` exists before using it.

---

## Example: Upload to Server

```python
import requests
from pathlib import Path
from app.core.plugin_loader import PostBuildPlugin

class UploadPlugin(PostBuildPlugin):
    NAME = "Upload Build"
    DESCRIPTION = "Uploads build to server"
    VERSION = "1.0.0"
    AUTHOR = "You"

    def execute(self, context):
        output_path = context.get('output_path')
        if not output_path or not Path(output_path).exists():
            self.logger.error("No output to upload")
            return False

        try:
            # find the exe file
            exe_files = list(Path(output_path).glob("*.exe"))
            if not exe_files:
                self.logger.error("No exe found")
                return False

            exe_path = exe_files[0]
            self.logger.info(f"Uploading {exe_path.name}...")

            with open(exe_path, 'rb') as f:
                response = requests.post(
                    "https://your-server.com/upload",
                    files={"file": f}
                )

            if response.ok:
                self.logger.success("Upload complete!")
                return True
            else:
                self.logger.error(f"Upload failed: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Upload error: {e}")
            return False
```

---

## Example: Desktop Notification

```python
from app.core.plugin_loader import PostBuildPlugin

class NotifyPlugin(PostBuildPlugin):
    NAME = "Desktop Notify"
    DESCRIPTION = "Shows notification when build completes"
    VERSION = "1.0.0"
    AUTHOR = "You"

    def execute(self, context):
        try:
            from plyer import notification

            result = context.get('build_result')
            config = context.get('build_config')

            title = "Build Complete"
            message = f"{config.app_name or 'App'} built in {result.build_time:.1f}s"

            notification.notify(
                title=title,
                message=message,
                timeout=5
            )
            return True

        except ImportError:
            self.logger.warning("plyer not installed, skipping notification")
            return True
```

---

## Need Help?

Check the included `zip_output.py` for a working reference.

Open an issue on GitHub if you're stuck.
