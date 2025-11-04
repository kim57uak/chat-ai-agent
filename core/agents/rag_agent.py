"""
RAG Agent
ConversationalRetrievalChain 기반
"""

from typing import List, Dict, Optional
from langchain.chains import ConversationalRetrievalChain
from langchain.retrievers import MultiQueryRetriever
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor
from langchain.tools import BaseTool
from core.logging import get_logger
from .base_agent import BaseAgent

logger = get_logger("rag_agent")


class RAGAgent(BaseAgent):
    """RAG (Retrieval-Augmented Generation) Agent"""
    
    def __init__(self, llm, vectorstore, memory=None, tools: Optional[List[BaseTool]] = None):
        """
        Initialize RAG agent
        
        Args:
            llm: LangChain LLM
            vectorstore: Vector store instance
            memory: Conversation memory
            tools: Additional tools
        """
        super().__init__(llm, tools)
        self.vectorstore = vectorstore
        self.memory = memory or ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.chain = None
    
    def _create_executor(self) -> AgentExecutor:
        """Create RAG chain (not AgentExecutor)"""
        # Multi-Query Retriever
        retriever = MultiQueryRetriever.from_llm(
            retriever=self.vectorstore.as_retriever(),
            llm=self.llm
        )
        
        # Conversational Retrieval Chain
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            return_source_documents=True
        )
        
        logger.info("RAG chain created")
        return self.chain  # Chain을 반환 (AgentExecutor 아님)
    
    def can_handle(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Check if query requires document retrieval using LLM
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if query needs RAG
        """
        from langchain.schema import HumanMessage
        
        try:
            prompt = f"""Does this query require searching or retrieving documents?

Query: {query}

Answer only 'YES' or 'NO'."""
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().upper()
            
            return "YES" in decision
            
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return False
