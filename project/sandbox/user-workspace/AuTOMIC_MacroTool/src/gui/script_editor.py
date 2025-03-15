"""
Script editor for macro scripting.
Copyright (c) 2025 AtomicArk
"""

import logging
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QSplitter, QTreeWidget,
    QTreeWidgetItem, QMessageBox, QMenu, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QTextCharFormat, QSyntaxHighlighter, QColor,
    QTextCursor, QFontMetrics, QFont
)

from ..core.macro_script import macro_script
from ..utils.debug_helper import get_debug_helper

class PythonHighlighter(QSyntaxHighlighter):
    """Python syntax highlighter."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Syntax styles
        self.styles = {
            'keyword': self._format('#0077CC', 'bold'),
            'string': self._format('#008000'),
            'comment': self._format('#999999', 'italic'),
            'numbers': self._format('#AA0000'),
            'function': self._format('#C65D09'),
            'api': self._format('#2B91AF', 'bold'),
        }
        
        # Python keywords
        self.keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue',
            'def', 'del', 'elif', 'else', 'except', 'False',
            'finally', 'for', 'from', 'global', 'if', 'import',
            'in', 'is', 'lambda', 'None', 'nonlocal', 'not',
            'or', 'pass', 'raise', 'return', 'True', 'try',
            'while', 'with', 'yield'
        ]
        
        # Python built-in functions
        self.functions = [
            'abs', 'all', 'any', 'bool', 'dict', 'float',
            'int', 'len', 'list', 'max', 'min', 'print',
            'range', 'round', 'set', 'str', 'sum', 'tuple'
        ]
        
        # API functions
        self.api_functions = [
            'key_press', 'mouse_move', 'mouse_click', 'mouse_scroll',
            'get_window', 'find_window', 'get_active_window',
            'bring_to_front', 'sleep', 'log', 'debug',
            'wait_for_window', 'repeat', 'wait_until'
        ]
        
        # Rules
        self.rules = []
        
        # Keywords
        self.rules += [(r'\b%s\b' % w, 0, self.styles['keyword'])
                      for w in self.keywords]
        
        # Functions
        self.rules += [(r'\b%s\b' % w, 0, self.styles['function'])
                      for w in self.functions]
        
        # API Functions
        self.rules += [(r'\b%s\b' % w, 0, self.styles['api'])
                      for w in self.api_functions]
        
        # String literals
        self.rules += [
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, self.styles['string']),
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, self.styles['string']),
        ]
        
        # Numbers
        self.rules += [
            (r'\b[0-9]+\b', 0, self.styles['numbers']),
            (r'\b0[xX][0-9A-Fa-f]+\b', 0, self.styles['numbers']),
            (r'\b[0-9]+\.[0-9]+\b', 0, self.styles['numbers']),
        ]
        
        # Comments
        self.rules += [
            (r'#[^\n]*', 0, self.styles['comment']),
        ]

    def _format(self, color: str, style: str = '') -> QTextCharFormat:
        """Create text format."""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        
        if 'bold' in style:
            fmt.setFontWeight(QFont.Weight.Bold)
        if 'italic' in style:
            fmt.setFontItalic(True)
        
        return fmt

    def highlightBlock(self, text: str):
        """Highlight text block."""
        for pattern, nth, format in self.rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)
        
        self.setCurrentBlockState(0)

class ScriptEditor(QWidget):
    """Macro script editor."""
    
    script_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('ScriptEditor')
        self.debug = get_debug_helper()
        
        # State
        self._current_script = ""
        self._modified = False
        
        # Initialize UI
        self._init_ui()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # API documentation
        api_widget = QWidget()
        api_layout = QVBoxLayout(api_widget)
        
        api_label = QLabel("API Reference")
        api_layout.addWidget(api_label)
        
        self.api_tree = QTreeWidget()
        self.api_tree.setHeaderLabels(["Function", "Description"])
        self.api_tree.setColumnWidth(0, 150)
        api_layout.addWidget(self.api_tree)
        
        splitter.addWidget(api_widget)
        
        # Editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        # Editor toolbar
        toolbar = QHBoxLayout()
        
        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self._run_script)
        toolbar.addWidget(run_btn)
        
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self._stop_script)
        toolbar.addWidget(stop_btn)
        
        check_btn = QPushButton("Check Syntax")
        check_btn.clicked.connect(self._check_syntax)
        toolbar.addWidget(check_btn)
        
        toolbar.addStretch()
        
        editor_layout.addLayout(toolbar)
        
        # Editor area
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 10))
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor.textChanged.connect(self._on_text_changed)
        
        # Syntax highlighter
        self.highlighter = PythonHighlighter(self.editor.document())
        
        editor_layout.addWidget(self.editor)
        
        splitter.addWidget(editor_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([200, 600])
        
        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
        # Context menu
        self.editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self._show_context_menu)
        
        # Load API documentation
        self._load_api_docs()

    def _load_api_docs(self):
        """Load API documentation."""
        try:
            docs = macro_script.get_api_docs()
            
            # Clear tree
            self.api_tree.clear()
            
            # Add functions
            for name, doc in docs.items():
                item = QTreeWidgetItem([name, ""])
                item.setToolTip(1, doc)
                self.api_tree.addTopLevelItem(item)
            
            # Sort items
            self.api_tree.sortItems(0, Qt.SortOrder.AscendingOrder)
            
        except Exception as e:
            self.logger.error(f"Failed to load API docs: {e}")

    def _show_context_menu(self, pos):
        """Show editor context menu."""
        try:
            menu = self.editor.createStandardContextMenu()
            
            # Add custom actions
            menu.addSeparator()
            
            check_action = menu.addAction("Check Syntax")
            check_action.triggered.connect(self._check_syntax)
            
            run_action = menu.addAction("Run")
            run_action.triggered.connect(self._run_script)
            
            menu.exec(self.editor.mapToGlobal(pos))
            
        except Exception as e:
            self.logger.error(f"Failed to show context menu: {e}")

    def _on_text_changed(self):
        """Handle text changes."""
        try:
            self._modified = True
            self.script_changed.emit()
            
        except Exception as e:
            self.logger.error(f"Failed to handle text change: {e}")

    def _check_syntax(self):
        """Check script syntax."""
        try:
            script = self.editor.toPlainText()
            error = macro_script.validate_script(script)
            
            if error:
                self.status_bar.showMessage(f"Syntax error: {error}", 5000)
                QMessageBox.warning(
                    self,
                    "Syntax Error",
                    str(error)
                )
            else:
                self.status_bar.showMessage("Syntax check passed", 5000)
            
        except Exception as e:
            self.logger.error(f"Failed to check syntax: {e}")

    def _run_script(self):
        """Run current script."""
        try:
            script = self.editor.toPlainText()
            
            # Check syntax first
            error = macro_script.validate_script(script)
            if error:
                QMessageBox.warning(
                    self,
                    "Syntax Error",
                    str(error)
                )
                return
            
            # Run script
            if macro_script.run_script(script):
                self.status_bar.showMessage("Script running...", 5000)
            else:
                self.status_bar.showMessage("Failed to run script", 5000)
            
        except Exception as e:
            self.logger.error(f"Failed to run script: {e}")

    def _stop_script(self):
        """Stop script execution."""
        try:
            if macro_script.stop_script():
                self.status_bar.showMessage("Script stopped", 5000)
            
        except Exception as e:
            self.logger.error(f"Failed to stop script: {e}")

    def get_script(self) -> str:
        """Get current script."""
        return self.editor.toPlainText()

    def set_script(self, script: str):
        """Set current script."""
        try:
            self.editor.setPlainText(script)
            self._modified = False
            
        except Exception as e:
            self.logger.error(f"Failed to set script: {e}")

    def is_modified(self) -> bool:
        """Check if script was modified."""
        return self._modified

    def clear(self):
        """Clear editor."""
        try:
            self.editor.clear()
            self._modified = False
            
        except Exception as e:
            self.logger.error(f"Failed to clear editor: {e}")
