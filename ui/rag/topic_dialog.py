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
        
        # Apply theme style
        self.setStyleSheet(self._get_dialog_style())
        
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
    
    def _get_dialog_style(self):
        """Get web-style dialog from theme"""
        from ui.styles.material_theme_manager import material_theme_manager
        
        colors = material_theme_manager.get_theme_colors()
        bg = colors.get('background', '#1e293b')
        surface = colors.get('surface', '#334155')
        primary = colors.get('primary', '#6366f1')
        primary_variant = colors.get('primary_variant', '#4f46e5')
        text_color = colors.get('text_primary', '#f1f5f9')
        border = colors.get('border', '#475569')
        surface_variant = colors.get('surface_variant', '#475569')
        
        # RGB 추출
        try:
            r = int(primary[1:3], 16)
            g = int(primary[3:5], 16)
            b = int(primary[5:7], 16)
            r2 = int(primary_variant[1:3], 16)
            g2 = int(primary_variant[3:5], 16)
            b2 = int(primary_variant[5:7], 16)
        except:
            r, g, b = 99, 102, 241
            r2, g2, b2 = 79, 70, 229
        
        return f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({r}, {g}, {b}, 0.05),
                    stop:1 rgba({r2}, {g2}, {b2}, 0.05));
                color: {text_color};
            }}
            QLabel {{
                color: {text_color};
                font-size: 14px;
                font-weight: 500;
                padding: 6px 0;
            }}
            QLineEdit, QTextEdit {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {surface},
                    stop:1 {surface_variant});
                color: {text_color};
                border: 2px solid rgba({r}, {g}, {b}, 0.2);
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: rgba({r}, {g}, {b}, 1);
                background-color: {surface};
            }}
            QLineEdit:hover, QTextEdit:hover {{
                border-color: rgba({r}, {g}, {b}, 0.5);
            }}
            QComboBox {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {surface},
                    stop:1 {surface_variant});
                color: {text_color};
                border: 2px solid rgba({r}, {g}, {b}, 0.2);
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                min-height: 24px;
            }}
            QComboBox:hover {{
                border-color: rgba({r}, {g}, {b}, 0.5);
            }}
            QComboBox:focus {{
                border-color: rgba({r}, {g}, {b}, 1);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 0.3),
                    stop:1 rgba({r2}, {g2}, {b2}, 0.3));
                border-radius: 4px;
                margin: 2px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {text_color};
                width: 0;
                height: 0;
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 1),
                    stop:1 rgba({r2}, {g2}, {b2}, 1));
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                margin: 4px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r2}, {g2}, {b2}, 1),
                    stop:1 rgba({r}, {g}, {b}, 1));
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r2}, {g2}, {b2}, 0.8),
                    stop:1 rgba({r}, {g}, {b}, 0.8));
            }}
        """
    
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
