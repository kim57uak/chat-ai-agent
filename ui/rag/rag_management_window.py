"""
RAG Management Window
"""

from typing import Optional
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QSplitter, QListWidget, QTextEdit,
                             QMessageBox, QFileDialog, QProgressDialog, QLabel, QFrame,
                             QDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from core.logging import get_logger
from .topic_tree_widget import TopicTreeWidget
from .topic_dialog import TopicDialog
from .search_dialog import SearchDialog
from .rag_management_styles import RAGManagementStyles

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
        
        # 윈도우가 뒤로 사라지지 않도록 설정
        self.setWindowFlags(Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        
        # 다이얼로그 닫힘 후 윈도우 활성화
        self.activateWindow()
        self.raise_()
        
        self._init_ui()
        self._apply_theme()
        
        # 화면 먼저 표시 후 백그라운드 로딩
        # show() 호출은 외부에서 하므로 여기서는 타이머만 설정
        QTimer.singleShot(100, self._load_topics)
    
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
        
        # 간격 추가 (8px)
        layout.addSpacing(8)
        
        # Splitter (3-way)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)  # 최소 너비 설정
        
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
        font.setPointSize(15)
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
        font.setPointSize(15)
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
        
        # Header with model info
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("👁️ Preview")
        header.setObjectName("panelHeader")
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        header.setFont(font)
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # Model info label
        self.model_info_label = QLabel("")
        self.model_info_label.setObjectName("modelInfo")
        model_font = QFont()
        model_font.setPointSize(10)
        self.model_info_label.setFont(model_font)
        self.model_info_label.setStyleSheet("""
            QLabel#modelInfo {
                color: #666;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 4px 8px;
                margin-left: 8px;
            }
        """)
        header_layout.addWidget(self.model_info_label)
        
        layout.addLayout(header_layout)
        
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
        
        # Optimize button (맨 앞)
        optimize_btn = QPushButton("🧹 OPTIMIZE DB")
        optimize_btn.setObjectName("successBtn")
        optimize_btn.clicked.connect(self._on_optimize_db)
        layout.addWidget(optimize_btn)
        
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
        
        # Settings
        settings_btn = QPushButton("⚙️ SETTINGS")
        settings_btn.setObjectName("primaryBtn")
        settings_btn.clicked.connect(self._on_settings)
        layout.addWidget(settings_btn)
        
        # Search
        search_btn = QPushButton("🔍 SEARCH")
        search_btn.setObjectName("successBtn")
        search_btn.clicked.connect(self._on_search)
        layout.addWidget(search_btn)
        
        # Refresh
        refresh_btn = QPushButton("🔄 REFRESH")
        refresh_btn.setObjectName("warningBtn")
        refresh_btn.clicked.connect(self._refresh_all)
        layout.addWidget(refresh_btn)
        
        return toolbar
    
    def _lazy_init(self):
        """Lazy initialization with model refresh (풀 사용)"""
        try:
            from core.rag.storage.rag_storage_manager import RAGStorageManager
            from core.rag.embeddings.embedding_pool import embedding_pool
            from core.rag.embeddings.embedding_model_manager import EmbeddingModelManager
            
            # 현재 설정된 모델 정보 가져오기
            model_manager = EmbeddingModelManager()
            current_model_id = model_manager.get_current_model()
            model_info = model_manager.get_model_info(current_model_id)
            new_model_name = model_info.get('name', current_model_id) if model_info else current_model_id
            
            # 풀에서 캐시된 임베딩 가져오기 (매번 초기화 방지)
            self.embeddings = embedding_pool.get_embeddings(current_model_id)
            logger.debug(f"Using cached embeddings: {new_model_name}")
            
            # UI 업데이트
            self.model_info_label.setText(f"🤖 {new_model_name}")
            
            if not self._initialized:
                self.storage = RAGStorageManager()
                self._initialized = True
                logger.info(f"RAG components initialized (model: {new_model_name})")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            raise
    
    def _load_topics(self):
        """Load topics asynchronously"""
        from PyQt6.QtCore import QThread, pyqtSignal
        from PyQt6.QtWidgets import QTreeWidgetItem
        
        # Topic 영역에 로딩 메시지 표시
        self.topic_tree.clear()
        loading_item = QTreeWidgetItem(["⏳ 토픽 로딩 중..."])
        self.topic_tree.addTopLevelItem(loading_item)
        
        # UI 즉시 업데이트
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        class LoadTopicsWorker(QThread):
            finished = pyqtSignal(list)
            error = pyqtSignal(str)
            
            def __init__(self, parent_window):
                super().__init__()
                self.parent_window = parent_window
            
            def run(self):
                try:
                    # 초기화를 백그라운드에서 수행 (풀 사용)
                    if not self.parent_window._initialized:
                        from core.rag.storage.rag_storage_manager import RAGStorageManager
                        from core.rag.embeddings.embedding_pool import embedding_pool
                        from core.rag.embeddings.embedding_model_manager import EmbeddingModelManager
                        
                        # 풀에서 캐시된 임베딩 가져오기
                        model_manager = EmbeddingModelManager()
                        current_model_id = model_manager.get_current_model()
                        model_info = model_manager.get_model_info(current_model_id)
                        model_name = model_info.get('name', current_model_id) if model_info else current_model_id
                        
                        self.parent_window.embeddings = embedding_pool.get_embeddings(current_model_id)
                        self.parent_window.storage = RAGStorageManager()
                        self.parent_window._initialized = True
                        
                        # Update model info display
                        self.parent_window.model_info_label.setText(f"🤖 {model_name}")
                        
                        logger.info(f"RAG components initialized in background (cached model: {model_name})")
                    
                    topics = self.parent_window.storage.get_all_topics()
                    self.finished.emit(topics)
                except Exception as e:
                    logger.error(f"Failed to load topics: {e}", exc_info=True)
                    self.error.emit(str(e))
        
        def on_finished(topics):
            self.topic_tree.load_topics(topics)
            logger.info(f"Loaded {len(topics)} topics")
            
            # 모델 정보 업데이트 (_lazy_init에서 처리됨)
            logger.info("Model info updated via _lazy_init")
        
        def on_error(error_msg):
            self.topic_tree.clear()
            error_item = QTreeWidgetItem([f"❌ 로딩 실패: {error_msg}"])
            self.topic_tree.addTopLevelItem(error_item)
            logger.error(f"Failed to load topics: {error_msg}")
        
        worker = LoadTopicsWorker(self)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()
        self._load_worker = worker  # Keep reference
    
    def _on_topic_selected(self, topic_id):
        """Handle topic selection"""
        self.current_topic_id = topic_id
        self._load_documents(topic_id)
    
    def _load_documents(self, topic_id):
        """Load documents for topic (현재 모델 기준 필터링)"""
        import time
        import sqlite3
        
        for attempt in range(3):
            try:
                self.doc_list.clear()
                self.doc_id_map.clear()
                
                # 현재 임베딩 모델 ID 가져오기
                current_model = self._get_current_embedding_model()
                
                # 현재 모델의 문서만 조회
                docs = self.storage.get_documents_by_topic(topic_id, embedding_model=current_model)
                break
                
            except sqlite3.OperationalError as e:
                if "disk i/o error" in str(e).lower() and attempt < 2:
                    logger.warning(f"DB I/O error (attempt {attempt+1}/3), retrying...")
                    time.sleep(0.1 * (2 ** attempt))
                else:
                    raise
        
        try:
            
            for doc in docs:
                item_text = f"{doc['filename']} ({doc['chunk_count']} chunks)"
                self.doc_list.addItem(item_text)
                self.doc_id_map[item_text] = doc['id']
            
            # 전체 문서 수와 현재 모델 문서 수 비교
            all_docs = self.storage.get_documents_by_topic(topic_id)
            total_docs = len(all_docs)
            current_docs = len(docs)
            
            preview_text = f"Topic: {topic_id}\n"
            preview_text += f"현재 모델 ({current_model}) 문서: {current_docs}개\n"
            
            if total_docs > current_docs:
                other_docs = total_docs - current_docs
                preview_text += f"다른 모델 문서: {other_docs}개 (숨김)\n\n"
                preview_text += "💡 다른 모델의 문서를 보려면:\n"
                preview_text += "1. 설정 > RAG 설정에서 모델 변경\n"
                preview_text += "2. 새로고침 버튼 클릭"
            
            self.preview.setPlainText(preview_text)
            logger.info(f"Loaded {current_docs}/{total_docs} documents for topic {topic_id} (model: {current_model})")
            
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            self.preview.setPlainText(f"❌ 문서 로드 실패\n\n{str(e)}\n\n🔄 새로고침 버튼을 클릭하세요.")
    
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
📅 Upload Date: {doc.get('upload_date', 'N/A')}
"""
            
            # Get first 5 chunks preview
            try:
                from core.rag.vector_store.lancedb_store import LanceDBStore
                vector_store = LanceDBStore()
                
                logger.info(f"Loading chunks for document: {doc_id}")
                
                # 테이블 초기화 확인 및 재시도
                logger.info(f"Current model table: {vector_store.table_name}")
                
                if vector_store.db and vector_store.table_name in vector_store.db.table_names():
                    if not vector_store.table:
                        vector_store.table = vector_store.db.open_table(vector_store.table_name)
                        logger.info(f"Opened existing table: {vector_store.table_name}")
                else:
                    logger.warning(f"Table {vector_store.table_name} not found in available tables: {vector_store.db.table_names() if vector_store.db else 'N/A'}")
                
                # Search chunks by document_id
                if vector_store.table:
                    try:
                        # Try different query methods
                        results = vector_store.table.search().where(f"metadata.document_id = '{doc_id}'").limit(10).to_list()
                        logger.info(f"Found {len(results)} chunks using where clause")
                    except Exception as e1:
                        logger.warning(f"Where clause failed: {e1}, trying alternative method")
                        try:
                            # Alternative: scan all and filter
                            all_results = vector_store.table.to_pandas()
                            results = all_results[all_results['metadata'].apply(lambda x: x.get('document_id') == doc_id)].head(10).to_dict('records')
                            logger.info(f"Found {len(results)} chunks using pandas filter")
                        except Exception as e2:
                            logger.error(f"Pandas filter also failed: {e2}")
                            results = []
                    
                    if results:
                        # 첫 번째 청크에서 임베딩 모델 확인
                        first_chunk = results[0]
                        chunk_metadata = first_chunk.get('metadata', {}) if isinstance(first_chunk, dict) else getattr(first_chunk, 'metadata', {})
                        stored_model = chunk_metadata.get('embedding_model', 'unknown')
                        
                        # 현재 모델 ID 가져오기 (이름이 아닌 ID로 비교)
                        from core.rag.embeddings.embedding_model_manager import EmbeddingModelManager
                        model_manager = EmbeddingModelManager()
                        current_model_id = model_manager.get_current_model()
                        
                        if stored_model != 'unknown' and stored_model != current_model_id:
                            # 표시용 이름 가져오기
                            current_model_info = model_manager.get_model_info(current_model_id)
                            current_model_name = current_model_info.get('name', current_model_id) if current_model_info else current_model_id
                            
                            stored_model_info = model_manager.get_model_info(stored_model)
                            stored_model_name = stored_model_info.get('name', stored_model) if stored_model_info else stored_model
                            
                            info += f"\n\n⚠️ 임베딩 모델 불일치 경고:\n"
                            info += f"현재 모델: {current_model_name}\n"
                            info += f"저장된 모델: {stored_model_name}\n"
                            info += f"검색 결과가 부정확할 수 있습니다.\n"
                        
                        info += "\n\n📋 Chunk Preview (First 10):\n"
                        info += "=" * 50 + "\n"
                        for i, row in enumerate(results, 1):
                            # Handle both dict and row objects
                            if isinstance(row, dict):
                                text = row.get('text', row.get('content', ''))[:300]
                            else:
                                text = getattr(row, 'text', getattr(row, 'content', ''))[:300]
                            
                            if text:
                                info += f"\n[Chunk {i}]\n{text}...\n\n"
                            else:
                                info += f"\n[Chunk {i}]\n(Empty chunk)\n\n"
                    else:
                        info += "\n\n⚠️ No chunks found in vector store"
                        logger.warning(f"No chunks found for document_id: {doc_id}")
                else:
                    # 현재 모델에 맞는 테이블이 없음
                    current_model = getattr(self.embeddings, 'model_name', 'unknown') if self.embeddings else 'unknown'
                    available_tables = vector_store.db.table_names() if vector_store.db else []
                    
                    info += f"\n\n🔄 모델 전환 필요:\n"
                    info += f"현재 모델: {current_model}\n"
                    info += f"찾는 테이블: {vector_store.table_name}\n"
                    info += f"사용 가능한 테이블: {', '.join(available_tables)}\n\n"
                    
                    if available_tables:
                        info += "해결 방법:\n"
                        info += "1. 설정 > 임베딩 모델에서 다른 모델로 전환\n"
                        info += "2. 또는 현재 모델로 새 문서 업로드"
                    else:
                        info += "아직 업로드된 문서가 없습니다."
                    
                    logger.error(f"Vector store table is None. Current model: {current_model}, Expected table: {vector_store.table_name}, Available tables: {available_tables}")
            except Exception as e:
                logger.error(f"Failed to load chunks: {e}", exc_info=True)
                info += f"\n\n⚠️ Failed to load chunks: {str(e)}"
            
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
            
            def on_topic_saved(topic_data):
                logger.info(f"Topic saved: {topic_data}")
                # 다이얼로그 닫힌 후 즉시 새로고침
                QTimer.singleShot(100, self._load_topics)
            
            dialog.topic_saved.connect(on_topic_saved)
            result = dialog.exec()
            
            # 다이얼로그 닫힌 후 윈도우 활성화
            self.activateWindow()
            self.raise_()
            
            # 저장 성공 시 추가 새로고침
            if result == QDialog.DialogCode.Accepted:
                logger.info("Topic dialog accepted, refreshing...")
                QTimer.singleShot(200, self._load_topics)
                
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
        
        def on_topic_saved(topic_data):
            logger.info(f"Topic updated: {topic_data}")
            QTimer.singleShot(100, self._load_topics)
        
        dialog.topic_saved.connect(on_topic_saved)
        result = dialog.exec()
        
        # 다이얼로그 닫힌 후 윈도우 활성화
        self.activateWindow()
        self.raise_()
        
        if result == QDialog.DialogCode.Accepted:
            QTimer.singleShot(200, self._load_topics)
    
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
            from PyQt6.QtCore import QCoreApplication
            
            # 중복 파일 체크
            existing_docs = self.storage.get_documents_by_topic(self.current_topic_id)
            existing_filenames = {doc['filename'] for doc in existing_docs}
            
            duplicate_files = []
            valid_files = []
            
            for file_path in files:
                filename = Path(file_path).name
                if filename in existing_filenames:
                    duplicate_files.append(filename)
                else:
                    valid_files.append(file_path)
            
            # 중복 파일이 있으면 경고
            if duplicate_files:
                dup_list = "\n".join(duplicate_files[:5])
                if len(duplicate_files) > 5:
                    dup_list += f"\n... 외 {len(duplicate_files) - 5}개 더"
                
                reply = QMessageBox.warning(
                    self,
                    "중복 파일 감지",
                    f"다음 파일들이 이미 존재합니다:\n\n{dup_list}\n\n"
                    f"업로드하려면 기존 파일을 먼저 삭제해주세요.\n\n"
                    f"나머지 {len(valid_files)}개 파일을 계속 진행하시겠습니까?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No or not valid_files:
                    return
            
            if not valid_files:
                return
            
            from core.rag.batch.batch_processor import BatchProcessor
            from core.rag.config.rag_config_manager import RAGConfigManager
            
            config_manager = RAGConfigManager()
            batch_config = config_manager.get_batch_config()
            
            # Get selected chunking strategy
            chunking_strategy = self._get_chunking_strategy()
            
            # Force max_workers=1 for SQLite stability
            processor = BatchProcessor(
                self.storage, 
                self.embeddings, 
                max_workers=1,  # SQLite WAL 안정성을 위해 순차 처리
                chunking_strategy=chunking_strategy
            )
            
            # Worker thread for file processing
            from PyQt6.QtCore import QThread, pyqtSignal
            import time
            
            class FileUploadWorker(QThread):
                status_update = pyqtSignal(str)  # status message
                finished = pyqtSignal(int, int)  # processed, total_chunks
                error = pyqtSignal(str)
                
                def __init__(self, processor, file_paths, topic_id, parent_window):
                    super().__init__()
                    self.processor = processor
                    self.file_paths = file_paths
                    self.topic_id = topic_id
                    self.parent_window = parent_window
                    self.should_cancel = False
                    self.processed = 0
                    self.total_chunks = 0
                    self.current_file = ""
                    self.total_files = len(file_paths)
                
                def run(self):
                    try:
                        def on_progress(file_path, current, total):
                            self.processed = current
                            self.current_file = file_path.name
                            if self.should_cancel:
                                return
                        
                        def on_complete(file_path, doc_id, chunk_count):
                            self.total_chunks += chunk_count
                        
                        def check_cancel():
                            return self.should_cancel
                        
                        self.processor.process_files(
                            self.file_paths,
                            self.topic_id,
                            on_progress=on_progress,
                            on_complete=on_complete,
                            check_cancel=check_cancel
                        )
                        
                        self.finished.emit(self.processed, self.total_chunks)
                    except Exception as e:
                        self.error.emit(str(e))
                
                def cancel(self):
                    self.should_cancel = True
                
                def get_status(self):
                    """Get current status for display"""
                    if self.processed == 0:
                        return "처리 시작 중..."
                    
                    percent = int((self.processed / self.total_files) * 100) if self.total_files > 0 else 0
                    return (
                        f"처리 중: {self.processed}/{self.total_files} 파일 ({percent}%)\n\n"
                        f"현재 파일: {self.current_file}\n"
                        f"생성된 청크: {self.total_chunks}"
                    )
            
            # Progress dialog
            progress = QProgressDialog(self)
            progress.setWindowTitle("파일 업로드 중")
            progress.setLabelText("업로드 시작 중...")
            progress.setCancelButtonText("취소")
            progress.setRange(0, 0)  # 무한 프로그레스바 (진행 중 표시)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumSize(550, 220)
            progress.setAutoClose(False)
            progress.setAutoReset(False)
            
            # Style
            progress_font = QFont()
            progress_font.setPointSize(12)
            progress.setFont(progress_font)
            
            # Cancel 버튼 중앙 정렬
            from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QWidget
            from PyQt6.QtCore import Qt as QtCore
            
            # 기존 버튼 찾기
            cancel_btn = None
            for child in progress.findChildren(QPushButton):
                if child.text() == "취소":
                    cancel_btn = child
                    break
            
            if cancel_btn:
                # 버튼 스타일 및 중앙 정렬
                cancel_btn.setStyleSheet("""
                    QPushButton {
                        margin-top: 15px;
                        padding: 8px 40px;
                        min-width: 100px;
                    }
                """)
                # 부모 레이아웃에서 중앙 정렬
                if cancel_btn.parent() and cancel_btn.parent().layout():
                    layout = cancel_btn.parent().layout()
                    if hasattr(layout, 'setAlignment'):
                        layout.setAlignment(cancel_btn, QtCore.AlignCenter)
            
            file_paths = [Path(f) for f in valid_files]
            
            # Create worker
            worker = FileUploadWorker(processor, file_paths, self.current_topic_id, self)
            
            # 1초마다 상태 업데이트
            update_timer = QTimer(self)
            
            def update_progress():
                if worker.isRunning():
                    status = worker.get_status()
                    progress.setLabelText(status)
            
            update_timer.timeout.connect(update_progress)
            update_timer.start(1000)  # 1초마다
            
            # Connect signals
            def on_finished(processed, total_chunks):
                update_timer.stop()
                progress.close()
                msg = f"처리 완료: {processed}/{len(valid_files)} 파일\n총 청크: {total_chunks}"
                if duplicate_files:
                    msg += f"\n\n건너뛴 중복 파일: {len(duplicate_files)}개"
                QMessageBox.information(self, "업로드 완료", msg)
                self._load_documents(self.current_topic_id)
            
            def on_error(error_msg):
                update_timer.stop()
                progress.close()
                QMessageBox.critical(self, "업로드 오류", f"파일 업로드 실패: {error_msg}")
            
            def on_cancel():
                update_timer.stop()
                worker.cancel()
            
            worker.finished.connect(on_finished)
            worker.error.connect(on_error)
            progress.canceled.connect(on_cancel)
            
            # Start worker
            progress.show()
            worker.start()
            self._upload_worker = worker  # Keep reference
            self._update_timer = update_timer  # Keep reference
            
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
            
            from PyQt6.QtCore import QCoreApplication
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
            
            # Worker thread for folder processing
            from PyQt6.QtCore import QThread, pyqtSignal
            
            class FolderUploadWorker(QThread):
                finished = pyqtSignal(dict)  # stats
                error = pyqtSignal(str)
                
                def __init__(self, uploader, folder, topic_id):
                    super().__init__()
                    self.uploader = uploader
                    self.folder = folder
                    self.topic_id = topic_id
                    self.should_cancel = False
                    self.current = 0
                    self.total = 0
                    self.chunks = 0
                
                def run(self):
                    try:
                        def on_progress(current, total, percentage, stats):
                            if self.should_cancel:
                                return
                            self.current = current
                            self.total = total
                            self.chunks = stats.get('total_chunks', 0)
                        
                        def on_complete(stats):
                            self.finished.emit(stats)
                        
                        stats = self.uploader.upload_folder(
                            self.folder,
                            self.topic_id,
                            on_progress=on_progress,
                            on_complete=on_complete
                        )
                    except Exception as e:
                        self.error.emit(str(e))
                
                def cancel(self):
                    self.should_cancel = True
                
                def get_status(self):
                    """Get current status for display"""
                    if self.total == 0:
                        return "폴더 스캔 중..."
                    
                    percent = int((self.current / self.total) * 100) if self.total > 0 else 0
                    return (
                        f"처리 중: {self.current}/{self.total} 파일 ({percent}%)\n\n"
                        f"생성된 청크: {self.chunks}"
                    )
            
            # Progress dialog
            progress = QProgressDialog(self)
            progress.setWindowTitle("폴더 업로드 중")
            progress.setLabelText("폴더 스캔 시작 중...")
            progress.setCancelButtonText("취소")
            progress.setRange(0, 0)  # 무한 프로그레스바
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumSize(550, 220)
            progress.setAutoClose(False)
            progress.setAutoReset(False)
            
            # Style
            progress_font = QFont()
            progress_font.setPointSize(12)
            progress.setFont(progress_font)
            
            # Cancel 버튼 중앙 정렬
            from PyQt6.QtWidgets import QPushButton
            from PyQt6.QtCore import Qt as QtCore
            
            cancel_btn = None
            for child in progress.findChildren(QPushButton):
                if child.text() == "취소":
                    cancel_btn = child
                    break
            
            if cancel_btn:
                cancel_btn.setStyleSheet("""
                    QPushButton {
                        margin-top: 15px;
                        padding: 8px 40px;
                        min-width: 100px;
                    }
                """)
                if cancel_btn.parent() and cancel_btn.parent().layout():
                    layout = cancel_btn.parent().layout()
                    if hasattr(layout, 'setAlignment'):
                        layout.setAlignment(cancel_btn, QtCore.AlignCenter)
            
            # Create worker
            worker = FolderUploadWorker(uploader, folder, self.current_topic_id)
            
            # 1초마다 상태 업데이트
            update_timer = QTimer(self)
            
            def update_progress():
                if worker.isRunning():
                    status = worker.get_status()
                    progress.setLabelText(status)
            
            update_timer.timeout.connect(update_progress)
            update_timer.start(1000)  # 1초마다
            
            # Connect signals
            def on_finished(stats):
                update_timer.stop()
                progress.close()
                
                msg = (
                    f"처리 완료: {stats['processed_files']}/{stats['total_files']} 파일\n"
                    f"총 청크: {stats['total_chunks']}\n"
                    f"소요 시간: {stats['elapsed_seconds']:.2f}초"
                )
                
                if stats.get('skipped_files', 0) > 0:
                    msg += f"\n\n건너뛴 중복 파일: {stats['skipped_files']}개"
                
                if stats.get('errors'):
                    msg += f"\n\n오류: {len(stats['errors'])}개"
                
                QMessageBox.information(self, "업로드 완료", msg)
                self._load_documents(self.current_topic_id)
            
            def on_error(error_msg):
                update_timer.stop()
                progress.close()
                QMessageBox.critical(self, "업로드 오류", f"폴더 업로드 실패: {error_msg}")
            
            def on_cancel():
                update_timer.stop()
                worker.cancel()
            
            worker.finished.connect(on_finished)
            worker.error.connect(on_error)
            progress.canceled.connect(on_cancel)
            
            # Start worker
            progress.show()
            worker.start()
            self._upload_worker = worker  # Keep reference
            self._update_timer = update_timer  # Keep reference
            
        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Upload failed: {e}")
    

    
    def _on_search(self):
        """Open search dialog"""
        try:
            self._lazy_init()
            
            # 선택된 토픽 전달
            selected_topic = self.current_topic_id
            if selected_topic:
                logger.info(f"[SEARCH] Opening search dialog with topic: {selected_topic}")
            else:
                logger.info(f"[SEARCH] Opening search dialog without topic filter")
            
            dialog = SearchDialog(self.storage, self.embeddings, self, selected_topic)
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
        stylesheet = RAGManagementStyles.get_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def update_theme(self):
        """테마 변경 시 호출되는 메서드"""
        self._apply_theme()
        self.repaint()
        self.update()
    
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
    
    def _get_current_embedding_model(self) -> str:
        """현재 임베딩 모델 ID 반환"""
        try:
            from core.rag.config.rag_config_manager import RAGConfigManager
            config_manager = RAGConfigManager()
            return config_manager.get_current_embedding_model()
        except Exception as e:
            logger.warning(f"Failed to get current embedding model: {e}")
            from core.rag.constants import DEFAULT_EMBEDDING_MODEL
            return DEFAULT_EMBEDDING_MODEL
    
    def _on_optimize_db(self):
        """Optimize vector database (비동기)"""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "DB 최적화",
            "삭제된 데이터를 물리적으로 정리합니다.\n시간이 걸릴 수 있습니다. 계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._start_optimize_worker()
    
    def _start_optimize_worker(self):
        """Start optimize worker thread"""
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class OptimizeWorker(QThread):
            finished = pyqtSignal(dict)
            error = pyqtSignal(str)
            
            def __init__(self, storage):
                super().__init__()
                self.storage = storage
            
            def run(self):
                try:
                    result = self.storage.optimize_vector_db()
                    self.finished.emit(result)
                except Exception as e:
                    self.error.emit(str(e))
        
        # Progress dialog
        progress = QProgressDialog(self)
        progress.setWindowTitle("🧹 벡터DB 최적화 중")
        progress.setLabelText("⏳ 삭제된 데이터 정리 중...\n\n잠시만 기다려주세요...")
        progress.setCancelButton(None)  # 취소 불가
        progress.setRange(0, 0)  # 무한 프로그레스바
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumSize(400, 150)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        
        # Style
        progress_font = QFont()
        progress_font.setPointSize(12)
        progress.setFont(progress_font)
        
        # Worker
        worker = OptimizeWorker(self.storage)
        
        def on_finished(result):
            progress.close()
            if result.get("success"):
                stats = result.get("cleanup_stats", {})
                msg = "✅ 벡터DB 최적화 완료!\n\n"
                if stats:
                    msg += f"정리된 버전: {stats}\n"
                msg += "디스크 공간이 확보되었습니다."
                QMessageBox.information(self, "최적화 완료", msg)
            else:
                error = result.get("error", "Unknown error")
                QMessageBox.warning(self, "최적화 실패", f"최적화 중 오류 발생:\n{error}")
        
        def on_error(error_msg):
            progress.close()
            QMessageBox.critical(self, "오류", f"최적화 실패:\n{error_msg}")
        
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        
        progress.show()
        worker.start()
        self._optimize_worker = worker  # Keep reference
    
    def _refresh_all(self):
        """전체 새로고침 (모델 변경 반영)"""
        try:
            # 임베딩 풀 캐시 클리어 (모델 변경 시)
            from core.rag.embeddings.embedding_pool import embedding_pool
            embedding_pool.clear_cache()
            logger.info("[REFRESH] Cleared embedding cache")
            
            # 강제 초기화 리셋
            self._initialized = False
            self.embeddings = None
            self.storage = None
            
            logger.info("[REFRESH] Force reset RAG components")
            
            # 임베딩 모델 새로고침
            self._lazy_init()
            
            # 토픽 새로고침
            self._load_topics()
            
            logger.info("[REFRESH] RAG management refreshed (model changes applied)")
        except Exception as e:
            logger.error(f"Failed to refresh: {e}")
    
    def _on_settings(self):
        """설정 다이얼로그 열기"""
        from ui.dialogs.rag_settings_dialog import RAGSettingsDialog
        
        dialog = RAGSettingsDialog(self)
        result = dialog.exec()
        
        # 다이얼로그 닫힘 후 윈도우 다시 활성화
        self.activateWindow()
        self.raise_()
        
        if result:
            # 설정 변경 후 새로고침
            self._refresh_all()
