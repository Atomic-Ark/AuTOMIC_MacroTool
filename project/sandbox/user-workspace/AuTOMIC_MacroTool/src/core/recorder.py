"""
Macro recording module.
"""

import logging
import time
import threading
from typing import List, Optional, Dict, Callable
from enum import Enum, auto
from dataclasses import dataclass
import keyboard
import mouse
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse

from ..utils.debug_helper import get_debug_helper
from .window_manager import window_manager, WindowInfo
from .input_simulator import InputEvent

class RecordingMode(Enum):
    """Recording modes."""
    WINDOW = auto()  # Record relative to window
    SCREEN = auto()  # Record absolute screen coordinates
    DIRECTX = auto()  # Record DirectX/OpenGL window

class RecordingState(Enum):
    """Recording states."""
    IDLE = auto()
    RECORDING = auto()
    PAUSED = auto()

@dataclass
class RecordingOptions:
    """Recording configuration."""
    mode: RecordingMode = RecordingMode.WINDOW
    record_mouse: bool = True
    record_keyboard: bool = True
    record_delays: bool = True
    min_delay: float = 0.01
    target_window: Optional[int] = None

class MacroRecorder:
    """Records user input for macro creation."""
    
    def __init__(self):
        self.logger = logging.getLogger('MacroRecorder')
        self.debug = get_debug_helper()
        
        # State
        self.state = RecordingState.IDLE
        self.options = RecordingOptions()
        self.events: List[InputEvent] = []
        self._start_time: Optional[float] = None
        self._last_event_time: Optional[float] = None
        
        # Threading
        self._lock = threading.Lock()
        self._stop_flag = threading.Event()
        
        # Callbacks
        self.on_state_change: Optional[Callable[[RecordingState], None]] = None
        self.on_event_recorded: Optional[Callable[[InputEvent], None]] = None
        
        # Initialize
        self._init_hooks()

    def _init_hooks(self):
        """Initialize input hooks."""
        try:
            # Keyboard hook
            self._keyboard_listener = pynput_keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            
            # Mouse hook
            self._mouse_listener = pynput_mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize hooks: {e}")
            raise

    def start_recording(self, options: Optional[RecordingOptions] = None) -> bool:
        """Start macro recording."""
        try:
            if self.state != RecordingState.IDLE:
                return False
            
            with self._lock:
                # Update options
                if options:
                    self.options = options
                
                # Clear previous recording
                self.events.clear()
                
                # Start hooks
                self._keyboard_listener.start()
                if self.options.record_mouse:
                    self._mouse_listener.start()
                
                # Set state
                self._start_time = time.time()
                self._last_event_time = self._start_time
                self.state = RecordingState.RECORDING
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False

    def stop_recording(self) -> bool:
        """Stop macro recording."""
        try:
            if self.state == RecordingState.IDLE:
                return False
            
            with self._lock:
                # Stop hooks
                self._keyboard_listener.stop()
                self._mouse_listener.stop()
                
                # Reset state
                self.state = RecordingState.IDLE
                self._start_time = None
                self._last_event_time = None
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return False

    def pause_recording(self) -> bool:
        """Pause macro recording."""
        try:
            if self.state != RecordingState.RECORDING:
                return False
            
            with self._lock:
                self.state = RecordingState.PAUSED
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause recording: {e}")
            return False

    def resume_recording(self) -> bool:
        """Resume macro recording."""
        try:
            if self.state != RecordingState.PAUSED:
                return False
            
            with self._lock:
                self.state = RecordingState.RECORDING
                self._last_event_time = time.time()
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume recording: {e}")
            return False

    def _record_event(self, event: InputEvent):
        """Record input event."""
        try:
            if self.state != RecordingState.RECORDING:
                return
            
            with self._lock:
                # Add delay if enabled
                current_time = time.time()
                if self.options.record_delays and self._last_event_time:
                    delay = current_time - self._last_event_time
                    if delay >= self.options.min_delay:
                        delay_event = InputEvent(
                            type='delay',
                            action='wait',
                            data={'duration': delay},
                            timestamp=current_time
                        )
                        self.events.append(delay_event)
                
                # Add window info if targeting window
                if self.options.mode == RecordingMode.WINDOW:
                    if self.options.target_window:
                        window = window_manager.get_window_info(
                            self.options.target_window
                        )
                    else:
                        window = window_manager.get_active_window()
                    
                    if window:
                        event.window_info = {
                            'hwnd': window.hwnd,
                            'title': window.title,
                            'rect': window.rect
                        }
                
                # Record event
                self.events.append(event)
                self._last_event_time = current_time
                
                # Notify callback
                if self.on_event_recorded:
                    self.on_event_recorded(event)
            
        except Exception as e:
            self.logger.error(f"Failed to record event: {e}")

    def _on_key_press(self, key):
        """Handle key press events."""
        try:
            if not self.options.record_keyboard:
                return
            
            # Convert key to string
            key_str = None
            if hasattr(key, 'char'):
                key_str = key.char
            elif hasattr(key, 'name'):
                key_str = key.name
            else:
                key_str = str(key)
            
            event = InputEvent(
                type='keyboard',
                action='press',
                data={'key': key_str},
                timestamp=time.time()
            )
            
            self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")

    def _on_key_release(self, key):
        """Handle key release events."""
        try:
            if not self.options.record_keyboard:
                return
            
            # Convert key to string
            key_str = None
            if hasattr(key, 'char'):
                key_str = key.char
            elif hasattr(key, 'name'):
                key_str = key.name
            else:
                key_str = str(key)
            
            event = InputEvent(
                type='keyboard',
                action='release',
                data={'key': key_str},
                timestamp=time.time()
            )
            
            self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error in key release handler: {e}")

    def _on_mouse_move(self, x, y):
        """Handle mouse move events."""
        try:
            if not self.options.record_mouse:
                return
            
            # Convert coordinates if needed
            if (self.options.mode == RecordingMode.WINDOW and 
                self.options.target_window):
                pos = window_manager.get_relative_pos(
                    self.options.target_window,
                    x,
                    y
                )
                if pos:
                    x, y = pos
            
            event = InputEvent(
                type='mouse',
                action='move',
                data={'x': x, 'y': y},
                timestamp=time.time()
            )
            
            self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error in mouse move handler: {e}")

    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        try:
            if not self.options.record_mouse:
                return
            
            # Convert coordinates if needed
            if (self.options.mode == RecordingMode.WINDOW and 
                self.options.target_window):
                pos = window_manager.get_relative_pos(
                    self.options.target_window,
                    x,
                    y
                )
                if pos:
                    x, y = pos
            
            event = InputEvent(
                type='mouse',
                action='press' if pressed else 'release',
                data={
                    'button': button.name,
                    'x': x,
                    'y': y
                },
                timestamp=time.time()
            )
            
            self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error in mouse click handler: {e}")

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events."""
        try:
            if not self.options.record_mouse:
                return
            
            event = InputEvent(
                type='mouse',
                action='scroll',
                data={'dx': dx, 'dy': dy},
                timestamp=time.time()
            )
            
            self._record_event(event)
            
        except Exception as e:
            self.logger.error(f"Error in mouse scroll handler: {e}")

    def get_events(self) -> List[InputEvent]:
        """Get recorded events."""
        with self._lock:
            return list(self.events)

    def clear_events(self):
        """Clear recorded events."""
        with self._lock:
            self.events.clear()

    def cleanup(self):
        """Clean up resources."""
        try:
            self._stop_flag.set()
            
            # Stop recording if active
            if self.state != RecordingState.IDLE:
                self.stop_recording()
            
            # Stop listeners
            if hasattr(self, '_keyboard_listener'):
                self._keyboard_listener.stop()
            if hasattr(self, '_mouse_listener'):
                self._mouse_listener.stop()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
macro_recorder = MacroRecorder()
