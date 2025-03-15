"""
Window management module.
Copyright (c) 2025 AtomicArk
"""

import logging
import threading
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
import win32gui
import win32con
import win32process
import win32api
import psutil
from ctypes import windll, byref, create_unicode_buffer, sizeof
from ctypes.wintypes import RECT, DWORD

from ..utils.debug_helper import get_debug_helper

@dataclass
class WindowInfo:
    """Window information container."""
    handle: int
    title: str
    class_name: str
    process_id: int
    process_name: str
    rect: RECT
    is_visible: bool
    is_enabled: bool
    is_unicode: bool
    is_zoomed: bool
    parent: Optional[int] = None
    children: List[int] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

class WindowManager:
    """Manages window detection and interaction."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('WindowManager')
            self.debug = get_debug_helper()
            
            # State
            self._windows: Dict[int, WindowInfo] = {}
            self._active_window: Optional[int] = None
            self._window_callbacks: Dict[str, List[Callable]] = {}
            
            # Initialize
            self._initialized = True

    def refresh_windows(self) -> None:
        """Refresh window list."""
        try:
            with self._lock:
                self._windows.clear()
                win32gui.EnumWindows(self._enum_window_proc, None)
                
        except Exception as e:
            self.logger.error(f"Failed to refresh windows: {e}")

    def _enum_window_proc(self, hwnd: int, _) -> bool:
        """Window enumeration callback."""
        try:
            # Skip invisible windows
            if not win32gui.IsWindowVisible(hwnd):
                return True
            
            # Get window info
            info = self._get_window_info(hwnd)
            if info:
                self._windows[hwnd] = info
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enumerate window: {e}")
            return True

    def _get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
        """Get window information."""
        try:
            # Get window properties
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            # Skip system windows
            if not title or class_name in ['Shell_TrayWnd', 'Progman']:
                return None
            
            # Get process info
            process_id = DWORD()
            win32process.GetWindowThreadProcessId(hwnd, byref(process_id))
            
            try:
                process = psutil.Process(process_id.value)
                process_name = process.name()
            except psutil.NoSuchProcess:
                process_name = "Unknown"
            
            # Get window rect
            rect = RECT()
            win32gui.GetWindowRect(hwnd, byref(rect))
            
            # Get window state
            is_visible = win32gui.IsWindowVisible(hwnd)
            is_enabled = win32gui.IsWindowEnabled(hwnd)
            is_unicode = win32gui.IsWindowUnicode(hwnd)
            is_zoomed = win32gui.IsZoomed(hwnd)
            
            # Get parent/child relationship
            parent = win32gui.GetParent(hwnd)
            children = []
            
            def enum_child_proc(child_hwnd: int, _) -> bool:
                children.append(child_hwnd)
                return True
            
            win32gui.EnumChildWindows(hwnd, enum_child_proc, None)
            
            return WindowInfo(
                handle=hwnd,
                title=title,
                class_name=class_name,
                process_id=process_id.value,
                process_name=process_name,
                rect=rect,
                is_visible=is_visible,
                is_enabled=is_enabled,
                is_unicode=is_unicode,
                is_zoomed=is_zoomed,
                parent=parent if parent else None,
                children=children
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get window info: {e}")
            return None

    def get_window(self, hwnd: int) -> Optional[WindowInfo]:
        """Get window information by handle."""
        try:
            with self._lock:
                if hwnd not in self._windows:
                    info = self._get_window_info(hwnd)
                    if info:
                        self._windows[hwnd] = info
                return self._windows.get(hwnd)
            
        except Exception as e:
            self.logger.error(f"Failed to get window: {e}")
            return None

    def find_window(self, title: str = None, class_name: str = None,
                   process_name: str = None) -> Optional[WindowInfo]:
        """Find window by properties."""
        try:
            self.refresh_windows()
            
            with self._lock:
                for window in self._windows.values():
                    if title and title.lower() not in window.title.lower():
                        continue
                    if class_name and class_name != window.class_name:
                        continue
                    if process_name and process_name.lower() not in window.process_name.lower():
                        continue
                    return window
                
                return None
            
        except Exception as e:
            self.logger.error(f"Failed to find window: {e}")
            return None

    def get_active_window(self) -> Optional[WindowInfo]:
        """Get active window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            return self.get_window(hwnd)
            
        except Exception as e:
            self.logger.error(f"Failed to get active window: {e}")
            return None

    def bring_to_front(self, hwnd: int) -> bool:
        """Bring window to front."""
        try:
            if not win32gui.IsWindow(hwnd):
                return False
            
            # Get window state
            placement = win32gui.GetWindowPlacement(hwnd)
            
            # Restore if minimized
            if placement[1] == win32con.SW_SHOWMINIMIZED:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # Set foreground window
            win32gui.SetForegroundWindow(hwnd)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to bring window to front: {e}")
            return False

    def get_window_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        """Get window rectangle."""
        try:
            if not win32gui.IsWindow(hwnd):
                return None
            
            rect = win32gui.GetWindowRect(hwnd)
            return rect
            
        except Exception as e:
            self.logger.error(f"Failed to get window rect: {e}")
            return None

    def get_client_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        """Get client area rectangle."""
        try:
            if not win32gui.IsWindow(hwnd):
                return None
            
            rect = win32gui.GetClientRect(hwnd)
            point = win32gui.ClientToScreen(hwnd, (0, 0))
            
            return (
                point[0],
                point[1],
                point[0] + rect[2],
                point[1] + rect[3]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get client rect: {e}")
            return None

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register window event callback."""
        try:
            with self._lock:
                if event not in self._window_callbacks:
                    self._window_callbacks[event] = []
                self._window_callbacks[event].append(callback)
            
        except Exception as e:
            self.logger.error(f"Failed to register callback: {e}")

    def unregister_callback(self, event: str, callback: Callable) -> None:
        """Unregister window event callback."""
        try:
            with self._lock:
                if event in self._window_callbacks:
                    self._window_callbacks[event].remove(callback)
            
        except Exception as e:
            self.logger.error(f"Failed to unregister callback: {e}")

    def _notify_callbacks(self, event: str, *args, **kwargs) -> None:
        """Notify registered callbacks."""
        try:
            with self._lock:
                if event in self._window_callbacks:
                    for callback in self._window_callbacks[event]:
                        try:
                            callback(*args, **kwargs)
                        except Exception as e:
                            self.logger.error(f"Callback error: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to notify callbacks: {e}")

    def cleanup(self):
        """Clean up resources."""
        try:
            with self._lock:
                self._windows.clear()
                self._window_callbacks.clear()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
window_manager = WindowManager()
