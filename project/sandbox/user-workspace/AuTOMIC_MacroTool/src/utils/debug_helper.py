"""
Debug and logging helper module.
"""

import logging
import sys
import os
import time
import threading
import traceback
from enum import Enum, auto
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime
import psutil
import win32api
import win32con
import win32gui
import win32process

class DebugLevel(Enum):
    """Debug logging levels."""
    NONE = auto()
    BASIC = auto()
    DETAILED = auto()
    VERBOSE = auto()

class DebugHelper:
    """Manages debugging and logging functionality."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            # Initialize logger
            self.logger = logging.getLogger('DebugHelper')
            
            # State
            self._level = DebugLevel.BASIC
            self._log_file: Optional[Path] = None
            self._crash_file: Optional[Path] = None
            self._debug_info: Dict = {}
            
            # Performance monitoring
            self._perf_data: List[Dict] = []
            self._perf_thread: Optional[threading.Thread] = None
            self._stop_flag = threading.Event()
            
            # Initialize
            self._init_logging()
            self._start_monitoring()
            self._initialized = True

    def _init_logging(self):
        """Initialize logging system."""
        try:
            # Get log directory
            log_dir = Path.home() / "Documents" / "AuTOMIC_MacroTool" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create log file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self._log_file = log_dir / f"debug_{timestamp}.log"
            self._crash_file = log_dir / f"crash_{timestamp}.log"
            
            # Configure logging
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # File handler
            file_handler = logging.FileHandler(
                self._log_file,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            
            # Set exception hook
            sys.excepthook = self._handle_exception
            
        except Exception as e:
            print(f"Failed to initialize logging: {e}")

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        try:
            # Log exception
            self.logger.error(
                "Uncaught exception:",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            # Save crash report
            if self._crash_file:
                with open(self._crash_file, 'w', encoding='utf-8') as f:
                    # Exception info
                    f.write("=== Exception Details ===\n")
                    f.write(f"Type: {exc_type.__name__}\n")
                    f.write(f"Message: {str(exc_value)}\n")
                    f.write("\n=== Traceback ===\n")
                    traceback.print_tb(exc_traceback, file=f)
                    
                    # System info
                    f.write("\n=== System Information ===\n")
                    self._write_system_info(f)
                    
                    # Debug info
                    f.write("\n=== Debug Information ===\n")
                    for key, value in self._debug_info.items():
                        f.write(f"{key}: {value}\n")
                    
                    # Performance data
                    f.write("\n=== Performance Data ===\n")
                    for data in self._perf_data[-100:]:  # Last 100 entries
                        f.write(f"{data}\n")
            
        except Exception as e:
            print(f"Failed to handle exception: {e}")

    def _write_system_info(self, file):
        """Write system information to file."""
        try:
            # Python info
            file.write(f"Python Version: {sys.version}\n")
            file.write(f"Platform: {sys.platform}\n")
            
            # System info
            import platform
            file.write(f"OS: {platform.platform()}\n")
            file.write(f"Machine: {platform.machine()}\n")
            file.write(f"Processor: {platform.processor()}\n")
            
            # Memory info
            memory = psutil.virtual_memory()
            file.write(f"Memory Total: {memory.total / 1024 / 1024:.1f} MB\n")
            file.write(f"Memory Available: {memory.available / 1024 / 1024:.1f} MB\n")
            
            # Display info
            dc = win32gui.GetDC(0)
            width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            dpi = win32gui.GetDeviceCaps(dc, win32con.LOGPIXELSX)
            win32gui.ReleaseDC(0, dc)
            file.write(f"Screen: {width}x{height} @ {dpi} DPI\n")
            
        except Exception as e:
            file.write(f"Error getting system info: {e}\n")

    def _start_monitoring(self):
        """Start performance monitoring."""
        try:
            def monitor():
                while not self._stop_flag.is_set():
                    try:
                        # Get process info
                        process = psutil.Process()
                        
                        # Collect data
                        data = {
                            'timestamp': time.time(),
                            'cpu_percent': process.cpu_percent(),
                            'memory_percent': process.memory_percent(),
                            'num_threads': process.num_threads(),
                            'num_handles': process.num_handles()
                        }
                        
                        # Store data
                        self._perf_data.append(data)
                        
                        # Keep last 1000 entries
                        if len(self._perf_data) > 1000:
                            self._perf_data = self._perf_data[-1000:]
                        
                        # Sleep
                        time.sleep(1.0)
                        
                    except Exception as e:
                        self.logger.error(f"Error in performance monitor: {e}")
            
            self._perf_thread = threading.Thread(
                target=monitor,
                daemon=True
            )
            self._perf_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")

    def set_debug_level(self, level: DebugLevel):
        """Set debug logging level."""
        try:
            self._level = level
            
            # Update root logger level
            root_logger = logging.getLogger()
            if level == DebugLevel.NONE:
                root_logger.setLevel(logging.WARNING)
            elif level == DebugLevel.BASIC:
                root_logger.setLevel(logging.INFO)
            elif level == DebugLevel.DETAILED:
                root_logger.setLevel(logging.DEBUG)
            elif level == DebugLevel.VERBOSE:
                root_logger.setLevel(logging.DEBUG)
            
            self.logger.info(f"Debug level set to {level.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to set debug level: {e}")

    def log(self, message: str, level: DebugLevel = DebugLevel.BASIC):
        """Log debug message at specified level."""
        try:
            if level.value <= self._level.value:
                self.logger.debug(message)
        except Exception as e:
            self.logger.error(f"Failed to log message: {e}")

    def add_debug_info(self, key: str, value: str):
        """Add debug information."""
        try:
            self._debug_info[key] = value
        except Exception as e:
            self.logger.error(f"Failed to add debug info: {e}")

    def get_debug_info(self) -> Dict:
        """Get current debug information."""
        try:
            return dict(self._debug_info)
        except Exception as e:
            self.logger.error(f"Failed to get debug info: {e}")
            return {}

    def get_performance_data(self) -> List[Dict]:
        """Get collected performance data."""
        try:
            return list(self._perf_data)
        except Exception as e:
            self.logger.error(f"Failed to get performance data: {e}")
            return []

    def cleanup(self):
        """Clean up resources."""
        try:
            self._stop_flag.set()
            
            if self._perf_thread and self._perf_thread.is_alive():
                self._perf_thread.join(timeout=1.0)
            
            # Close log files
            logging.shutdown()
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

def get_debug_helper() -> DebugHelper:
    """Get global debug helper instance."""
    return DebugHelper()
