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
    
    def __init__(self, storage_manager, embeddings, parent=None):
        """
        Initialize search dialog
        
        Args:
            storage_manager: RAGStorageManager instance
            embeddings: Embedding model
            parent: Parent widget
        """
        super().__init__(parent)
        self.storage = storage_manager
        self.embeddings = embeddings
        
        self.setWindowTitle("RAG Search")
        self.setMinimumSize(600, 400)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
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
        
        try:
            # Generate query embedding
            query_vector = self.embeddings.embed_query(query)
            
            # Search
            results = self.storage.search_chunks(
                query=query,
                k=k,
                query_vector=query_vector
            )
            
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
