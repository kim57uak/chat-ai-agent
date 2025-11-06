"""
LanceDB Vector Store Implementation
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain.schema import Document
from core.logging import get_logger
from .base_vector_store import BaseVectorStore

logger = get_logger("lancedb_store")


class LanceDBStore(BaseVectorStore):
    """LanceDB 벡터 스토어 구현"""
    
    def __init__(self, db_path: Optional[str] = None, table_name: str = "documents"):
        """
        Initialize LanceDB store
        
        Args:
            db_path: Database path (None for default user config path)
            table_name: Table name
        """
        if db_path is None:
            db_path = self._get_default_db_path()
        
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.db = None
        self.table = None
        
        self._init_database()
        logger.info(f"LanceDB initialized: {db_path}/{table_name}")
    
    def _get_default_db_path(self) -> str:
        """기본 벡터 DB 경로 반환 (SQLite와 동일한 로직)"""
        try:
            # 지연 import로 순환 참조 방지
            from utils.config_path import config_path_manager
            
            # 사용자 설정 경로가 있으면 사용 (vectordb 폴더)
            user_config_path = config_path_manager.get_user_config_path()
            if user_config_path and user_config_path.exists():
                db_path = user_config_path / "vectordb"
                db_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Using user-configured vector DB path: {db_path}")
                return str(db_path)
            else:
                logger.info("No user config path set, using default")
        except ImportError as e:
            logger.warning(f"config_path_manager not available: {e}")
        except AttributeError as e:
            logger.warning(f"config_path_manager not initialized: {e}")
        except Exception as e:
            logger.warning(f"Failed to get user config path: {e}")
        
        # 폴백: 기본 외부 경로
        import os
        
        if os.name == "nt":  # Windows
            data_dir = Path.home() / "AppData" / "Local" / "ChatAIAgent" / "vectordb"
        else:  # macOS, Linux
            data_dir = Path.home() / ".chat-ai-agent" / "vectordb"
        
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using default vector DB path: {data_dir}")
        return str(data_dir)
    
    def _init_database(self):
        """Initialize database (lazy loading)"""
        try:
            import lancedb
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db = lancedb.connect(str(self.db_path))
            logger.info(f"Connected to LanceDB at {self.db_path}")
        except ImportError as e:
            logger.error(f"lancedb not installed: {e}")
            self.db = None
        except Exception as e:
            logger.error(f"Failed to connect to LanceDB: {e}", exc_info=True)
            self.db = None
    
    def add_documents(self, documents: List[Document], **kwargs) -> List[str]:
        """
        Add documents to LanceDB
        
        Args:
            documents: List of documents
            **kwargs: Additional parameters (embeddings, etc.)
            
        Returns:
            List of document IDs
        """
        if self.db is None:
            logger.error(f"LanceDB not available: db={self.db}, db_path={self.db_path}")
            return []
        
        try:
            # 문서를 LanceDB 형식으로 변환
            data = []
            doc_ids = []
            
            for i, doc in enumerate(documents):
                doc_id = f"doc_{i}_{hash(doc.page_content)}"
                doc_ids.append(doc_id)
                
                data.append({
                    "id": doc_id,
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "vector": kwargs.get("embeddings", [None])[i] if "embeddings" in kwargs else None
                })
            
            # 테이블이 없으면 생성
            if self.table_name not in self.db.table_names():
                self.table = self.db.create_table(self.table_name, data)
            else:
                self.table = self.db.open_table(self.table_name)
                self.table.add(data)
            
            logger.info(f"Added {len(documents)} documents to LanceDB")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return []
    
    def search(
        self, 
        query: str, 
        k: int = 5, 
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Document]:
        """
        Search similar documents
        
        Args:
            query: Search query
            k: Number of results
            filter: Metadata filter
            **kwargs: query_vector for vector search
            
        Returns:
            List of similar documents
        """
        if self.db is None:
            logger.warning("LanceDB not available, returning empty results")
            return []
        
        # 테이블 열기 시도
        if self.table is None and self.table_name in self.db.table_names():
            self.table = self.db.open_table(self.table_name)
        
        if self.table is None:
            logger.warning(f"Table {self.table_name} not found, returning empty results")
            return []
        
        try:
            # 벡터 검색
            if "query_vector" in kwargs and kwargs["query_vector"]:
                results = self.table.search(kwargs["query_vector"]).limit(k)
            else:
                # 텍스트 검색 비활성화 (INVERTED 인덱스 필요)
                logger.warning("Vector search requires query_vector, returning empty results")
                return []
            
            # 메타데이터 필터 적용
            if filter:
                results = results.where(self._build_filter_expression(filter))
            
            # Document 객체로 변환
            documents = []
            for row in results.to_list():
                doc = Document(
                    page_content=row.get("text", ""),
                    metadata=row.get("metadata", {})
                )
                documents.append(doc)
            
            logger.info(f"Found {len(documents)} documents for query: {query[:50]}")
            return documents
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete(self, ids: List[str]) -> bool:
        """
        Delete documents by IDs
        
        Args:
            ids: List of document IDs
            
        Returns:
            Success status
        """
        if not self.table:
            logger.error("Table not available for delete")
            return False
        
        if not ids:
            logger.warning("No IDs provided for delete")
            return False
        
        try:
            # LanceDB delete 문법: "id IN ('id1', 'id2', 'id3')"
            ids_str = ", ".join([f"'{id}'" for id in ids])
            delete_expr = f"id IN ({ids_str})"
            logger.info(f"Deleting with expression: {delete_expr}")
            
            self.table.delete(delete_expr)
            logger.info(f"Successfully deleted {len(ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}", exc_info=True)
            return False
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Get document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document or None
        """
        if not self.table:
            return None
        
        try:
            results = self.table.search().where(f"id = '{doc_id}'").limit(1).to_list()
            if results:
                row = results[0]
                return Document(
                    page_content=row.get("text", ""),
                    metadata=row.get("metadata", {})
                )
        except Exception as e:
            logger.error(f"Get document failed: {e}")
        
        return None
    
    def update_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update document metadata
        
        Args:
            doc_id: Document ID
            metadata: New metadata
            
        Returns:
            Success status
        """
        if not self.table:
            return False
        
        try:
            # LanceDB는 직접 업데이트를 지원하지 않으므로 삭제 후 재추가
            doc = self.get_document(doc_id)
            if doc:
                doc.metadata.update(metadata)
                self.delete([doc_id])
                self.add_documents([doc])
                logger.info(f"Updated metadata for document {doc_id}")
                return True
        except Exception as e:
            logger.error(f"Update metadata failed: {e}")
        
        return False
    
    def _build_filter_expression(self, filter: Dict[str, Any]) -> str:
        """
        Build filter expression for LanceDB
        
        Args:
            filter: Metadata filter
            
        Returns:
            Filter expression string
        """
        expressions = []
        for key, value in filter.items():
            if isinstance(value, str):
                expressions.append(f"metadata.{key} = '{value}'")
            else:
                expressions.append(f"metadata.{key} = {value}")
        
        return " AND ".join(expressions)
    
    def as_retriever(self, **kwargs):
        """
        Return LangChain-compatible retriever
        
        Args:
            **kwargs: search_kwargs (k, filter, etc.)
            
        Returns:
            Retriever instance
        """
        from langchain.schema.retriever import BaseRetriever
        from langchain.callbacks.manager import CallbackManagerForRetrieverRun
        
        class LanceDBRetriever(BaseRetriever):
            vectorstore: Any
            search_kwargs: Dict[str, Any] = {}
            
            def _get_relevant_documents(
                self, query: str, *, run_manager: CallbackManagerForRetrieverRun
            ) -> List[Document]:
                # embeddings를 통한 벡터 검색
                from core.rag.embeddings.korean_embeddings import KoreanEmbeddings
                embeddings = KoreanEmbeddings()
                query_vector = embeddings.embed_query(query)
                return self.vectorstore.search(query, query_vector=query_vector, **self.search_kwargs)
        
        return LanceDBRetriever(vectorstore=self, search_kwargs=kwargs.get('search_kwargs', {}))
