"""
Window management and detection module.
"""

import logging
import threading
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
import win32gui
import win32api
import win32con
import win32process
import cv2
import numpy as np
from PIL import ImageGrab

from ..utils.debug_helper import get_debug_helper

@dataclass
class WindowInfo:
    """Window information container."""
    hwnd: int
    title: str
    class_name: str
    process_id: int
    process_name: str
    rect: Tuple[int, int, int, int]  # left, top, right, bottom
    is_visible: bool
    is_minimized: bool
    is_maximized: bool
    dpi_scale: float

class SmartWindowManager:
    """Manages window detection and interaction."""
    
    def __init__(self):
        self.logger = logging.getLogger('WindowManager')
        self.debug = get_debug_helper()
        
        # State
        self._windows: Dict[int, WindowInfo] = {}
        self._active_window: Optional[int] = None
        self._lock = threading.Lock()
        
        # Window monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        
        # Callbacks
        self.on_window_change: Optional[Callable[[int], None]] = None
        
        # Start monitoring
        self._start_monitoring()

    def _start_monitoring(self):
        """Start window monitoring thread."""
        try:
            def monitor():
                while not self._stop_flag.is_set():
                    try:
                        # Get current active window
                        hwnd = win32gui.GetForegroundWindow()
                        
                        # Check if changed
                        if hwnd != self._active_window:
                            with self._lock:
                                self._active_window = hwnd
                                if self.on_window_change:
                                    self.on_window_change(hwnd)
                        
                        # Update window list periodically
                        self.refresh_windows()
                        
                        # Sleep
                        self._stop_flag.wait(0.1)
                        
                    except Exception as e:
                        self.logger.error(f"Error in window monitor: {e}")
            
            self._monitor_thread = threading.Thread(
                target=monitor,
                daemon=True
            )
            self._monitor_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start window monitor: {e}")

    def refresh_windows(self):
        """Update window list."""
        try:
            windows = {}
            
            def enum_windows_callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    try:
                        info = self._get_window_info(hwnd)
                        if info:
                            windows[hwnd] = info
                    except:
                        pass
            
            win32gui.EnumWindows(enum_windows_callback, None)
            
            with self._lock:
                self._windows = windows
            
        except Exception as e:
            self.logger.error(f"Error refreshing windows: {e}")

    def _get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
        """Get window information."""
        try:
            # Skip invalid windows
            if not hwnd or not win32gui.IsWindow(hwnd):
                return None
            
            # Get window properties
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            # Skip empty or system windows
            if not title or class_name in ['Shell_TrayWnd', 'Progman']:
                return None
            
            # Get process info
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            process_handle = win32api.OpenProcess(
                win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
                False,
                process_id
            )
            process_name = win32process.GetModuleFileNameEx(process_handle, 0)
            process_handle.close()
            
            # Get window state
            placement = win32gui.GetWindowPlacement(hwnd)
            is_minimized = placement[1] == win32con.SW_SHOWMINIMIZED
            is_maximized = placement[1] == win32con.SW_SHOWMAXIMIZED
            
            # Get window rect
            rect = win32gui.GetWindowRect(hwnd)
            
            # Get DPI scale
            dpi = win32gui.GetDpiForWindow(hwnd)
            dpi_scale = dpi / 96.0
            
            return WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                process_id=process_id,
                process_name=process_name,
                rect=rect,
                is_visible=win32gui.IsWindowVisible(hwnd),
                is_minimized=is_minimized,
                is_maximized=is_maximized,
                dpi_scale=dpi_scale
            )
            
        except Exception as e:
            self.logger.error(f"Error getting window info: {e}")
            return None

    def get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
        """Get information about specific window."""
        try:
            with self._lock:
                # Try from cache first
                if hwnd in self._windows:
                    return self._windows[hwnd]
                
                # Get fresh info
                return self._get_window_info(hwnd)
            
        except Exception as e:
            self.logger.error(f"Error getting window info: {e}")
            return None

    def get_active_window(self) -> Optional[WindowInfo]:
        """Get active window information."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            return self.get_window_info(hwnd)
        except Exception as e:
            self.logger.error(f"Error getting active window: {e}")
            return None

    def get_window_at(self, x: int, y: int) -> Optional[WindowInfo]:
        """Get window at screen coordinates."""
        try:
            hwnd = win32gui.WindowFromPoint((x, y))
            return self.get_window_info(hwnd)
        except Exception as e:
            self.logger.error(f"Error getting window at point: {e}")
            return None

    def get_window_by_title(self, title: str) -> Optional[WindowInfo]:
        """Find window by title."""
        try:
            with self._lock:
                for window in self._windows.values():
                    if title.lower() in window.title.lower():
                        return window
            return None
        except Exception as e:
            self.logger.error(f"Error finding window: {e}")
            return None

    def get_window_screenshot(self, hwnd: int) -> Optional[np.ndarray]:
        """Get screenshot of specific window."""
        try:
            window = self.get_window_info(hwnd)
            if not window:
                return None
            
            # Get window bounds
            left, top, right, bottom = window.rect
            width = right - left
            height = bottom - top
            
            # Capture window
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            
            # Convert to OpenCV format
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            self.logger.error(f"Error capturing window: {e}")
            return None

    def bring_window_to_front(self, hwnd: int) -> bool:
        """Bring window to foreground."""
        try:
            if not win32gui.IsWindow(hwnd):
                return False
            
            # Show window if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # Bring to front
            win32gui.SetForegroundWindow(hwnd)
            return True
            
        except Exception as e:
            self.logger.error(f"Error bringing window to front: {e}")
            return False

    def set_window_pos(self, hwnd: int, x: int, y: int) -> bool:
        """Set window position."""
        try:
            if not win32gui.IsWindow(hwnd):
                return False
            
            # Get current size
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Move window
            win32gui.SetWindowPos(
                hwnd,
                0,
                x,
                y,
                width,
                height,
                win32con.SWP_NOSIZE | win32con.SWP_NOZORDER
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting window position: {e}")
            return False

    def set_window_size(self, hwnd: int, width: int, height: int) -> bool:
        """Set window size."""
        try:
            if not win32gui.IsWindow(hwnd):
                return False
            
            # Get current position
            left, top, _, _ = win32gui.GetWindowRect(hwnd)
            
            # Resize window
            win32gui.SetWindowPos(
                hwnd,
                0,
                left,
                top,
                width,
                height,
                win32con.SWP_NOMOVE | win32con.SWP_NOZORDER
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting window size: {e}")
            return False

    def get_relative_pos(self, hwnd: int, x: int, y: int) -> Optional[Tuple[float, float]]:
        """Convert absolute coordinates to window-relative."""
        try:
            window = self.get_window_info(hwnd)
            if not window:
                return None
            
            # Get window bounds
            left, top, right, bottom = window.rect
            width = right - left
            height = bottom - top
            
            # Calculate relative position
            rel_x = (x - left) / width
            rel_y = (y - top) / height
            
            return (rel_x, rel_y)
            
        except Exception as e:
            self.logger.error(f"Error calculating relative position: {e}")
            return None

    def get_absolute_pos(self, hwnd: int, rel_x: float, rel_y: float) -> Optional[Tuple[int, int]]:
        """Convert window-relative coordinates to absolute."""
        try:
            window = self.get_window_info(hwnd)
            if not window:
                return None
            
            # Get window bounds
            left, top, right, bottom = window.rect
            width = right - left
            height = bottom - top
            
            # Calculate absolute position
            abs_x = int(left + (width * rel_x))
            abs_y = int(top + (height * rel_y))
            
            return (abs_x, abs_y)
            
        except Exception as e:
            self.logger.error(f"Error calculating absolute position: {e}")
            return None

    def cleanup(self):
        """Clean up resources."""
        try:
            self._stop_flag.set()
            
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=1.0)
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
window_manager = SmartWindowManager()
