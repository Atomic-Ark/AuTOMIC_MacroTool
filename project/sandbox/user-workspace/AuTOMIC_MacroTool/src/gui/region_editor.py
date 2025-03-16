"""
Screen region editor module.
Copyright (c) 2025 AtomicArk
"""

import logging
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
import uuid

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QDialog, QMessageBox, QMenu, QSpinBox, QFrame,
    QApplication, QMainWindow, QToolBar, QStatusBar
)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QMouseEvent,
    QKeyEvent, QScreen, QPixmap, QIcon
)

from ..utils.debug_helper import get_debug_helper
from ..core.image_recognition import Region

class SelectionFrame(QFrame):
    """Frame for region selection."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setLineWidth(2)
        
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(255, 0, 0, 50))
        palette.setColor(self.foregroundRole(), QColor(255, 0, 0))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

class RegionSelector(QMainWindow):
    """Window for selecting screen regions."""
    
    region_selected = pyqtSignal(QRect)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('RegionSelector')
        
        # Setup window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # State
        self._start_pos = None
        self._selection_frame = None
        
        # Setup UI
        self._setup_ui()
        
        # Take screenshot
        self._take_screenshot()

    def _setup_ui(self):
        """Setup user interface."""
        # Status bar with instructions
        status = QStatusBar()
        status.showMessage("Click and drag to select region. Press Esc to cancel.")
        self.setStatusBar(status)
        
        # Central widget for screenshot
        self._screenshot_label = QLabel()
        self.setCentralWidget(self._screenshot_label)

    def _take_screenshot(self):
        """Take screenshot of primary screen."""
        try:
            screen = QApplication.primaryScreen()
            if screen:
                self._screenshot = screen.grabWindow(0)
                self._screenshot_label.setPixmap(self._screenshot)
                self.setGeometry(screen.geometry())
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.pos()
            
            if self._selection_frame:
                self._selection_frame.deleteLater()
            
            self._selection_frame = SelectionFrame(self)
            self._selection_frame.setGeometry(QRect(self._start_pos, QSize()))
            self._selection_frame.show()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move."""
        if self._selection_frame and self._start_pos:
            rect = QRect(self._start_pos, event.pos()).normalized()
            self._selection_frame.setGeometry(rect)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton and self._selection_frame:
            rect = self._selection_frame.geometry()
            if rect.width() > 0 and rect.height() > 0:
                self.region_selected.emit(rect)
            self.close()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()

class RegionEditor(QWidget):
    """Region editor widget."""
    
    region_changed = pyqtSignal(str, Region)  # name, region
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('RegionEditor')
        self.debug = get_debug_helper()
        
        # Data
        self._regions: Dict[str, Region] = {}
        
        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        layout.addLayout(toolbar)
        
        # Add button
        add_btn = QPushButton("Add Region")
        add_btn.clicked.connect(self._add_region)
        toolbar.addWidget(add_btn)
        
        # Region list
        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_context_menu)
        self._list.itemDoubleClicked.connect(self._edit_region)
        layout.addWidget(self._list)

    def _add_region(self):
        """Add new region."""
        try:
            # Create selector
            selector = RegionSelector()
            selector.region_selected.connect(self._handle_selection)
            selector.show()
            
        except Exception as e:
            self.logger.error(f"Failed to add region: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _handle_selection(self, rect: QRect):
        """Handle region selection."""
        try:
            # Show properties dialog
            name, ok = self._show_properties_dialog()
            if ok and name:
                # Create region
                region = Region(
                    x=rect.x(),
                    y=rect.y(),
                    width=rect.width(),
                    height=rect.height(),
                    name=name
                )
                
                # Add to list
                self._add_region_item(name, region)
                
                # Notify change
                self.region_changed.emit(name, region)
            
        except Exception as e:
            self.logger.error(f"Failed to handle selection: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _show_properties_dialog(self) -> Tuple[str, bool]:
        """Show region properties dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Region Properties")
        
        # Layout
        layout = QVBoxLayout(dialog)
        
        # Name input
        name_layout = QHBoxLayout()
        layout.addLayout(name_layout)
        
        name_label = QLabel("Name:")
        name_layout.addWidget(name_label)
        
        name_input = QLineEdit()
        name_layout.addWidget(name_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return name_input.text().strip(), True
        return "", False

    def _add_region_item(self, name: str, region: Region):
        """Add region to list."""
        try:
            # Create item
            item = QListWidgetItem(
                f"{name} ({region.x}, {region.y}, {region.width}, {region.height})"
            )
            item.setData(Qt.ItemDataRole.UserRole, name)
            
            # Add to list
            self._list.addItem(item)
            
            # Store region
            self._regions[name] = region
            
        except Exception as e:
            self.logger.error(f"Failed to add region item: {e}")
            raise

    def _show_context_menu(self, pos: QPoint):
        """Show context menu for region item."""
        try:
            item = self._list.itemAt(pos)
            if item:
                menu = QMenu(self)
                
                # Edit action
                edit_action = menu.addAction("Edit")
                edit_action.triggered.connect(
                    lambda: self._edit_region(item)
                )
                
                # Delete action
                delete_action = menu.addAction("Delete")
                delete_action.triggered.connect(
                    lambda: self._delete_region(item)
                )
                
                menu.exec(self._list.mapToGlobal(pos))
            
        except Exception as e:
            self.logger.error(f"Failed to show context menu: {e}")

    def _edit_region(self, item: QListWidgetItem):
        """Edit region."""
        try:
            name = item.data(Qt.ItemDataRole.UserRole)
            region = self._regions.get(name)
            if region:
                # Create selector
                selector = RegionSelector()
                selector.region_selected.connect(
                    lambda rect: self._update_region(name, rect)
                )
                selector.show()
            
        except Exception as e:
            self.logger.error(f"Failed to edit region: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _update_region(self, name: str, rect: QRect):
        """Update existing region."""
        try:
            # Update region
            region = Region(
                x=rect.x(),
                y=rect.y(),
                width=rect.width(),
                height=rect.height(),
                name=name
            )
            
            self._regions[name] = region
            
            # Update list item
            for i in range(self._list.count()):
                item = self._list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == name:
                    item.setText(
                        f"{name} ({region.x}, {region.y}, "
                        f"{region.width}, {region.height})"
                    )
                    break
            
            # Notify change
            self.region_changed.emit(name, region)
            
        except Exception as e:
            self.logger.error(f"Failed to update region: {e}")
            raise

    def _delete_region(self, item: QListWidgetItem):
        """Delete region."""
        try:
            name = item.data(Qt.ItemDataRole.UserRole)
            
            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Delete region '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Remove from list
                self._list.takeItem(self._list.row(item))
                
                # Remove from storage
                if name in self._regions:
                    del self._regions[name]
                
                # Notify change
                self.region_changed.emit(name, None)
            
        except Exception as e:
            self.logger.error(f"Failed to delete region: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def get_region(self, name: str) -> Optional[Region]:
        """Get region by name."""
        return self._regions.get(name)

    def get_regions(self) -> Dict[str, Region]:
        """Get all regions."""
        return self._regions.copy()

    def clear(self):
        """Clear all regions."""
        self._list.clear()
        self._regions.clear()
