"""
RAG Search Dialog
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit, QSpinBox)
from PyQt6.QtCore import Qt
from core.logging import get_logger

logger = get_logger("search_dialog")


class SearchDialog(QDialog):
    """RAG 검색 다이얼로그"""
    
    def __init__(self, storage_manager, embeddings, parent=None, selected_topic_id=None):
        """
        Initialize search dialog
        
        Args:
            storage_manager: RAGStorageManager instance
            embeddings: Embedding model
            parent: Parent widget
            selected_topic_id: Currently selected topic ID for filtering
        """
        super().__init__(parent)
        self.storage = storage_manager
        self.embeddings = embeddings
        self.selected_topic_id = selected_topic_id
        
        self.setWindowTitle("RAG Search")
        self.setMinimumSize(600, 400)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Topic info
        if self.selected_topic_id:
            topic_label = QLabel(f"📁 검색 범위: Topic {self.selected_topic_id}")
            topic_label.setStyleSheet("color: #1976d2; font-weight: bold; padding: 5px;")
            layout.addWidget(topic_label)
        else:
            topic_label = QLabel("🌍 검색 범위: 전체 토픽")
            topic_label.setStyleSheet("color: #666; padding: 5px;")
            layout.addWidget(topic_label)
        
        # Query input
        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel("Query:"))
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter search query")
        self.query_input.returnPressed.connect(self._on_search)
        query_layout.addWidget(self.query_input)
        layout.addLayout(query_layout)
        
        # Options
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Results:"))
        self.k_spin = QSpinBox()
        self.k_spin.setRange(1, 20)
        self.k_spin.setValue(5)
        options_layout.addWidget(self.k_spin)
        options_layout.addStretch()
        
        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self._on_search)
        options_layout.addWidget(search_btn)
        layout.addLayout(options_layout)
        
        # Results
        layout.addWidget(QLabel("Results:"))
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
    
    def _on_search(self):
        """Perform search"""
        query = self.query_input.text().strip()
        if not query:
            return
        
        k = self.k_spin.value()
        
        # 디버그: 콘솔에도 출력
        print("\n" + "="*60)
        print(f"[SEARCH DIALOG] RAG Search Started")
        print(f"[SEARCH DIALOG] Query: '{query}'")
        print(f"[SEARCH DIALOG] Top-K: {k}")
        print(f"[SEARCH DIALOG] Topic ID: {self.selected_topic_id}")
        print(f"[SEARCH DIALOG] Storage type: {type(self.storage).__name__}")
        print("="*60)
        
        try:
            logger.info("="*60)
            logger.info(f"[SEARCH DIALOG] RAG Search Started")
            logger.info(f"[SEARCH DIALOG] Query: '{query}'")
            logger.info(f"[SEARCH DIALOG] Top-K: {k}")
            logger.info(f"[SEARCH DIALOG] Topic ID: {self.selected_topic_id}")
            logger.info("="*60)
            
            # Generate query embedding
            logger.info(f"[SEARCH DIALOG] Step 1: Generating embedding...")
            query_vector = self.embeddings.embed_query(query)
            logger.info(f"[SEARCH DIALOG] ✓ Embedding generated (dimension: {len(query_vector)})")
            
            # Search with topic filter (Reranker will be applied automatically)
            logger.info(f"[SEARCH DIALOG] Step 2: Calling search_chunks()...")
            print(f"[SEARCH DIALOG] Step 2: Calling search_chunks()...")
            
            results = self.storage.search_chunks(
                query=query,
                k=k,
                topic_id=self.selected_topic_id,
                query_vector=query_vector
            )
            
            print(f"[SEARCH DIALOG] ✓ Search complete: {len(results)} results returned")
            logger.info(f"[SEARCH DIALOG] ✓ Search complete: {len(results)} results returned")
            logger.info("="*60)
            
            # Display results
            if results:
                output = f"Found {len(results)} results:\n\n"
                for i, doc in enumerate(results, 1):
                    output += f"--- Result {i} ---\n"
                    output += f"{doc.page_content[:200]}...\n"
                    output += f"Metadata: {doc.metadata}\n\n"
            else:
                output = "No results found."
            
            self.results_text.setPlainText(output)
            logger.info(f"Search completed: {len(results)} results")
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.results_text.setPlainText(f"Error: {e}")
