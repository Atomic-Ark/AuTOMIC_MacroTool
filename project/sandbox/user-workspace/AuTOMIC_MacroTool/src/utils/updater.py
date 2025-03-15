"""
Application update management module.
Copyright (c) 2025 AtomicArk
"""

import logging
import threading
import json
import os
import sys
import shutil
import tempfile
import hashlib
from typing import Optional, Dict, Callable
from enum import Enum, auto
from pathlib import Path
import requests
from packaging import version

from .. import __version__
from .debug_helper import get_debug_helper

class UpdateState(Enum):
    """Update states."""
    IDLE = auto()
    CHECKING = auto()
    AVAILABLE = auto()
    DOWNLOADING = auto()
    INSTALLING = auto()
    ERROR = auto()

class UpdateInfo:
    """Update information container."""
    
    def __init__(self, data: Dict):
        self.version = data.get('version', '')
        self.url = data.get('url', '')
        self.checksum = data.get('checksum', '')
        self.changelog = data.get('changelog', '')
        self.release_date = data.get('release_date', '')
        self.min_version = data.get('min_version', '0.0.0')
        self.is_critical = data.get('is_critical', False)

class UpdateManager:
    """Manages application updates."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('UpdateManager')
            self.debug = get_debug_helper()
            
            # State
            self.state = UpdateState.IDLE
            self._update_info: Optional[UpdateInfo] = None
            self._download_progress = 0
            self._error_message = ''
            
            # Threading
            self._check_thread: Optional[threading.Thread] = None
            self._download_thread: Optional[threading.Thread] = None
            self._lock = threading.Lock()
            
            # Callbacks
            self.on_state_change: Optional[Callable[[UpdateState], None]] = None
            self.on_progress: Optional[Callable[[float], None]] = None
            
            # Configuration
            self._update_url = "https://api.github.com/repos/Atomic-Ark/AuTOMIC_MacroTool/releases/latest"
            self._contact_email = "atomicarkft@gmail.com"
            self._initialized = True

    def check_for_updates(self, silent: bool = False) -> bool:
        """Check for available updates."""
        try:
            if self.state not in [UpdateState.IDLE, UpdateState.ERROR]:
                return False
            
            with self._lock:
                self.state = UpdateState.CHECKING
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                self._check_thread = threading.Thread(
                    target=self._check_updates_thread,
                    args=(silent,),
                    daemon=True
                )
                self._check_thread.start()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to check updates: {e}")
            return False

    def _check_updates_thread(self, silent: bool):
        """Update check thread."""
        try:
            # Get current version
            current_ver = version.parse(__version__)
            
            # Get latest release info
            response = requests.get(
                self._update_url,
                headers={'Accept': 'application/vnd.github.v3+json'},
                timeout=10
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            latest_ver = version.parse(data['tag_name'].lstrip('v'))
            
            # Check version
            if latest_ver > current_ver:
                # Get update info
                assets = data['assets']
                if not assets:
                    raise ValueError("No update assets found")
                
                installer = next(
                    (a for a in assets if a['name'].endswith('.exe')),
                    None
                )
                if not installer:
                    raise ValueError("No installer found")
                
                # Create update info
                self._update_info = UpdateInfo({
                    'version': str(latest_ver),
                    'url': installer['browser_download_url'],
                    'checksum': installer.get('checksum', ''),
                    'changelog': data['body'],
                    'release_date': data['published_at'],
                    'min_version': data.get('min_version', '0.0.0'),
                    'is_critical': data.get('is_critical', False)
                })
                
                # Update state
                with self._lock:
                    self.state = UpdateState.AVAILABLE
                    if self.on_state_change:
                        self.on_state_change(self.state)
                
            elif not silent:
                self.logger.info("Application is up to date")
                
            # Reset state if no update
            with self._lock:
                if self.state == UpdateState.CHECKING:
                    self.state = UpdateState.IDLE
                    if self.on_state_change:
                        self.on_state_change(self.state)
            
        except Exception as e:
            self.logger.error(f"Update check failed: {e}")
            self._error_message = str(e)
            
            with self._lock:
                self.state = UpdateState.ERROR
                if self.on_state_change:
                    self.on_state_change(self.state)

    def download_update(self) -> bool:
        """Download available update."""
        try:
            if self.state != UpdateState.AVAILABLE or not self._update_info:
                return False
            
            with self._lock:
                self.state = UpdateState.DOWNLOADING
                self._download_progress = 0
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                self._download_thread = threading.Thread(
                    target=self._download_thread_func,
                    daemon=True
                )
                self._download_thread.start()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to start download: {e}")
            return False

    def _download_thread_func(self):
        """Update download thread."""
        try:
            if not self._update_info:
                raise ValueError("No update info")
            
            # Create temp directory
            temp_dir = Path(tempfile.mkdtemp())
            installer_path = temp_dir / "AuTOMIC_MacroTool_Setup.exe"
            
            # Download file
            response = requests.get(
                self._update_info.url,
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            # Get file size
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            # Download chunks
            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        if total_size:
                            progress = downloaded / total_size
                            self._download_progress = progress
                            if self.on_progress:
                                self.on_progress(progress)
            
            # Verify checksum if available
            if self._update_info.checksum:
                with open(installer_path, 'rb') as f:
                    checksum = hashlib.sha256(f.read()).hexdigest()
                    if checksum != self._update_info.checksum:
                        raise ValueError("Checksum verification failed")
            
            # Start installation
            self._install_update(installer_path)
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            self._error_message = str(e)
            
            with self._lock:
                self.state = UpdateState.ERROR
                if self.on_state_change:
                    self.on_state_change(self.state)

    def _install_update(self, installer_path: Path):
        """Install downloaded update."""
        try:
            with self._lock:
                self.state = UpdateState.INSTALLING
                if self.on_state_change:
                    self.on_state_change(self.state)
            
            # Run installer
            import subprocess
            subprocess.Popen([
                str(installer_path),
                '/SILENT',  # Silent installation
                '/CLOSEAPPLICATIONS',  # Close running instances
                '/RESTARTAPPLICATIONS',  # Restart after install
                '/NOCANCEL'  # Disable cancel button
            ])
            
            # Exit application
            sys.exit(0)
            
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            self._error_message = str(e)
            
            with self._lock:
                self.state = UpdateState.ERROR
                if self.on_state_change:
                    self.on_state_change(self.state)

    def get_update_info(self) -> Optional[UpdateInfo]:
        """Get available update information."""
        return self._update_info

    def get_error_message(self) -> str:
        """Get last error message."""
        return self._error_message

    def get_download_progress(self) -> float:
        """Get download progress (0-1)."""
        return self._download_progress

    def cleanup(self):
        """Clean up resources."""
        try:
            # Wait for threads
            if self._check_thread and self._check_thread.is_alive():
                self._check_thread.join(timeout=1.0)
            
            if self._download_thread and self._download_thread.is_alive():
                self._download_thread.join(timeout=1.0)
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
update_manager = UpdateManager()
