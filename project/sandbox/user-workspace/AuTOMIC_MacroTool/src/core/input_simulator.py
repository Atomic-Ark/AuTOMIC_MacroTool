"""
Input simulation module.
Copyright (c) 2025 AtomicArk
"""

import logging
import threading
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum, auto
import time
import ctypes
import win32api
import win32con
import keyboard
import mouse
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse

from ..utils.debug_helper import get_debug_helper
from ..core.config_manager import config_manager

class InputType(Enum):
    """Input event types."""
    KEYBOARD = auto()
    MOUSE_MOVE = auto()
    MOUSE_CLICK = auto()
    MOUSE_SCROLL = auto()
    MOUSE_DRAG = auto()

class MouseButton(Enum):
    """Mouse button types."""
    LEFT = auto()
    RIGHT = auto()
    MIDDLE = auto()

@dataclass
class InputEvent:
    """Input event container."""
    type: InputType
    timestamp: float
    data: Dict
    window_handle: Optional[int] = None
    window_title: Optional[str] = None
    relative_pos: Optional[Tuple[float, float]] = None

class StealthMode:
    """Stealth mode input simulation using Interception driver."""
    
    def __init__(self):
        self.logger = logging.getLogger('StealthMode')
        self._initialized = False
        
        try:
            import interception
            self._interception = interception.Interception()
            self._initialized = True
        except Exception as e:
            self.logger.error(f"Failed to initialize stealth mode: {e}")

    def is_available(self) -> bool:
        """Check if stealth mode is available."""
        return self._initialized

    def send_keyboard(self, scan_code: int, key_down: bool) -> bool:
        """Send keyboard input."""
        try:
            if not self._initialized:
                return False
            
            stroke = self._interception.KeyStroke(
                code=scan_code,
                state=1 if key_down else 0
            )
            return self._interception.send(stroke)
            
        except Exception as e:
            self.logger.error(f"Failed to send keyboard input: {e}")
            return False

    def send_mouse(self, x: int, y: int, buttons: int = 0,
                  wheel: int = 0) -> bool:
        """Send mouse input."""
        try:
            if not self._initialized:
                return False
            
            stroke = self._interception.MouseStroke(
                x=x,
                y=y,
                state=buttons,
                rolling=wheel
            )
            return self._interception.send(stroke)
            
        except Exception as e:
            self.logger.error(f"Failed to send mouse input: {e}")
            return False

