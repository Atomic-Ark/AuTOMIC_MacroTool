from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QSystemTrayIcon, QMenu, QMessageBox,
    QFrame, QSizePolicy, QSpacerItem, QToolBar, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QIcon, QAction, QCloseEvent

import logging
import sys
from typing import Dict, Optional
from pathlib import Path

from ..core.config_manager import ConfigManager
from ..core.window_manager import SmartWindowManager
from ..core.input_simulator import InputSimulator
from ..core.macro_manager import MacroManager
from ..core.recorder import MacroRecorder
from ..core.player import MacroPlayer, PlaybackSettings, PlaybackMode
from .settings_dialog import SettingsDialog
from .script_editor import ScriptEditor
from ..utils.debug_helper import get_debug_helper
from ..utils.updater import update_manager

class MacroSlot(QFrame):
    """Widget representing a macro slot."""
    
    clicked = pyqtSignal()
    
    def __init__(self, slot_id: int, parent=None):
        super().__init__(parent)
        self.slot_id = slot_id
        self.macro = None
        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(100)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(f"Slot {self.slot_id + 1}")
        self.status_label = QLabel("Empty")
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.status_label)
        layout.addLayout(header_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.record_button = QPushButton("Record")
        self.play_button = QPushButton("Play")
        self.edit_button = QPushButton("Edit")
        self.clear_button = QPushButton("Clear")
        
        for button in [self.record_button, self.play_button,
                      self.edit_button, self.clear_button]:
            button.setEnabled(False)
            button_layout.addWidget(button)
        
        layout.addLayout(button_layout)
        
        # Hotkey label
        self.hotkey_label = QLabel("No hotkey set")
        layout.addWidget(self.hotkey_label)

    def update_state(self, macro=None, hotkey: str = None):
        """Update slot state."""
        self.macro = macro
        
        if macro:
            self.status_label.setText(macro.metadata.name)
            self.record_button.setEnabled(True)
            self.play_button.setEnabled(True)
            self.edit_button.setEnabled(True)
            self.clear_button.setEnabled(True)
        else:
            self.status_label.setText("Empty")
            self.record_button.setEnabled(True)
            self.play_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.clear_button.setEnabled(False)
        
        if hotkey:
            self.hotkey_label.setText(f"Hotkey: {hotkey}")
        else:
            self.hotkey_label.setText("No hotkey set")

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        super().mousePressEvent(event)
        self.clicked.emit()

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, config_manager: ConfigManager,
                 window_manager: SmartWindowManager,
                 input_simulator: InputSimulator,
                 macro_manager: MacroManager):
        super().__init__()
        
        # Store managers
        self.config_manager = config_manager
        self.window_manager = window_manager
        self.input_simulator = input_simulator
        self.macro_manager = macro_manager
        
        # Create recorder and player
        self.recorder = MacroRecorder(window_manager)
        self.player = MacroPlayer(window_manager, input_simulator)
        
        # Initialize logging and debug
        self.logger = logging.getLogger('MainWindow')
        self.debug = get_debug_helper()
        
        # Initialize UI
        self._init_ui()
        self._init_tray()
        self._init_connections()
        self._load_macros()
        
        # Register panic button callback
        self.debug.register_panic_callback(self._handle_panic)
        
        # Start minimized if configured
        if self.config_manager.config.minimize_to_tray:
            QTimer.singleShot(0, self.hide)

    def _init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("AuTOMIC MacroTool")
        self.setMinimumSize(800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        self._create_toolbar()
        
        # Create macro slots
        slots_layout = QGridLayout()
        self.macro_slots = []
        
        for i in range(6):
            slot = MacroSlot(i)
            row, col = divmod(i, 2)
            slots_layout.addWidget(slot, row, col)
            self.macro_slots.append(slot)
        
        layout.addLayout(slots_layout)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status indicators
        self.recording_label = QLabel()
        self.playing_label = QLabel()
        self.status_bar.addPermanentWidget(self.recording_label)
        self.status_bar.addPermanentWidget(self.playing_label)
        
        self._update_status()

    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Settings action
        settings_action = QAction(
            QIcon("src/resources/icons/settings.png"),
            "Settings",
            self
        )
        settings_action.triggered.connect(self._show_settings)
        toolbar.addAction(settings_action)
        
        toolbar.addSeparator()
        
        # Stop all action
        stop_action = QAction(
            QIcon("src/resources/icons/stop.png"),
            "Stop All",
            self
        )
        stop_action.triggered.connect(self._stop_all)
        toolbar.addAction(stop_action)
        
        # Pause all action
        self.pause_action = QAction(
            QIcon("src/resources/icons/pause.png"),
            "Pause All",
            self
        )
        self.pause_action.setCheckable(True)
        self.pause_action.triggered.connect(self._toggle_pause)
        toolbar.addAction(self.pause_action)

    def _init_tray(self):
        """Initialize system tray icon."""
        self.tray_icon = QSystemTrayIcon(
            QIcon("src/resources/icons/app.ico"),
            self
        )
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        
        stop_action = tray_menu.addAction("Stop All")
        stop_action.triggered.connect(self._stop_all)
        
        self.tray_pause_action = tray_menu.addAction("Pause All")
        self.tray_pause_action.setCheckable(True)
        self.tray_pause_action.triggered.connect(self._toggle_pause)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self._quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _init_connections(self):
        """Initialize signal connections."""
        # Slot connections
        for slot in self.macro_slots:
            slot.record_button.clicked.connect(
                lambda s=slot: self._start_recording(s)
            )
            slot.play_button.clicked.connect(
                lambda s=slot: self._start_playback(s)
            )
            slot.edit_button.clicked.connect(
                lambda s=slot: self._edit_macro(s)
            )
            slot.clear_button.clicked.connect(
                lambda s=slot: self._clear_slot(s)
            )
        
        # Player connections
        self.player.on_playback_start = self._on_playback_start
        self.player.on_playback_stop = self._on_playback_stop
        self.player.on_playback_pause = self._on_playback_pause
        self.player.on_playback_resume = self._on_playback_resume
        self.player.on_progress = self._on_playback_progress
        
        # Update manager connections
        update_manager.on_update_available.connect(self._show_update_dialog)

    def _load_macros(self):
        """Load macros into slots."""
        for slot_id, slot in enumerate(self.macro_slots):
            macro = self.macro_manager.slots.get(slot_id)
            hotkey = self.config_manager.config.macro_hotkeys.get(slot_id)
            slot.update_state(macro, hotkey)

    def _start_recording(self, slot: MacroSlot):
        """Start macro recording."""
        try:
            if self.recorder.recording:
                return
            
            # Get target window
            target_window = self.window_manager.get_active_window()
            if not target_window:
                QMessageBox.warning(
                    self,
                    "Recording Error",
                    "No active window detected."
                )
                return
            
            # Start recording
            if self.recorder.start_recording(target_window):
                slot.status_label.setText("Recording...")
                self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")
            QMessageBox.critical(
                self,
                "Recording Error",
                f"Failed to start recording: {e}"
            )

    def _start_playback(self, slot: MacroSlot):
        """Start macro playback."""
        try:
            if not slot.macro or self.player.state != PlaybackState.STOPPED:
                return
            
            # Create playback settings
            settings = PlaybackSettings(
                mode=self.config_manager.config.default_playback_mode,
                repeat_count=self.config_manager.config.repeat_count,
                speed_multiplier=1.0,
                stealth_mode=self.config_manager.config.stealth_mode,
                stop_on_input=self.config_manager.config.stop_on_input,
                restore_mouse=self.config_manager.config.restore_mouse,
                randomize_delays=self.config_manager.config.randomize_delays,
                random_factor=self.config_manager.config.random_factor
            )
            
            # Start playback
            if self.player.start_playback(slot.macro.events, settings):
                slot.status_label.setText("Playing...")
                self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error starting playback: {e}")
            QMessageBox.critical(
                self,
                "Playback Error",
                f"Failed to start playback: {e}"
            )

    def _edit_macro(self, slot: MacroSlot):
        """Edit macro script."""
        try:
            if not slot.macro:
                return
            
            editor = ScriptEditor(slot.macro, self)
            if editor.exec() == QDialog.DialogCode.Accepted:
                self._load_macros()
            
        except Exception as e:
            self.logger.error(f"Error editing macro: {e}")
            QMessageBox.critical(
                self,
                "Editor Error",
                f"Failed to open editor: {e}"
            )

    def _clear_slot(self, slot: MacroSlot):
        """Clear macro slot."""
        try:
            reply = QMessageBox.question(
                self,
                "Clear Slot",
                "Are you sure you want to clear this slot?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.macro_manager.remove_from_slot(slot.slot_id)
                slot.update_state()
            
        except Exception as e:
            self.logger.error(f"Error clearing slot: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to clear slot: {e}"
            )

    def _stop_all(self):
        """Stop all macro operations."""
        try:
            if self.recorder.recording:
                self.recorder.stop_recording()
            
            if self.player.state != PlaybackState.STOPPED:
                self.player.stop_playback()
            
            self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error stopping operations: {e}")

    def _toggle_pause(self):
        """Toggle pause state."""
        try:
            if self.player.state == PlaybackState.PLAYING:
                self.player.pause_playback()
            elif self.player.state == PlaybackState.PAUSED:
                self.player.resume_playback()
            
            self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error toggling pause: {e}")

    def _handle_panic(self):
        """Handle panic button press."""
        try:
            self._stop_all()
            self.show()
            self.activateWindow()
            
            QMessageBox.information(
                self,
                "Panic Button",
                "All macro operations have been stopped."
            )
            
        except Exception as e:
            self.logger.error(f"Error handling panic: {e}")

    def _show_settings(self):
        """Show settings dialog."""
        try:
            dialog = SettingsDialog(self.config_manager, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._load_macros()
            
        except Exception as e:
            self.logger.error(f"Error showing settings: {e}")
            QMessageBox.critical(
                self,
                "Settings Error",
                f"Failed to open settings: {e}"
            )

    def _show_update_dialog(self, update_info: Dict):
        """Show update available dialog."""
        try:
            reply = QMessageBox.question(
                self,
                "Update Available",
                f"Version {update_info['version']} is available.\n\n"
                f"Changes:\n{update_info['description']}\n\n"
                "Would you like to update now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                update_manager.download_update(update_info)
            
        except Exception as e:
            self.logger.error(f"Error showing update dialog: {e}")

    def _update_status(self):
        """Update status indicators."""
        try:
            # Recording status
            if self.recorder.recording:
                self.recording_label.setText("Recording")
                self.recording_label.setStyleSheet("color: red")
            else:
                self.recording_label.setText("")
            
            # Playback status
            if self.player.state == PlaybackState.PLAYING:
                self.playing_label.setText("Playing")
                self.playing_label.setStyleSheet("color: green")
                self.pause_action.setChecked(False)
                self.tray_pause_action.setChecked(False)
            elif self.player.state == PlaybackState.PAUSED:
                self.playing_label.setText("Paused")
                self.playing_label.setStyleSheet("color: orange")
                self.pause_action.setChecked(True)
                self.tray_pause_action.setChecked(True)
            else:
                self.playing_label.setText("")
                self.pause_action.setChecked(False)
                self.tray_pause_action.setChecked(False)
            
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")

    def _quit_application(self):
        """Quit application."""
        try:
            self._stop_all()
            
            # Clean up resources
            self.recorder.cleanup()
            self.player.cleanup()
            self.macro_manager.cleanup()
            self.debug.cleanup()
            update_manager.cleanup()
            
            QApplication.quit()
            
        except Exception as e:
            self.logger.error(f"Error quitting application: {e}")
            sys.exit(1)

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        try:
            if self.config_manager.config.minimize_to_tray:
                event.ignore()
                self.hide()
            else:
                self._quit_application()
            
        except Exception as e:
            self.logger.error(f"Error handling close event: {e}")
            event.accept()

    def changeEvent(self, event):
        """Handle window state changes."""
        try:
            if event.type() == Qt.WindowType.WindowStateChange:
                if self.isMinimized() and self.config_manager.config.minimize_to_tray:
                    event.ignore()
                    self.hide()
            
        except Exception as e:
            self.logger.error(f"Error handling state change: {e}")
        
        super().changeEvent(event)
