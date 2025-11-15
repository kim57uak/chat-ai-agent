"""
RAG Manager
RAG 시스템 통합 관리자
"""

from typing import List, Optional
from pathlib import Path
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from core.logging import get_logger

logger = get_logger("rag_manager")


class RAGManager:
    """RAG 시스템 통합 관리자"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize RAG Manager
        
        Args:
            db_path: Vector database path (None for auto-detection)
        """
        # LanceDBStore가 자동으로 경로를 찾도록 None 전달
        self.db_path = db_path
        self.vectorstore = None
        self.embeddings = None
        self.storage = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        self._init_components()
    
    def _init_components(self):
        """Initialize components"""
        try:
            # Embeddings 초기화 (설정된 모델 사용)
            from core.rag.embeddings.embedding_factory import EmbeddingFactory
            self.embeddings = EmbeddingFactory.create_embeddings()
            logger.info("Embeddings initialized")
            
            # Vector store 초기화 (현재 모델에 맞는 테이블 사용)
            from core.rag.vector_store.lancedb_store import LanceDBStore
            from core.rag.embeddings.embedding_model_manager import EmbeddingModelManager
            
            manager = EmbeddingModelManager()
            table_name = manager.get_table_name()
            
            self.vectorstore = LanceDBStore(db_path=self.db_path, table_name=table_name)
            logger.info("Vector store initialized")
            
            # Storage manager 초기화
            from core.rag.storage.rag_storage_manager import RAGStorageManager
            self.storage = RAGStorageManager(lazy_load_vector=True)
            logger.info("Storage manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
    
    def add_document(self, file_path: str) -> bool:
        """
        Add document to RAG system with proper chunking strategy
        
        Args:
            file_path: Document file path
            
        Returns:
            Success status
        """
        try:
            # 문서 로드 (청킹 전략 자동 적용)
            from core.rag.loaders.document_loader_factory import DocumentLoaderFactory
            chunks = DocumentLoaderFactory.load_document(file_path)
            
            if not chunks:
                logger.warning(f"No chunks loaded from {file_path}")
                return False
            
            logger.info(f"Loaded {len(chunks)} chunks with auto-chunking strategy")
            
            # 임베딩 생성
            texts = [chunk.page_content for chunk in chunks]
            embeddings = self.embeddings.embed_documents(texts)
            
            # Vector store에 추가
            doc_ids = self.vectorstore.add_documents(
                chunks,
                embeddings=embeddings
            )
            
            logger.info(f"Added {len(doc_ids)} chunks to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def search(self, query: str, k: int = 5, topic_id: Optional[str] = None) -> List[Document]:
        """
        Search similar documents
        
        Args:
            query: Search query
            k: Number of results
            topic_id: Optional topic filter (None = use selected topic)
            
        Returns:
            List of similar documents
        """
        try:
            if not self.vectorstore or not self.embeddings:
                logger.warning("RAG components not initialized")
                return []
            
            # topic_id가 없으면 선택된 topic 사용
            if topic_id is None and self.storage:
                selected_topic = self.storage.get_selected_topic()
                if selected_topic:
                    topic_id = selected_topic['id']
                    logger.info(f"Using selected topic: {selected_topic['name']}")
            
            # 쿼리 임베딩
            query_vector = self.embeddings.embed_query(query)
            
            # 검색 (항상 storage.search_chunks 사용 - Reranker 자동 적용)
            results = self.storage.search_chunks(
                query,
                k=k,
                topic_id=topic_id,  # None이면 전체 검색
                query_vector=query_vector
            )
            
            if topic_id:
                logger.info(f"Found {len(results)} results in topic {topic_id} for: {query[:50]}")
            else:
                logger.info(f"Found {len(results)} results (all topics) for: {query[:50]}")
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if RAG system is available"""
        return self.vectorstore is not None and self.embeddings is not None
    
    def get_current_model_info(self) -> dict:
        """현재 사용 중인 임베딩 모델 정보 반환"""
        if hasattr(self.embeddings, 'get_model_info'):
            return self.embeddings.get_model_info()
        else:
            return {
                "model_name": "Unknown",
                "dimension": getattr(self.embeddings, 'dimension', 0)
            }
    
    def refresh_embeddings(self):
        """임베딩 모델 새로고침 (모델 변경 시 호출)"""
        try:
            from core.rag.embeddings.embedding_factory import EmbeddingFactory
            from core.rag.embeddings.embedding_model_manager import EmbeddingModelManager
            
            # 새 임베딩 모델 로드
            self.embeddings = EmbeddingFactory.create_embeddings()
            
            # 새 테이블로 벡터 스토어 업데이트
            manager = EmbeddingModelManager()
            table_name = manager.get_table_name()
            
            if self.vectorstore:
                self.vectorstore.table_name = table_name
                # 테이블 재초기화
                self.vectorstore.table = None
                if self.vectorstore.db and table_name in self.vectorstore.db.table_names():
                    self.vectorstore.table = self.vectorstore.db.open_table(table_name)
                    logger.info(f"Switched to table: {table_name}")
                else:
                    logger.info(f"Table {table_name} not found, will be created when needed")
            
            logger.info("Embeddings refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh embeddings: {e}")
            return False
