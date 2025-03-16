"""
Visual macro editor module.
Copyright (c) 2025 AtomicArk
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum, auto
from dataclasses import dataclass, asdict
import json
import uuid

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QMenu, QLineEdit, QSpinBox,
    QComboBox, QCheckBox, QToolBar, QSizePolicy,
    QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QMimeData
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPalette, QIcon,
    QDrag, QMouseEvent, QPainterPath
)

from ..utils.debug_helper import get_debug_helper

class BlockType(Enum):
    """Block types."""
    START = auto()
    END = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    ACTION = auto()
    WAIT = auto()
    COMMENT = auto()

@dataclass
class BlockData:
    """Block data container."""
    id: str
    type: BlockType
    title: str
    description: str
    parameters: Dict[str, Any]
    position: QPointF
    size: QRectF

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'type': self.type.name,
            'title': self.title,
            'description': self.description,
            'parameters': self.parameters,
            'position': {'x': self.position.x(), 'y': self.position.y()},
            'size': {
                'x': self.size.x(),
                'y': self.size.y(),
                'width': self.size.width(),
                'height': self.size.height()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BlockData':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            type=BlockType[data['type']],
            title=data['title'],
            description=data['description'],
            parameters=data['parameters'],
            position=QPointF(data['position']['x'], data['position']['y']),
            size=QRectF(
                data['size']['x'],
                data['size']['y'],
                data['size']['width'],
                data['size']['height']
            )
        )

class BlockGraphicsItem(QGraphicsRectItem):
    """Visual block item."""
    
    def __init__(self, data: BlockData, parent: Optional[QGraphicsItem] = None):
        super().__init__(data.size, parent)
        
        self.data = data
        self.setPos(data.position)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Add title
        self.title = QGraphicsTextItem(self)
        self.title.setPlainText(data.title)
        self.title.setDefaultTextColor(Qt.GlobalColor.white)
        self.title.setPos(10, 5)
        
        # Style
        self._update_style()

    def _update_style(self):
        """Update block style."""
        # Color by type
        colors = {
            BlockType.START: QColor(100, 200, 100),    # Green
            BlockType.END: QColor(200, 100, 100),      # Red
            BlockType.IF: QColor(100, 100, 200),       # Blue
            BlockType.ELSE: QColor(150, 150, 200),     # Light blue
            BlockType.FOR: QColor(200, 100, 200),      # Purple
            BlockType.WHILE: QColor(200, 150, 200),    # Light purple
            BlockType.ACTION: QColor(200, 200, 100),   # Yellow
            BlockType.WAIT: QColor(150, 200, 200),     # Cyan
            BlockType.COMMENT: QColor(200, 200, 200)   # Gray
        }
        
        color = colors.get(self.data.type, QColor(200, 200, 200))
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.GlobalColor.black, 2))

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        """Custom paint."""
        # Draw background
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.rect(), 10, 10)
        
        # Draw connection points
        point_radius = 5
        painter.setBrush(Qt.GlobalColor.black)
        
        # Input point (top)
        painter.drawEllipse(
            QPointF(self.rect().center().x(), 0),
            point_radius, point_radius
        )
        
        # Output points (bottom)
        if self.data.type == BlockType.IF:
            # True branch (bottom-left)
            painter.drawEllipse(
                QPointF(self.rect().left() + 20,
                       self.rect().bottom()),
                point_radius, point_radius
            )
            # False branch (bottom-right)
            painter.drawEllipse(
                QPointF(self.rect().right() - 20,
                       self.rect().bottom()),
                point_radius, point_radius
            )
        else:
            # Single output (bottom-center)
            painter.drawEllipse(
                QPointF(self.rect().center().x(),
                       self.rect().bottom()),
                point_radius, point_radius
            )

class ConnectionGraphicsItem(QGraphicsLineItem):
    """Visual connection line."""
    
    def __init__(self, source: BlockGraphicsItem, target: BlockGraphicsItem,
                 branch: Optional[str] = None, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        
        self.source = source
        self.target = target
        self.branch = branch  # 'true' or 'false' for if-blocks
        
        self.setPen(QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.SolidLine))
        self.setZValue(-1)  # Draw below blocks
        
        self.update_position()

    def update_position(self):
        """Update line position."""
        source_pos = self.source.scenePos()
        target_pos = self.target.scenePos()
        
        # Source point
        if self.branch == 'true':
            start = source_pos + QPointF(20, self.source.rect().height())
        elif self.branch == 'false':
            start = source_pos + QPointF(self.source.rect().width() - 20,
                                       self.source.rect().height())
        else:
            start = source_pos + QPointF(self.source.rect().width() / 2,
                                       self.source.rect().height())
        
        # Target point
        end = target_pos + QPointF(self.target.rect().width() / 2, 0)
        
        # Draw line
        self.setLine(start.x(), start.y(), end.x(), end.y())

class VisualEditor(QWidget):
    """Visual macro editor widget."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.logger = logging.getLogger('VisualEditor')
        self.debug = get_debug_helper()
        
        # Data
        self.blocks: Dict[str, BlockGraphicsItem] = {}
        self.connections: List[ConnectionGraphicsItem] = []
        
        # UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QToolBar()
        layout.addWidget(toolbar)
        
        # Add block buttons
        for block_type in BlockType:
            button = QPushButton(block_type.name.title())
            button.clicked.connect(lambda checked, t=block_type:
                                 self._add_block(t))
            toolbar.addWidget(button)
        
        # Scene and view
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 2000, 2000)
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        layout.addWidget(self.view)

    def _add_block(self, block_type: BlockType):
        """Add new block."""
        try:
            # Create block data
            data = BlockData(
                id=str(uuid.uuid4()),
                type=block_type,
                title=block_type.name.title(),
                description="",
                parameters={},
                position=QPointF(100, 100),
                size=QRectF(0, 0, 150, 80)
            )
            
            # Create block item
            block = BlockGraphicsItem(data)
            self.scene.addItem(block)
            self.blocks[data.id] = block
            
        except Exception as e:
            self.logger.error(f"Failed to add block: {e}")

    def _connect_blocks(self, source: BlockGraphicsItem,
                       target: BlockGraphicsItem,
                       branch: Optional[str] = None):
        """Connect two blocks."""
        try:
            connection = ConnectionGraphicsItem(source, target, branch)
            self.scene.addItem(connection)
            self.connections.append(connection)
            
        except Exception as e:
            self.logger.error(f"Failed to connect blocks: {e}")

    def load_macro(self, data: Dict):
        """Load macro from data."""
        try:
            # Clear current
            self.scene.clear()
            self.blocks.clear()
            self.connections.clear()
            
            # Load blocks
            for block_data in data.get('blocks', []):
                block = BlockGraphicsItem(BlockData.from_dict(block_data))
                self.scene.addItem(block)
                self.blocks[block_data['id']] = block
            
            # Load connections
            for conn_data in data.get('connections', []):
                source = self.blocks.get(conn_data['source'])
                target = self.blocks.get(conn_data['target'])
                if source and target:
                    self._connect_blocks(source, target, conn_data.get('branch'))
            
        except Exception as e:
            self.logger.error(f"Failed to load macro: {e}")

    def save_macro(self) -> Dict:
        """Save macro to data."""
        try:
            return {
                'blocks': [block.data.to_dict() for block in self.blocks.values()],
                'connections': [{
                    'source': conn.source.data.id,
                    'target': conn.target.data.id,
                    'branch': conn.branch
                } for conn in self.connections]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save macro: {e}")
            return {}

    def generate_script(self) -> str:
        """Generate Python script from blocks."""
        try:
            script = []
            
            # Add imports
            script.append("from time import sleep")
            script.append("")
            
            # Process blocks
            processed = set()
            current = self._find_start_block()
            
            while current and current.data.id not in processed:
                script.extend(self._block_to_script(current))
                processed.add(current.data.id)
                current = self._find_next_block(current)
            
            return "\n".join(script)
            
        except Exception as e:
            self.logger.error(f"Failed to generate script: {e}")
            return ""

    def _block_to_script(self, block: BlockGraphicsItem) -> List[str]:
        """Convert block to script lines."""
        try:
            lines = []
            
            if block.data.type == BlockType.START:
                lines.append("# Start")
            
            elif block.data.type == BlockType.END:
                lines.append("# End")
            
            elif block.data.type == BlockType.IF:
                condition = block.data.parameters.get('condition', 'True')
                lines.append(f"if {condition}:")
                
                # Process true branch
                true_block = self._find_connected_block(block, 'true')
                if true_block:
                    lines.extend("    " + line
                               for line in self._block_to_script(true_block))
                
                # Process false branch
                false_block = self._find_connected_block(block, 'false')
                if false_block:
                    lines.append("else:")
                    lines.extend("    " + line
                               for line in self._block_to_script(false_block))
            
            elif block.data.type == BlockType.FOR:
                count = block.data.parameters.get('count', '1')
                lines.append(f"for _ in range({count}):")
                
                # Process loop body
                next_block = self._find_next_block(block)
                if next_block:
                    lines.extend("    " + line
                               for line in self._block_to_script(next_block))
            
            elif block.data.type == BlockType.WHILE:
                condition = block.data.parameters.get('condition', 'True')
                lines.append(f"while {condition}:")
                
                # Process loop body
                next_block = self._find_next_block(block)
                if next_block:
                    lines.extend("    " + line
                               for line in self._block_to_script(next_block))
            
            elif block.data.type == BlockType.ACTION:
                action = block.data.parameters.get('action', 'pass')
                lines.append(action)
            
            elif block.data.type == BlockType.WAIT:
                seconds = block.data.parameters.get('seconds', '1')
                lines.append(f"sleep({seconds})")
            
            elif block.data.type == BlockType.COMMENT:
                comment = block.data.parameters.get('text', '')
                lines.append(f"# {comment}")
            
            return lines
            
        except Exception as e:
            self.logger.error(f"Failed to convert block to script: {e}")
            return []

    def _find_start_block(self) -> Optional[BlockGraphicsItem]:
        """Find start block."""
        for block in self.blocks.values():
            if block.data.type == BlockType.START:
                return block
        return None

    def _find_next_block(self, block: BlockGraphicsItem) -> Optional[BlockGraphicsItem]:
        """Find next connected block."""
        for conn in self.connections:
            if conn.source == block and not conn.branch:
                return conn.target
        return None

    def _find_connected_block(self, block: BlockGraphicsItem,
                            branch: str) -> Optional[BlockGraphicsItem]:
        """Find block connected to specific branch."""
        for conn in self.connections:
            if conn.source == block and conn.branch == branch:
                return conn.target
        return None
