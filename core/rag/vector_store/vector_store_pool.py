"""
Vector Store Connection Pool (Singleton)
"""

from typing import Dict, Optional
from threading import Lock
from core.logging import get_logger

logger = get_logger("vector_store_pool")


class VectorStorePool:
    """벡터 스토어 커넥션 풀 (싱글톤)"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._stores: Dict[str, any] = {}  # model_id -> LanceDBStore
        self._initialized = True
        logger.info("VectorStorePool initialized")
    
    def get_store(self, model_id: Optional[str] = None) -> any:
        """
        Get or create vector store for model
        
        Args:
            model_id: Embedding model ID (None for current)
            
        Returns:
            LanceDBStore instance
        """
        if model_id is None:
            model_id = self._get_current_model_id()
        
        # 캐시된 스토어 반환
        if model_id in self._stores:
            logger.debug(f"Reusing cached store for model: {model_id}")
            return self._stores[model_id]
        
        # 새 스토어 생성 및 캐시
        with self._lock:
            if model_id not in self._stores:
                from .lancedb_store import LanceDBStore
                store = LanceDBStore()
                self._stores[model_id] = store
                logger.info(f"Created new store for model: {model_id}")
        
        return self._stores[model_id]
    
    def clear_cache(self):
        """Clear all cached stores"""
        with self._lock:
            self._stores.clear()
            logger.info("Cleared vector store cache")
    
    def _get_current_model_id(self) -> str:
        """Get current embedding model ID"""
        try:
            from ..embeddings.embedding_model_manager import EmbeddingModelManager
            manager = EmbeddingModelManager()
            return manager.get_current_model()
        except Exception as e:
            logger.warning(f"Failed to get current model: {e}")
            from ..constants import DEFAULT_EMBEDDING_MODEL
            return DEFAULT_EMBEDDING_MODEL


# 전역 싱글톤 인스턴스
vector_store_pool = VectorStorePool()
