"""
Google Embeddings Strategy
"""

from typing import List
from core.logging import get_logger
from .base_embeddings import BaseEmbeddings

logger = get_logger("google_embeddings")


class GoogleEmbeddings(BaseEmbeddings):
    """Google Embeddings (embedding-001)"""
    
    def __init__(self, api_key: str, model: str = "embedding-001"):
        """
        Initialize Google embeddings
        
        Args:
            api_key: Google API key
            model: Model name (embedding-001)
        """
        self.api_key = api_key
        self.model = model
        self._dimension = 768
        self.client = None
        self._load_client()
        logger.info(f"Google embeddings initialized: {model}")
    
    def _load_client(self):
        """Load Google client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai
        except ImportError:
            logger.error("google-generativeai package not installed")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Google client: {e}")
            self.client = None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        if not self.client:
            logger.warning("Google client not available")
            return [[0.0] * self._dimension for _ in texts]
        
        try:
            results = []
            for text in texts:
                result = self.client.embed_content(
                    model=f"models/{self.model}",
                    content=text,
                    task_type="retrieval_document"
                )
                results.append(result['embedding'])
            return results
        except Exception as e:
            logger.error(f"Google embedding failed: {e}")
            return [[0.0] * self._dimension for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        if not self.client:
            logger.warning("Google client not available")
            return [0.0] * self._dimension
        
        try:
            result = self.client.embed_content(
                model=f"models/{self.model}",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Google query embedding failed: {e}")
            return [0.0] * self._dimension
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension
