"""
Main entry point for AuTOMIC MacroTool.
Copyright (c) 2025 AtomicArk
"""

import sys
import os
import logging
import argparse
import locale
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QLocale
from PyQt6.QtGui import QIcon

from . import (
    APP_NAME, APP_ID, APP_ICON, get_version,
    get_supported_languages, is_feature_enabled
)
from .utils.debug_helper import setup_logging, get_debug_helper
from .core.config_manager import config_manager
from .core.macro_manager import macro_manager
from .gui.main_window import MainWindow
from .gui.styles import style_manager, Theme

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=APP_NAME)
    
    # General options
    parser.add_argument('--version', action='version',
                       version=f'{APP_NAME} {get_version()}')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--portable', action='store_true',
                       help='Run in portable mode')
    
    # Configuration
    parser.add_argument('--config', type=str, metavar='FILE',
                       help='Use specific config file')
    parser.add_argument('--lang', type=str, choices=get_supported_languages().keys(),
                       help='Override language setting')
    parser.add_argument('--theme', type=str, choices=['light', 'dark', 'system'],
                       help='Override theme setting')
    
    # Features
    parser.add_argument('--no-stealth', action='store_true',
                       help='Disable stealth mode')
    parser.add_argument('--no-directx', action='store_true',
                       help='Disable DirectX support')
    
    # Development
    parser.add_argument('--dev', action='store_true',
                       help='Enable development mode')
    parser.add_argument('--profile', action='store_true',
                       help='Enable performance profiling')
    
    return parser.parse_args()

def setup_environment(args: argparse.Namespace) -> None:
    """Setup application environment."""
    # Set application ID
    if hasattr(sys, 'frozen'):
        import win32gui
        win32gui.SetAppUserModelID(APP_ID)
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)
    
    # Get logger
    logger = logging.getLogger('main')
    debug = get_debug_helper()
    
    try:
        # Initialize configuration
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                logger.warning(f"Config file not found: {args.config}")
        
        # Override settings
        if args.lang:
            config_manager.set_value('language', args.lang)
        if args.theme:
            config_manager.set_value('theme', args.theme)
        
        # Feature flags
        if args.no_stealth:
            debug.log_debug("Stealth mode disabled")
        if args.no_directx:
            debug.log_debug("DirectX support disabled")
        
        # Development mode
        if args.dev:
            debug.set_development_mode(True)
            debug.log_debug("Development mode enabled")
        
        # Profiling
        if args.profile:
            debug.enable_profiling()
            debug.log_debug("Performance profiling enabled")
        
    except Exception as e:
        logger.error(f"Failed to setup environment: {e}")
        sys.exit(1)

def setup_locale() -> None:
    """Setup application locale."""
    logger = logging.getLogger('main')
    
    try:
        # Get configured language
        lang = config_manager.get_value('language', '')
        
        # Auto-detect if not set
        if not lang:
            system_locale = QLocale.system().name()
            if system_locale in get_supported_languages():
                lang = system_locale
            else:
                lang = 'en_US'
        
        # Set locale
        locale.setlocale(locale.LC_ALL, lang)
        QLocale.setDefault(QLocale(lang))
        
        logger.info(f"Using language: {lang}")
        
    except Exception as e:
        logger.error(f"Failed to setup locale: {e}")
        # Fallback to English
        locale.setlocale(locale.LC_ALL, 'en_US')
        QLocale.setDefault(QLocale('en_US'))

def setup_style() -> None:
    """Setup application style."""
    logger = logging.getLogger('main')
    
    try:
        # Get configured theme
        theme = config_manager.get_value('theme', '')
        
        # Auto-detect if not set
        if not theme:
            theme = Theme.SYSTEM.value
        
        # Set theme
        style_manager.set_theme(Theme(theme))
        
        logger.info(f"Using theme: {theme}")
        
    except Exception as e:
        logger.error(f"Failed to setup style: {e}")
        # Fallback to system theme
        style_manager.set_theme(Theme.SYSTEM)

def setup_qt_options() -> None:
    """Setup Qt application options."""
    # High DPI support
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    
    # Set organization info
    QApplication.setOrganizationName("AtomicArk")
    QApplication.setOrganizationDomain("atomicark.com")
    QApplication.setApplicationName(APP_NAME)
    QApplication.setApplicationVersion(get_version())

def run_application(args: Optional[List[str]] = None) -> int:
    """Run the application."""
    # Parse arguments
    if args is None:
        args = sys.argv[1:]
    parsed_args = parse_arguments()
    
    # Setup environment
    setup_environment(parsed_args)
    
    # Create application
    app = QApplication(args)
    
    try:
        # Setup application
        setup_qt_options()
        setup_locale()
        setup_style()
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), APP_ICON)
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # Create main window
        window = MainWindow()
        window.show()
        
        # Run event loop
        return app.exec()
        
    except Exception as e:
        logging.error(f"Application error: {e}")
        return 1
    
    finally:
        # Cleanup
        config_manager.cleanup()
        macro_manager.cleanup()

def main() -> int:
    """Main entry point."""
    try:
        return run_application()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
