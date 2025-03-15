# AuTOMIC MacroTool

Advanced Macro Recording and Automation Tool for Windows

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Windows](https://img.shields.io/badge/platform-Windows-blue.svg)](https://www.microsoft.com/windows)

## Overview

AuTOMIC MacroTool is a powerful and user-friendly macro recording and automation tool designed for Windows. It allows you to record, edit, and playback mouse and keyboard actions with advanced features like scripting, window detection, and stealth mode.

### Key Features

- **Advanced Recording**
  - Mouse movement and clicks
  - Keyboard input
  - Delay timing
  - Window-specific recording
  - DirectX mode support

- **Smart Playback**
  - Multiple playback modes (once, loop, count)
  - Adjustable playback speed
  - Randomized delays
  - Stop on input
  - Position restoration
  - Stealth mode

- **Scripting Support**
  - Python-based scripting
  - Built-in script editor
  - API documentation
  - Syntax highlighting
  - Real-time validation

- **User Interface**
  - Modern Qt-based interface
  - Multiple language support
  - Light/Dark themes
  - Customizable hotkeys
  - System tray integration

- **Professional Features**
  - 6 macro slots
  - Window detection
  - DirectX compatibility
  - Backup/Restore
  - Portable mode

## Installation

### Option 1: Installer

1. Download the latest installer from [Releases](https://github.com/Atomic-Ark/AuTOMIC_MacroTool/releases)
2. Run `AuTOMIC_MacroTool_Setup.exe`
3. Follow the installation wizard

### Option 2: Portable Version

1. Download the ZIP archive from [Releases](https://github.com/Atomic-Ark/AuTOMIC_MacroTool/releases)
2. Extract to your preferred location
3. Run `AuTOMIC_MacroTool.exe`

### Option 3: From Source

```bash
# Clone repository
git clone https://github.com/Atomic-Ark/AuTOMIC_MacroTool.git
cd AuTOMIC_MacroTool

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run application
python src/main.py
```

## Usage

### Quick Start

1. Launch AuTOMIC MacroTool
2. Press F1 to start recording
3. Perform actions you want to record
4. Press F1 again to stop recording
5. Press F2 to play the recorded macro

### Macro Slots

- Use the 6 available slots to store different macros
- Assign hotkeys to each slot for quick access
- Drag and drop macros between slots
- Export/Import macros for sharing

### Scripting

```python
# Example script
from time import sleep

# Get active window
window = get_active_window()
bring_to_front(window)

# Perform actions
mouse_move(100, 100)
mouse_click('left')
sleep(0.5)
key_press('ctrl+c')

# Wait for specific window
notepad = wait_for_window('Notepad')
if notepad:
    bring_to_front(notepad)
    key_press('ctrl+v')
```

### Advanced Features

- **Window Mode**: Record actions relative to specific windows
- **DirectX Mode**: Capture input in DirectX applications
- **Stealth Mode**: Simulate hardware-level input
- **Backup/Restore**: Automatically save macro configurations
- **Portable Mode**: Run without installation

## Configuration

Settings can be accessed through:
- Menu: File > Settings
- Hotkey: Ctrl+Alt+S
- Command line: `--config`

### Key Settings

- Recording options
- Playback behavior
- Hotkey assignments
- Language selection
- Theme preferences
- Backup settings

## Building

### Prerequisites

- Python 3.8 or later
- Qt 6.5.0 or later
- Inno Setup 6 (for installer)

### Build Steps

1. Install build dependencies:
   ```bash
   pip install -e .[dev]
   ```

2. Run build script:
   ```bash
   # Windows
   build.bat

   # Linux/Mac
   python build_standalone.py
   ```

3. Find outputs in:
   - `dist/standalone/` - Portable version
   - `dist/installer/` - Windows installer
   - `dist/` - ZIP archive

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests`
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- **Author**: AtomicArk (atomicarkft@gmail.com)
- **Contributors**: See [GitHub contributors](https://github.com/Atomic-Ark/AuTOMIC_MacroTool/graphs/contributors)

### Third-Party Libraries

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [keyboard](https://github.com/boppreh/keyboard) - Keyboard input
- [mouse](https://github.com/boppreh/mouse) - Mouse input
- [pynput](https://github.com/moses-palmer/pynput) - Input monitoring
- [interception](https://github.com/oblitum/Interception) - Stealth mode
- [pywin32](https://github.com/mhammond/pywin32) - Windows API

## Support

- [Issue Tracker](https://github.com/Atomic-Ark/AuTOMIC_MacroTool/issues)
- [Discussions](https://github.com/Atomic-Ark/AuTOMIC_MacroTool/discussions)
- Email: atomicarkft@gmail.com

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Roadmap

- Linux support
- Cloud sync
- Macro marketplace
- Plugin system
- AI-assisted automation

---

Made with ❤️ by AtomicArk
