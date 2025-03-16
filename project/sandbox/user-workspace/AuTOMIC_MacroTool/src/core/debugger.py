"""
Macro debugger module.
Copyright (c) 2025 AtomicArk
"""

import logging
import threading
from typing import Dict, List, Optional, Set, Any, Callable
import time
import inspect
import sys
import traceback
from dataclasses import dataclass
from enum import Enum, auto
import bdb
import linecache

from ..utils.debug_helper import get_debug_helper

class DebuggerState(Enum):
    """Debugger states."""
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()
    STEPPING = auto()

@dataclass
class Breakpoint:
    """Breakpoint information."""
    id: int
    file: str
    line: int
    condition: Optional[str] = None
    enabled: bool = True
    hit_count: int = 0

@dataclass
class Variable:
    """Variable information."""
    name: str
    value: Any
    type: str
    scope: str  # 'local' or 'global'

class MacroDebugger(bdb.Bdb):
    """Debugs macro execution."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self.logger = logging.getLogger('MacroDebugger')
            self.debug = get_debug_helper()
            
            # State
            self._state = DebuggerState.STOPPED
            self._breakpoints: Dict[int, Breakpoint] = {}
            self._next_breakpoint_id = 1
            self._watch_variables: Set[str] = set()
            self._current_frame = None
            self._step_mode = False
            
            # Event handlers
            self._on_line: Optional[Callable] = None
            self._on_return: Optional[Callable] = None
            self._on_exception: Optional[Callable] = None
            self._on_variable_changed: Optional[Callable] = None
            
            self._initialized = True

    def start(self, script: str) -> bool:
        """Start debugging script."""
        try:
            if self._state != DebuggerState.STOPPED:
                return False
            
            self._state = DebuggerState.RUNNING
            
            # Run in separate thread
            threading.Thread(
                target=self.run,
                args=(script,),
                name="DebuggerThread"
            ).start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start debugger: {e}")
            return False

    def stop(self) -> bool:
        """Stop debugging."""
        try:
            if self._state == DebuggerState.STOPPED:
                return False
            
            self._state = DebuggerState.STOPPED
            self.set_quit()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop debugger: {e}")
            return False

    def pause(self) -> bool:
        """Pause execution."""
        try:
            if self._state != DebuggerState.RUNNING:
                return False
            
            self._state = DebuggerState.PAUSED
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause debugger: {e}")
            return False

    def resume(self) -> bool:
        """Resume execution."""
        try:
            if self._state != DebuggerState.PAUSED:
                return False
            
            self._state = DebuggerState.RUNNING
            self._step_mode = False
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume debugger: {e}")
            return False

    def step(self) -> bool:
        """Step to next line."""
        try:
            if self._state != DebuggerState.PAUSED:
                return False
            
            self._state = DebuggerState.STEPPING
            self._step_mode = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to step: {e}")
            return False

    def add_breakpoint(self, file: str, line: int,
                      condition: Optional[str] = None) -> Optional[int]:
        """Add breakpoint."""
        try:
            bp = Breakpoint(
                id=self._next_breakpoint_id,
                file=file,
                line=line,
                condition=condition
            )
            
            self._breakpoints[bp.id] = bp
            self._next_breakpoint_id += 1
            
            return bp.id
            
        except Exception as e:
            self.logger.error(f"Failed to add breakpoint: {e}")
            return None

    def remove_breakpoint(self, id: int) -> bool:
        """Remove breakpoint."""
        try:
            if id not in self._breakpoints:
                return False
            
            del self._breakpoints[id]
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove breakpoint: {e}")
            return False

    def add_watch(self, variable: str) -> bool:
        """Add variable to watch list."""
        try:
            self._watch_variables.add(variable)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add watch: {e}")
            return False

    def remove_watch(self, variable: str) -> bool:
        """Remove variable from watch list."""
        try:
            if variable not in self._watch_variables:
                return False
            
            self._watch_variables.remove(variable)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove watch: {e}")
            return False

    def get_variables(self) -> List[Variable]:
        """Get current variables."""
        try:
            if not self._current_frame:
                return []
            
            variables = []
            
            # Local variables
            for name, value in self._current_frame.f_locals.items():
                variables.append(Variable(
                    name=name,
                    value=value,
                    type=type(value).__name__,
                    scope='local'
                ))
            
            # Global variables
            for name, value in self._current_frame.f_globals.items():
                if name not in self._current_frame.f_locals:
                    variables.append(Variable(
                        name=name,
                        value=value,
                        type=type(value).__name__,
                        scope='global'
                    ))
            
            return variables
            
        except Exception as e:
            self.logger.error(f"Failed to get variables: {e}")
            return []

    def get_stack(self) -> List[str]:
        """Get current call stack."""
        try:
            if not self._current_frame:
                return []
            
            stack = []
            frame = self._current_frame
            
            while frame:
                stack.append(
                    f"{frame.f_code.co_filename}:{frame.f_lineno} "
                    f"in {frame.f_code.co_name}"
                )
                frame = frame.f_back
            
            return stack
            
        except Exception as e:
            self.logger.error(f"Failed to get stack: {e}")
            return []

    def get_current_line(self) -> Optional[str]:
        """Get current source line."""
        try:
            if not self._current_frame:
                return None
            
            return linecache.getline(
                self._current_frame.f_code.co_filename,
                self._current_frame.f_lineno
            ).strip()
            
        except Exception as e:
            self.logger.error(f"Failed to get line: {e}")
            return None

    def set_line_handler(self, handler: Callable) -> None:
        """Set line event handler."""
        self._on_line = handler

    def set_return_handler(self, handler: Callable) -> None:
        """Set return event handler."""
        self._on_return = handler

    def set_exception_handler(self, handler: Callable) -> None:
        """Set exception event handler."""
        self._on_exception = handler

    def set_variable_handler(self, handler: Callable) -> None:
        """Set variable change handler."""
        self._on_variable_changed = handler

    def user_line(self, frame) -> None:
        """Handle line event."""
        try:
            self._current_frame = frame
            
            # Check breakpoints
            for bp in self._breakpoints.values():
                if (bp.enabled and
                    bp.file == frame.f_code.co_filename and
                    bp.line == frame.f_lineno):
                    
                    # Check condition
                    if bp.condition:
                        try:
                            if not eval(bp.condition,
                                      frame.f_globals,
                                      frame.f_locals):
                                continue
                        except:
                            continue
                    
                    bp.hit_count += 1
                    self._state = DebuggerState.PAUSED
            
            # Check watched variables
            for var in self._watch_variables:
                if var in frame.f_locals:
                    if self._on_variable_changed:
                        self._on_variable_changed(var, frame.f_locals[var])
            
            # Notify line event
            if self._on_line:
                self._on_line(frame.f_code.co_filename, frame.f_lineno)
            
            # Handle stepping
            if self._step_mode:
                self._state = DebuggerState.PAUSED
                self._step_mode = False
            
            # Wait if paused
            while self._state == DebuggerState.PAUSED:
                time.sleep(0.1)
                if self._state == DebuggerState.STOPPED:
                    sys.exit()
            
        except Exception as e:
            self.logger.error(f"Line event error: {e}")

    def user_return(self, frame, return_value) -> None:
        """Handle return event."""
        try:
            if self._on_return:
                self._on_return(frame.f_code.co_name, return_value)
            
        except Exception as e:
            self.logger.error(f"Return event error: {e}")

    def user_exception(self, frame, exc_info) -> None:
        """Handle exception event."""
        try:
            if self._on_exception:
                self._on_exception(exc_info[0].__name__, str(exc_info[1]))
            
        except Exception as e:
            self.logger.error(f"Exception event error: {e}")

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop()
            self._breakpoints.clear()
            self._watch_variables.clear()
            self._current_frame = None
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
macro_debugger = MacroDebugger()
