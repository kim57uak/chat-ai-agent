"""
RAG Management Window
"""

from typing import Optional
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QSplitter, QListWidget, QTextEdit,
                             QMessageBox, QFileDialog, QProgressDialog, QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from core.logging import get_logger
from ui.styles.material_theme_manager import material_theme_manager
from .topic_tree_widget import TopicTreeWidget
from .topic_dialog import TopicDialog
from .search_dialog import SearchDialog

logger = get_logger("rag_management_window")


class RAGManagementWindow(QMainWindow):
    """RAG 관리 메인 윈도우"""
    
    def __init__(self, parent=None):
        """
        Initialize RAG management window
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.storage = None
        self.embeddings = None
        self.current_topic_id = None
        self._initialized = False
        
        self.setWindowTitle("📚 RAG Document Management")
        self.setMinimumSize(1400, 800)
        self.resize(1600, 900)
        
        self._init_ui()
        self._apply_theme()
    
    def _init_ui(self):
        """Initialize UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Splitter (3-way)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        
        # Left: Topic Tree
        left_panel = self._create_topic_panel()
        splitter.addWidget(left_panel)
        
        # Middle: Document List
        middle_panel = self._create_document_panel()
        splitter.addWidget(middle_panel)
        
        # Right: Preview
        right_panel = self._create_preview_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 500, 500])
        layout.addWidget(splitter)
    
    def _create_topic_panel(self):
        """Create topic tree panel"""
        panel = QFrame()
        panel.setObjectName("glassPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        header = QLabel("📁 Topics")
        header.setObjectName("panelHeader")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        header.setFont(font)
        layout.addWidget(header)
        
        self.topic_tree = TopicTreeWidget()
        self.topic_tree.topic_selected.connect(self._on_topic_selected)
        self.topic_tree.topic_edit_requested.connect(self._on_edit_topic)
        self.topic_tree.topic_delete_requested.connect(self._on_delete_topic)
        layout.addWidget(self.topic_tree)
        
        return panel
    
    def _create_document_panel(self):
        """Create document list panel"""
        panel = QFrame()
        panel.setObjectName("glassPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        header = QLabel("📄 Documents")
        header.setObjectName("panelHeader")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        header.setFont(font)
        layout.addWidget(header)
        
        self.doc_list = QListWidget()
        self.doc_list.setObjectName("glassList")
        self.doc_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.doc_list.customContextMenuRequested.connect(self._on_document_context_menu)
        self.doc_list.itemClicked.connect(self._on_document_selected)
        layout.addWidget(self.doc_list)
        
        self.doc_id_map = {}
        
        return panel
    
    def _create_preview_panel(self):
        """Create preview panel"""
        panel = QFrame()
        panel.setObjectName("glassPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        header = QLabel("👁️ Preview")
        header.setObjectName("panelHeader")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        header.setFont(font)
        layout.addWidget(header)
        
        self.preview = QTextEdit()
        self.preview.setObjectName("glassPreview")
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)
        
        return panel
    
    def _create_toolbar(self):
        """Create toolbar"""
        toolbar = QFrame()
        toolbar.setObjectName("glassToolbar")
        toolbar.setMaximumHeight(60)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Topic buttons
        new_topic_btn = QPushButton("📁 NEW TOPIC")
        new_topic_btn.setObjectName("primaryBtn")
        new_topic_btn.clicked.connect(self._on_new_topic)
        layout.addWidget(new_topic_btn)
        
        # Upload buttons
        upload_file_btn = QPushButton("📤 UPLOAD FILES")
        upload_file_btn.setObjectName("primaryBtn")
        upload_file_btn.clicked.connect(self._on_upload_files)
        layout.addWidget(upload_file_btn)
        
        upload_folder_btn = QPushButton("📂 UPLOAD FOLDER")
        upload_folder_btn.setObjectName("primaryBtn")
        upload_folder_btn.clicked.connect(self._on_upload_folder)
        layout.addWidget(upload_folder_btn)
        
        # Chunking strategy selector
        from PyQt6.QtWidgets import QComboBox
        self.chunking_combo = QComboBox()
        self.chunking_combo.setObjectName("chunkingCombo")
        self.chunking_combo.addItems(["Auto", "Sliding Window", "Semantic", "Code", "Markdown"])
        self.chunking_combo.setCurrentText("Auto")
        layout.addWidget(self.chunking_combo)
        
        layout.addStretch()
        
        # Search
        search_btn = QPushButton("🔍 SEARCH")
        search_btn.setObjectName("successBtn")
        search_btn.clicked.connect(self._on_search)
        layout.addWidget(search_btn)
        
        # Refresh
        refresh_btn = QPushButton("🔄 REFRESH")
        refresh_btn.setObjectName("warningBtn")
        refresh_btn.clicked.connect(self._load_topics)
        layout.addWidget(refresh_btn)
        
        return toolbar
    
    def _lazy_init(self):
        """Lazy initialization"""
        if self._initialized:
            return
        
        try:
            from core.rag.storage.rag_storage_manager import RAGStorageManager
            from core.rag.embeddings.embedding_factory import EmbeddingFactory
            from core.rag.config.rag_config_manager import RAGConfigManager
            
            config_manager = RAGConfigManager()
            embedding_config = config_manager.get_embedding_config()
            embedding_type = embedding_config.pop('type')
            
            self.embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)
            self.storage = RAGStorageManager()
            self._initialized = True
            
            logger.info("RAG components initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            raise
    
    def _load_topics(self):
        """Load topics"""
        try:
            self._lazy_init()
            topics = self.storage.get_all_topics()
            self.topic_tree.load_topics(topics)
            logger.info(f"Loaded {len(topics)} topics")
        except Exception as e:
            logger.error(f"Failed to load topics: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load: {e}")
    
    def _on_topic_selected(self, topic_id):
        """Handle topic selection"""
        self.current_topic_id = topic_id
        self._load_documents(topic_id)
    
    def _load_documents(self, topic_id):
        """Load documents for topic"""
        try:
            self.doc_list.clear()
            self.doc_id_map.clear()
            docs = self.storage.get_documents_by_topic(topic_id)
            
            for doc in docs:
                item_text = f"{doc['filename']} ({doc['chunk_count']} chunks)"
                self.doc_list.addItem(item_text)
                self.doc_id_map[item_text] = doc['id']
            
            self.preview.setPlainText(f"Topic: {topic_id}\nDocuments: {len(docs)}")
            logger.info(f"Loaded {len(docs)} documents for topic {topic_id}")
            
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
    
    def _on_document_selected(self, item):
        """Handle document selection"""
        try:
            item_text = item.text()
            doc_id = self.doc_id_map.get(item_text)
            
            if not doc_id:
                self.preview.setPlainText(f"Document: {item_text}\n\nNo details available")
                return
            
            # Get document metadata
            doc = self.storage.get_document(doc_id)
            if not doc:
                self.preview.setPlainText(f"Document not found: {doc_id}")
                return
            
            # Format document info
            info = f"""📄 Document Details

📝 Filename: {doc.get('filename', 'N/A')}
🆔 Document ID: {doc.get('id', 'N/A')}
📁 Topic ID: {doc.get('topic_id', 'N/A')}
📦 File Type: {doc.get('file_type', 'N/A')}
📊 File Size: {doc.get('file_size', 0):,} bytes
🔢 Chunk Count: {doc.get('chunk_count', 0)}
⚙️ Chunking Strategy: {doc.get('chunking_strategy', 'N/A')}
📅 Created: {doc.get('created_at', 'N/A')}
"""
            
            # Get first 3 chunks preview
            try:
                from core.rag.vector_store.lancedb_store import LanceDBStore
                vector_store = LanceDBStore()
                
                # Search chunks by document_id
                if vector_store.table:
                    results = vector_store.table.search().where(f"metadata.document_id = '{doc_id}'").limit(3).to_list()
                    
                    if results:
                        info += "\n\n📋 Chunk Preview (First 3):\n"
                        info += "=" * 50 + "\n"
                        for i, row in enumerate(results, 1):
                            text = row.get('text', '')[:200]
                            info += f"\n[Chunk {i}]\n{text}...\n"
                    else:
                        info += "\n\n⚠️ No chunks found in vector store"
            except Exception as e:
                logger.error(f"Failed to load chunks: {e}")
                info += f"\n\n⚠️ Failed to load chunks: {e}"
            
            self.preview.setPlainText(info)
            
        except Exception as e:
            logger.error(f"Failed to show document details: {e}")
            self.preview.setPlainText(f"Error: {e}")
    
    def _on_new_topic(self):
        """Create new topic"""
        try:
            self._lazy_init()
            topics = self.storage.get_all_topics()
            dialog = TopicDialog(self.storage, topics, parent=self)
            dialog.topic_saved.connect(lambda t: self._load_topics())
            dialog.exec()
        except Exception as e:
            logger.error(f"Failed to create topic: {e}")
            QMessageBox.critical(self, "Error", f"Failed: {e}")
    
    def _on_edit_topic(self, topic_id):
        """Edit topic"""
        topic = self.storage.get_topic(topic_id)
        if not topic:
            return
        
        topics = self.storage.get_all_topics()
        dialog = TopicDialog(self.storage, topics, edit_topic=topic, parent=self)
        dialog.topic_saved.connect(lambda t: self._load_topics())
        dialog.exec()
    
    def _on_delete_topic(self, topic_id):
        """Delete topic with cascading deletion"""
        topic = self.storage.get_topic(topic_id)
        if not topic:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Topic",
            f"Delete topic '{topic['name']}' and all its documents/vectors?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.storage.delete_topic(topic_id)
                self.current_topic_id = None
                self.doc_list.clear()
                self.doc_id_map.clear()
                self.preview.clear()
                self._load_topics()
                logger.info(f"Deleted topic with cascading: {topic_id}")
            except Exception as e:
                logger.error(f"Failed to delete topic: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete topic: {e}")
    
    def _on_upload_files(self):
        """Upload files"""
        try:
            self._lazy_init()
            
            if not self.current_topic_id:
                QMessageBox.warning(self, "Warning", "Please select a topic first")
                return
            
            files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
            if not files:
                return
            
            from pathlib import Path
            from core.rag.batch.batch_processor import BatchProcessor
            from core.rag.config.rag_config_manager import RAGConfigManager
            
            config_manager = RAGConfigManager()
            batch_config = config_manager.get_batch_config()
            
            # Get selected chunking strategy
            chunking_strategy = self._get_chunking_strategy()
            
            processor = BatchProcessor(
                self.storage, 
                self.embeddings, 
                batch_config.get('max_workers', 1),
                chunking_strategy=chunking_strategy
            )
            
            # Progress dialog
            progress = QProgressDialog("Processing files...", "Cancel", 0, len(files), self)
            progress.setWindowTitle("Uploading Files")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setMinimumSize(500, 150)
            progress.setValue(0)
            
            # Style progress dialog
            progress_font = QFont()
            progress_font.setPointSize(12)
            progress.setFont(progress_font)
            
            file_paths = [Path(f) for f in files]
            processed = 0
            total_chunks = 0
            
            def on_progress(file_path, current, total):
                nonlocal processed
                processed = current
                if progress.wasCanceled():
                    return
                progress.setValue(current)
                percent = int((current / total) * 100) if total > 0 else 0
                progress.setLabelText(
                    f"Processing: {current}/{total} files ({percent}%)\n"
                    f"File: {file_path.name}"
                )
            
            def on_complete(file_path, doc_id, chunk_count):
                nonlocal total_chunks
                total_chunks += chunk_count
            
            def check_cancel():
                return progress.wasCanceled()
            
            processor.process_files(
                file_paths,
                self.current_topic_id,
                on_progress=on_progress,
                on_complete=on_complete,
                check_cancel=check_cancel
            )
            
            progress.close()
            QMessageBox.information(
                self,
                "Upload Complete",
                f"Processed: {processed}/{len(files)} files\n"
                f"Total chunks: {total_chunks}"
            )
            self._load_documents(self.current_topic_id)
            
        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Upload failed: {e}")
    
    def _on_upload_folder(self):
        """Upload folder"""
        try:
            self._lazy_init()
            
            if not self.current_topic_id:
                QMessageBox.warning(self, "Warning", "Please select a topic first")
                return
            
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if not folder:
                return
            
            from core.rag.batch.batch_uploader import BatchUploader
            from core.rag.config.rag_config_manager import RAGConfigManager
            
            config_manager = RAGConfigManager()
            batch_config = config_manager.get_batch_config()
            
            # Get selected chunking strategy
            chunking_strategy = self._get_chunking_strategy()
            logger.info(f"Selected chunking strategy: {chunking_strategy}")
            if chunking_strategy:
                batch_config['chunking_strategy'] = chunking_strategy
            logger.info(f"Batch config: {batch_config}")
            
            uploader = BatchUploader(self.storage, self.embeddings, batch_config)
            
            # Progress dialog
            progress = QProgressDialog("Scanning files...", "Cancel", 0, 100, self)
            progress.setWindowTitle("Uploading Folder")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setMinimumSize(500, 150)
            progress.setValue(0)
            
            # Style progress dialog
            progress_font = QFont()
            progress_font.setPointSize(12)
            progress.setFont(progress_font)
            
            def on_progress(current, total, percentage, stats):
                if progress.wasCanceled():
                    return
                progress.setMaximum(total)
                progress.setValue(current)
                percent = int((current / total) * 100) if total > 0 else 0
                progress.setLabelText(
                    f"Processing: {current}/{total} files ({percent}%)\n"
                    f"Chunks: {stats.get('total_chunks', 0)}"
                )
            
            def on_complete(stats):
                progress.close()
                QMessageBox.information(
                    self,
                    "Upload Complete",
                    f"Processed: {stats['processed_files']}/{stats['total_files']}\n"
                    f"Chunks: {stats['total_chunks']}\n"
                    f"Errors: {len(stats.get('errors', []))}\n"
                    f"Time: {stats['elapsed_seconds']:.2f}s"
                )
                self._load_documents(self.current_topic_id)
            
            # Start upload
            QTimer.singleShot(100, lambda: self._do_upload(
                uploader, folder, progress, on_progress, on_complete
            ))
            
        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Upload failed: {e}")
    
    def _do_upload(self, uploader, folder, progress, on_progress, on_complete):
        """Execute upload"""
        try:
            stats = uploader.upload_folder(
                folder,
                self.current_topic_id,
                on_progress=on_progress,
                on_complete=on_complete
            )
        except Exception as e:
            progress.close()
            logger.error(f"Upload error: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Upload failed: {e}")
    
    def _on_search(self):
        """Open search dialog"""
        try:
            self._lazy_init()
            dialog = SearchDialog(self.storage, self.embeddings, self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Failed to open search: {e}")
            QMessageBox.critical(self, "Error", f"Failed: {e}")
    
    def _on_document_context_menu(self, position):
        """Show document context menu"""
        item = self.doc_list.itemAt(position)
        if not item:
            return
        
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu(self)
        delete_action = QAction("🗑️ Delete Document", self)
        delete_action.triggered.connect(lambda: self._on_delete_document(item))
        menu.addAction(delete_action)
        
        menu.exec(self.doc_list.viewport().mapToGlobal(position))
    
    def _on_delete_document(self, item):
        """Delete document with cascading deletion"""
        item_text = item.text()
        doc_id = self.doc_id_map.get(item_text)
        
        if not doc_id:
            logger.error(f"Document ID not found for: {item_text}")
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Document",
            f"Delete document '{item_text}' and all its vectors?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.storage.delete_document(doc_id)
                self._load_documents(self.current_topic_id)
                self.preview.clear()
                logger.info(f"Deleted document with cascading: {doc_id}")
            except Exception as e:
                logger.error(f"Failed to delete document: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete document: {e}")
    
    def _apply_theme(self):
        """Apply glassmorphism theme"""
        colors = material_theme_manager.get_theme_colors()
        glass_config = material_theme_manager.get_glassmorphism_config()
        is_dark = material_theme_manager.is_dark_theme()
        
        bg = colors.get('background', '#121212')
        surface = colors.get('surface', '#1e1e1e')
        primary = colors.get('primary', '#bb86fc')
        text = colors.get('text_primary', '#ffffff')
        text_sec = colors.get('text_secondary', '#b3b3b3')
        
        blur = glass_config.get('blur_intensity', '30px')
        border_op = glass_config.get('border_opacity', 0.2)
        
        stylesheet = f"""
        QMainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {bg}, stop:0.3 {surface}, stop:0.7 {surface}, stop:1 {bg});
        }}
        
        QFrame#glassToolbar {{
            background: rgba({self._hex_to_rgba(surface, 0.7)});
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, {border_op});
        }}
        
        QFrame#glassPanel {{
            background: rgba({self._hex_to_rgba(surface, 0.5)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 12px;
            margin: 0px 4px 4px 4px;
        }}
        
        QLabel#panelHeader {{
            color: {text};
            padding: 2px 0;
            background: transparent;
            margin-bottom: 2px;
        }}
        
        QPushButton#primaryBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary}, stop:1 {self._adjust_color(primary, 0.8)});
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 7px;
            padding: 7px 15px;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 0.3px;
        }}
        
        QPushButton#primaryBtn:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self._adjust_color(primary, 1.2)}, stop:1 {primary});
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}
        
        QPushButton#successBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #4CAF50, stop:1 #388E3C);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 7px;
            padding: 7px 15px;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 0.3px;
        }}
        
        QPushButton#successBtn:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #66BB6A, stop:1 #4CAF50);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}
        
        QPushButton#warningBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FF9800, stop:1 #F57C00);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 7px;
            padding: 7px 15px;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 0.3px;
        }}
        
        QPushButton#warningBtn:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FFB74D, stop:1 #FF9800);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}
        
        QTreeWidget, QListWidget#glassList {{
            background: rgba({self._hex_to_rgba(bg, 0.3)});
            border: 1px solid rgba(255, 255, 255, {border_op * 0.5});
            border-radius: 10px;
            color: {text};
            padding: 6px;
            font-size: 13px;
        }}
        
        QTreeWidget::item, QListWidget::item {{
            padding: 6px 8px;
            border-radius: 6px;
            margin: 1px 0;
        }}
        
        QTreeWidget::item:hover, QListWidget::item:hover {{
            background: rgba({self._hex_to_rgba(primary, 0.2)});
        }}
        
        QTreeWidget::item:selected, QListWidget::item:selected {{
            background: rgba({self._hex_to_rgba(primary, 0.4)});
            color: white;
        }}
        
        QTextEdit#glassPreview {{
            background: rgba({self._hex_to_rgba(bg, 0.3)});
            border: 1px solid rgba(255, 255, 255, {border_op * 0.5});
            border-radius: 10px;
            color: {text};
            padding: 10px;
            font-size: 13px;
            line-height: 1.5;
        }}
        
        QSplitter::handle {{
            background: rgba(255, 255, 255, {border_op * 0.3});
        }}
        
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background: rgba({self._hex_to_rgba(primary, 0.5)});
            border-radius: 5px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: rgba({self._hex_to_rgba(primary, 0.7)});
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QComboBox#chunkingCombo {{
            background: rgba({self._hex_to_rgba(surface, 0.7)});
            color: {text};
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 7px;
            padding: 6px 12px;
            font-size: 11px;
            min-width: 120px;
        }}
        
        QComboBox#chunkingCombo:hover {{
            border: 1px solid rgba(255, 255, 255, {border_op * 1.5});
        }}
        
        QComboBox#chunkingCombo::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox#chunkingCombo QAbstractItemView {{
            background: {surface};
            color: {text};
            border: 1px solid rgba(255, 255, 255, {border_op});
            selection-background-color: rgba({self._hex_to_rgba(primary, 0.4)});
        }}
        
        QProgressDialog {{
            background: rgba({self._hex_to_rgba(surface, 0.95)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 12px;
        }}
        
        QProgressDialog QLabel {{
            color: {text};
            font-size: 13px;
            padding: 10px;
        }}
        
        QProgressDialog QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary}, stop:1 {self._adjust_color(primary, 0.8)});
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 11px;
            min-width: 80px;
        }}
        
        QProgressDialog QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self._adjust_color(primary, 1.2)}, stop:1 {primary});
        }}
        
        QProgressBar {{
            background: rgba({self._hex_to_rgba(bg, 0.5)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 8px;
            text-align: center;
            color: {text};
            font-size: 12px;
            font-weight: bold;
            min-height: 25px;
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary}, stop:1 {self._adjust_color(primary, 1.2)});
            border-radius: 7px;
        }}
        
        QMessageBox {{
            background: rgba({self._hex_to_rgba(surface, 0.95)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 12px;
        }}
        
        QMessageBox QLabel {{
            color: {text};
            font-size: 13px;
            padding: 10px;
        }}
        
        QMessageBox QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary}, stop:1 {self._adjust_color(primary, 0.8)});
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 11px;
            min-width: 80px;
        }}
        
        QMessageBox QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self._adjust_color(primary, 1.2)}, stop:1 {primary});
        }}
        
        QDialog {{
            background: rgba({self._hex_to_rgba(surface, 0.95)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 12px;
        }}
        
        QDialog QLabel {{
            color: {text};
        }}
        
        QDialog QLineEdit, QDialog QTextEdit {{
            background: rgba({self._hex_to_rgba(bg, 0.5)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 6px;
            color: {text};
            padding: 6px;
            font-size: 12px;
        }}
        
        QDialog QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary}, stop:1 {self._adjust_color(primary, 0.8)});
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 11px;
            min-width: 80px;
        }}
        
        QDialog QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self._adjust_color(primary, 1.2)}, stop:1 {primary});
        }}
        
        QMenu {{
            background: rgba({self._hex_to_rgba(surface, 0.95)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 8px;
            padding: 4px;
        }}
        
        QMenu::item {{
            color: {text};
            padding: 6px 20px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background: rgba({self._hex_to_rgba(primary, 0.4)});
        }}
        """
        
        self.setStyleSheet(stylesheet)
    
    def _hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> str:
        """Convert hex to RGBA"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}, {alpha}"
        return f"30, 30, 30, {alpha}"
    
    def _adjust_color(self, hex_color: str, factor: float) -> str:
        """Adjust color brightness"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = min(255, int(int(hex_color[0:2], 16) * factor))
            g = min(255, int(int(hex_color[2:4], 16) * factor))
            b = min(255, int(int(hex_color[4:6], 16) * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        return hex_color
    
    def _get_chunking_strategy(self) -> Optional[str]:
        """Get selected chunking strategy"""
        selected = self.chunking_combo.currentText()
        strategy_map = {
            "Auto": None,  # Auto-select based on file type
            "Sliding Window": "sliding_window",
            "Semantic": "semantic",
            "Code": "code",
            "Markdown": "markdown"
        }
        return strategy_map.get(selected)
