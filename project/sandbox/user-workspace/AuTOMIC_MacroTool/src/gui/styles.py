"""
Application styling and theme management.
Copyright (c) 2025 AtomicArk
"""

import logging
from enum import Enum
from typing import Dict, Optional
from pathlib import Path
import darkdetect

from ..utils.debug_helper import get_debug_helper

class Theme(Enum):
    """Application themes."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"
    CUSTOM = "custom"

class StyleManager:
    """Manages application styling and themes."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('StyleManager')
            self.debug = get_debug_helper()
            
            # State
            self._current_theme = Theme.SYSTEM
            self._custom_stylesheet = ""
            
            # Initialize
            self._init_styles()
            self._initialized = True

    def _init_styles(self):
        """Initialize style definitions."""
        # Color schemes
        self._colors = {
            Theme.LIGHT: {
                'background': '#f0f0f0',
                'foreground': '#202020',
                'primary': '#007bff',
                'secondary': '#6c757d',
                'success': '#28a745',
                'warning': '#ffc107',
                'error': '#dc3545',
                'border': '#d0d0d0',
                'hover': '#e8e8e8',
                'selected': '#cce5ff',
                'disabled': '#a0a0a0',
                'input_bg': '#ffffff',
                'input_border': '#ced4da',
                'button_bg': '#f8f9fa',
                'button_hover': '#e2e6ea',
                'button_pressed': '#dae0e5',
                'scrollbar': '#c1c1c1',
                'scrollbar_hover': '#a8a8a8',
                'tooltip_bg': '#ffffff',
                'tooltip_text': '#202020',
            },
            Theme.DARK: {
                'background': '#202020',
                'foreground': '#f0f0f0',
                'primary': '#0d6efd',
                'secondary': '#6c757d',
                'success': '#198754',
                'warning': '#ffc107',
                'error': '#dc3545',
                'border': '#404040',
                'hover': '#303030',
                'selected': '#0d47a1',
                'disabled': '#606060',
                'input_bg': '#303030',
                'input_border': '#404040',
                'button_bg': '#404040',
                'button_hover': '#505050',
                'button_pressed': '#606060',
                'scrollbar': '#505050',
                'scrollbar_hover': '#606060',
                'tooltip_bg': '#303030',
                'tooltip_text': '#f0f0f0',
            }
        }
        
        # Base styles
        self._base_style = """
            /* Global styles */
            QWidget {
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 10pt;
            }
            
            /* Main window */
            QMainWindow {
                background-color: %(background)s;
                color: %(foreground)s;
            }
            
            /* Menu bar */
            QMenuBar {
                background-color: %(background)s;
                color: %(foreground)s;
                border-bottom: 1px solid %(border)s;
            }
            
            QMenuBar::item {
                padding: 4px 8px;
                background-color: transparent;
            }
            
            QMenuBar::item:selected {
                background-color: %(hover)s;
            }
            
            /* Menu */
            QMenu {
                background-color: %(background)s;
                color: %(foreground)s;
                border: 1px solid %(border)s;
            }
            
            QMenu::item {
                padding: 4px 20px;
            }
            
            QMenu::item:selected {
                background-color: %(hover)s;
            }
            
            /* Tool bar */
            QToolBar {
                background-color: %(background)s;
                border: none;
                spacing: 4px;
                padding: 2px;
            }
            
            QToolButton {
                background-color: %(button_bg)s;
                border: 1px solid %(border)s;
                border-radius: 4px;
                padding: 4px;
            }
            
            QToolButton:hover {
                background-color: %(button_hover)s;
            }
            
            QToolButton:pressed {
                background-color: %(button_pressed)s;
            }
            
            /* Status bar */
            QStatusBar {
                background-color: %(background)s;
                color: %(foreground)s;
                border-top: 1px solid %(border)s;
            }
            
            /* Buttons */
            QPushButton {
                background-color: %(button_bg)s;
                color: %(foreground)s;
                border: 1px solid %(border)s;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: %(button_hover)s;
            }
            
            QPushButton:pressed {
                background-color: %(button_pressed)s;
            }
            
            QPushButton:disabled {
                background-color: %(background)s;
                color: %(disabled)s;
                border-color: %(border)s;
            }
            
            /* Input fields */
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: %(input_bg)s;
                color: %(foreground)s;
                border: 1px solid %(input_border)s;
                border-radius: 4px;
                padding: 4px;
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: %(primary)s;
            }
            
            QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
                background-color: %(background)s;
                color: %(disabled)s;
                border-color: %(border)s;
            }
            
            /* Combo box */
            QComboBox {
                background-color: %(input_bg)s;
                color: %(foreground)s;
                border: 1px solid %(input_border)s;
                border-radius: 4px;
                padding: 4px;
                min-width: 100px;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: url(resources/icons/down_arrow.png);
            }
            
            /* Spin box */
            QSpinBox, QDoubleSpinBox {
                background-color: %(input_bg)s;
                color: %(foreground)s;
                border: 1px solid %(input_border)s;
                border-radius: 4px;
                padding: 4px;
            }
            
            /* Check box */
            QCheckBox {
                color: %(foreground)s;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            
            /* Radio button */
            QRadioButton {
                color: %(foreground)s;
                spacing: 8px;
            }
            
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            
            /* Group box */
            QGroupBox {
                background-color: %(background)s;
                color: %(foreground)s;
                border: 1px solid %(border)s;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
            }
            
            /* Tab widget */
            QTabWidget::pane {
                border: 1px solid %(border)s;
            }
            
            QTabBar::tab {
                background-color: %(button_bg)s;
                color: %(foreground)s;
                border: 1px solid %(border)s;
                padding: 6px 12px;
            }
            
            QTabBar::tab:selected {
                background-color: %(selected)s;
            }
            
            QTabBar::tab:hover {
                background-color: %(button_hover)s;
            }
            
            /* Scroll bar */
            QScrollBar:vertical {
                background-color: %(background)s;
                width: 12px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background-color: %(scrollbar)s;
                min-height: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: %(scrollbar_hover)s;
            }
            
            QScrollBar:horizontal {
                background-color: %(background)s;
                height: 12px;
                margin: 0;
            }
            
            QScrollBar::handle:horizontal {
                background-color: %(scrollbar)s;
                min-width: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: %(scrollbar_hover)s;
            }
            
            /* Progress bar */
            QProgressBar {
                background-color: %(input_bg)s;
                color: %(foreground)s;
                border: 1px solid %(border)s;
                border-radius: 4px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background-color: %(primary)s;
            }
            
            /* Tooltip */
            QToolTip {
                background-color: %(tooltip_bg)s;
                color: %(tooltip_text)s;
                border: 1px solid %(border)s;
                padding: 4px;
            }
            
            /* Custom widgets */
            MacroSlot {
                background-color: %(input_bg)s;
                color: %(foreground)s;
                border: 1px solid %(border)s;
                border-radius: 4px;
                padding: 8px;
            }
            
            MacroSlot:hover {
                background-color: %(hover)s;
            }
            
            MacroSlot[active="true"] {
                border-color: %(primary)s;
            }
            
            RecordButton {
                background-color: %(error)s;
                border-radius: 20px;
                min-width: 40px;
                min-height: 40px;
            }
            
            RecordButton:hover {
                background-color: %(error)s;
                opacity: 0.8;
            }
            
            RecordButton[recording="true"] {
                background-color: %(success)s;
            }
        """

    def set_theme(self, theme: Theme):
        """Set application theme."""
        try:
            if theme == Theme.SYSTEM:
                system_theme = darkdetect.theme()
                if system_theme:
                    theme = Theme.DARK if system_theme.lower() == 'dark' else Theme.LIGHT
                else:
                    theme = Theme.LIGHT
            
            self._current_theme = theme
            
        except Exception as e:
            self.logger.error(f"Failed to set theme: {e}")

    def get_stylesheet(self) -> str:
        """Get current stylesheet."""
        try:
            # Get color scheme
            if self._current_theme == Theme.CUSTOM and self._custom_stylesheet:
                return self._custom_stylesheet
            
            colors = self._colors[self._current_theme]
            
            # Apply colors to base style
            return self._base_style % colors
            
        except Exception as e:
            self.logger.error(f"Failed to get stylesheet: {e}")
            return ""

    def load_custom_theme(self, path: Path) -> bool:
        """Load custom theme from file."""
        try:
            if not path.exists():
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                self._custom_stylesheet = f.read()
            
            self._current_theme = Theme.CUSTOM
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load custom theme: {e}")
            return False

    def get_current_theme(self) -> Theme:
        """Get current theme."""
        return self._current_theme

    def get_color(self, name: str) -> str:
        """Get color from current theme."""
        try:
            colors = self._colors[self._current_theme]
            return colors.get(name, '')
        except Exception as e:
            self.logger.error(f"Failed to get color: {e}")
            return ''

# Global instance
style_manager = StyleManager()
