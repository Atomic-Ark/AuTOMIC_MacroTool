"""
Macro recording module.
Copyright (c) 2025 AtomicArk
"""

import logging
import threading
from typing import Dict, List, Optional, Set, Callable
from enum import Enum, auto
import time
from datetime import datetime
import win32gui
import keyboard
import mouse
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse

from ..utils.debug_helper import get_debug_helper
from .window_manager import window_manager
from .input_simulator import InputType, InputEvent, MouseButton

class RecordingMode(Enum):
    """Recording modes."""
    WINDOW = auto()  # Record relative to window
    SCREEN = auto()  # Record absolute screen coordinates
    DIRECTX = auto()  # Record DirectX window input

class RecordingState(Enum):
    """Recording states."""
    STOPPED = auto()
    RECORDING = auto()
    PAUSED = auto()

class MacroRecorder:
    """Records keyboard and mouse input."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('MacroRecorder')
            self.debug = get_debug_helper()
            
            # State
            self._state = RecordingState.STOPPED
            self._mode = RecordingMode.WINDOW
            self._events: List[InputEvent] = []
            self._start_time: Optional[float] = None
            self._last_time: Optional[float] = None
            self._target_window: Optional[int] = None
            self._record_mouse = True
            self._record_keyboard = True
            self._record_delays = True
            self._min_delay = 0.01  # Minimum delay in seconds
            
            # Input tracking
            self._pressed_keys: Set[str] = set()
            self._pressed_buttons: Set[MouseButton] = set()
            self._last_pos: Optional[tuple[int, int]] = None
            
            # Callbacks
            self._state_callbacks: List[Callable[[RecordingState], None]] = []
            
            # Initialize listeners
            self._keyboard_listener = pynput_keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            
            self._mouse_listener = pynput_mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            
            self._initialized = True

    def start(self, mode: RecordingMode = RecordingMode.WINDOW,
              target_window: Optional[int] = None) -> bool:
        """Start recording."""
        try:
            with self._lock:
                if self._state != RecordingState.STOPPED:
                    return False
                
                # Reset state
                self._events.clear()
                self._pressed_keys.clear()
                self._pressed_buttons.clear()
                self._last_pos = None
                
                # Set mode and target
                self._mode = mode
                self._target_window = target_window
                
                # Start timing
                self._start_time = time.time()
                self._last_time = self._start_time
                
                # Start listeners
                if self._record_keyboard:
                    self._keyboard_listener.start()
                if self._record_mouse:
                    self._mouse_listener.start()
                
                # Update state
                self._state = RecordingState.RECORDING
                self._notify_state_change()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False

    def stop(self) -> bool:
        """Stop recording."""
        try:
            with self._lock:
                if self._state == RecordingState.STOPPED:
                    return False
                
                # Stop listeners
                if self._keyboard_listener.running:
                    self._keyboard_listener.stop()
                if self._mouse_listener.running:
                    self._mouse_listener.stop()
                
                # Release tracking
                self._pressed_keys.clear()
                self._pressed_buttons.clear()
                
                # Update state
                self._state = RecordingState.STOPPED
                self._notify_state_change()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return False

    def pause(self) -> bool:
        """Pause recording."""
        try:
            with self._lock:
                if self._state != RecordingState.RECORDING:
                    return False
                
                # Stop listeners
                if self._keyboard_listener.running:
                    self._keyboard_listener.stop()
                if self._mouse_listener.running:
                    self._mouse_listener.stop()
                
                # Update state
                self._state = RecordingState.PAUSED
                self._notify_state_change()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause recording: {e}")
            return False

    def resume(self) -> bool:
        """Resume recording."""
        try:
            with self._lock:
                if self._state != RecordingState.PAUSED:
                    return False
                
                # Update timing
                current_time = time.time()
                if self._last_time:
                    self._start_time += (current_time - self._last_time)
                self._last_time = current_time
                
                # Start listeners
                if self._record_keyboard:
                    self._keyboard_listener.start()
                if self._record_mouse:
                    self._mouse_listener.start()
                
                # Update state
                self._state = RecordingState.RECORDING
                self._notify_state_change()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume recording: {e}")
            return False

    def _on_key_press(self, key) -> None:
        """Handle key press event."""
        try:
            if self._state != RecordingState.RECORDING:
                return
            
            # Convert key to string
            try:
                key_str = key.char
            except AttributeError:
                key_str = str(key).replace('Key.', '')
            
            # Skip if already pressed
            if key_str in self._pressed_keys:
                return
            
            # Add event
            self._add_event(InputType.KEYBOARD, {
                'key': key_str,
                'action': 'press'
            })
            
            # Update tracking
            self._pressed_keys.add(key_str)
            
        except Exception as e:
            self.logger.error(f"Failed to handle key press: {e}")

    def _on_key_release(self, key) -> None:
        """Handle key release event."""
        try:
            if self._state != RecordingState.RECORDING:
                return
            
            # Convert key to string
            try:
                key_str = key.char
            except AttributeError:
                key_str = str(key).replace('Key.', '')
            
            # Skip if not pressed
            if key_str not in self._pressed_keys:
                return
            
            # Add event
            self._add_event(InputType.KEYBOARD, {
                'key': key_str,
                'action': 'release'
            })
            
            # Update tracking
            self._pressed_keys.remove(key_str)
            
        except Exception as e:
            self.logger.error(f"Failed to handle key release: {e}")

    def _on_mouse_move(self, x: int, y: int) -> None:
        """Handle mouse move event."""
        try:
            if self._state != RecordingState.RECORDING:
                return
            
            # Skip if position unchanged
            if self._last_pos == (x, y):
                return
            
            # Convert coordinates
            if self._mode == RecordingMode.WINDOW and self._target_window:
                # Get window position
                window_rect = win32gui.GetWindowRect(self._target_window)
                if window_rect:
                    # Calculate relative position
                    rel_x = x - window_rect[0]
                    rel_y = y - window_rect[1]
                    
                    # Add event
                    self._add_event(InputType.MOUSE_MOVE, {
                        'x': x,
                        'y': y,
                        'relative_x': rel_x,
                        'relative_y': rel_y
                    })
            else:
                # Add absolute position
                self._add_event(InputType.MOUSE_MOVE, {
                    'x': x,
                    'y': y
                })
            
            # Update tracking
            self._last_pos = (x, y)
            
        except Exception as e:
            self.logger.error(f"Failed to handle mouse move: {e}")

    def _on_mouse_click(self, x: int, y: int, button, pressed: bool) -> None:
        """Handle mouse click event."""
        try:
            if self._state != RecordingState.RECORDING:
                return
            
            # Convert button
            button_map = {
                pynput_mouse.Button.left: MouseButton.LEFT,
                pynput_mouse.Button.right: MouseButton.RIGHT,
                pynput_mouse.Button.middle: MouseButton.MIDDLE
            }
            mouse_button = button_map.get(button)
            if not mouse_button:
                return
            
            # Skip if state unchanged
            if pressed and mouse_button in self._pressed_buttons:
                return
            if not pressed and mouse_button not in self._pressed_buttons:
                return
            
            # Add event
            self._add_event(InputType.MOUSE_CLICK, {
                'button': mouse_button.name,
                'action': 'press' if pressed else 'release',
                'x': x,
                'y': y
            })
            
            # Update tracking
            if pressed:
                self._pressed_buttons.add(mouse_button)
            else:
                self._pressed_buttons.remove(mouse_button)
            
        except Exception as e:
            self.logger.error(f"Failed to handle mouse click: {e}")

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Handle mouse scroll event."""
        try:
            if self._state != RecordingState.RECORDING:
                return
            
            # Add event
            self._add_event(InputType.MOUSE_SCROLL, {
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy
            })
            
        except Exception as e:
            self.logger.error(f"Failed to handle mouse scroll: {e}")

    def _add_event(self, event_type: InputType, data: Dict) -> None:
        """Add input event."""
        try:
            # Get timing
            current_time = time.time()
            timestamp = current_time - self._start_time
            
            # Skip if delay too small
            if self._last_time and self._record_delays:
                delay = current_time - self._last_time
                if delay < self._min_delay:
                    return
            
            # Get window info
            window_handle = None
            window_title = None
            if self._mode == RecordingMode.WINDOW:
                if self._target_window:
                    window_handle = self._target_window
                    window_title = win32gui.GetWindowText(window_handle)
                else:
                    window_handle = win32gui.GetForegroundWindow()
                    window_title = win32gui.GetWindowText(window_handle)
            
            # Create event
            event = InputEvent(
                type=event_type,
                timestamp=timestamp,
                data=data,
                window_handle=window_handle,
                window_title=window_title
            )
            
            # Add event
            with self._lock:
                self._events.append(event)
                self._last_time = current_time
            
        except Exception as e:
            self.logger.error(f"Failed to add event: {e}")

    def get_events(self) -> List[InputEvent]:
        """Get recorded events."""
        with self._lock:
            return self._events.copy()

    def get_state(self) -> RecordingState:
        """Get current state."""
        return self._state

    def get_mode(self) -> RecordingMode:
        """Get current mode."""
        return self._mode

    def set_options(self, record_mouse: bool = True,
                   record_keyboard: bool = True,
                   record_delays: bool = True,
                   min_delay: float = 0.01) -> None:
        """Set recording options."""
        with self._lock:
            self._record_mouse = record_mouse
            self._record_keyboard = record_keyboard
            self._record_delays = record_delays
            self._min_delay = min_delay

    def add_state_callback(self, callback: Callable[[RecordingState], None]) -> None:
        """Add state change callback."""
        with self._lock:
            self._state_callbacks.append(callback)

    def remove_state_callback(self, callback: Callable[[RecordingState], None]) -> None:
        """Remove state change callback."""
        with self._lock:
            self._state_callbacks.remove(callback)

    def _notify_state_change(self) -> None:
        """Notify state change callbacks."""
        for callback in self._state_callbacks:
            try:
                callback(self._state)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop()
            with self._lock:
                self._events.clear()
                self._state_callbacks.clear()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
macro_recorder = MacroRecorder()
