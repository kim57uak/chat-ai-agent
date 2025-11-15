"""
Reranking Retriever
LangChain Retriever with Reranker support
"""

from typing import List, Any
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever
from pydantic import Field
from core.logging import get_logger

logger = get_logger(__name__)


class RerankingRetriever(BaseRetriever):
    """Retriever with automatic reranking support"""
    
    storage_manager: Any = Field(description="RAGStorageManager instance")
    embeddings: Any = Field(description="Embedding model")
    k: int = Field(default=5, description="Number of results to return")
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, storage_manager, embeddings, k: int = 5, **kwargs):
        """
        Initialize reranking retriever
        
        Args:
            storage_manager: RAGStorageManager instance
            embeddings: Embedding model
            k: Number of results to return
        """
        super().__init__(
            storage_manager=storage_manager,
            embeddings=embeddings,
            k=k,
            **kwargs
        )
        logger.info(f"[RERANKING RETRIEVER] Initialized with k={k}")
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """
        Get relevant documents with reranking
        
        Args:
            query: Search query
            
        Returns:
            List of relevant documents (reranked if enabled)
        """
        logger.info(f"[RERANKING RETRIEVER] Retrieving documents for query: '{query[:50]}...'")
        
        try:
            # Generate query embedding
            query_vector = self.embeddings.embed_query(query)
            logger.debug(f"[RERANKING RETRIEVER] Query embedding generated (dim: {len(query_vector)})")
            
            # Search with automatic reranking
            results = self.storage_manager.search_chunks(
                query=query,
                k=self.k,
                topic_id=None,  # Search all topics
                query_vector=query_vector
            )
            
            logger.info(f"[RERANKING RETRIEVER] Retrieved {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"[RERANKING RETRIEVER] Retrieval failed: {e}", exc_info=True)
            return []
    
    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Async version (fallback to sync)"""
        return self._get_relevant_documents(query)
