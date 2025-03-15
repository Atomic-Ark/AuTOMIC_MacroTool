"""
Macro playback module.
Copyright (c) 2025 AtomicArk
"""

import logging
import threading
from typing import List, Optional, Callable
from enum import Enum, auto
import time
import random
import keyboard
import mouse
import win32gui

from ..utils.debug_helper import get_debug_helper
from .window_manager import window_manager
from .input_simulator import input_simulator, InputType, InputEvent, MouseButton
from .recorder import RecordingMode

class PlaybackMode(Enum):
    """Playback modes."""
    ONCE = auto()      # Play once
    LOOP = auto()      # Loop indefinitely
    COUNT = auto()     # Play specific number of times

class PlaybackState(Enum):
    """Playback states."""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()

class MacroPlayer:
    """Plays back recorded macros."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('MacroPlayer')
            self.debug = get_debug_helper()
            
            # State
            self._state = PlaybackState.STOPPED
            self._mode = PlaybackMode.ONCE
            self._events: List[InputEvent] = []
            self._current_index = 0
            self._repeat_count = 1
            self._current_repeat = 0
            self._start_time: Optional[float] = None
            self._pause_time: Optional[float] = None
            self._speed_multiplier = 1.0
            self._randomize_delays = False
            self._stop_on_input = True
            self._restore_position = True
            self._original_position: Optional[tuple[int, int]] = None
            
            # Playback thread
            self._playback_thread: Optional[threading.Thread] = None
            self._stop_event = threading.Event()
            
            # Callbacks
            self._state_callbacks: List[Callable[[PlaybackState], None]] = []
            self._progress_callbacks: List[Callable[[float], None]] = []
            
            # Input monitoring
            self._monitor_thread: Optional[threading.Thread] = None
            self._last_input_time = 0
            
            self._initialized = True

    def play(self, events: List[InputEvent], mode: PlaybackMode = PlaybackMode.ONCE,
             repeat_count: int = 1) -> bool:
        """Start playback."""
        try:
            with self._lock:
                if self._state != PlaybackState.STOPPED:
                    return False
                
                # Validate input
                if not events:
                    return False
                if mode == PlaybackMode.COUNT and repeat_count < 1:
                    return False
                
                # Store original cursor position
                if self._restore_position:
                    self._original_position = input_simulator.get_cursor_pos()
                
                # Set up playback
                self._events = events
                self._mode = mode
                self._repeat_count = repeat_count
                self._current_repeat = 0
                self._current_index = 0
                self._start_time = time.time()
                self._stop_event.clear()
                
                # Start monitoring if needed
                if self._stop_on_input:
                    self._start_input_monitoring()
                
                # Start playback thread
                self._playback_thread = threading.Thread(
                    target=self._playback_loop,
                    name="MacroPlayback"
                )
                self._playback_thread.start()
                
                # Update state
                self._state = PlaybackState.PLAYING
                self._notify_state_change()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to start playback: {e}")
            return False

    def stop(self) -> bool:
        """Stop playback."""
        try:
            with self._lock:
                if self._state == PlaybackState.STOPPED:
                    return False
                
                # Signal stop
                self._stop_event.set()
                
                # Wait for thread
                if self._playback_thread and self._playback_thread.is_alive():
                    self._playback_thread.join()
                
                # Stop monitoring
                self._stop_input_monitoring()
                
                # Restore position
                if self._restore_position and self._original_position:
                    input_simulator.mouse_move(*self._original_position)
                
                # Reset state
                self._state = PlaybackState.STOPPED
                self._notify_state_change()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop playback: {e}")
            return False

    def pause(self) -> bool:
        """Pause playback."""
        try:
            with self._lock:
                if self._state != PlaybackState.PLAYING:
                    return False
                
                # Store pause time
                self._pause_time = time.time()
                
                # Update state
                self._state = PlaybackState.PAUSED
                self._notify_state_change()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause playback: {e}")
            return False

    def resume(self) -> bool:
        """Resume playback."""
        try:
            with self._lock:
                if self._state != PlaybackState.PAUSED:
                    return False
                
                # Adjust start time
                if self._pause_time and self._start_time:
                    pause_duration = time.time() - self._pause_time
                    self._start_time += pause_duration
                
                # Update state
                self._state = PlaybackState.PLAYING
                self._notify_state_change()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume playback: {e}")
            return False

    def _playback_loop(self) -> None:
        """Main playback loop."""
        try:
            while not self._stop_event.is_set():
                # Check if we should stop
                if self._should_stop():
                    break
                
                # Get current event
                event = self._events[self._current_index]
                
                # Wait for correct timing
                self._wait_for_timing(event.timestamp)
                
                # Process event
                if self._state == PlaybackState.PLAYING:
                    self._process_event(event)
                
                # Update progress
                self._notify_progress()
                
                # Move to next event
                self._current_index += 1
                
                # Check if we reached the end
                if self._current_index >= len(self._events):
                    if self._mode == PlaybackMode.ONCE:
                        break
                    elif self._mode == PlaybackMode.COUNT:
                        self._current_repeat += 1
                        if self._current_repeat >= self._repeat_count:
                            break
                    
                    # Reset for next iteration
                    self._current_index = 0
                    self._start_time = time.time()
            
            # Clean up
            self.stop()
            
        except Exception as e:
            self.logger.error(f"Playback error: {e}")
            self.stop()

    def _should_stop(self) -> bool:
        """Check if playback should stop."""
        # Check stop event
        if self._stop_event.is_set():
            return True
        
        # Check input if enabled
        if self._stop_on_input:
            current_time = time.time()
            if current_time - self._last_input_time < 0.1:  # 100ms threshold
                return True
        
        return False

    def _wait_for_timing(self, target_time: float) -> None:
        """Wait for correct event timing."""
        if self._state != PlaybackState.PLAYING:
            return
        
        current_time = time.time()
        elapsed = current_time - self._start_time
        wait_time = (target_time / self._speed_multiplier) - elapsed
        
        if wait_time > 0:
            if self._randomize_delays:
                # Add random variation (±20%)
                variation = wait_time * 0.2
                wait_time += random.uniform(-variation, variation)
                wait_time = max(0, wait_time)
            
            time.sleep(wait_time)

    def _process_event(self, event: InputEvent) -> None:
        """Process input event."""
        try:
            # Handle window-relative events
            if event.window_handle and event.window_title:
                # Find window
                window = window_manager.find_window(title=event.window_title)
                if not window:
                    self.logger.warning(f"Target window not found: {event.window_title}")
                    return
                
                # Bring to front
                window_manager.bring_to_front(window.handle)
            
            # Process by type
            if event.type == InputType.KEYBOARD:
                if event.data['action'] == 'press':
                    input_simulator.key_down(event.data['key'])
                else:
                    input_simulator.key_up(event.data['key'])
                
            elif event.type == InputType.MOUSE_MOVE:
                x = event.data['x']
                y = event.data['y']
                
                # Handle relative coordinates
                if 'relative_x' in event.data and event.window_handle:
                    window_rect = win32gui.GetWindowRect(event.window_handle)
                    x = window_rect[0] + event.data['relative_x']
                    y = window_rect[1] + event.data['relative_y']
                
                input_simulator.mouse_move(x, y)
                
            elif event.type == InputType.MOUSE_CLICK:
                button = MouseButton[event.data['button']]
                if event.data['action'] == 'press':
                    input_simulator.mouse_click(button)
                
            elif event.type == InputType.MOUSE_SCROLL:
                input_simulator.mouse_scroll(event.data['dy'])
            
        except Exception as e:
            self.logger.error(f"Failed to process event: {e}")

    def _start_input_monitoring(self) -> None:
        """Start input monitoring."""
        try:
            if self._monitor_thread and self._monitor_thread.is_alive():
                return
            
            self._monitor_thread = threading.Thread(
                target=self._monitor_input,
                name="InputMonitor"
            )
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start input monitoring: {e}")

    def _stop_input_monitoring(self) -> None:
        """Stop input monitoring."""
        try:
            if self._monitor_thread:
                self._monitor_thread = None
            
        except Exception as e:
            self.logger.error(f"Failed to stop input monitoring: {e}")

    def _monitor_input(self) -> None:
        """Monitor for user input."""
        try:
            while self._monitor_thread:
                if keyboard.is_pressed() or mouse.is_pressed():
                    self._last_input_time = time.time()
                time.sleep(0.01)  # 10ms polling
            
        except Exception as e:
            self.logger.error(f"Input monitoring error: {e}")

    def set_options(self, speed: float = 1.0,
                   randomize_delays: bool = False,
                   stop_on_input: bool = True,
                   restore_position: bool = True) -> None:
        """Set playback options."""
        with self._lock:
            self._speed_multiplier = max(0.1, min(10.0, speed))
            self._randomize_delays = randomize_delays
            self._stop_on_input = stop_on_input
            self._restore_position = restore_position

    def get_state(self) -> PlaybackState:
        """Get current state."""
        return self._state

    def get_progress(self) -> float:
        """Get playback progress (0-1)."""
        if not self._events:
            return 0.0
        return self._current_index / len(self._events)

    def add_state_callback(self, callback: Callable[[PlaybackState], None]) -> None:
        """Add state change callback."""
        with self._lock:
            self._state_callbacks.append(callback)

    def remove_state_callback(self, callback: Callable[[PlaybackState], None]) -> None:
        """Remove state change callback."""
        with self._lock:
            self._state_callbacks.remove(callback)

    def add_progress_callback(self, callback: Callable[[float], None]) -> None:
        """Add progress callback."""
        with self._lock:
            self._progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable[[float], None]) -> None:
        """Remove progress callback."""
        with self._lock:
            self._progress_callbacks.remove(callback)

    def _notify_state_change(self) -> None:
        """Notify state change callbacks."""
        for callback in self._state_callbacks:
            try:
                callback(self._state)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")

    def _notify_progress(self) -> None:
        """Notify progress callbacks."""
        progress = self.get_progress()
        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop()
            with self._lock:
                self._state_callbacks.clear()
                self._progress_callbacks.clear()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
macro_player = MacroPlayer()
