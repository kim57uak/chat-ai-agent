"""
Topic Tree Widget
"""

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction
from core.logging import get_logger

logger = get_logger("topic_tree_widget")


class TopicTreeWidget(QTreeWidget):
    """토픽 트리 위젯"""
    
    topic_selected = pyqtSignal(str)  # topic_id
    topic_edit_requested = pyqtSignal(str)  # topic_id
    topic_delete_requested = pyqtSignal(str)  # topic_id
    
    def __init__(self, parent=None):
        """Initialize topic tree widget"""
        super().__init__(parent)
        
        self.setHeaderLabels(["Topics", "Documents"])
        self.setColumnWidth(0, 200)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemClicked.connect(self._on_item_clicked)
        
        self.topics_map = {}  # topic_id -> QTreeWidgetItem
    
    def load_topics(self, topics):
        """
        Load topics into tree
        
        Args:
            topics: List of topic dicts
        """
        self.clear()
        self.topics_map.clear()
        
        # Create items
        for topic in topics:
            item = QTreeWidgetItem()
            item.setText(0, topic['name'])
            item.setText(1, str(topic.get('document_count', 0)))
            item.setData(0, Qt.ItemDataRole.UserRole, topic['id'])
            self.topics_map[topic['id']] = item
        
        # Build hierarchy
        for topic in topics:
            item = self.topics_map[topic['id']]
            parent_id = topic.get('parent_id')
            
            if parent_id and parent_id in self.topics_map:
                self.topics_map[parent_id].addChild(item)
            else:
                self.addTopLevelItem(item)
        
        self.expandAll()
        logger.info(f"Loaded {len(topics)} topics")
    
    def get_selected_topic_id(self):
        """Get selected topic ID"""
        item = self.currentItem()
        if item:
            return item.data(0, Qt.ItemDataRole.UserRole)
        return None
    
    def _on_item_clicked(self, item, column):
        """Handle item click"""
        topic_id = item.data(0, Qt.ItemDataRole.UserRole)
        if topic_id:
            self.topic_selected.emit(topic_id)
    
    def _show_context_menu(self, position):
        """Show context menu"""
        item = self.itemAt(position)
        if not item:
            return
        
        topic_id = item.data(0, Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.topic_edit_requested.emit(topic_id))
        menu.addAction(edit_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.topic_delete_requested.emit(topic_id))
        menu.addAction(delete_action)
        
        menu.exec(self.viewport().mapToGlobal(position))
