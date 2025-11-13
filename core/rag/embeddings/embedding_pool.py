"""
Embedding Model Pool (Singleton)
임베딩 모델 캐싱으로 매번 초기화 방지
"""

from typing import Dict, Optional
from threading import Lock
from core.logging import get_logger

logger = get_logger("embedding_pool")


class EmbeddingPool:
    """임베딩 모델 풀 (싱글톤)"""
    
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
        
        self._models: Dict[str, any] = {}  # model_id -> Embeddings
        self._initialized = True
        logger.info("EmbeddingPool initialized")
    
    def get_embeddings(self, model_id: Optional[str] = None) -> any:
        """
        Get or create embeddings for model
        
        Args:
            model_id: Embedding model ID (None for current)
            
        Returns:
            Embeddings instance
        """
        if model_id is None:
            model_id = self._get_current_model_id()
        
        # 캐시된 모델 반환
        if model_id in self._models:
            logger.debug(f"Reusing cached embeddings for: {model_id}")
            return self._models[model_id]
        
        # 새 모델 생성 및 캐시
        with self._lock:
            if model_id not in self._models:
                from .embedding_factory import EmbeddingFactory
                embeddings = EmbeddingFactory.create_embeddings()
                self._models[model_id] = embeddings
                logger.info(f"Created new embeddings for: {model_id}")
        
        return self._models[model_id]
    
    def clear_cache(self, model_id: Optional[str] = None):
        """
        Clear cached embeddings
        
        Args:
            model_id: Specific model to clear (None for all)
        """
        with self._lock:
            if model_id:
                if model_id in self._models:
                    del self._models[model_id]
                    logger.info(f"Cleared embeddings cache for: {model_id}")
            else:
                self._models.clear()
                logger.info("Cleared all embeddings cache")
    
    def _get_current_model_id(self) -> str:
        """Get current embedding model ID"""
        try:
            from .embedding_model_manager import EmbeddingModelManager
            manager = EmbeddingModelManager()
            return manager.get_current_model()
        except Exception as e:
            logger.warning(f"Failed to get current model: {e}")
            from ..constants import DEFAULT_EMBEDDING_MODEL
            return DEFAULT_EMBEDDING_MODEL


# 전역 싱글톤 인스턴스
embedding_pool = EmbeddingPool()
