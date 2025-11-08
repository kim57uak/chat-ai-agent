"""
Base Chunker Interface
"""

from abc import ABC, abstractmethod
from typing import List
from langchain.schema import Document


class BaseChunker(ABC):
    """청킹 전략 추상 인터페이스"""
    
    @abstractmethod
    def chunk(self, text: str, metadata: dict = None) -> List[Document]:
        """
        Split text into chunks
        
        Args:
            text: Input text
            metadata: Metadata to attach to chunks
            
        Returns:
            List of Document chunks
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name"""
        pass
