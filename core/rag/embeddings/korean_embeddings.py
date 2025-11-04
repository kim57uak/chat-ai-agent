"""
Korean Embeddings Implementation
dragonkue/KoEn-E5-Tiny 모델 사용
"""

from typing import List
from core.logging import get_logger
from .base_embeddings import BaseEmbeddings

logger = get_logger("korean_embeddings")


class KoreanEmbeddings(BaseEmbeddings):
    """한국어 임베딩 모델 (exp-models/dragonkue-KoEn-E5-Tiny)"""
    
    def __init__(self, model_name: str = "exp-models/dragonkue-KoEn-E5-Tiny", cache_folder: str = None):
        """
        Initialize Korean embeddings
        
        Args:
            model_name: HuggingFace model name
            cache_folder: Cache directory
        """
        self.model_name = model_name
        self.cache_folder = cache_folder
        self.model = None
        self._dimension = 384  # multilingual-e5-small dimension
        
        self._load_model()
        logger.info(f"Korean embeddings initialized: {model_name}")
    
    def _load_model(self):
        """Load embedding model (lazy loading)"""
        try:
            from sentence_transformers import SentenceTransformer
            from pathlib import Path
            import sys
            
            # 로컬 모델 경로 결정
            if getattr(sys, 'frozen', False):
                # 패키징된 앱
                if sys.platform == 'darwin':
                    base_path = Path(sys.executable).parent.parent / 'Resources'
                else:
                    base_path = Path(sys.executable).parent
            else:
                # 개발 환경
                base_path = Path(__file__).parent.parent.parent.parent
            
            local_model_path = base_path / "models" / "embeddings" / "dragonkue-KoEn-E5-Tiny"
            
            # 로컬 모델이 있으면 사용, 없으면 HuggingFace에서 다운로드
            if local_model_path.exists():
                model_path = str(local_model_path)
                logger.info(f"Loading local model from: {model_path}")
            else:
                model_path = self.model_name
                logger.info(f"Loading model from HuggingFace: {model_path}")
            
            self.model = SentenceTransformer(
                model_path,
                cache_folder=self.cache_folder
            )
            logger.info(f"Loaded model: {model_path}")
            
        except ImportError:
            logger.warning("sentence-transformers not installed, using mock mode")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents
        
        Args:
            texts: List of text documents
            
        Returns:
            List of embedding vectors
        """
        if not self.model:
            logger.warning("Model not available, returning zero vectors")
            return [[0.0] * self._dimension for _ in texts]
        
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            logger.debug(f"Embedded {len(texts)} documents")
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return [[0.0] * self._dimension for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query
        
        Args:
            text: Query text
            
        Returns:
            Embedding vector
        """
        if not self.model:
            logger.warning("Model not available, returning zero vector")
            return [0.0] * self._dimension
        
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            logger.debug(f"Embedded query: {text[:50]}")
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            return [0.0] * self._dimension
    
    @property
    def dimension(self) -> int:
        """
        Get embedding dimension
        
        Returns:
            Dimension size (384 for E5-Tiny)
        """
        return self._dimension
