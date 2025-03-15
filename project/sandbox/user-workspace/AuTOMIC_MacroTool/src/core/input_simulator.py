"""
Input simulation module with stealth mode support.
"""

import logging
import time
import threading
from typing import Optional, Tuple, List, Dict
from enum import Enum, auto
from dataclasses import dataclass
import ctypes
import win32api
import win32con
import win32gui
import keyboard
import mouse
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse

from ..utils.debug_helper import get_debug_helper
from .window_manager import window_manager

class InputMode(Enum):
    """Input simulation modes."""
    NORMAL = auto()  # Standard Windows API
    STEALTH = auto()  # Hardware-level simulation

@dataclass
class InputEvent:
    """Input event container."""
    type: str  # 'keyboard' or 'mouse'
    action: str  # 'press', 'release', 'move', 'click', 'scroll'
    data: Dict  # Event-specific data
    timestamp: float
    window_info: Optional[Dict] = None  # Window context

class InputSimulator:
    """Manages input simulation with stealth mode support."""
    
    def __init__(self):
        self.logger = logging.getLogger('InputSimulator')
        self.debug = get_debug_helper()
        
        # State
        self.mode = InputMode.NORMAL
        self._interception_loaded = False
        self._stop_flag = threading.Event()
        self._lock = threading.Lock()
        
        # Input state tracking
        self._pressed_keys: set = set()
        self._mouse_position: Tuple[int, int] = (0, 0)
        self._mouse_buttons: Dict[str, bool] = {
            'left': False,
            'right': False,
            'middle': False
        }
        
        # Initialize
        self._init_input_hooks()

    def _init_input_hooks(self):
        """Initialize input monitoring hooks."""
        try:
            # Keyboard hook
            self._keyboard_listener = pynput_keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._keyboard_listener.start()
            
            # Mouse hook
            self._mouse_listener = pynput_mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self._mouse_listener.start()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize input hooks: {e}")

    def _on_key_press(self, key):
        """Handle key press events."""
        try:
            with self._lock:
                if hasattr(key, 'vk'):
                    self._pressed_keys.add(key.vk)
                elif hasattr(key, 'char'):
                    self._pressed_keys.add(ord(key.char))
        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")

    def _on_key_release(self, key):
        """Handle key release events."""
        try:
            with self._lock:
                if hasattr(key, 'vk'):
                    self._pressed_keys.discard(key.vk)
                elif hasattr(key, 'char'):
                    self._pressed_keys.discard(ord(key.char))
        except Exception as e:
            self.logger.error(f"Error in key release handler: {e}")

    def _on_mouse_move(self, x, y):
        """Handle mouse move events."""
        try:
            with self._lock:
                self._mouse_position = (x, y)
        except Exception as e:
            self.logger.error(f"Error in mouse move handler: {e}")

    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        try:
            with self._lock:
                self._mouse_position = (x, y)
                button_name = button.name.lower()
                if button_name in self._mouse_buttons:
                    self._mouse_buttons[button_name] = pressed
        except Exception as e:
            self.logger.error(f"Error in mouse click handler: {e}")

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events."""
        try:
            with self._lock:
                self._mouse_position = (x, y)
        except Exception as e:
            self.logger.error(f"Error in mouse scroll handler: {e}")

    def set_mode(self, mode: InputMode) -> bool:
        """Set input simulation mode."""
        try:
            if mode == InputMode.STEALTH and not self._interception_loaded:
                if not self._load_interception():
                    return False
            
            self.mode = mode
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting input mode: {e}")
            return False

    def _load_interception(self) -> bool:
        """Load Interception driver."""
        try:
            # Try to load Interception DLL
            try:
                self._interception = ctypes.CDLL('interception.dll')
                self._interception_loaded = True
                self.logger.info("Interception driver loaded")
                return True
            except:
                self.logger.warning("Interception driver not available")
                return False
            
        except Exception as e:
            self.logger.error(f"Error loading Interception: {e}")
            return False

    def simulate_key(self, key: str, press: bool = True):
        """Simulate keyboard input."""
        try:
            if self.mode == InputMode.STEALTH and self._interception_loaded:
                self._simulate_key_stealth(key, press)
            else:
                self._simulate_key_normal(key, press)
            
        except Exception as e:
            self.logger.error(f"Error simulating key: {e}")

    def _simulate_key_normal(self, key: str, press: bool):
        """Simulate keyboard input using standard API."""
        try:
            if press:
                keyboard.press(key)
            else:
                keyboard.release(key)
            
        except Exception as e:
            self.logger.error(f"Error in normal key simulation: {e}")

    def _simulate_key_stealth(self, key: str, press: bool):
        """Simulate keyboard input using Interception."""
        try:
            if not self._interception_loaded:
                return
            
            # Convert key to scan code
            scan_code = keyboard.key_to_scan_codes(key)[0]
            
            # Create stroke
            stroke = self._interception.InterceptionKeyStroke()
            stroke.code = scan_code
            stroke.state = 0 if press else 1
            
            # Send stroke
            self._interception.interception_send(
                self._interception.interception_create_context(),
                1,  # Keyboard device
                ctypes.byref(stroke),
                1
            )
            
        except Exception as e:
            self.logger.error(f"Error in stealth key simulation: {e}")

    def simulate_mouse_move(self, x: int, y: int, relative: bool = False):
        """Simulate mouse movement."""
        try:
            if relative:
                current_x, current_y = win32api.GetCursorPos()
                x += current_x
                y += current_y
            
            if self.mode == InputMode.STEALTH and self._interception_loaded:
                self._simulate_mouse_move_stealth(x, y)
            else:
                self._simulate_mouse_move_normal(x, y)
            
        except Exception as e:
            self.logger.error(f"Error simulating mouse move: {e}")

    def _simulate_mouse_move_normal(self, x: int, y: int):
        """Simulate mouse movement using standard API."""
        try:
            win32api.SetCursorPos((x, y))
        except Exception as e:
            self.logger.error(f"Error in normal mouse move: {e}")

    def _simulate_mouse_move_stealth(self, x: int, y: int):
        """Simulate mouse movement using Interception."""
        try:
            if not self._interception_loaded:
                return
            
            # Create stroke
            stroke = self._interception.InterceptionMouseStroke()
            stroke.x = x
            stroke.y = y
            stroke.flags = 0x01  # INTERCEPTION_MOUSE_MOVE_ABSOLUTE
            
            # Send stroke
            self._interception.interception_send(
                self._interception.interception_create_context(),
                11,  # Mouse device
                ctypes.byref(stroke),
                1
            )
            
        except Exception as e:
            self.logger.error(f"Error in stealth mouse move: {e}")

    def simulate_mouse_button(self, button: str, press: bool = True):
        """Simulate mouse button."""
        try:
            if self.mode == InputMode.STEALTH and self._interception_loaded:
                self._simulate_mouse_button_stealth(button, press)
            else:
                self._simulate_mouse_button_normal(button, press)
            
        except Exception as e:
            self.logger.error(f"Error simulating mouse button: {e}")

    def _simulate_mouse_button_normal(self, button: str, press: bool):
        """Simulate mouse button using standard API."""
        try:
            if press:
                mouse.press(button=button)
            else:
                mouse.release(button=button)
            
        except Exception as e:
            self.logger.error(f"Error in normal mouse button: {e}")

    def _simulate_mouse_button_stealth(self, button: str, press: bool):
        """Simulate mouse button using Interception."""
        try:
            if not self._interception_loaded:
                return
            
            # Map button to flag
            button_flags = {
                'left': 0x02,    # INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN
                'right': 0x08,   # INTERCEPTION_MOUSE_RIGHT_BUTTON_DOWN
                'middle': 0x20   # INTERCEPTION_MOUSE_MIDDLE_BUTTON_DOWN
            }
            
            if button not in button_flags:
                return
            
            # Create stroke
            stroke = self._interception.InterceptionMouseStroke()
            stroke.flags = button_flags[button] if press else button_flags[button] << 1
            
            # Send stroke
            self._interception.interception_send(
                self._interception.interception_create_context(),
                11,  # Mouse device
                ctypes.byref(stroke),
                1
            )
            
        except Exception as e:
            self.logger.error(f"Error in stealth mouse button: {e}")

    def simulate_mouse_scroll(self, delta: int):
        """Simulate mouse wheel."""
        try:
            if self.mode == InputMode.STEALTH and self._interception_loaded:
                self._simulate_mouse_scroll_stealth(delta)
            else:
                self._simulate_mouse_scroll_normal(delta)
            
        except Exception as e:
            self.logger.error(f"Error simulating mouse scroll: {e}")

    def _simulate_mouse_scroll_normal(self, delta: int):
        """Simulate mouse wheel using standard API."""
        try:
            mouse.wheel(delta=delta)
        except Exception as e:
            self.logger.error(f"Error in normal mouse scroll: {e}")

    def _simulate_mouse_scroll_stealth(self, delta: int):
        """Simulate mouse wheel using Interception."""
        try:
            if not self._interception_loaded:
                return
            
            # Create stroke
            stroke = self._interception.InterceptionMouseStroke()
            stroke.rolling = delta
            stroke.flags = 0x400  # INTERCEPTION_MOUSE_WHEEL
            
            # Send stroke
            self._interception.interception_send(
                self._interception.interception_create_context(),
                11,  # Mouse device
                ctypes.byref(stroke),
                1
            )
            
        except Exception as e:
            self.logger.error(f"Error in stealth mouse scroll: {e}")

    def get_input_state(self) -> Dict:
        """Get current input state."""
        try:
            with self._lock:
                return {
                    'keyboard': {
                        'pressed_keys': list(self._pressed_keys)
                    },
                    'mouse': {
                        'position': self._mouse_position,
                        'buttons': dict(self._mouse_buttons)
                    }
                }
        except Exception as e:
            self.logger.error(f"Error getting input state: {e}")
            return {}

    def cleanup(self):
        """Clean up resources."""
        try:
            self._stop_flag.set()
            
            # Stop listeners
            if hasattr(self, '_keyboard_listener'):
                self._keyboard_listener.stop()
            if hasattr(self, '_mouse_listener'):
                self._mouse_listener.stop()
            
            # Unload Interception
            if self._interception_loaded:
                try:
                    self._interception.interception_destroy_context(
                        self._interception.interception_create_context()
                    )
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
input_simulator = InputSimulator()
