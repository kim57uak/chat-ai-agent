"""
Topic Dialog
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QComboBox, QPushButton)
from PyQt6.QtCore import pyqtSignal
from core.logging import get_logger

logger = get_logger("topic_dialog")


class TopicDialog(QDialog):
    """토픽 생성/편집 다이얼로그"""
    
    topic_saved = pyqtSignal(dict)
    
    def __init__(self, storage_manager, parent_topics=None, edit_topic=None, parent=None):
        """
        Initialize topic dialog
        
        Args:
            storage_manager: RAGStorageManager instance
            parent_topics: List of available parent topics
            edit_topic: Topic to edit (None for create)
            parent: Parent widget
        """
        super().__init__(parent)
        self.storage = storage_manager
        self.parent_topics = parent_topics or []
        self.edit_topic = edit_topic
        
        self.setWindowTitle("Edit Topic" if edit_topic else "Create Topic")
        self.setMinimumWidth(400)
        
        self._init_ui()
        
        if edit_topic:
            self._load_topic_data()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Name
        layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter topic name")
        layout.addWidget(self.name_input)
        
        # Parent
        layout.addWidget(QLabel("Parent Topic:"))
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("(None)", None)
        for topic in self.parent_topics:
            self.parent_combo.addItem(topic['name'], topic['id'])
        layout.addWidget(self.parent_combo)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Enter description (optional)")
        self.desc_input.setMaximumHeight(100)
        layout.addWidget(self.desc_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save)
        save_btn.setDefault(True)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_topic_data(self):
        """Load topic data for editing"""
        self.name_input.setText(self.edit_topic['name'])
        self.desc_input.setPlainText(self.edit_topic.get('description', ''))
        
        # Set parent
        parent_id = self.edit_topic.get('parent_id')
        if parent_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break
    
    def _on_save(self):
        """Save topic"""
        name = self.name_input.text().strip()
        if not name:
            logger.warning("Topic name is required")
            return
        
        parent_id = self.parent_combo.currentData()
        description = self.desc_input.toPlainText().strip()
        
        try:
            if self.edit_topic:
                # Update
                self.storage.update_topic(
                    self.edit_topic['id'],
                    name=name,
                    description=description
                )
                topic_id = self.edit_topic['id']
            else:
                # Create
                topic_id = self.storage.create_topic(
                    name=name,
                    parent_id=parent_id,
                    description=description
                )
            
            self.topic_saved.emit({
                'id': topic_id,
                'name': name,
                'parent_id': parent_id,
                'description': description
            })
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save topic: {e}")
