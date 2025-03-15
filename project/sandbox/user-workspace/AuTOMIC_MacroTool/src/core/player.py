"""
Macro playback module.
"""

import logging
import time
import threading
import random
from typing import List, Optional, Dict, Callable
from enum import Enum, auto
from dataclasses import dataclass

from ..utils.debug_helper import get_debug_helper
from .window_manager import window_manager, WindowInfo
from .input_simulator import input_simulator, InputMode, InputEvent
from .recorder import RecordingMode

class PlaybackMode(Enum):
    """Playback modes."""
    ONCE = auto()
    LOOP = auto()
    COUNT = auto()

class PlaybackState(Enum):
    """Playback states."""
    IDLE = auto()
    PLAYING = auto()
    PAUSED = auto()

@dataclass
class PlaybackOptions:
    """Playback configuration."""
    mode: PlaybackMode = PlaybackMode.ONCE
    repeat_count: int = 1
    speed: float = 1.0
    randomize_delays: bool = False
    random_factor: float = 0.2
    stop_on_input: bool = True
    restore_mouse: bool = True
    stealth_mode: bool = False

class MacroPlayer:
    """Plays back recorded macros."""
    
    def __init__(self):
        self.logger = logging.getLogger('MacroPlayer')
        self.debug = get_debug_helper()
        
        # State
        self.state = PlaybackState.IDLE
        self.options = PlaybackOptions()
        self._events: List[InputEvent] = []
        self._current_index = 0
        self._repeat_count = 0
        self._original_mouse_pos = (0, 0)
        
        # Threading
        self._playback_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()
        
        # Callbacks
        self.on_state_change: Optional[Callable[[PlaybackState], None]] = None
        self.on_event_played: Optional[Callable[[InputEvent], None]] = None
        self.on_playback_complete: Optional[Callable[[], None]] = None
        
        # Input monitoring
        self._init_input_monitoring()

    def _init_input_monitoring(self):
        """Initialize input monitoring for stop conditions."""
        try:
            import keyboard
            import mouse
            
            # Monitor keyboard
            keyboard.hook(self._check_input)
            
            # Monitor mouse
            mouse.hook(self._check_input)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize input monitoring: {e}")

    def _check_input(self, event):
        """Check for user input to stop playback."""
        try:
            if (self.state == PlaybackState.PLAYING and 
                self.options.stop_on_input):
                self.stop_playback()
            
        except Exception as e:
            self.logger.error(f"Error checking input: {e}")

    def start_playback(self, events: List[InputEvent],
                      options: Optional[PlaybackOptions] = None) -> bool:
        """Start macro playback."""
        try:
            if self.state != PlaybackState.IDLE:
                return False
            
            with self._lock:
                # Update options
                if options:
                    self.options = options
                
                # Store events
                self._events = list(events)
                if not self._events:
                    return False
                
                # Reset state
                self._current_index = 0
                self._repeat_count = 0
                self._stop_flag.clear()
                self._pause_flag.clear()
                
                # Store mouse position
                if self.options.restore_mouse:
                    self._original_mouse_pos = win32api.GetCursorPos()
                
                # Set stealth mode
                if self.options.stealth_mode:
                    input_simulator.set_mode(InputMode.STEALTH)
                else:
                    input_simulator.set_mode(InputMode.NORMAL)
                
                # Start playback thread
                self._playback_thread = threading.Thread(
                    target=self._playback_loop,
                    daemon=True
                )
                self._playback_thread.start()
                
                # Update state
                self.state = PlaybackState.PLAYING
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to start playback: {e}")
            return False

    def stop_playback(self) -> bool:
        """Stop macro playback."""
        try:
            if self.state == PlaybackState.IDLE:
                return False
            
            with self._lock:
                # Signal stop
                self._stop_flag.set()
                self._pause_flag.clear()
                
                # Wait for thread
                if self._playback_thread:
                    self._playback_thread.join(timeout=1.0)
                
                # Restore mouse position
                if self.options.restore_mouse:
                    win32api.SetCursorPos(self._original_mouse_pos)
                
                # Reset state
                self.state = PlaybackState.IDLE
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop playback: {e}")
            return False

    def pause_playback(self) -> bool:
        """Pause macro playback."""
        try:
            if self.state != PlaybackState.PLAYING:
                return False
            
            with self._lock:
                self._pause_flag.set()
                self.state = PlaybackState.PAUSED
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause playback: {e}")
            return False

    def resume_playback(self) -> bool:
        """Resume macro playback."""
        try:
            if self.state != PlaybackState.PAUSED:
                return False
            
            with self._lock:
                self._pause_flag.clear()
                self.state = PlaybackState.PLAYING
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume playback: {e}")
            return False

    def _playback_loop(self):
        """Main playback loop."""
        try:
            while not self._stop_flag.is_set():
                # Check completion
                if self._current_index >= len(self._events):
                    if self.options.mode == PlaybackMode.ONCE:
                        break
                    elif self.options.mode == PlaybackMode.COUNT:
                        self._repeat_count += 1
                        if self._repeat_count >= self.options.repeat_count:
                            break
                    
                    # Reset for next iteration
                    self._current_index = 0
                
                # Check pause
                if self._pause_flag.is_set():
                    time.sleep(0.1)
                    continue
                
                # Play current event
                event = self._events[self._current_index]
                self._play_event(event)
                
                # Move to next event
                self._current_index += 1
            
            # Playback complete
            if self.on_playback_complete:
                self.on_playback_complete()
            
            # Reset state
            with self._lock:
                self.state = PlaybackState.IDLE
                if self.on_state_change:
                    self.on_state_change(self.state)
            
        except Exception as e:
            self.logger.error(f"Error in playback loop: {e}")
            self.stop_playback()

    def _play_event(self, event: InputEvent):
        """Play single event."""
        try:
            # Handle delay events
            if event.type == 'delay':
                delay = event.data['duration']
                
                # Apply speed factor
                delay /= self.options.speed
                
                # Apply randomization
                if self.options.randomize_delays:
                    factor = 1.0 + (random.random() * 2 - 1) * self.options.random_factor
                    delay *= factor
                
                time.sleep(max(0, delay))
                return
            
            # Handle window context
            if event.window_info:
                window = window_manager.get_window_info(event.window_info['hwnd'])
                if not window:
                    # Try finding window by title
                    window = window_manager.get_window_by_title(
                        event.window_info['title']
                    )
                
                if window:
                    # Convert coordinates if needed
                    if event.type == 'mouse':
                        if 'x' in event.data and 'y' in event.data:
                            pos = window_manager.get_absolute_pos(
                                window.hwnd,
                                event.data['x'],
                                event.data['y']
                            )
                            if pos:
                                event.data['x'], event.data['y'] = pos
            
            # Play event
            if event.type == 'keyboard':
                if event.action == 'press':
                    input_simulator.simulate_key(event.data['key'], True)
                elif event.action == 'release':
                    input_simulator.simulate_key(event.data['key'], False)
                
            elif event.type == 'mouse':
                if event.action == 'move':
                    input_simulator.simulate_mouse_move(
                        event.data['x'],
                        event.data['y']
                    )
                elif event.action in ['press', 'release']:
                    input_simulator.simulate_mouse_button(
                        event.data['button'],
                        event.action == 'press'
                    )
                elif event.action == 'scroll':
                    input_simulator.simulate_mouse_scroll(
                        event.data['dy']
                    )
            
            # Notify callback
            if self.on_event_played:
                self.on_event_played(event)
            
        except Exception as e:
            self.logger.error(f"Error playing event: {e}")

    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop playback if active
            if self.state != PlaybackState.IDLE:
                self.stop_playback()
            
            # Remove input hooks
            import keyboard
            import mouse
            keyboard.unhook_all()
            mouse.unhook_all()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
macro_player = MacroPlayer()
