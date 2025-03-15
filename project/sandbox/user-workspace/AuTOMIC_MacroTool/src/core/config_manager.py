"""
Configuration management module.
Copyright (c) 2025 AtomicArk
"""

import logging
import json
import threading
from typing import Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict, field
import locale
import darkdetect

from ..utils.debug_helper import get_debug_helper, DebugLevel

@dataclass
class HotkeyConfig:
    """Hotkey configuration."""
    record_start: str = 'F1'
    record_stop: str = 'F1'
    play_start: str = 'F2'
    play_stop: str = 'F2'
    play_pause: str = 'F3'
    script_execute: str = 'F4'
    script_stop: str = 'F4'
    panic_button: str = 'Ctrl+Alt+P'
    show_hide: str = 'Ctrl+Alt+H'

@dataclass
class RecordingConfig:
    """Recording configuration."""
    record_mouse: bool = True
    record_keyboard: bool = True
    record_delays: bool = True
    min_delay: float = 0.01
    window_mode: bool = True
    directx_mode: bool = False

@dataclass
class PlaybackConfig:
    """Playback configuration."""
    repeat_mode: str = 'once'  # 'once', 'loop', 'count'
    repeat_count: int = 1
    speed: float = 1.0
    randomize_delays: bool = False
    random_factor: float = 0.2
    stop_on_input: bool = True
    restore_mouse: bool = True
    stealth_mode: bool = False

@dataclass
class AppConfig:
    """Application configuration."""
    # General
    language: str = ''  # Auto-detect if empty
    theme: str = ''  # Auto-detect if empty
    ui_scale: float = 1.0
    autostart: bool = False
    minimize_to_tray: bool = True
    check_updates: bool = True
    
    # Directories
    macro_directory: str = ''  # Default to user documents
    backup_directory: str = ''  # Default to macro directory
    
    # Hotkeys
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    
    # Recording
    recording: RecordingConfig = field(default_factory=RecordingConfig)
    
    # Playback
    playback: PlaybackConfig = field(default_factory=PlaybackConfig)
    
    # Advanced
    debug_level: str = 'basic'  # 'none', 'basic', 'detailed', 'verbose'
    performance_mode: bool = False
    save_window_state: bool = True
    backup_interval: int = 5  # minutes
    max_backups: int = 10

class ConfigManager:
    """Manages application configuration."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('ConfigManager')
            self.debug = get_debug_helper()
            
            # State
            self.config = AppConfig()
            self._config_file: Optional[Path] = None
            self._backup_file: Optional[Path] = None
            self._initialized = False
            
            # Initialize
            self._init_config()
            self._initialized = True

    def _init_config(self):
        """Initialize configuration."""
        try:
            # Get config directory
            config_dir = Path.home() / "Documents" / "AuTOMIC_MacroTool" / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            self._config_file = config_dir / "config.json"
            self._backup_file = config_dir / "config.backup.json"
            
            # Load or create config
            if self._config_file.exists():
                self.load_config()
            else:
                self._init_default_config()
                self.save_config()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize config: {e}")
            self._init_default_config()

    def _init_default_config(self):
        """Initialize default configuration."""
        try:
            # Get system language
            system_lang = locale.getdefaultlocale()[0]
            if system_lang:
                self.config.language = system_lang
            
            # Get system theme
            system_theme = darkdetect.theme()
            if system_theme:
                self.config.theme = system_theme.lower()
            
            # Set directories
            docs_dir = Path.home() / "Documents" / "AuTOMIC_MacroTool"
            self.config.macro_directory = str(docs_dir / "macros")
            self.config.backup_directory = str(docs_dir / "backups")
            
            # Create directories
            Path(self.config.macro_directory).mkdir(parents=True, exist_ok=True)
            Path(self.config.backup_directory).mkdir(parents=True, exist_ok=True)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize default config: {e}")

    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            if not self._config_file or not self._config_file.exists():
                return False
            
            # Load config
            with open(self._config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to dataclass
            config_dict = {}
            
            # General settings
            for key in ['language', 'theme', 'ui_scale', 'autostart',
                       'minimize_to_tray', 'check_updates', 'macro_directory',
                       'backup_directory', 'debug_level', 'performance_mode',
                       'save_window_state', 'backup_interval', 'max_backups']:
                if key in data:
                    config_dict[key] = data[key]
            
            # Hotkeys
            if 'hotkeys' in data:
                config_dict['hotkeys'] = HotkeyConfig(**data['hotkeys'])
            
            # Recording
            if 'recording' in data:
                config_dict['recording'] = RecordingConfig(**data['recording'])
            
            # Playback
            if 'playback' in data:
                config_dict['playback'] = PlaybackConfig(**data['playback'])
            
            # Update config
            self.config = AppConfig(**config_dict)
            
            # Apply debug level
            debug_level = getattr(DebugLevel, self.config.debug_level.upper(),
                                DebugLevel.BASIC)
            self.debug.set_debug_level(debug_level)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return False

    def save_config(self) -> bool:
        """Save configuration to file."""
        try:
            if not self._config_file:
                return False
            
            # Create backup
            if self._config_file.exists() and self._backup_file:
                self._config_file.rename(self._backup_file)
            
            # Convert to dict
            config_dict = asdict(self.config)
            
            # Save config
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            
            # Restore backup
            if self._backup_file and self._backup_file.exists():
                self._backup_file.rename(self._config_file)
            
            return False

    def reset_config(self) -> bool:
        """Reset configuration to defaults."""
        try:
            self._init_default_config()
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Failed to reset config: {e}")
            return False

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        try:
            # Split nested keys
            keys = key.split('.')
            value = self.config
            
            # Navigate to value
            for k in keys:
                value = getattr(value, k)
            
            return value
            
        except Exception:
            return default

    def set_value(self, key: str, value: Any) -> bool:
        """Set configuration value."""
        try:
            # Split nested keys
            keys = key.split('.')
            target = self.config
            
            # Navigate to parent
            for k in keys[:-1]:
                target = getattr(target, k)
            
            # Set value
            setattr(target, keys[-1], value)
            
            # Save config
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Failed to set config value: {e}")
            return False

    def cleanup(self):
        """Clean up resources."""
        try:
            # Save config
            self.save_config()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
config_manager = ConfigManager()
