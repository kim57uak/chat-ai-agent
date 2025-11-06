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
from core.rag.retrieval import MultiQueryRetrieverWrapper

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
        try:
            # 기본 retriever 사용 (embeddings 포함)
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
            logger.info("Using base retriever with embeddings")
        except Exception as e:
            logger.error(f"Retriever creation failed: {e}")
            return None
        
        # Conversational Retrieval Chain
        from langchain.chains import LLMChain
        from langchain.chains.question_answering import load_qa_chain
        
        # Memory와 함께 사용 시 output_key 명시
        self.chain = ConversationalRetrievalChain(
            retriever=retriever,
            combine_docs_chain=load_qa_chain(self.llm, chain_type="stuff"),
            question_generator=LLMChain(
                llm=self.llm,
                prompt=self._get_question_prompt()
            ),
            return_source_documents=True,
            output_key="answer"  # 명시적 지정
        )
        
        logger.info("RAG chain created")
        return self.chain  # Chain을 반환 (AgentExecutor 아님)
    
    def _get_question_prompt(self):
        """Get question generation prompt"""
        from langchain.prompts import PromptTemplate
        
        template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
        
        return PromptTemplate.from_template(template)
    
    def can_handle(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Check if query requires document retrieval using LLM context understanding
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if query needs RAG
        """
        from langchain.schema import HumanMessage
        
        # Context 정보
        context_info = ""
        if context:
            if context.get('documents'):
                context_info += "\n- Documents are available in context"
            context_info += f"\n- Additional context: {str(context)[:200]}"
        
        prompt = f"""Analyze if this query requires searching or retrieving information from documents.

Query: {query}{context_info}

Consider:
1. Does the query ask for information that might be in stored documents?
2. Does it require summarization, analysis, or retrieval of document content?
3. Is there context indicating documents are available?

Answer ONLY 'YES' or 'NO':"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().upper()
            result = "YES" in decision
            logger.info(f"RAG Agent can_handle: {result} for query: {query[:50]}...")
            return result
        except Exception as e:
            logger.error(f"RAG Agent can_handle failed: {e}")
            return False
