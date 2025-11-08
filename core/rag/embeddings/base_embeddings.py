"""
Base Embeddings Interface
Strategy 패턴: 임베딩 모델 추상화
"""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddings(ABC):
    """임베딩 모델 추상 인터페이스"""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents
        
        Args:
            texts: List of text documents
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query
        
        Args:
            text: Query text
            
        Returns:
            Embedding vector
        """
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Get embedding dimension
        
        Returns:
            Dimension size
        """
        pass
