"""
Folder management module.
Copyright (c) 2025 AtomicArk
"""

import logging
import threading
from typing import Dict, List, Optional, Set, Union
from pathlib import Path
import json
import shutil
import os
import time

from ..utils.debug_helper import get_debug_helper

class FolderNode:
    """Represents a folder in the macro hierarchy."""
    
    def __init__(self, name: str, parent: Optional['FolderNode'] = None):
        self.name = name
        self.parent = parent
        self.children: Dict[str, Union['FolderNode', 'MacroNode']] = {}
        self.tags: Set[str] = set()
        self.description: str = ""
        self.created: float = time.time()
        self.modified: float = self.created

    def add_child(self, name: str, node: Union['FolderNode', 'MacroNode']) -> bool:
        """Add child node."""
        if name in self.children:
            return False
        self.children[name] = node
        if isinstance(node, FolderNode):
            node.parent = self
        self.modified = time.time()
        return True

    def remove_child(self, name: str) -> bool:
        """Remove child node."""
        if name not in self.children:
            return False
        del self.children[name]
        self.modified = time.time()
        return True

    def get_path(self) -> str:
        """Get full path from root."""
        if self.parent:
            return os.path.join(self.parent.get_path(), self.name)
        return self.name

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': 'folder',
            'children': {name: node.to_dict() for name, node in self.children.items()},
            'tags': list(self.tags),
            'description': self.description,
            'created': self.created,
            'modified': self.modified
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'FolderNode':
        """Create from dictionary."""
        node = cls(data['name'])
        node.tags = set(data.get('tags', []))
        node.description = data.get('description', '')
        node.created = data.get('created', 0.0)
        node.modified = data.get('modified', 0.0)
        return node

class MacroNode:
    """Represents a macro in the hierarchy."""
    
    def __init__(self, name: str, macro_id: str):
        self.name = name
        self.macro_id = macro_id
        self.tags: Set[str] = set()
        self.description: str = ""
        self.created: float = time.time()
        self.modified: float = self.created

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': 'macro',
            'macro_id': self.macro_id,
            'tags': list(self.tags),
            'description': self.description,
            'created': self.created,
            'modified': self.modified
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MacroNode':
        """Create from dictionary."""
        node = cls(data['name'], data['macro_id'])
        node.tags = set(data.get('tags', []))
        node.description = data.get('description', '')
        node.created = data.get('created', 0.0)
        node.modified = data.get('modified', 0.0)
        return node

