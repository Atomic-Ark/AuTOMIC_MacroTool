"""
AuTOMIC MacroTool - Advanced Macro Recording and Automation Tool
Copyright (c) 2025 AtomicArk
"""

__title__ = "AuTOMIC MacroTool"
__version__ = "1.0.0"
__author__ = "AtomicArk"
__author_email__ = "atomicarkft@gmail.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 AtomicArk"
__website__ = "https://github.com/Atomic-Ark/AuTOMIC_MacroTool"
__description__ = "Advanced Macro Recording and Automation Tool"
__release_date__ = "2025-03-15"

# Package information
PACKAGE_NAME = "atomic_macro"
PACKAGE_DIR = "AuTOMIC_MacroTool"

# Application information
APP_NAME = "AuTOMIC MacroTool"
APP_ID = "com.atomicark.atomic_macro"
APP_ICON = "resources/icons/app.ico"
APP_CONFIG = "config.json"

# Feature flags
FEATURES = {
    'stealth_mode': True,      # Enable stealth mode input simulation
    'directx_support': True,   # Enable DirectX window support
    'cloud_sync': False,       # Future: Cloud synchronization
    'plugins': False,          # Future: Plugin system
    'marketplace': False,      # Future: Macro marketplace
    'ai_assist': False,        # Future: AI-assisted automation
}

# Default configuration
DEFAULT_CONFIG = {
    'language': '',            # Auto-detect if empty
    'theme': '',              # Auto-detect if empty
    'ui_scale': 1.0,
    'autostart': False,
    'minimize_to_tray': True,
    'check_updates': True,
}

# Supported languages
SUPPORTED_LANGUAGES = {
    'en_US': 'English',
    'pl_PL': 'Polski',
    'de_DE': 'Deutsch',
    'fr_FR': 'Français',
    'it_IT': 'Italiano',
    'es_ES': 'Español',
}

# Supported themes
SUPPORTED_THEMES = [
    'light',
    'dark',
    'system',
    'custom',
]

# File extensions
FILE_EXTENSIONS = {
    'macro': '.atomic',        # Macro files
    'script': '.py',           # Script files
    'theme': '.qss',          # Theme files
    'config': '.json',         # Configuration files
    'backup': '.zip',         # Backup archives
}

# API version
API_VERSION = "1.0"

# Documentation URLs
DOCS = {
    'main': f"{__website__}/wiki",
    'api': f"{__website__}/wiki/api",
    'scripting': f"{__website__}/wiki/scripting",
    'examples': f"{__website__}/wiki/examples",
}

# Update information
UPDATE_INFO = {
    'check_url': f"{__website__}/releases/latest",
    'download_url': f"{__website__}/releases/download",
    'changelog_url': f"{__website__}/releases",
    'min_version': "1.0.0",
}

# Contact information
CONTACT_INFO = {
    'email': __author_email__,
    'website': __website__,
    'issues': f"{__website__}/issues",
    'discussions': f"{__website__}/discussions",
}

# System requirements
SYSTEM_REQUIREMENTS = {
    'os': 'Windows',
    'python': ">=3.8",
    'memory': "256MB",
    'storage': "100MB",
}

def get_version():
    """Get package version."""
    return __version__

def get_app_info():
    """Get application information."""
    return {
        'name': APP_NAME,
        'version': __version__,
        'author': __author__,
        'email': __author_email__,
        'license': __license__,
        'website': __website__,
        'description': __description__,
        'release_date': __release_date__,
    }

def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled."""
    return FEATURES.get(feature, False)

def get_supported_languages():
    """Get supported languages."""
    return SUPPORTED_LANGUAGES.copy()

def get_supported_themes():
    """Get supported themes."""
    return SUPPORTED_THEMES.copy()

def get_file_extension(file_type: str) -> str:
    """Get file extension for given type."""
    return FILE_EXTENSIONS.get(file_type, '')

def get_docs_url(section: str = 'main') -> str:
    """Get documentation URL."""
    return DOCS.get(section, DOCS['main'])

def get_update_info():
    """Get update information."""
    return UPDATE_INFO.copy()

def get_contact_info():
    """Get contact information."""
    return CONTACT_INFO.copy()

def get_system_requirements():
    """Get system requirements."""
    return SYSTEM_REQUIREMENTS.copy()
