"""
Macro scripting module.
Copyright (c) 2025 AtomicArk
"""

import logging
import threading
from typing import Dict, List, Optional, Any, Callable
import time
import ast
import inspect
from pathlib import Path
import traceback

from ..utils.debug_helper import get_debug_helper
from .window_manager import window_manager
from .input_simulator import input_simulator, MouseButton
from .recorder import RecordingMode

class ScriptAPI:
    """API for macro scripts."""
    
    def __init__(self):
        self.logger = logging.getLogger('ScriptAPI')
        self._locals: Dict[str, Any] = {}
        self._globals: Dict[str, Any] = {}
        self._stop_flag = False
        
        # Initialize API
        self._init_api()

    def _init_api(self):
        """Initialize API functions."""
        # Input functions
        self._globals['key_press'] = self.key_press
        self._globals['key_down'] = self.key_down
        self._globals['key_up'] = self.key_up
        self._globals['mouse_move'] = self.mouse_move
        self._globals['mouse_click'] = self.mouse_click
        self._globals['mouse_scroll'] = self.mouse_scroll
        
        # Window functions
        self._globals['get_window'] = self.get_window
        self._globals['find_window'] = self.find_window
        self._globals['get_active_window'] = self.get_active_window
        self._globals['bring_to_front'] = self.bring_to_front
        
        # Utility functions
        self._globals['sleep'] = self.sleep
        self._globals['log'] = self.log
        self._globals['debug'] = self.debug
        self._globals['wait_for_window'] = self.wait_for_window
        self._globals['repeat'] = self.repeat
        self._globals['wait_until'] = self.wait_until
        
        # Constants
        self._globals['MOUSE_LEFT'] = MouseButton.LEFT.name
        self._globals['MOUSE_RIGHT'] = MouseButton.RIGHT.name
        self._globals['MOUSE_MIDDLE'] = MouseButton.MIDDLE.name

    def key_press(self, key: str, duration: Optional[float] = None) -> bool:
        """Press and release a key."""
        self._check_stop()
        return input_simulator.key_press(key, duration)

    def key_down(self, key: str) -> bool:
        """Press a key."""
        self._check_stop()
        return input_simulator.key_down(key)

    def key_up(self, key: str) -> bool:
        """Release a key."""
        self._check_stop()
        return input_simulator.key_up(key)

    def mouse_move(self, x: int, y: int, duration: Optional[float] = None,
                  relative: bool = False) -> bool:
        """Move mouse cursor."""
        self._check_stop()
        return input_simulator.mouse_move(x, y, duration, relative)

    def mouse_click(self, button: str, duration: Optional[float] = None) -> bool:
        """Click mouse button."""
        self._check_stop()
        return input_simulator.mouse_click(button, duration)

    def mouse_scroll(self, delta: int) -> bool:
        """Scroll mouse wheel."""
        self._check_stop()
        return input_simulator.mouse_scroll(delta)

    def get_window(self, handle: int) -> Optional[Dict]:
        """Get window information."""
        self._check_stop()
        window = window_manager.get_window(handle)
        if window:
            return {
                'handle': window.handle,
                'title': window.title,
                'class_name': window.class_name,
                'process_name': window.process_name,
                'rect': (window.rect.left, window.rect.top,
                        window.rect.right, window.rect.bottom)
            }
        return None

    def find_window(self, title: Optional[str] = None,
                   class_name: Optional[str] = None,
                   process_name: Optional[str] = None) -> Optional[Dict]:
        """Find window by properties."""
        self._check_stop()
        window = window_manager.find_window(title, class_name, process_name)
        if window:
            return {
                'handle': window.handle,
                'title': window.title,
                'class_name': window.class_name,
                'process_name': window.process_name,
                'rect': (window.rect.left, window.rect.top,
                        window.rect.right, window.rect.bottom)
            }
        return None

    def get_active_window(self) -> Optional[Dict]:
        """Get active window."""
        self._check_stop()
        window = window_manager.get_active_window()
        if window:
            return {
                'handle': window.handle,
                'title': window.title,
                'class_name': window.class_name,
                'process_name': window.process_name,
                'rect': (window.rect.left, window.rect.top,
                        window.rect.right, window.rect.bottom)
            }
        return None

    def bring_to_front(self, handle: int) -> bool:
        """Bring window to front."""
        self._check_stop()
        return window_manager.bring_to_front(handle)

    def sleep(self, seconds: float) -> None:
        """Sleep for specified duration."""
        self._check_stop()
        time.sleep(seconds)

    def log(self, message: str) -> None:
        """Log message."""
        self.logger.info(message)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)

    def wait_for_window(self, title: str, timeout: float = 10.0) -> Optional[Dict]:
        """Wait for window to appear."""
        self._check_stop()
        start_time = time.time()
        while time.time() - start_time < timeout:
            window = self.find_window(title=title)
            if window:
                return window
            time.sleep(0.1)
            self._check_stop()
        return None

    def repeat(self, count: int, func: Callable, *args, **kwargs) -> None:
        """Repeat function multiple times."""
        self._check_stop()
        for _ in range(count):
            func(*args, **kwargs)
            self._check_stop()

    def wait_until(self, condition: Callable[[], bool],
                  timeout: float = 10.0) -> bool:
        """Wait until condition is met."""
        self._check_stop()
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition():
                return True
            time.sleep(0.1)
            self._check_stop()
        return False

    def _check_stop(self) -> None:
        """Check if script should stop."""
        if self._stop_flag:
            raise InterruptedError("Script execution stopped")

    def stop(self) -> None:
        """Stop script execution."""
        self._stop_flag = True

    def reset(self) -> None:
        """Reset script state."""
        self._stop_flag = False
        self._locals.clear()

