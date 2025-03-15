"""
AuTOMIC MacroTool - Advanced Macro Recording and Automation Tool
Copyright (c) 2023 AtomicArk
"""

__title__ = "AuTOMIC MacroTool"
__version__ = "1.0.0"
__author__ = "AtomicArk"
__license__ = "MIT"
__copyright__ = "Copyright 2023 AtomicArk"

import sys
import os
import logging
from pathlib import Path

# Package metadata
PACKAGE_NAME = "atomic_macro_tool"
PACKAGE_AUTHOR = "AtomicArk"
PACKAGE_EMAIL = "atomicark@example.com"
PACKAGE_URL = "https://github.com/atomicark/atomic-macro-tool"
PACKAGE_DESCRIPTION = "Advanced Macro Recording and Automation Tool"

# Application paths
APP_DIR = Path(__file__).parent
RESOURCES_DIR = APP_DIR / "resources"
LANGS_DIR = RESOURCES_DIR / "langs"
ICONS_DIR = RESOURCES_DIR / "icons"
THEMES_DIR = RESOURCES_DIR / "themes"

# User data paths
USER_DIR = Path.home() / "Documents" / "AuTOMIC_MacroTool"
CONFIG_DIR = USER_DIR / "config"
MACROS_DIR = USER_DIR / "macros"
LOGS_DIR = USER_DIR / "logs"
DEBUG_DIR = USER_DIR / "debug"

# Ensure directories exist
for directory in [USER_DIR, CONFIG_DIR, MACROS_DIR, LOGS_DIR, DEBUG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            LOGS_DIR / f"atomic_macro_{__version__}.log",
            encoding='utf-8'
        )
    ]
)

# Logger for this module
logger = logging.getLogger(__name__)

def is_frozen():
    """Check if running as frozen executable."""
    return getattr(sys, 'frozen', False)

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if is_frozen():
        # Running as frozen executable
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development
        base_path = APP_DIR
    
    return base_path / relative_path

def is_portable():
    """Check if running in portable mode."""
    if is_frozen():
        portable_marker = Path(sys.executable).parent / "portable.txt"
        return portable_marker.exists()
    return False

def get_data_dir() -> Path:
    """Get data directory based on mode."""
    if is_portable():
        # Use local directory in portable mode
        return Path(sys.executable).parent / "data"
    return USER_DIR

def init_application():
    """Initialize application environment."""
    try:
        logger.info(f"Initializing {__title__} v{__version__}")
        logger.info(f"Running {'frozen' if is_frozen() else 'development'} mode")
        logger.info(f"Running {'portable' if is_portable() else 'installed'} mode")
        
        # Set application paths
        if is_portable():
            global USER_DIR, CONFIG_DIR, MACROS_DIR, LOGS_DIR, DEBUG_DIR
            base_dir = get_data_dir()
            USER_DIR = base_dir
            CONFIG_DIR = base_dir / "config"
            MACROS_DIR = base_dir / "macros"
            LOGS_DIR = base_dir / "logs"
            DEBUG_DIR = base_dir / "debug"
            
            # Create directories
            for directory in [USER_DIR, CONFIG_DIR, MACROS_DIR, LOGS_DIR, DEBUG_DIR]:
                directory.mkdir(parents=True, exist_ok=True)
        
        # Log system information
        import platform
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Data directory: {USER_DIR}")
        
        # Check write permissions
        for directory in [USER_DIR, CONFIG_DIR, MACROS_DIR, LOGS_DIR, DEBUG_DIR]:
            if not os.access(directory, os.W_OK):
                logger.warning(f"No write permission: {directory}")
        
        # Import optional dependencies
        try:
            import win32api
            import win32con
            logger.info("Windows API available")
        except ImportError:
            logger.warning("Windows API not available")
        
        try:
            import cv2
            logger.info("OpenCV available")
        except ImportError:
            logger.warning("OpenCV not available")
        
        logger.info("Initialization complete")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise

# Initialize on import
init_application()
