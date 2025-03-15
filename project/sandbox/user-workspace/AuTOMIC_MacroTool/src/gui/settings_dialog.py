"""
Settings dialog for application configuration.
Copyright (c) 2025 AtomicArk
"""

import logging
from typing import Dict, Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QPushButton, QFileDialog, QGroupBox, QFormLayout,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence

from ..core.config_manager import config_manager
from ..utils.debug_helper import get_debug_helper, DebugLevel
from .styles import style_manager, Theme

class HotkeyEdit(QLineEdit):
    """Custom line edit for hotkey capture."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self._recording = False
        self._key_sequence = QKeySequence()
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if self._recording:
            # Convert to key sequence
            self._key_sequence = QKeySequence(event.key() | int(event.modifiers()))
            self.setText(self._key_sequence.toString())
            self._recording = False
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._recording = True
            self.setText("Press key combination...")
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def get_hotkey(self) -> str:
        """Get current hotkey."""
        return self._key_sequence.toString()
    
    def set_hotkey(self, hotkey: str):
        """Set hotkey."""
        self._key_sequence = QKeySequence(hotkey)
        self.setText(self._key_sequence.toString())

class SettingsDialog(QDialog):
    """Application settings dialog."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('SettingsDialog')
        self.debug = get_debug_helper()
        
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Initialize UI
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)
        
        # Tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Language group
        language_group = QGroupBox("Language")
        language_layout = QFormLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItems(['System', 'English', 'Polish', 'German',
                                    'French', 'Italian', 'Spanish'])
        language_layout.addRow("Interface Language:", self.language_combo)
        language_group.setLayout(language_layout)
        general_layout.addWidget(language_group)
        
        # Theme group
        theme_group = QGroupBox("Appearance")
        theme_layout = QFormLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([t.value for t in Theme])
        theme_layout.addRow("Theme:", self.theme_combo)
        self.ui_scale_spin = QDoubleSpinBox()
        self.ui_scale_spin.setRange(0.5, 2.0)
        self.ui_scale_spin.setSingleStep(0.1)
        theme_layout.addRow("UI Scale:", self.ui_scale_spin)
        theme_group.setLayout(theme_layout)
        general_layout.addWidget(theme_group)
        
        # Startup group
        startup_group = QGroupBox("Startup")
        startup_layout = QVBoxLayout()
        self.autostart_check = QCheckBox("Start with Windows")
        self.minimize_check = QCheckBox("Start minimized to tray")
        self.updates_check = QCheckBox("Check for updates")
        startup_layout.addWidget(self.autostart_check)
        startup_layout.addWidget(self.minimize_check)
        startup_layout.addWidget(self.updates_check)
        startup_group.setLayout(startup_layout)
        general_layout.addWidget(startup_group)
        
        tabs.addTab(general_tab, "General")
        
        # Recording tab
        recording_tab = QWidget()
        recording_layout = QVBoxLayout(recording_tab)
        
        # Input group
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout()
        self.mouse_check = QCheckBox("Record mouse")
        self.keyboard_check = QCheckBox("Record keyboard")
        self.delays_check = QCheckBox("Record delays")
        input_layout.addWidget(self.mouse_check)
        input_layout.addWidget(self.keyboard_check)
        input_layout.addWidget(self.delays_check)
        input_group.setLayout(input_layout)
        recording_layout.addWidget(input_group)
        
        # Mode group
        mode_group = QGroupBox("Recording Mode")
        mode_layout = QVBoxLayout()
        self.window_mode_check = QCheckBox("Window mode")
        self.directx_mode_check = QCheckBox("DirectX mode")
        mode_layout.addWidget(self.window_mode_check)
        mode_layout.addWidget(self.directx_mode_check)
        mode_group.setLayout(mode_layout)
        recording_layout.addWidget(mode_group)
        
        tabs.addTab(recording_tab, "Recording")
        
        # Playback tab
        playback_tab = QWidget()
        playback_layout = QVBoxLayout(playback_tab)
        
        # Playback group
        playback_group = QGroupBox("Playback")
        playback_form = QFormLayout()
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(['Once', 'Loop', 'Count'])
        playback_form.addRow("Repeat Mode:", self.repeat_combo)
        self.repeat_spin = QSpinBox()
        self.repeat_spin.setRange(1, 9999)
        playback_form.addRow("Repeat Count:", self.repeat_spin)
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 10.0)
        self.speed_spin.setSingleStep(0.1)
        playback_form.addRow("Speed:", self.speed_spin)
        playback_group.setLayout(playback_form)
        playback_layout.addWidget(playback_group)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        self.randomize_check = QCheckBox("Randomize delays")
        self.stop_input_check = QCheckBox("Stop on input")
        self.restore_mouse_check = QCheckBox("Restore mouse position")
        self.stealth_check = QCheckBox("Stealth mode")
        options_layout.addWidget(self.randomize_check)
        options_layout.addWidget(self.stop_input_check)
        options_layout.addWidget(self.restore_mouse_check)
        options_layout.addWidget(self.stealth_check)
        options_group.setLayout(options_layout)
        playback_layout.addWidget(options_group)
        
        tabs.addTab(playback_tab, "Playback")
        
        # Hotkeys tab
        hotkeys_tab = QWidget()
        hotkeys_layout = QFormLayout(hotkeys_tab)
        
        self.hotkey_edits = {}
        for action in ['record_start', 'record_stop', 'play_start', 'play_stop',
                      'play_pause', 'script_execute', 'script_stop', 'panic_button',
                      'show_hide']:
            edit = HotkeyEdit()
            self.hotkey_edits[action] = edit
            hotkeys_layout.addRow(action.replace('_', ' ').title() + ":", edit)
        
        tabs.addTab(hotkeys_tab, "Hotkeys")
        
        # Advanced tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # Debug group
        debug_group = QGroupBox("Debug")
        debug_layout = QFormLayout()
        self.debug_combo = QComboBox()
        self.debug_combo.addItems(['None', 'Basic', 'Detailed', 'Verbose'])
        debug_layout.addRow("Debug Level:", self.debug_combo)
        debug_group.setLayout(debug_layout)
        advanced_layout.addWidget(debug_group)
        
        # Performance group
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout()
        self.performance_check = QCheckBox("Performance mode")
        perf_layout.addWidget(self.performance_check)
        perf_group.setLayout(perf_layout)
        advanced_layout.addWidget(perf_group)
        
        # Directories group
        dir_group = QGroupBox("Directories")
        dir_layout = QFormLayout()
        
        self.macro_dir_edit = QLineEdit()
        macro_dir_btn = QPushButton("Browse...")
        macro_dir_layout = QHBoxLayout()
        macro_dir_layout.addWidget(self.macro_dir_edit)
        macro_dir_layout.addWidget(macro_dir_btn)
        dir_layout.addRow("Macro Directory:", macro_dir_layout)
        
        self.backup_dir_edit = QLineEdit()
        backup_dir_btn = QPushButton("Browse...")
        backup_dir_layout = QHBoxLayout()
        backup_dir_layout.addWidget(self.backup_dir_edit)
        backup_dir_layout.addWidget(backup_dir_btn)
        dir_layout.addRow("Backup Directory:", backup_dir_layout)
        
        dir_group.setLayout(dir_layout)
        advanced_layout.addWidget(dir_group)
        
        tabs.addTab(advanced_tab, "Advanced")
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_settings)
        button_layout.addWidget(reset_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)

    def _load_settings(self):
        """Load current settings."""
        try:
            # General
            self.language_combo.setCurrentText(
                config_manager.config.language or 'System'
            )
            self.theme_combo.setCurrentText(
                config_manager.config.theme or 'System'
            )
            self.ui_scale_spin.setValue(config_manager.config.ui_scale)
            self.autostart_check.setChecked(config_manager.config.autostart)
            self.minimize_check.setChecked(config_manager.config.minimize_to_tray)
            self.updates_check.setChecked(config_manager.config.check_updates)
            
            # Recording
            self.mouse_check.setChecked(config_manager.config.recording.record_mouse)
            self.keyboard_check.setChecked(config_manager.config.recording.record_keyboard)
            self.delays_check.setChecked(config_manager.config.recording.record_delays)
            self.window_mode_check.setChecked(config_manager.config.recording.window_mode)
            self.directx_mode_check.setChecked(config_manager.config.recording.directx_mode)
            
            # Playback
            self.repeat_combo.setCurrentText(
                config_manager.config.playback.repeat_mode.title()
            )
            self.repeat_spin.setValue(config_manager.config.playback.repeat_count)
            self.speed_spin.setValue(config_manager.config.playback.speed)
            self.randomize_check.setChecked(config_manager.config.playback.randomize_delays)
            self.stop_input_check.setChecked(config_manager.config.playback.stop_on_input)
            self.restore_mouse_check.setChecked(config_manager.config.playback.restore_mouse)
            self.stealth_check.setChecked(config_manager.config.playback.stealth_mode)
            
            # Hotkeys
            for action, edit in self.hotkey_edits.items():
                edit.set_hotkey(getattr(config_manager.config.hotkeys, action))
            
            # Advanced
            self.debug_combo.setCurrentText(
                config_manager.config.debug_level.title()
            )
            self.performance_check.setChecked(config_manager.config.performance_mode)
            self.macro_dir_edit.setText(config_manager.config.macro_directory)
            self.backup_dir_edit.setText(config_manager.config.backup_directory)
            
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")

    def _save_settings(self):
        """Save current settings."""
        try:
            # General
            config_manager.config.language = self.language_combo.currentText()
            if config_manager.config.language == 'System':
                config_manager.config.language = ''
            
            config_manager.config.theme = self.theme_combo.currentText()
            if config_manager.config.theme == 'System':
                config_manager.config.theme = ''
            
            config_manager.config.ui_scale = self.ui_scale_spin.value()
            config_manager.config.autostart = self.autostart_check.isChecked()
            config_manager.config.minimize_to_tray = self.minimize_check.isChecked()
            config_manager.config.check_updates = self.updates_check.isChecked()
            
            # Recording
            config_manager.config.recording.record_mouse = self.mouse_check.isChecked()
            config_manager.config.recording.record_keyboard = self.keyboard_check.isChecked()
            config_manager.config.recording.record_delays = self.delays_check.isChecked()
            config_manager.config.recording.window_mode = self.window_mode_check.isChecked()
            config_manager.config.recording.directx_mode = self.directx_mode_check.isChecked()
            
            # Playback
            config_manager.config.playback.repeat_mode = self.repeat_combo.currentText().lower()
            config_manager.config.playback.repeat_count = self.repeat_spin.value()
            config_manager.config.playback.speed = self.speed_spin.value()
            config_manager.config.playback.randomize_delays = self.randomize_check.isChecked()
            config_manager.config.playback.stop_on_input = self.stop_input_check.isChecked()
            config_manager.config.playback.restore_mouse = self.restore_mouse_check.isChecked()
            config_manager.config.playback.stealth_mode = self.stealth_check.isChecked()
            
            # Hotkeys
            for action, edit in self.hotkey_edits.items():
                setattr(config_manager.config.hotkeys, action, edit.get_hotkey())
            
            # Advanced
            config_manager.config.debug_level = self.debug_combo.currentText().lower()
            config_manager.config.performance_mode = self.performance_check.isChecked()
            config_manager.config.macro_directory = self.macro_dir_edit.text()
            config_manager.config.backup_directory = self.backup_dir_edit.text()
            
            # Save config
            if config_manager.save_config():
                self.settings_changed.emit()
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False

    def _reset_settings(self):
        """Reset settings to defaults."""
        try:
            reply = QMessageBox.question(
                self,
                "Reset Settings",
                "Are you sure you want to reset all settings to defaults?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if config_manager.reset_config():
                    self._load_settings()
                    self.settings_changed.emit()
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to reset settings"
                    )
            
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")

    def accept(self):
        """Handle dialog acceptance."""
        if self._save_settings():
            super().accept()
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to save settings"
            )
