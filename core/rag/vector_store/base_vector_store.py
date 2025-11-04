"""
Base Vector Store Interface
Strategy 패턴: 벡터 DB 추상화
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain.schema import Document


class BaseVectorStore(ABC):
    """벡터 스토어 추상 인터페이스"""
    
    @abstractmethod
    def add_documents(self, documents: List[Document], **kwargs) -> List[str]:
        """
        Add documents to vector store
        
        Args:
            documents: List of LangChain Document objects
            **kwargs: Additional parameters
            
        Returns:
            List of document IDs
        """
        pass
    
    @abstractmethod
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
            **kwargs: Additional parameters
            
        Returns:
            List of similar documents
        """
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """
        Delete documents by IDs
        
        Args:
            ids: List of document IDs
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Get document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document or None
        """
        pass
    
    @abstractmethod
    def update_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update document metadata
        
        Args:
            doc_id: Document ID
            metadata: New metadata
            
        Returns:
            Success status
        """
        pass
