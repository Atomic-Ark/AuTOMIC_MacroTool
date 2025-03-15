from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox,
    QTabWidget, QWidget, QSplitter, QTreeWidget, QTreeWidgetItem,
    QMenu, QMessageBox, QToolBar, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import (
    QTextCharFormat, QSyntaxHighlighter, QColor,
    QTextCursor, QKeySequence, QIcon
)

import re
import logging
from typing import Dict, List, Optional
from pathlib import Path

from ..core.macro_script import MacroScript
from ..core.macro_manager import Macro, MacroType
from ..utils.debug_helper import get_debug_helper

class ScriptHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for macro scripts."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_formats()

    def _init_formats(self):
        """Initialize text formats."""
        self.formats = {
            'keyword': self._create_format('#569CD6'),
            'function': self._create_format('#DCDCAA'),
            'string': self._create_format('#CE9178'),
            'number': self._create_format('#B5CEA8'),
            'comment': self._create_format('#6A9955', italic=True),
            'operator': self._create_format('#D4D4D4'),
            'variable': self._create_format('#9CDCFE'),
            'constant': self._create_format('#4FC1FF'),
        }
        
        # Define patterns
        self.patterns = {
            'keyword': r'\b(if|else|while|for|break|continue|return|and|or|not)\b',
            'function': r'\b\w+(?=\()',
            'string': r'\".*?\"|\'.*?\'',
            'number': r'\b\d+\b',
            'comment': r'#[^\n]*',
            'operator': r'[\+\-\*/=<>!&\|]+',
            'variable': r'\$\w+',
            'constant': r'\b[A-Z_]+\b',
        }

    def _create_format(self, color: str, bold: bool = False,
                      italic: bool = False) -> QTextCharFormat:
        """Create text format."""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontWeight(700 if bold else 400)
        fmt.setFontItalic(italic)
        return fmt

    def highlightBlock(self, text: str):
        """Highlight text block."""
        for pattern_type, pattern in self.patterns.items():
            for match in re.finditer(pattern, text):
                self.setFormat(
                    match.start(),
                    match.end() - match.start(),
                    self.formats[pattern_type]
                )

