"""
Multi-Query Retriever
쿼리를 재작성하여 검색 품질 향상
"""

from typing import List, Optional
from langchain.retrievers import MultiQueryRetriever
from langchain.schema import Document
from langchain_core.language_models import BaseLanguageModel
from langchain_core.vectorstores import VectorStore
from core.logging import get_logger

logger = get_logger("multi_query_retriever")


class MultiQueryRetrieverWrapper:
    """Multi-Query Retriever 래퍼"""
    
    def __init__(
        self, 
        llm: BaseLanguageModel,
        vectorstore: VectorStore,
        k: int = 5
    ):
        """
        Initialize Multi-Query Retriever
        
        Args:
            llm: LLM for query generation
            vectorstore: Vector store
            k: Number of documents to retrieve
        """
        self.llm = llm
        self.vectorstore = vectorstore
        self.k = k
        
        # Create base retriever
        self.base_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        
        # Create multi-query retriever
        self.retriever = MultiQueryRetriever.from_llm(
            retriever=self.base_retriever,
            llm=llm
        )
        
        logger.info(f"Multi-Query Retriever initialized with k={k}")
    
    def retrieve(self, query: str) -> List[Document]:
        """
        Retrieve documents using multi-query approach
        
        Args:
            query: Search query
            
        Returns:
            List of relevant documents
        """
        try:
            logger.info(f"Retrieving with multi-query: {query[:100]}")
            
            # Multi-query retrieval
            documents = self.retriever.get_relevant_documents(query)
            
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Multi-query retrieval failed: {e}")
            # Fallback to base retriever
            logger.info("Falling back to base retriever")
            return self._fallback_retrieve(query)
    
    def _fallback_retrieve(self, query: str) -> List[Document]:
        """
        Fallback to base retriever
        
        Args:
            query: Search query
            
        Returns:
            List of documents
        """
        try:
            return self.base_retriever.get_relevant_documents(query)
        except Exception as e:
            logger.error(f"Fallback retrieval failed: {e}")
            return []
    
    def retrieve_with_scores(self, query: str) -> List[tuple]:
        """
        Retrieve documents with relevance scores
        
        Args:
            query: Search query
            
        Returns:
            List of (document, score) tuples
        """
        try:
            # Use vectorstore's similarity search with scores
            results = self.vectorstore.similarity_search_with_score(query, k=self.k)
            logger.info(f"Retrieved {len(results)} documents with scores")
            return results
            
        except Exception as e:
            logger.error(f"Retrieval with scores failed: {e}")
            return []
    
    def get_generated_queries(self, query: str) -> List[str]:
        """
        Get generated queries from LLM
        
        Args:
            query: Original query
            
        Returns:
            List of generated queries
        """
        from langchain.schema import HumanMessage
        
        prompt = f"""Generate 3 different versions of the following query to improve retrieval:

Original Query: {query}

Generate 3 alternative queries that:
1. Rephrase the question
2. Add relevant context
3. Use different keywords

Return ONLY the 3 queries, one per line:"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            queries = [q.strip() for q in response.content.strip().split('\n') if q.strip()]
            
            # Include original query
            all_queries = [query] + queries[:3]
            logger.info(f"Generated {len(all_queries)} queries")
            
            return all_queries
            
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            return [query]
    
    def retrieve_parallel(self, query: str) -> List[Document]:
        """
        Retrieve using parallel queries
        
        Args:
            query: Search query
            
        Returns:
            Deduplicated list of documents
        """
        try:
            # Generate multiple queries
            queries = self.get_generated_queries(query)
            
            # Retrieve for each query
            all_docs = []
            seen_ids = set()
            
            for q in queries:
                docs = self.base_retriever.get_relevant_documents(q)
                for doc in docs:
                    doc_id = hash(doc.page_content)
                    if doc_id not in seen_ids:
                        all_docs.append(doc)
                        seen_ids.add(doc_id)
            
            logger.info(f"Parallel retrieval: {len(all_docs)} unique documents")
            return all_docs[:self.k * 2]  # Return top 2k documents
            
        except Exception as e:
            logger.error(f"Parallel retrieval failed: {e}")
            return self._fallback_retrieve(query)
    
    def update_k(self, k: int):
        """
        Update number of documents to retrieve
        
        Args:
            k: New k value
        """
        self.k = k
        self.base_retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        self.retriever = MultiQueryRetriever.from_llm(
            retriever=self.base_retriever,
            llm=self.llm
        )
        logger.info(f"Updated k to {k}")
