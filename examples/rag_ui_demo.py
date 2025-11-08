"""
RAG UI Demo
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from ui.rag.rag_management_window import RAGManagementWindow
from core.rag.storage.rag_storage_manager import RAGStorageManager
from core.rag.embeddings.embedding_factory import EmbeddingFactory
from core.rag.config.rag_config_manager import RAGConfigManager


def main():
    """Run RAG UI demo"""
    app = QApplication(sys.argv)
    
    # Initialize
    config_manager = RAGConfigManager()
    embedding_config = config_manager.get_embedding_config()
    
    embedding_type = embedding_config.pop('type')
    embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)
    
    storage = RAGStorageManager()
    
    # Create window
    window = RAGManagementWindow(storage, embeddings)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
