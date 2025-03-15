"""
Macro scripting module for advanced automation.
"""

import logging
import time
import threading
import inspect
from typing import Dict, List, Optional, Any, Callable
from enum import Enum, auto
import ast
import sys
from pathlib import Path

from ..utils.debug_helper import get_debug_helper
from .window_manager import window_manager, WindowInfo
from .input_simulator import input_simulator, InputMode, InputEvent
from .recorder import RecordingMode

class ScriptState(Enum):
    """Script execution states."""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR = auto()

class ScriptContext:
    """Execution context for macro scripts."""
    
    def __init__(self):
        self.logger = logging.getLogger('ScriptContext')
        self.debug = get_debug_helper()
        
        # State
        self.state = ScriptState.IDLE
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()
        
        # Script variables
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, Callable] = {}
        
        # Initialize API
        self._init_api()

    def _init_api(self):
        """Initialize script API functions."""
        # Input functions
        self.key_press = input_simulator.simulate_key
        self.mouse_move = input_simulator.simulate_mouse_move
        self.mouse_click = input_simulator.simulate_mouse_button
        self.mouse_scroll = input_simulator.simulate_mouse_scroll
        
        # Window functions
        self.get_window = window_manager.get_window_info
        self.find_window = window_manager.get_window_by_title
        self.get_active_window = window_manager.get_active_window
        self.bring_to_front = window_manager.bring_window_to_front
        
        # Utility functions
        self.sleep = time.sleep
        self.log = self.logger.info
        self.debug = self.debug.log
        
        # Helper functions
        def wait_for_window(title: str, timeout: float = 10.0) -> Optional[WindowInfo]:
            """Wait for window to appear."""
            start_time = time.time()
            while time.time() - start_time < timeout:
                window = window_manager.get_window_by_title(title)
                if window:
                    return window
                time.sleep(0.1)
            return None
        
        def repeat(count: int, func: Callable, *args, **kwargs):
            """Repeat function multiple times."""
            for _ in range(count):
                if self._stop_flag.is_set():
                    break
                func(*args, **kwargs)
        
        def wait_until(condition: Callable, timeout: float = 10.0) -> bool:
            """Wait until condition is met."""
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self._stop_flag.is_set():
                    return False
                if condition():
                    return True
                time.sleep(0.1)
            return False
        
        # Add helper functions
        self.wait_for_window = wait_for_window
        self.repeat = repeat
        self.wait_until = wait_until

class MacroScript:
    """Handles macro script execution."""
    
    def __init__(self):
        self.logger = logging.getLogger('MacroScript')
        self.debug = get_debug_helper()
        
        # State
        self.state = ScriptState.IDLE
        self._context = ScriptContext()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Callbacks
        self.on_state_change: Optional[Callable[[ScriptState], None]] = None
        self.on_script_complete: Optional[Callable[[], None]] = None
        self.on_script_error: Optional[Callable[[str], None]] = None

    def validate_script(self, script: str) -> Optional[str]:
        """Validate script syntax."""
        try:
            ast.parse(script)
            return None
        except Exception as e:
            return str(e)

    def run_script(self, script: str) -> bool:
        """Run macro script."""
        try:
            if self.state != ScriptState.IDLE:
                return False
            
            # Validate script
            error = self.validate_script(script)
            if error:
                if self.on_script_error:
                    self.on_script_error(error)
                return False
            
            with self._lock:
                # Reset state
                self._context._stop_flag.clear()
                self._context._pause_flag.clear()
                self._context.state = ScriptState.RUNNING
                self.state = ScriptState.RUNNING
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                # Start execution thread
                self._thread = threading.Thread(
                    target=self._run_script_thread,
                    args=(script,),
                    daemon=True
                )
                self._thread.start()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to run script: {e}")
            return False

    def _run_script_thread(self, script: str):
        """Script execution thread."""
        try:
            # Prepare globals
            globals_dict = {
                '__builtins__': {
                    name: getattr(__builtins__, name)
                    for name in dir(__builtins__)
                    if name in [
                        'True', 'False', 'None',
                        'int', 'float', 'str', 'bool',
                        'list', 'dict', 'tuple', 'set',
                        'len', 'range', 'enumerate',
                        'print', 'isinstance', 'hasattr',
                        'min', 'max', 'abs', 'round'
                    ]
                }
            }
            
            # Add API functions
            for name, func in inspect.getmembers(self._context):
                if not name.startswith('_'):
                    if inspect.ismethod(func) or inspect.isfunction(func):
                        globals_dict[name] = func
            
            # Execute script
            exec(script, globals_dict, self._context.variables)
            
            # Script complete
            if self.on_script_complete:
                self.on_script_complete()
            
        except Exception as e:
            self.logger.error(f"Script error: {e}")
            if self.on_script_error:
                self.on_script_error(str(e))
            self.state = ScriptState.ERROR
            if self.on_state_change:
                self.on_state_change(self.state)
            
        finally:
            # Reset state
            with self._lock:
                self.state = ScriptState.IDLE
                self._context.state = ScriptState.IDLE
                if self.on_state_change:
                    self.on_state_change(self.state)

    def stop_script(self) -> bool:
        """Stop script execution."""
        try:
            if self.state == ScriptState.IDLE:
                return False
            
            with self._lock:
                # Signal stop
                self._context._stop_flag.set()
                self._context._pause_flag.clear()
                
                # Wait for thread
                if self._thread:
                    self._thread.join(timeout=1.0)
                
                # Reset state
                self.state = ScriptState.IDLE
                self._context.state = ScriptState.IDLE
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop script: {e}")
            return False

    def pause_script(self) -> bool:
        """Pause script execution."""
        try:
            if self.state != ScriptState.RUNNING:
                return False
            
            with self._lock:
                self._context._pause_flag.set()
                self.state = ScriptState.PAUSED
                self._context.state = ScriptState.PAUSED
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause script: {e}")
            return False

    def resume_script(self) -> bool:
        """Resume script execution."""
        try:
            if self.state != ScriptState.PAUSED:
                return False
            
            with self._lock:
                self._context._pause_flag.clear()
                self.state = ScriptState.RUNNING
                self._context.state = ScriptState.RUNNING
                
                if self.on_state_change:
                    self.on_state_change(self.state)
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume script: {e}")
            return False

    def get_api_docs(self) -> Dict[str, str]:
        """Get API documentation."""
        docs = {}
        
        for name, func in inspect.getmembers(self._context):
            if not name.startswith('_'):
                if inspect.ismethod(func) or inspect.isfunction(func):
                    docs[name] = inspect.getdoc(func) or "No documentation available."
        
        return docs

    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop script if running
            if self.state != ScriptState.IDLE:
                self.stop_script()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
macro_script = MacroScript()
