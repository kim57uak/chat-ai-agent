"""
OpenAI Embeddings Strategy
"""

from typing import List
from core.logging import get_logger
from .base_embeddings import BaseEmbeddings

logger = get_logger("openai_embeddings")


class OpenAIEmbeddings(BaseEmbeddings):
    """OpenAI Embeddings (text-embedding-3-small/large)"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embeddings
        
        Args:
            api_key: OpenAI API key
            model: Model name (text-embedding-3-small or text-embedding-3-large)
        """
        self.api_key = api_key
        self.model = model
        self._dimension = 1536 if "small" in model else 3072
        self.client = None
        self._load_client()
        logger.info(f"OpenAI embeddings initialized: {model}")
    
    def _load_client(self):
        """Load OpenAI client"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            logger.error("openai package not installed")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        if not self.client:
            logger.warning("OpenAI client not available")
            return [[0.0] * self._dimension for _ in texts]
        
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return [[0.0] * self._dimension for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        if not self.client:
            logger.warning("OpenAI client not available")
            return [0.0] * self._dimension
        
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI query embedding failed: {e}")
            return [0.0] * self._dimension
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension
