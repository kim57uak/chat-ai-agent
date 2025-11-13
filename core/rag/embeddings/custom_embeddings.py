"""
Custom Embeddings Strategy
사용자 정의 임베딩 모델
"""

from typing import List
from core.logging import get_logger
from .base_embeddings import BaseEmbeddings

logger = get_logger("custom_embeddings")


class CustomEmbeddings(BaseEmbeddings):
    """사용자 정의 임베딩 (HuggingFace SentenceTransformer)"""
    
    def __init__(self, model_path: str, dimension: int = 768, enable_cache: bool = True, **kwargs):
        """
        Initialize custom embeddings
        
        Args:
            model_path: HuggingFace 모델 경로 (로컬 또는 HF Hub)
            dimension: 임베딩 차원
            enable_cache: 캐시 사용 여부
            **kwargs: 추가 파라미터
        """
        self.model_path = model_path
        self._dimension = dimension
        self.enable_cache = enable_cache
        self.model = None
        self._load_model(**kwargs)
        logger.info(f"Custom embeddings initialized: {model_path}")
    
    def _load_model(self, **kwargs):
        """HuggingFace SentenceTransformer 모델 로드"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_path)
            logger.info(f"Loaded SentenceTransformer: {self.model_path}")
        except ImportError:
            logger.error("sentence-transformers not installed. Install: pip install sentence-transformers")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서 임베딩"""
        if not self.model:
            logger.warning("Model not available, returning zero vectors")
            return [[0.0] * self._dimension for _ in texts]
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return [[0.0] * self._dimension for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """쿼리 임베딩"""
        if not self.model:
            logger.warning("Model not available, returning zero vector")
            return [0.0] * self._dimension
        
        try:
            embedding = self.model.encode([text], convert_to_numpy=True)[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            return [0.0] * self._dimension
    
    @property
    def dimension(self) -> int:
        """임베딩 차원"""
        return self._dimension