class CommandTreeWidget(QTreeWidget):
    """Tree widget for command suggestions."""
    
    command_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_commands()

    def _init_ui(self):
        """Initialize user interface."""
        self.setHeaderLabels(['Command', 'Description'])
        self.setColumnWidth(0, 150)
        self.setAlternatingRowColors(True)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _load_commands(self):
        """Load available commands."""
        commands = {
            'Input': {
                'click(x, y)': 'Click at coordinates',
                'right_click(x, y)': 'Right click at coordinates',
                'double_click(x, y)': 'Double click at coordinates',
                'move(x, y)': 'Move mouse to coordinates',
                'press_key(key)': 'Press keyboard key',
                'release_key(key)': 'Release keyboard key',
                'type_text(text)': 'Type text string',
                'scroll(amount)': 'Scroll mouse wheel',
            },
            'Window': {
                'focus_window(title)': 'Focus window by title',
                'get_window_pos()': 'Get window position',
                'set_window_pos(x, y)': 'Set window position',
                'get_window_size()': 'Get window size',
                'set_window_size(w, h)': 'Set window size',
            },
            'Flow Control': {
                'wait(seconds)': 'Wait for duration',
                'repeat(count)': 'Repeat following commands',
                'if condition:': 'Conditional execution',
                'while condition:': 'Loop while condition is true',
                'break': 'Exit current loop',
                'continue': 'Skip to next iteration',
            },
            'Image': {
                'find_image(path)': 'Find image on screen',
                'wait_for_image(path)': 'Wait for image to appear',
                'click_image(path)': 'Click on found image',
                'image_exists(path)': 'Check if image exists',
            },
            'Variables': {
                '$variable = value': 'Assign value to variable',
                '$mouse_x, $mouse_y': 'Current mouse position',
                '$window_x, $window_y': 'Current window position',
                '$screen_width': 'Screen width',
                '$screen_height': 'Screen height',
            },
        }
        
        for category, items in commands.items():
            category_item = QTreeWidgetItem([category])
            self.addTopLevelItem(category_item)
            
            for command, description in items.items():
                item = QTreeWidgetItem([command, description])
                category_item.addChild(item)
            
        self.expandAll()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double click."""
        if item.parent():  # Only emit for child items
            self.command_selected.emit(item.text(0))

class ScriptEditor(QDialog):
    """Macro script editor dialog."""
    
    def __init__(self, macro: Macro, parent=None):
        super().__init__(parent)
        self.macro = macro
        self.logger = logging.getLogger('ScriptEditor')
        self.debug = get_debug_helper()
        self._init_ui()
        self._load_script()

    def _init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("Script Editor")
        self.setMinimumSize(1000, 600)
        
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # Actions
        save_action = toolbar.addAction(
            QIcon("src/resources/icons/save.png"),
            "Save"
        )
        save_action.triggered.connect(self._save_script)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        
        toolbar.addSeparator()
        
        check_action = toolbar.addAction(
            QIcon("src/resources/icons/check.png"),
            "Check Syntax"
        )
        check_action.triggered.connect(self._check_syntax)
        
        run_action = toolbar.addAction(
            QIcon("src/resources/icons/run.png"),
            "Test Run"
        )
        run_action.triggered.connect(self._test_run)
        
        layout.addWidget(toolbar)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Command tree
        self.command_tree = CommandTreeWidget()
        self.command_tree.command_selected.connect(self._insert_command)
        splitter.addWidget(self.command_tree)
        
        # Editor area
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        # Editor tabs
        self.tab_widget = QTabWidget()
        
        # Script tab
        self.script_editor = QPlainTextEdit()
        self.script_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.script_editor.setTabStopDistance(40)
        self.highlighter = ScriptHighlighter(self.script_editor.document())
        self.tab_widget.addTab(self.script_editor, "Script")
        
        # Events tab
        self.events_editor = QPlainTextEdit()
        self.events_editor.setReadOnly(True)
        self.tab_widget.addTab(self.events_editor, "Recorded Events")
        
        editor_layout.addWidget(self.tab_widget)
        
        splitter.addWidget(editor_widget)
        splitter.setSizes([200, 800])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)

    def _load_script(self):
        """Load macro script and events."""
        try:
            # Load script if exists
            if self.macro.script:
                self.script_editor.setPlainText(self.macro.script)
            
            # Load events
            events_text = ""
            for event in self.macro.events:
                events_text += f"{event.type.value}: {event.data}\n"
            self.events_editor.setPlainText(events_text)
            
        except Exception as e:
            self.logger.error(f"Error loading script: {e}")
            self.status_bar.showMessage("Error loading script", 5000)

    def _save_script(self):
        """Save script changes."""
        try:
            script = self.script_editor.toPlainText()
            
            # Check syntax before saving
            if not self._check_syntax(show_success=False):
                return
            
            # Update macro
            self.macro.script = script
            if self.macro.metadata.type == MacroType.RECORDED:
                self.macro.metadata.type = MacroType.HYBRID
            
            self.status_bar.showMessage("Script saved", 3000)
            
        except Exception as e:
            self.logger.error(f"Error saving script: {e}")
            self.status_bar.showMessage("Error saving script", 5000)

    def _check_syntax(self, show_success: bool = True) -> bool:
        """Check script syntax."""
        try:
            script = self.script_editor.toPlainText()
            
            # Create temporary script object
            temp_script = MacroScript(script)
            
            # Try to compile
            if temp_script.compile():
                if show_success:
                    self.status_bar.showMessage("Syntax check passed", 3000)
                return True
            else:
                self.status_bar.showMessage(
                    f"Syntax error: {temp_script.last_error}",
                    5000
                )
                return False
            
        except Exception as e:
            self.logger.error(f"Error checking syntax: {e}")
            self.status_bar.showMessage(f"Error checking syntax: {e}", 5000)
            return False

    def _test_run(self):
        """Test run the script."""
        try:
            script = self.script_editor.toPlainText()
            
            # Check syntax first
            if not self._check_syntax(show_success=False):
                return
            
            # Create temporary script
            temp_script = MacroScript(script)
            
            # Run in test mode
            if temp_script.run(test_mode=True):
                self.status_bar.showMessage("Test run successful", 3000)
            else:
                self.status_bar.showMessage(
                    f"Test run failed: {temp_script.last_error}",
                    5000
                )
            
        except Exception as e:
            self.logger.error(f"Error during test run: {e}")
            self.status_bar.showMessage(f"Error during test run: {e}", 5000)

    def _insert_command(self, command: str):
        """Insert command at cursor position."""
        try:
            cursor = self.script_editor.textCursor()
            cursor.insertText(command)
            self.script_editor.setFocus()
            
        except Exception as e:
            self.logger.error(f"Error inserting command: {e}")

    def accept(self):
        """Handle dialog acceptance."""
        try:
            # Save changes before accepting
            self._save_script()
            
            if self.macro.script:
                super().accept()
            
        except Exception as e:
            self.logger.error(f"Error accepting dialog: {e}")
            self.status_bar.showMessage("Error saving changes", 5000)

    def closeEvent(self, event):
        """Handle window close event."""
        try:
            if self.script_editor.document().isModified():
                reply = QMessageBox.question(
                    self,
                    "Save Changes",
                    "Do you want to save your changes?",
                    QMessageBox.StandardButton.Yes |
                    QMessageBox.StandardButton.No |
                    QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self._save_script()
                    event.accept()
                elif reply == QMessageBox.StandardButton.No:
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()
            
        except Exception as e:
            self.logger.error(f"Error handling close event: {e}")
            event.accept()
