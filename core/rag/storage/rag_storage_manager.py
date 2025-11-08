"""
RAG Storage Manager
SQLite + LanceDB 통합 관리
"""

from typing import List, Dict, Optional
from pathlib import Path
from core.logging import get_logger
from .topic_database import TopicDatabase
from ..vector_store.lancedb_store import LanceDBStore

logger = get_logger("rag_storage_manager")


class RAGStorageManager:
    """SQLite + LanceDB 통합 관리자"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, sqlite_path: Optional[str] = None, 
                lancedb_path: Optional[str] = None,
                lazy_load_vector: bool = False):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, sqlite_path: Optional[str] = None, 
                 lancedb_path: Optional[str] = None,
                 lazy_load_vector: bool = False):
        if self._initialized:
            if sqlite_path and sqlite_path != getattr(self, '_sqlite_path', None):
                logger.warning(f"RAGStorageManager already initialized with different path")
            return
        
        self._sqlite_path = sqlite_path
        self._lancedb_path = lancedb_path
        """
        Initialize RAG storage manager
        
        Args:
            sqlite_path: SQLite database path (None for auto-detection)
            lancedb_path: LanceDB path (None for auto-detection)
            lazy_load_vector: Lazy load vector store (True for UI operations)
        """
        self.topic_db = TopicDatabase(sqlite_path)
        self.lancedb_path = lancedb_path
        self.vector_store = None if lazy_load_vector else LanceDBStore(lancedb_path)
        self._initialized = True
        logger.info(f"RAG Storage Manager initialized (lazy_vector={lazy_load_vector})")
    
    def _ensure_vector_store(self):
        """Lazy load vector store"""
        if self.vector_store is None:
            self.vector_store = LanceDBStore(self.lancedb_path)
            logger.info("Vector store lazy loaded")
    
    # ========== Topic Operations ==========
    
    def create_topic(self, name: str, parent_id: Optional[str] = None,
                    description: str = "") -> str:
        """Create topic"""
        return self.topic_db.create_topic(name, parent_id, description)
    
    def get_topic(self, topic_id: str) -> Optional[Dict]:
        """Get topic"""
        return self.topic_db.get_topic(topic_id)
    
    def get_all_topics(self) -> List[Dict]:
        """Get all topics"""
        return self.topic_db.get_all_topics()
    
    def get_selected_topic(self) -> Optional[Dict]:
        """Get selected topic"""
        return self.topic_db.get_selected_topic()
    
    def set_selected_topic(self, topic_id: str) -> bool:
        """Set selected topic"""
        return self.topic_db.set_selected_topic(topic_id)
    
    def clear_selected_topic(self) -> bool:
        """Clear selected topic"""
        return self.topic_db.clear_selected_topic()
    
    def update_topic(self, topic_id: str, name: Optional[str] = None,
                    description: Optional[str] = None) -> bool:
        """Update topic"""
        return self.topic_db.update_topic(topic_id, name, description)
    
    def delete_topic(self, topic_id: str, progress_callback=None) -> bool:
        """
        Delete topic with cascading deletion
        
        Deletes:
        1. SQLite documents (100개씩)
        2. LanceDB vectors (100개씩)
        3. Topic itself
        
        Args:
            topic_id: 토픽 ID
            progress_callback: 진행 콜백 (deleted_count, total_count)
        
        Returns:
            Success status
        """
        try:
            # 1. Get all document IDs
            documents = self.topic_db.get_documents_by_topic(topic_id)
            doc_ids = [doc["id"] for doc in documents]
            total_docs = len(doc_ids)
            
            if not doc_ids:
                self.topic_db.conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
                self.topic_db.conn.commit()
                logger.info(f"Empty topic deleted: {topic_id}")
                return True
            
            # 2. Delete in batches of 100
            batch_size = 100
            for i in range(0, total_docs, batch_size):
                batch_ids = doc_ids[i:i+batch_size]
                
                # Delete SQLite documents
                placeholders = ','.join(['?'] * len(batch_ids))
                self.topic_db.conn.execute(
                    f"DELETE FROM documents WHERE id IN ({placeholders})",
                    batch_ids
                )
                self.topic_db.conn.commit()
                
                # Delete LanceDB vectors (without compact)
                self._ensure_vector_store()
                for doc_id in batch_ids:
                    try:
                        if self.vector_store and self.vector_store.table:
                            delete_expr = f"metadata['document_id'] = '{doc_id}'"
                            self.vector_store.table.delete(delete_expr)
                    except Exception as e:
                        logger.warning(f"Vector delete failed for {doc_id}: {e}")
                
                deleted_count = min(i + batch_size, total_docs)
                if progress_callback:
                    progress_callback(deleted_count, total_docs)
                logger.debug(f"삭제 진행: {deleted_count}/{total_docs}")
            
            # 3. Delete topic
            self.topic_db.conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
            self.topic_db.conn.commit()
            
            # 4. Final cleanup - physically remove deleted data
            self._ensure_vector_store()
            try:
                if self.vector_store and self.vector_store.db and self.vector_store.table_name in self.vector_store.db.table_names():
                    table = self.vector_store.db.open_table(self.vector_store.table_name)
                    
                    # Step 1: Compact files to merge fragments
                    table.compact_files()
                    logger.info("Compacted files")
                    
                    # Step 2: Cleanup old versions (no time limit)
                    from datetime import timedelta
                    stats = table.cleanup_old_versions(
                        older_than=timedelta(seconds=0),
                        delete_unverified=True
                    )
                    logger.info(f"Cleanup stats: {stats}")
                    
                    # Step 3: Optimize to physically remove deleted rows
                    table.optimize()
                    logger.info(f"Vector DB optimized after deleting topic {topic_id}")
            except Exception as e:
                logger.error(f"Optimize failed: {e}", exc_info=True)
            
            logger.info(f"Topic deleted: {topic_id}, docs={total_docs}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete topic: {e}", exc_info=True)
            return False
    
    # ========== Document Operations ==========
    
    def create_document(self, topic_id: str, filename: str, file_path: str,
                       file_type: str, file_size: int = 0,
                       chunking_strategy: str = "sliding_window") -> str:
        """Create document metadata"""
        return self.topic_db.create_document(
            topic_id, filename, file_path, file_type, 
            file_size, chunking_strategy
        )
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get document"""
        return self.topic_db.get_document(doc_id)
    
    def get_documents_by_topic(self, topic_id: str) -> List[Dict]:
        """Get documents by topic"""
        return self.topic_db.get_documents_by_topic(topic_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document with cascading deletion
        
        Deletes:
        1. All chunks in LanceDB
        2. Document metadata in SQLite
        
        Returns:
            Success status
        """
        try:
            # 1. Delete vectors without compact
            self._ensure_vector_store()
            if self.vector_store and self.vector_store.table:
                delete_expr = f"metadata['document_id'] = '{doc_id}'"
                self.vector_store.table.delete(delete_expr)
            
            # 2. Delete document metadata
            self.topic_db.delete_document(doc_id)
            
            # 3. Optimize to physically remove deleted data
            self._ensure_vector_store()
            try:
                if self.vector_store and self.vector_store.db and self.vector_store.table_name in self.vector_store.db.table_names():
                    table = self.vector_store.db.open_table(self.vector_store.table_name)
                    
                    # Step 1: Compact files
                    table.compact_files()
                    
                    # Step 2: Cleanup old versions
                    from datetime import timedelta
                    table.cleanup_old_versions(
                        older_than=timedelta(seconds=0),
                        delete_unverified=True
                    )
                    
                    # Step 3: Optimize to physically remove
                    table.optimize()
                    logger.info(f"Vector DB optimized after deleting document {doc_id}")
            except Exception as e:
                logger.error(f"Optimize failed: {e}", exc_info=True)
            
            logger.info(f"Document deleted: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}", exc_info=True)
            return False
    
    # ========== Chunk Operations ==========
    
    def add_chunks(self, doc_id: str, chunks: List, embeddings: List,
                  chunking_strategy: str = "sliding_window") -> List[str]:
        """
        Add chunks to LanceDB with metadata
        
        Args:
            doc_id: Document ID
            chunks: List of Document objects
            embeddings: Pre-computed embeddings
            chunking_strategy: Chunking strategy name
            
        Returns:
            List of chunk IDs
        """
        # Get document info
        doc = self.topic_db.get_document(doc_id)
        if not doc:
            logger.error(f"Document not found: {doc_id}")
            return []
        
        # Add to LanceDB with extended metadata
        self._ensure_vector_store()
        chunk_ids = self.vector_store.add_documents(
            chunks,
            embeddings=embeddings,
            document_id=doc_id,
            topic_id=doc["topic_id"],
            chunking_strategy=chunking_strategy
        )
        
        # Update chunk count in SQLite
        self.topic_db.update_document_chunks(doc_id, len(chunk_ids))
        
        logger.info(f"Added {len(chunk_ids)} chunks for document {doc_id}")
        return chunk_ids
    
    def search_chunks(self, query: str, k: int = 5, 
                     topic_id: Optional[str] = None,
                     query_vector: Optional[List[float]] = None) -> List:
        """
        Search chunks with optional topic filtering
        
        Args:
            query: Search query
            k: Number of results
            topic_id: Optional topic filter
            query_vector: Pre-computed query embedding
            
        Returns:
            List of Document objects
        """
        filter_dict = {"topic_id": topic_id} if topic_id else None
        
        self._ensure_vector_store()
        return self.vector_store.search(
            query,
            k=k,
            filter=filter_dict,
            query_vector=query_vector
        )
    
    # ========== Statistics ==========
    
    def get_statistics(self) -> Dict:
        """Get storage statistics"""
        topics = self.topic_db.get_all_topics()
        
        total_docs = 0
        for topic in topics:
            total_docs += topic.get("document_count", 0)
        
        return {
            "total_topics": len(topics),
            "total_documents": total_docs,
            "topics": topics
        }
    
    def close(self):
        """Close all connections"""
        self.topic_db.close()
        logger.info("RAG Storage Manager closed")
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton (for testing)"""
        cls._instance = None
        cls._initialized = False