class MacroScript:
    """Manages macro script execution."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('MacroScript')
            self.debug = get_debug_helper()
            
            # Script API
            self._api = ScriptAPI()
            
            # State
            self._script_thread: Optional[threading.Thread] = None
            self._running = False
            
            self._initialized = True

    def validate_script(self, script: str) -> Optional[str]:
        """Validate script syntax."""
        try:
            ast.parse(script)
            return None
        except SyntaxError as e:
            return f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return str(e)

    def run_script(self, script: str) -> bool:
        """Run script."""
        try:
            # Check if already running
            if self._running:
                return False
            
            # Validate script
            error = self.validate_script(script)
            if error:
                self.logger.error(f"Script validation failed: {error}")
                return False
            
            # Reset API
            self._api.reset()
            
            # Start script thread
            self._script_thread = threading.Thread(
                target=self._run_script_thread,
                args=(script,),
                name="MacroScript"
            )
            self._script_thread.start()
            self._running = True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to run script: {e}")
            return False

    def stop_script(self) -> bool:
        """Stop script execution."""
        try:
            if not self._running:
                return False
            
            # Signal stop
            self._api.stop()
            
            # Wait for thread
            if self._script_thread and self._script_thread.is_alive():
                self._script_thread.join(timeout=1.0)
            
            # Reset state
            self._running = False
            self._script_thread = None
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop script: {e}")
            return False

    def _run_script_thread(self, script: str) -> None:
        """Script execution thread."""
        try:
            # Prepare globals
            globals_dict = self._api._globals.copy()
            globals_dict['__builtins__'] = __builtins__
            
            # Execute script
            exec(script, globals_dict, self._api._locals)
            
        except InterruptedError:
            self.logger.info("Script execution stopped")
        except Exception as e:
            self.logger.error(f"Script error: {traceback.format_exc()}")
        finally:
            self._running = False

    def is_running(self) -> bool:
        """Check if script is running."""
        return self._running

    def get_api_docs(self) -> Dict[str, str]:
        """Get API documentation."""
        docs = {}
        for name, func in self._api._globals.items():
            if callable(func) and not name.startswith('_'):
                doc = inspect.getdoc(func)
                if doc:
                    docs[name] = doc
        return docs

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop_script()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
macro_script = MacroScript()