class FolderManager:
    """Manages macro folder hierarchy."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger('FolderManager')
            self.debug = get_debug_helper()
            
            # Root folder
            self._root = FolderNode('root')
            
            # Cache
            self._path_cache: Dict[str, Union[FolderNode, MacroNode]] = {}
            self._tag_cache: Dict[str, Set[Union[FolderNode, MacroNode]]] = {}
            
            # State
            self._modified = False
            self._storage_path = Path.home() / '.atomic_macro' / 'folders'
            
            # Initialize
            self._load_structure()
            self._initialized = True

    def create_folder(self, path: str, description: str = "") -> bool:
        """Create new folder."""
        try:
            with self._lock:
                # Split path
                parts = self._split_path(path)
                if not parts:
                    return False
                
                # Navigate to parent
                parent = self._root
                for part in parts[:-1]:
                    if part not in parent.children:
                        node = FolderNode(part)
                        parent.add_child(part, node)
                    parent = parent.children[part]
                    if not isinstance(parent, FolderNode):
                        return False
                
                # Create folder
                name = parts[-1]
                if name in parent.children:
                    return False
                
                node = FolderNode(name)
                node.description = description
                parent.add_child(name, node)
                
                # Update cache
                self._update_cache()
                self._modified = True
                self._save_structure()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to create folder: {e}")
            return False

    def add_macro(self, path: str, macro_id: str, description: str = "") -> bool:
        """Add macro to folder."""
        try:
            with self._lock:
                # Split path
                parts = self._split_path(path)
                if not parts:
                    return False
                
                # Navigate to parent
                parent = self._root
                for part in parts[:-1]:
                    if part not in parent.children:
                        node = FolderNode(part)
                        parent.add_child(part, node)
                    parent = parent.children[part]
                    if not isinstance(parent, FolderNode):
                        return False
                
                # Add macro
                name = parts[-1]
                if name in parent.children:
                    return False
                
                node = MacroNode(name, macro_id)
                node.description = description
                parent.add_child(name, node)
                
                # Update cache
                self._update_cache()
                self._modified = True
                self._save_structure()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to add macro: {e}")
            return False

    def remove_node(self, path: str) -> bool:
        """Remove node (folder or macro)."""
        try:
            with self._lock:
                # Split path
                parts = self._split_path(path)
                if not parts:
                    return False
                
                # Navigate to parent
                parent = self._root
                for part in parts[:-1]:
                    if part not in parent.children:
                        return False
                    parent = parent.children[part]
                    if not isinstance(parent, FolderNode):
                        return False
                
                # Remove node
                name = parts[-1]
                if name not in parent.children:
                    return False
                
                parent.remove_child(name)
                
                # Update cache
                self._update_cache()
                self._modified = True
                self._save_structure()
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove node: {e}")
            return False

    def get_node(self, path: str) -> Optional[Union[FolderNode, MacroNode]]:
        """Get node by path."""
        try:
            with self._lock:
                return self._path_cache.get(path)
            
        except Exception as e:
            self.logger.error(f"Failed to get node: {e}")
            return None

    def find_by_tag(self, tag: str) -> List[Union[FolderNode, MacroNode]]:
        """Find nodes by tag."""
        try:
            with self._lock:
                return list(self._tag_cache.get(tag, set()))
            
        except Exception as e:
            self.logger.error(f"Failed to find by tag: {e}")
            return []

    def search(self, query: str) -> List[Union[FolderNode, MacroNode]]:
        """Search nodes by name or description."""
        try:
            results = []
            query = query.lower()
            
            with self._lock:
                for node in self._path_cache.values():
                    if (query in node.name.lower() or
                        query in node.description.lower()):
                        results.append(node)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search: {e}")
            return []

    def _split_path(self, path: str) -> List[str]:
        """Split path into parts."""
        if not path:
            return []
        return [part for part in path.split('/') if part]

    def _update_cache(self) -> None:
        """Update path and tag caches."""
        try:
            self._path_cache.clear()
            self._tag_cache.clear()
            
            def process_node(node: Union[FolderNode, MacroNode], path: str) -> None:
                # Update path cache
                self._path_cache[path] = node
                
                # Update tag cache
                for tag in node.tags:
                    if tag not in self._tag_cache:
                        self._tag_cache[tag] = set()
                    self._tag_cache[tag].add(node)
                
                # Process children
                if isinstance(node, FolderNode):
                    for name, child in node.children.items():
                        process_node(child, os.path.join(path, name))
            
            process_node(self._root, self._root.name)
            
        except Exception as e:
            self.logger.error(f"Failed to update cache: {e}")

    def _load_structure(self) -> None:
        """Load folder structure from disk."""
        try:
            path = self._storage_path / 'structure.json'
            if not path.exists():
                return
            
            with open(path, 'r') as f:
                data = json.load(f)
            
            def process_dict(data: Dict) -> Union[FolderNode, MacroNode]:
                if data['type'] == 'folder':
                    node = FolderNode.from_dict(data)
                    for name, child_data in data['children'].items():
                        child = process_dict(child_data)
                        node.add_child(name, child)
                    return node
                else:
                    return MacroNode.from_dict(data)
            
            self._root = process_dict(data)
            self._update_cache()
            
        except Exception as e:
            self.logger.error(f"Failed to load structure: {e}")

    def _save_structure(self) -> None:
        """Save folder structure to disk."""
        try:
            if not self._modified:
                return
            
            # Create directory
            self._storage_path.mkdir(parents=True, exist_ok=True)
            
            # Save structure
            path = self._storage_path / 'structure.json'
            with open(path, 'w') as f:
                json.dump(self._root.to_dict(), f, indent=2)
            
            self._modified = False
            
        except Exception as e:
            self.logger.error(f"Failed to save structure: {e}")

    def cleanup(self):
        """Clean up resources."""
        try:
            self._save_structure()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Global instance
folder_manager = FolderManager()
