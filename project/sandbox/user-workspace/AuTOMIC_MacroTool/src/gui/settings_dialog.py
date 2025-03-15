from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QPushButton, QGroupBox, QFormLayout, QProgressBar,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence

import logging
import json
from pathlib import Path
from typing import Dict, Optional
import keyboard
import win32api
import win32con

from ..core.config_manager import ConfigManager
from ..utils.debug_helper import get_debug_helper, DebugLevel
from ..utils.updater import update_manager
from .styles import Theme

class HotkeyEdit(QLineEdit):
    """Custom line edit for hotkey capture."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.current_keys = set()
        self.capturing = False

    def keyPressEvent(self, event):
        """Handle key press events."""
        if self.capturing:
            key = QKeySequence(event.key()).toString()
            if key not in self.current_keys:
                self.current_keys.add(key)
                self.setText('+'.join(sorted(self.current_keys)))
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Handle key release events."""
        if self.capturing:
            key = QKeySequence(event.key()).toString()
            if key in self.current_keys:
                self.current_keys.remove(key)
            event.accept()
        else:
            super().keyReleaseEvent(event)

    def focusInEvent(self, event):
        """Handle focus in event."""
        super().focusInEvent(event)
        self.capturing = True
        self.current_keys.clear()
        self.setText("Press keys...")

    def focusOutEvent(self, event):
        """Handle focus out event."""
        super().focusOutEvent(event)
        self.capturing = False
        if not self.current_keys:
            self.setText(self.placeholderText())