class InputSimulator:
    """Simulates keyboard and mouse input."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('InputSimulator')
            self.debug = get_debug_helper()
            
            # State
            self._stealth_mode = StealthMode()
            self._use_stealth = False
            self._last_pos: Optional[Tuple[int, int]] = None
            self._pressed_keys: Dict[str, bool] = {}
            self._pressed_buttons: Dict[MouseButton, bool] = {}
            
            # Initialize
            self._initialized = True

    def set_stealth_mode(self, enabled: bool) -> bool:
        """Enable/disable stealth mode."""
        try:
            if enabled and not self._stealth_mode.is_available():
                self.logger.warning("Stealth mode not available")
                return False
            
            self._use_stealth = enabled
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set stealth mode: {e}")
            return False

    def key_press(self, key: str, duration: Optional[float] = None) -> bool:
        """Simulate key press."""
        try:
            if self._use_stealth:
                # Convert key to scan code
                scan_code = keyboard.key_to_scan_codes(key)[0]
                
                # Press key
                if not self._stealth_mode.send_keyboard(scan_code, True):
                    return False
                
                # Hold if duration specified
                if duration:
                    time.sleep(duration)
                
                # Release key
                return self._stealth_mode.send_keyboard(scan_code, False)
            
            else:
                keyboard.press(key)
                if duration:
                    time.sleep(duration)
                keyboard.release(key)
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to simulate key press: {e}")
            return False

    def key_down(self, key: str) -> bool:
        """Simulate key down."""
        try:
            if key in self._pressed_keys and self._pressed_keys[key]:
                return True
            
            if self._use_stealth:
                scan_code = keyboard.key_to_scan_codes(key)[0]
                result = self._stealth_mode.send_keyboard(scan_code, True)
            else:
                keyboard.press(key)
                result = True
            
            if result:
                self._pressed_keys[key] = True
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to simulate key down: {e}")
            return False

    def key_up(self, key: str) -> bool:
        """Simulate key up."""
        try:
            if key not in self._pressed_keys or not self._pressed_keys[key]:
                return True
            
            if self._use_stealth:
                scan_code = keyboard.key_to_scan_codes(key)[0]
                result = self._stealth_mode.send_keyboard(scan_code, False)
            else:
                keyboard.release(key)
                result = True
            
            if result:
                self._pressed_keys[key] = False
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to simulate key up: {e}")
            return False

    def mouse_move(self, x: int, y: int, duration: Optional[float] = None,
                  relative: bool = False) -> bool:
        """Simulate mouse movement."""
        try:
            # Get current position
            current_x, current_y = win32api.GetCursorPos()
            
            if relative:
                target_x = current_x + x
                target_y = current_y + y
            else:
                target_x = x
                target_y = y
            
            if duration:
                # Smooth movement
                steps = int(duration * 60)  # 60 FPS
                dx = (target_x - current_x) / steps
                dy = (target_y - current_y) / steps
                
                for i in range(steps):
                    x = int(current_x + dx * i)
                    y = int(current_y + dy * i)
                    
                    if self._use_stealth:
                        if not self._stealth_mode.send_mouse(x, y):
                            return False
                    else:
                        win32api.SetCursorPos((x, y))
                    
                    time.sleep(duration / steps)
            
            # Final position
            if self._use_stealth:
                result = self._stealth_mode.send_mouse(target_x, target_y)
            else:
                win32api.SetCursorPos((target_x, target_y))
                result = True
            
            if result:
                self._last_pos = (target_x, target_y)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to simulate mouse movement: {e}")
            return False

    def mouse_click(self, button: Union[str, MouseButton],
                   duration: Optional[float] = None) -> bool:
        """Simulate mouse click."""
        try:
            # Convert string to enum
            if isinstance(button, str):
                button = MouseButton[button.upper()]
            
            # Get button state
            if button in self._pressed_buttons and self._pressed_buttons[button]:
                return True
            
            # Map buttons
            if self._use_stealth:
                button_map = {
                    MouseButton.LEFT: 1,
                    MouseButton.RIGHT: 2,
                    MouseButton.MIDDLE: 4
                }
                buttons = button_map[button]
                
                # Click
                if not self._stealth_mode.send_mouse(0, 0, buttons):
                    return False
                
                if duration:
                    time.sleep(duration)
                
                return self._stealth_mode.send_mouse(0, 0, 0)
            
            else:
                button_map = {
                    MouseButton.LEFT: 'left',
                    MouseButton.RIGHT: 'right',
                    MouseButton.MIDDLE: 'middle'
                }
                mouse.press(button=button_map[button])
                
                if duration:
                    time.sleep(duration)
                
                mouse.release(button=button_map[button])
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to simulate mouse click: {e}")
            return False

    def mouse_scroll(self, delta: int) -> bool:
        """Simulate mouse wheel."""
        try:
            if self._use_stealth:
                return self._stealth_mode.send_mouse(0, 0, wheel=delta)
            else:
                mouse.wheel(delta)
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to simulate mouse wheel: {e}")
            return False

    def get_cursor_pos(self) -> Optional[Tuple[int, int]]:
        """Get current cursor position."""
        try:
            return win32api.GetCursorPos()
        except Exception as e:
            self.logger.error(f"Failed to get cursor position: {e}")
            return None

    def restore_cursor_pos(self) -> bool:
        """Restore last cursor position."""
        try:
            if self._last_pos:
                return self.mouse_move(*self._last_pos)
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to restore cursor position: {e}")
            return False

    def release_all(self) -> None:
        """Release all pressed keys and buttons."""
        try:
            # Release keys
            for key in list(self._pressed_keys.keys()):
                if self._pressed_keys[key]:
                    self.key_up(key)
            
            # Release buttons
            for button in list(self._pressed_buttons.keys()):
                if self._pressed_buttons[button]:
                    self.mouse_click(button)
            
        except Exception as e:
            self.logger.error(f"Failed to release all inputs: {e}")

    def cleanup(self):
        """Clean up resources."""
        try:
            self.release_all()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
input_simulator = InputSimulator()
