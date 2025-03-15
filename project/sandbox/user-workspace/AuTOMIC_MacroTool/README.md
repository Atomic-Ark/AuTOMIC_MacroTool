# AuTOMIC MacroTool

Advanced Macro Recording and Automation Tool for Windows

## Features

- **Smart Recording**: Automatically detects and adapts to window positions and sizes
- **Multiple Recording Modes**: Record mouse movements, keyboard inputs, and window interactions
- **Intelligent Playback**: Adjusts macro execution based on window state and context
- **Stealth Mode**: Optional undetectable input simulation using hardware-level drivers
- **Multi-Language Support**: Available in English, Polish, German, French, Italian, and Spanish
- **Customizable Hotkeys**: Fully configurable keyboard shortcuts for all actions
- **Macro Slots**: 6 dedicated slots for quick access to frequently used macros
- **Advanced Settings**: Fine-tune recording and playback behavior
- **Script Support**: Create and edit macro scripts for complex automation
- **Portable Version**: Available as installer or portable application

## Requirements

- Windows 10/11 (64-bit)
- Python 3.8 or higher (for development)
- Administrator rights (for stealth mode)

## Installation

### From Installer
1. Download the latest installer from the [releases page](https://github.com/atomicark/atomic-macro-tool/releases)
2. Run the installer and follow the instructions
3. Launch AuTOMIC MacroTool from the Start Menu

### Portable Version
1. Download the portable version from the [releases page](https://github.com/atomicark/atomic-macro-tool/releases)
2. Extract the archive to your desired location
3. Run `atomic_macro.exe`

### From Source
```bash
# Clone repository
git clone https://github.com/atomicark/atomic-macro-tool.git
cd atomic-macro-tool

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run application
python src/main.py
```

## Development

### Setup Development Environment
```bash
# Install development dependencies
pip install -r requirements.txt[dev]

# Run tests
pytest tests

# Run linting
pylint src
black src

# Build documentation
cd docs
make html
```

### Building Executable
```bash
# Basic build
build.bat

# Debug build with console
build.bat --debug --console

# Clean build with tests and documentation
build.bat --clean --test --doc
```

## Usage

### Quick Start
1. Launch AuTOMIC MacroTool
2. Press F1 (default) to start recording
3. Perform actions you want to record
4. Press F1 again to stop recording
5. Press F2 (default) to play the recorded macro
6. Press Ctrl+Alt+P (default) to stop playback at any time

### Advanced Features
- **Window Detection**: Select specific windows for recording
- **Relative Positioning**: Macros adapt to window position and size
- **Delay Customization**: Adjust or randomize delays between actions
- **Script Editor**: Create complex macros using Python scripts
- **Stealth Mode**: Enable undetectable input simulation
- **Macro Management**: Save, load, and organize macros in slots

## Configuration

### Settings
- **General**: Language, theme, startup behavior
- **Recording**: Input types, delay settings, window detection
- **Playback**: Speed, repeat options, safety features
- **Hotkeys**: Customize keyboard shortcuts
- **Advanced**: Debug level, performance options

### Macro Storage
- Default location: `%USERPROFILE%\Documents\AuTOMIC_MacroTool\macros`
- Portable mode: Stores macros in application directory
- Automatic backups: Created every 5 minutes during recording

## Troubleshooting

### Common Issues
- **Admin Rights Required**: Some features need administrator privileges
- **Antivirus Warnings**: May occur due to input simulation
- **Playback Issues**: Check window position and state
- **Performance Problems**: Adjust recording settings

### Debug Mode
1. Launch with `--debug --console` flags
2. Check log files in `%USERPROFILE%\Documents\AuTOMIC_MacroTool\logs`
3. Enable detailed logging in settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Credits

- Author: AtomicArk
- Icons: [Material Design Icons](https://materialdesignicons.com/)
- Stealth Mode: [Interception Driver](https://github.com/oblitum/Interception)

## Support

- [Documentation](https://atomic-macro-tool.readthedocs.io/)
- [Issue Tracker](https://github.com/atomicark/atomic-macro-tool/issues)
- [Discussions](https://github.com/atomicark/atomic-macro-tool/discussions)

---

Made with ❤️ by AtomicArk
