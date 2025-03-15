#!/usr/bin/env python3
"""
Main entry point for AuTOMIC MacroTool.
"""

import sys
import os
import logging
import argparse
import locale
import ctypes
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTranslator
from PyQt6.QtGui import QIcon

from . import (
    __version__,
    get_resource_path,
    is_frozen,
    is_portable,
    logger
)
from .gui.main_window import MainWindow
from .gui.styles import style_manager, Theme
from .core.config_manager import ConfigManager
from .utils.debug_helper import get_debug_helper, DebugLevel

def is_admin() -> bool:
    """Check if running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    """Request administrator privileges."""
    try:
        if not is_admin():
            script = os.path.abspath(sys.argv[0])
            params = ' '.join(sys.argv[1:])
            
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                f'"{script}" {params}',
                None,
                1
            )
            sys.exit()
            
    except Exception as e:
        logger.error(f"Failed to request admin rights: {e}")

def setup_high_dpi():
    """Configure high DPI support."""
    try:
        # Enable high DPI scaling
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Set process DPI awareness
        if sys.platform == 'win32':
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            
    except Exception as e:
        logger.error(f"Failed to setup high DPI: {e}")

def load_translator(app: QApplication, config_manager: ConfigManager) -> Optional[QTranslator]:
    """Load language translator."""
    try:
        # Get system language if not set
        language = config_manager.config.language
        if not language:
            language = locale.getdefaultlocale()[0]
        
        # Load translation file
        translator = QTranslator()
        lang_file = get_resource_path(f"resources/langs/{language}.qm")
        
        if lang_file.exists():
            if translator.load(str(lang_file)):
                app.installTranslator(translator)
                logger.info(f"Loaded language: {language}")
                return translator
            else:
                logger.warning(f"Failed to load language: {language}")
        else:
            logger.warning(f"Language file not found: {language}")
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to load translator: {e}")
        return None

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='AuTOMIC MacroTool')
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--console',
        action='store_true',
        help='Show console window'
    )
    
    parser.add_argument(
        '--admin',
        action='store_true',
        help='Request administrator privileges'
    )
    
    parser.add_argument(
        '--portable',
        action='store_true',
        help='Force portable mode'
    )
    
    parser.add_argument(
        '--theme',
        choices=[t.value for t in Theme],
        help='Set application theme'
    )
    
    parser.add_argument(
        '--lang',
        help='Set interface language'
    )
    
    return parser.parse_args()

def main():
    """Main application entry point."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Setup logging
        debug_helper = get_debug_helper()
        if args.debug:
            debug_helper.set_debug_level(DebugLevel.VERBOSE)
        
        # Request admin rights if needed
        if args.admin and not is_admin():
            request_admin()
        
        # Initialize application
        setup_high_dpi()
        app = QApplication(sys.argv)
        app.setApplicationName("AuTOMIC MacroTool")
        app.setApplicationVersion(__version__)
        
        # Set application icon
        icon_path = get_resource_path("resources/icons/app.ico")
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Initialize configuration
        config_manager = ConfigManager()
        
        # Override settings from arguments
        if args.theme:
            config_manager.config.theme = Theme(args.theme)
        if args.lang:
            config_manager.config.language = args.lang
        
        # Load translator
        translator = load_translator(app, config_manager)
        
        # Apply style
        style_manager.set_theme(config_manager.config.theme)
        app.setStyleSheet(style_manager.get_stylesheet())
        
        # Create main window
        window = MainWindow(config_manager)
        
        # Show window
        if config_manager.config.minimize_to_tray:
            window.hide()
        else:
            window.show()
        
        # Run application
        exit_code = app.exec()
        
        # Cleanup
        if translator:
            app.removeTranslator(translator)
        
        # Save settings
        config_manager.save_config()
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
