"""
Macro management module.
Copyright (c) 2025 AtomicArk
"""

import logging
import json
import threading
import time
import shutil
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

from ..utils.debug_helper import get_debug_helper
from .config_manager import config_manager
from .input_simulator import InputEvent
from .recorder import RecordingMode

@dataclass
class MacroMetadata:
    """Macro metadata."""
    name: str
    description: str = ""
    author: str = "AtomicArk"
    version: str = "1.0.0"
    created: str = ""
    modified: str = ""
    tags: List[str] = None
    recording_mode: str = "window"  # window, screen, directx
    target_window: Optional[str] = None
    hotkey: Optional[str] = None
    slot: Optional[int] = None
    
    def __post_init__(self):
        if not self.created:
            self.created = datetime.now().isoformat()
        if not self.modified:
            self.modified = self.created
        if self.tags is None:
            self.tags = []

@dataclass
class MacroData:
    """Macro data container."""
    metadata: MacroMetadata
    events: List[InputEvent]
    script: Optional[str] = None
    checksum: str = ""

class MacroManager:
    """Manages macro storage and organization."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('MacroManager')
            self.debug = get_debug_helper()
            
            # State
            self._macros: Dict[str, MacroData] = {}
            self._slots: Dict[int, str] = {}  # slot -> macro_id
            self._hotkeys: Dict[str, str] = {}  # hotkey -> macro_id
            
            # Auto-save
            self._last_save = time.time()
            self._save_interval = 300  # 5 minutes
            self._max_backups = 10
            
            # Initialize
            self._init_storage()
            self._initialized = True

    def _init_storage(self):
        """Initialize macro storage."""
        try:
            # Get macro directory
            macro_dir = Path(config_manager.get_value('macro_directory'))
            if not macro_dir:
                macro_dir = Path.home() / "Documents" / "AuTOMIC_MacroTool" / "macros"
            macro_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing macros
            for file in macro_dir.glob("*.atomic"):
                try:
                    macro = self.load_macro(file)
                    if macro:
                        self._macros[file.stem] = macro
                        
                        # Register slot
                        if macro.metadata.slot is not None:
                            self._slots[macro.metadata.slot] = file.stem
                        
                        # Register hotkey
                        if macro.metadata.hotkey:
                            self._hotkeys[macro.metadata.hotkey] = file.stem
                except Exception as e:
                    self.logger.error(f"Failed to load macro {file}: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize storage: {e}")

    def create_macro(self, name: str, events: List[InputEvent],
                    metadata: Optional[MacroMetadata] = None,
                    script: Optional[str] = None) -> Optional[str]:
        """Create new macro."""
        try:
            # Generate ID
            macro_id = hashlib.md5(name.encode()).hexdigest()[:8]
            
            # Create metadata if not provided
            if not metadata:
                metadata = MacroMetadata(name=name)
            
            # Create macro data
            macro = MacroData(
                metadata=metadata,
                events=events,
                script=script
            )
            
            # Calculate checksum
            macro.checksum = self._calculate_checksum(macro)
            
            # Save macro
            with self._lock:
                self._macros[macro_id] = macro
                
                # Register slot
                if metadata.slot is not None:
                    self._slots[metadata.slot] = macro_id
                
                # Register hotkey
                if metadata.hotkey:
                    self._hotkeys[metadata.hotkey] = macro_id
                
                self._auto_save()
            
            return macro_id
            
        except Exception as e:
            self.logger.error(f"Failed to create macro: {e}")
            return None

    def update_macro(self, macro_id: str, events: Optional[List[InputEvent]] = None,
                    metadata: Optional[MacroMetadata] = None,
                    script: Optional[str] = None) -> bool:
        """Update existing macro."""
        try:
            with self._lock:
                if macro_id not in self._macros:
                    return False
                
                macro = self._macros[macro_id]
                
                # Update events
                if events is not None:
                    macro.events = events
                
                # Update metadata
                if metadata:
                    # Unregister old slot
                    if macro.metadata.slot is not None:
                        self._slots.pop(macro.metadata.slot, None)
                    
                    # Unregister old hotkey
                    if macro.metadata.hotkey:
                        self._hotkeys.pop(macro.metadata.hotkey, None)
                    
                    # Update metadata
                    macro.metadata = metadata
                    
                    # Register new slot
                    if metadata.slot is not None:
                        self._slots[metadata.slot] = macro_id
                    
                    # Register new hotkey
                    if metadata.hotkey:
                        self._hotkeys[metadata.hotkey] = macro_id
                
                # Update script
                if script is not None:
                    macro.script = script
                
                # Update modification time
                macro.metadata.modified = datetime.now().isoformat()
                
                # Update checksum
                macro.checksum = self._calculate_checksum(macro)
                
                self._auto_save()
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to update macro: {e}")
            return False

    def delete_macro(self, macro_id: str) -> bool:
        """Delete macro."""
        try:
            with self._lock:
                if macro_id not in self._macros:
                    return False
                
                macro = self._macros[macro_id]
                
                # Unregister slot
                if macro.metadata.slot is not None:
                    self._slots.pop(macro.metadata.slot, None)
                
                # Unregister hotkey
                if macro.metadata.hotkey:
                    self._hotkeys.pop(macro.metadata.hotkey, None)
                
                # Delete file
                macro_file = self._get_macro_path(macro_id)
                if macro_file.exists():
                    macro_file.unlink()
                
                # Remove from memory
                del self._macros[macro_id]
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete macro: {e}")
            return False

    def get_macro(self, macro_id: str) -> Optional[MacroData]:
        """Get macro by ID."""
        try:
            with self._lock:
                return self._macros.get(macro_id)
        except Exception as e:
            self.logger.error(f"Failed to get macro: {e}")
            return None

    def get_macro_by_slot(self, slot: int) -> Optional[MacroData]:
        """Get macro by slot number."""
        try:
            with self._lock:
                macro_id = self._slots.get(slot)
                if macro_id:
                    return self._macros.get(macro_id)
                return None
        except Exception as e:
            self.logger.error(f"Failed to get macro by slot: {e}")
            return None

    def get_macro_by_hotkey(self, hotkey: str) -> Optional[MacroData]:
        """Get macro by hotkey."""
        try:
            with self._lock:
                macro_id = self._hotkeys.get(hotkey)
                if macro_id:
                    return self._macros.get(macro_id)
                return None
        except Exception as e:
            self.logger.error(f"Failed to get macro by hotkey: {e}")
            return None

    def list_macros(self) -> List[Tuple[str, MacroMetadata]]:
        """List all macros."""
        try:
            with self._lock:
                return [(id, macro.metadata) for id, macro in self._macros.items()]
        except Exception as e:
            self.logger.error(f"Failed to list macros: {e}")
            return []

    def _get_macro_path(self, macro_id: str) -> Path:
        """Get macro file path."""
        macro_dir = Path(config_manager.get_value('macro_directory'))
        return macro_dir / f"{macro_id}.atomic"

    def _calculate_checksum(self, macro: MacroData) -> str:
        """Calculate macro checksum."""
        try:
            # Convert to JSON
            data = {
                'metadata': asdict(macro.metadata),
                'events': [asdict(e) for e in macro.events],
                'script': macro.script
            }
            json_data = json.dumps(data, sort_keys=True)
            
            # Calculate hash
            return hashlib.sha256(json_data.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Failed to calculate checksum: {e}")
            return ""

    def load_macro(self, path: Path) -> Optional[MacroData]:
        """Load macro from file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create metadata
            metadata = MacroMetadata(**data['metadata'])
            
            # Create events
            events = [InputEvent(**e) for e in data['events']]
            
            # Create macro
            macro = MacroData(
                metadata=metadata,
                events=events,
                script=data.get('script'),
                checksum=data.get('checksum', '')
            )
            
            # Verify checksum
            if macro.checksum:
                current_checksum = self._calculate_checksum(macro)
                if current_checksum != macro.checksum:
                    self.logger.warning(f"Checksum mismatch for {path}")
            
            return macro
            
        except Exception as e:
            self.logger.error(f"Failed to load macro {path}: {e}")
            return None

    def save_macro(self, macro_id: str) -> bool:
        """Save macro to file."""
        try:
            with self._lock:
                if macro_id not in self._macros:
                    return False
                
                macro = self._macros[macro_id]
                path = self._get_macro_path(macro_id)
                
                # Convert to JSON
                data = {
                    'metadata': asdict(macro.metadata),
                    'events': [asdict(e) for e in macro.events],
                    'script': macro.script,
                    'checksum': macro.checksum
                }
                
                # Save file
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to save macro: {e}")
            return False

    def _auto_save(self):
        """Auto-save macros."""
        try:
            current_time = time.time()
            if current_time - self._last_save >= self._save_interval:
                # Save all macros
                for macro_id in self._macros:
                    self.save_macro(macro_id)
                
                self._last_save = current_time
                
                # Create backup
                self._create_backup()
            
        except Exception as e:
            self.logger.error(f"Failed to auto-save: {e}")

    def _create_backup(self):
        """Create backup of macro directory."""
        try:
            # Get directories
            macro_dir = Path(config_manager.get_value('macro_directory'))
            backup_dir = Path(config_manager.get_value('backup_directory'))
            if not backup_dir:
                backup_dir = macro_dir / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / f"macros_{timestamp}.zip"
            
            shutil.make_archive(
                str(backup_path.with_suffix('')),
                'zip',
                macro_dir
            )
            
            # Remove old backups
            backups = sorted(backup_dir.glob('*.zip'))
            while len(backups) > self._max_backups:
                backups[0].unlink()
                backups = backups[1:]
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")

    def cleanup(self):
        """Clean up resources."""
        try:
            # Save all macros
            with self._lock:
                for macro_id in self._macros:
                    self.save_macro(macro_id)
            
            # Create final backup
            self._create_backup()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
macro_manager = MacroManager()