class SettingsDialog(QDialog):
    """Application settings dialog."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger('SettingsDialog')
        self.debug = get_debug_helper()
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_general_tab()
        self._create_recording_tab()
        self._create_playback_tab()
        self._create_hotkeys_tab()
        self._create_advanced_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_settings)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)

    def _create_general_tab(self):
        """Create general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Language group
        lang_group = QGroupBox("Language")
        lang_layout = QFormLayout(lang_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(['English', 'Polish', 'German', 'French', 'Italian', 'Spanish'])
        lang_layout.addRow("Interface Language:", self.language_combo)
        
        layout.addWidget(lang_group)
        
        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([t.value for t in Theme])
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.5, 2.0)
        self.scale_spin.setSingleStep(0.1)
        appearance_layout.addRow("UI Scale:", self.scale_spin)
        
        layout.addWidget(appearance_group)
        
        # Startup group
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout(startup_group)
        
        self.autostart_check = QCheckBox("Start with Windows")
        startup_layout.addRow(self.autostart_check)
        
        self.minimize_check = QCheckBox("Start minimized")
        startup_layout.addRow(self.minimize_check)
        
        layout.addWidget(startup_group)
        
        # Updates group
        updates_group = QGroupBox("Updates")
        updates_layout = QFormLayout(updates_group)
        
        self.check_updates_check = QCheckBox("Check for updates automatically")
        updates_layout.addRow(self.check_updates_check)
        
        self.check_now_button = QPushButton("Check Now")
        self.check_now_button.clicked.connect(self._check_updates)
        updates_layout.addRow(self.check_now_button)
        
        layout.addWidget(updates_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "General")

    def _create_recording_tab(self):
        """Create recording settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Input group
        input_group = QGroupBox("Input Recording")
        input_layout = QFormLayout(input_group)
        
        self.record_mouse_check = QCheckBox("Record mouse movements")
        input_layout.addRow(self.record_mouse_check)
        
        self.record_keyboard_check = QCheckBox("Record keyboard input")
        input_layout.addRow(self.record_keyboard_check)
        
        self.record_delays_check = QCheckBox("Record delays")
        input_layout.addRow(self.record_delays_check)
        
        self.min_delay_spin = QDoubleSpinBox()
        self.min_delay_spin.setRange(0.01, 1.0)
        self.min_delay_spin.setSingleStep(0.01)
        input_layout.addRow("Minimum Delay (s):", self.min_delay_spin)
        
        layout.addWidget(input_group)
        
        # Window group
        window_group = QGroupBox("Window Detection")
        window_layout = QFormLayout(window_group)
        
        self.window_mode_combo = QComboBox()
        self.window_mode_combo.addItems(['Auto', 'Manual', 'Fullscreen'])
        window_layout.addRow("Detection Mode:", self.window_mode_combo)
        
        layout.addWidget(window_group)
        
        # Storage group
        storage_group = QGroupBox("Storage")
        storage_layout = QFormLayout(storage_group)
        
        self.macro_dir_edit = QLineEdit()
        self.macro_dir_edit.setReadOnly(True)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_macro_dir)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.macro_dir_edit)
        dir_layout.addWidget(browse_button)
        
        storage_layout.addRow("Macro Directory:", dir_layout)
        
        layout.addWidget(storage_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Recording")

    def _create_playback_tab(self):
        """Create playback settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Playback group
        playback_group = QGroupBox("Playback")
        playback_layout = QFormLayout(playback_group)
        
        self.playback_mode_combo = QComboBox()
        self.playback_mode_combo.addItems(['Once', 'Loop', 'Count'])
        playback_layout.addRow("Default Mode:", self.playback_mode_combo)
        
        self.repeat_count_spin = QSpinBox()
        self.repeat_count_spin.setRange(1, 9999)
        playback_layout.addRow("Repeat Count:", self.repeat_count_spin)
        
        layout.addWidget(playback_group)
        
        # Timing group
        timing_group = QGroupBox("Timing")
        timing_layout = QFormLayout(timing_group)
        
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 10.0)
        self.speed_spin.setSingleStep(0.1)
        timing_layout.addRow("Default Speed:", self.speed_spin)
        
        self.randomize_delays_check = QCheckBox("Randomize delays")
        timing_layout.addRow(self.randomize_delays_check)
        
        self.random_factor_spin = QDoubleSpinBox()
        self.random_factor_spin.setRange(0.0, 1.0)
        self.random_factor_spin.setSingleStep(0.1)
        timing_layout.addRow("Random Factor:", self.random_factor_spin)
        
        layout.addWidget(timing_group)
        
        # Safety group
        safety_group = QGroupBox("Safety")
        safety_layout = QFormLayout(safety_group)
        
        self.stop_on_input_check = QCheckBox("Stop on user input")
        safety_layout.addRow(self.stop_on_input_check)
        
        self.restore_mouse_check = QCheckBox("Restore mouse position")
        safety_layout.addRow(self.restore_mouse_check)
        
        layout.addWidget(safety_group)
        
        # Stealth group
        stealth_group = QGroupBox("Stealth Mode")
        stealth_layout = QFormLayout(stealth_group)
        
        self.stealth_mode_check = QCheckBox("Enable stealth mode")
        stealth_layout.addRow(self.stealth_mode_check)
        
        self.install_driver_button = QPushButton("Install Interception Driver")
        self.install_driver_button.clicked.connect(self._install_driver)
        stealth_layout.addRow(self.install_driver_button)
        
        self.driver_progress = QProgressBar()
        self.driver_progress.hide()
        stealth_layout.addRow(self.driver_progress)
        
        layout.addWidget(stealth_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Playback")

    def _create_hotkeys_tab(self):
        """Create hotkeys settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Global hotkeys group
        global_group = QGroupBox("Global Hotkeys")
        global_layout = QFormLayout(global_group)
        
        self.panic_hotkey = HotkeyEdit()
        global_layout.addRow("Panic Button:", self.panic_hotkey)
        
        layout.addWidget(global_group)
        
        # Macro hotkeys group
        macro_group = QGroupBox("Macro Hotkeys")
        macro_layout = QFormLayout(macro_group)
        
        self.macro_hotkeys = []
        for i in range(6):
            hotkey = HotkeyEdit()
            macro_layout.addRow(f"Macro {i+1}:", hotkey)
            self.macro_hotkeys.append(hotkey)
        
        layout.addWidget(macro_group)
        
        # Action hotkeys group
        action_group = QGroupBox("Action Hotkeys")
        action_layout = QFormLayout(action_group)
        
        self.record_hotkey = HotkeyEdit()
        action_layout.addRow("Start/Stop Recording:", self.record_hotkey)
        
        self.play_hotkey = HotkeyEdit()
        action_layout.addRow("Play/Pause:", self.play_hotkey)
        
        layout.addWidget(action_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Hotkeys")

    def _create_advanced_tab(self):
        """Create advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Debug group
        debug_group = QGroupBox("Debugging")
        debug_layout = QFormLayout(debug_group)
        
        self.debug_level_combo = QComboBox()
        self.debug_level_combo.addItems([level.name for level in DebugLevel])
        debug_layout.addRow("Debug Level:", self.debug_level_combo)
        
        self.open_logs_button = QPushButton("Open Log Directory")
        self.open_logs_button.clicked.connect(self._open_logs)
        debug_layout.addRow(self.open_logs_button)
        
        layout.addWidget(debug_group)
        
        # Performance group
        perf_group = QGroupBox("Performance")
        perf_layout = QFormLayout(perf_group)
        
        self.performance_mode_check = QCheckBox("Enable performance mode")
        perf_layout.addRow(self.performance_mode_check)
        
        layout.addWidget(perf_group)
        
        # Reset group
        reset_group = QGroupBox("Reset")
        reset_layout = QVBoxLayout(reset_group)
        
        self.reset_button = QPushButton("Reset All Settings")
        self.reset_button.clicked.connect(self._reset_settings)
        reset_layout.addWidget(self.reset_button)
        
        layout.addWidget(reset_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Advanced")

    def _load_settings(self):
        """Load current settings."""
        try:
            config = self.config_manager.config
            
            # General
            self.language_combo.setCurrentText(config.language)
            self.theme_combo.setCurrentText(config.theme.value)
            self.scale_spin.setValue(config.ui_scale)
            self.autostart_check.setChecked(config.autostart)
            self.minimize_check.setChecked(config.minimize_to_tray)
            self.check_updates_check.setChecked(config.check_updates)
            
            # Recording
            self.record_mouse_check.setChecked(config.record_mouse)
            self.record_keyboard_check.setChecked(config.record_keyboard)
            self.record_delays_check.setChecked(config.record_delays)
            self.min_delay_spin.setValue(config.min_delay)
            self.window_mode_combo.setCurrentText(config.window_mode)
            self.macro_dir_edit.setText(str(config.macro_directory))
            
            # Playback
            self.playback_mode_combo.setCurrentText(config.default_playback_mode.value)
            self.repeat_count_spin.setValue(config.repeat_count)
            self.speed_spin.setValue(config.default_speed)
            self.randomize_delays_check.setChecked(config.randomize_delays)
            self.random_factor_spin.setValue(config.random_factor)
            self.stop_on_input_check.setChecked(config.stop_on_input)
            self.restore_mouse_check.setChecked(config.restore_mouse)
            self.stealth_mode_check.setChecked(config.stealth_mode)
            
            # Hotkeys
            self.panic_hotkey.setText(config.panic_hotkey)
            for i, hotkey in enumerate(self.macro_hotkeys):
                hotkey.setText(config.macro_hotkeys.get(i, ""))
            self.record_hotkey.setText(config.record_hotkey)
            self.play_hotkey.setText(config.play_hotkey)
            
            # Advanced
            self.debug_level_combo.setCurrentText(config.debug_level.name)
            self.performance_mode_check.setChecked(config.performance_mode)
            
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            QMessageBox.warning(
                self,
                "Settings Error",
                "Failed to load settings. Using defaults."
            )

    def _apply_settings(self):
        """Apply current settings."""
        try:
            config = self.config_manager.config
            
            # General
            config.language = self.language_combo.currentText()
            config.theme = Theme(self.theme_combo.currentText())
            config.ui_scale = self.scale_spin.value()
            config.autostart = self.autostart_check.isChecked()
            config.minimize_to_tray = self.minimize_check.isChecked()
            config.check_updates = self.check_updates_check.isChecked()
            
            # Recording
            config.record_mouse = self.record_mouse_check.isChecked()
            config.record_keyboard = self.record_keyboard_check.isChecked()
            config.record_delays = self.record_delays_check.isChecked()
            config.min_delay = self.min_delay_spin.value()
            config.window_mode = self.window_mode_combo.currentText()
            config.macro_directory = Path(self.macro_dir_edit.text())
            
            # Playback
            config.default_playback_mode = self.playback_mode_combo.currentText()
            config.repeat_count = self.repeat_count_spin.value()
            config.default_speed = self.speed_spin.value()
            config.randomize_delays = self.randomize_delays_check.isChecked()
            config.random_factor = self.random_factor_spin.value()
            config.stop_on_input = self.stop_on_input_check.isChecked()
            config.restore_mouse = self.restore_mouse_check.isChecked()
            config.stealth_mode = self.stealth_mode_check.isChecked()
            
            # Hotkeys
            config.panic_hotkey = self.panic_hotkey.text()
            config.macro_hotkeys = {
                i: hotkey.text()
                for i, hotkey in enumerate(self.macro_hotkeys)
                if hotkey.text()
            }
            config.record_hotkey = self.record_hotkey.text()
            config.play_hotkey = self.play_hotkey.text()
            
            # Advanced
            config.debug_level = DebugLevel[self.debug_level_combo.currentText()]
            config.performance_mode = self.performance_mode_check.isChecked()
            
            # Save changes
            self.config_manager.save_config()
            self.settings_changed.emit()
            
            QMessageBox.information(
                self,
                "Settings",
                "Settings applied successfully."
            )
            
        except Exception as e:
            self.logger.error(f"Error applying settings: {e}")
            QMessageBox.critical(
                self,
                "Settings Error",
                f"Failed to apply settings: {e}"
            )

    def _browse_macro_dir(self):
        """Browse for macro directory."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Macro Directory",
                str(self.config_manager.config.macro_directory)
            )
            if directory:
                self.macro_dir_edit.setText(directory)
            
        except Exception as e:
            self.logger.error(f"Error browsing directory: {e}")

    def _check_updates(self):
        """Check for updates."""
        try:
            self.check_now_button.setEnabled(False)
            update_manager.check_for_updates(force=True)
            self.check_now_button.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Error checking updates: {e}")
            self.check_now_button.setEnabled(True)

    def _install_driver(self):
        """Install Interception driver."""
        try:
            reply = QMessageBox.question(
                self,
                "Install Driver",
                "This will install the Interception driver for stealth mode.\n"
                "Administrator rights are required.\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.driver_progress.show()
                self.install_driver_button.setEnabled(False)
                
                def progress_callback(value):
                    self.driver_progress.setValue(value)
                    if value >= 100:
                        self.driver_progress.hide()
                        self.install_driver_button.setEnabled(True)
                        QMessageBox.information(
                            self,
                            "Driver Installation",
                            "Driver installed successfully."
                        )
                
                update_manager.install_interception(progress_callback)
            
        except Exception as e:
            self.logger.error(f"Error installing driver: {e}")
            self.driver_progress.hide()
            self.install_driver_button.setEnabled(True)
            QMessageBox.critical(
                self,
                "Installation Error",
                f"Failed to install driver: {e}"
            )

    def _open_logs(self):
        """Open log directory."""
        try:
            path = self.debug.log_dir
            if path.exists():
                os.startfile(str(path))
            else:
                QMessageBox.warning(
                    self,
                    "Logs",
                    "Log directory does not exist."
                )
            
        except Exception as e:
            self.logger.error(f"Error opening logs: {e}")

    def _reset_settings(self):
        """Reset all settings to defaults."""
        try:
            reply = QMessageBox.question(
                self,
                "Reset Settings",
                "This will reset all settings to their default values.\n"
                "Are you sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.config_manager.reset_config()
                self._load_settings()
                self.settings_changed.emit()
                
                QMessageBox.information(
                    self,
                    "Reset Settings",
                    "Settings have been reset to defaults."
                )
            
        except Exception as e:
            self.logger.error(f"Error resetting settings: {e}")
            QMessageBox.critical(
                self,
                "Reset Error",
                f"Failed to reset settings: {e}"
            )

    def accept(self):
        """Handle dialog acceptance."""
        self._apply_settings()
        super().accept()
