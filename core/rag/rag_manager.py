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
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        self._init_components()
    
    def _init_components(self):
        """Initialize components"""
        try:
            # Embeddings 초기화
            from core.rag.embeddings.korean_embeddings import KoreanEmbeddings
            self.embeddings = KoreanEmbeddings()
            logger.info("Embeddings initialized")
            
            # Vector store 초기화 (None이면 자동으로 사용자 경로 사용)
            from core.rag.vector_store.lancedb_store import LanceDBStore
            self.vectorstore = LanceDBStore(db_path=self.db_path)
            logger.info("Vector store initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
    
    def add_document(self, file_path: str) -> bool:
        """
        Add document to RAG system
        
        Args:
            file_path: Document file path
            
        Returns:
            Success status
        """
        try:
            # 문서 로드
            from core.rag.loaders.document_loader_factory import DocumentLoaderFactory
            documents = DocumentLoaderFactory.load_document(file_path)
            
            if not documents:
                logger.warning(f"No documents loaded from {file_path}")
                return False
            
            # 청크 분할
            chunks = []
            for doc in documents:
                split_docs = self.text_splitter.split_documents([doc])
                chunks.extend(split_docs)
            
            logger.info(f"Split into {len(chunks)} chunks")
            
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
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Search similar documents
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of similar documents
        """
        try:
            if not self.vectorstore or not self.embeddings:
                logger.warning("RAG components not initialized")
                return []
            
            # 쿼리 임베딩
            query_vector = self.embeddings.embed_query(query)
            
            # 검색
            results = self.vectorstore.search(
                query,
                k=k,
                query_vector=query_vector
            )
            
            logger.info(f"Found {len(results)} results for: {query[:50]}")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if RAG system is available"""
        return self.vectorstore is not None and self.embeddings is not None
