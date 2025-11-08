"""
RAG Agent
ConversationalRetrievalChain 기반
"""

from typing import List, Dict, Optional
try:
    from langchain.chains import ConversationalRetrievalChain
except ImportError:
    from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor
from langchain.tools import BaseTool
from core.logging import get_logger
from .base_agent import BaseAgent

logger = get_logger("rag_agent")


class RAGAgent(BaseAgent):
    """Searches and retrieves information from internal documents stored in vector database. Answers questions based on uploaded files and company knowledge base."""
    
    is_chain_based = True  # Chain 사용
    
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
        """Create RAG chain (returns Chain, not AgentExecutor)"""
        # Load top_k from RAGConfigManager
        top_k = self._load_top_k()
        
        try:
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": top_k})
            logger.info(f"Using base retriever with embeddings (k={top_k})")
        except Exception as e:
            logger.error(f"Retriever creation failed: {e}")
            return None
        
        try:
            from langchain.chains import RetrievalQA
        except ImportError:
            from langchain.chains.retrieval_qa.base import RetrievalQA
        from langchain.prompts import PromptTemplate
        from ui.prompts import prompt_manager
        
        # 모델 타입 감지
        model_name = str(getattr(self.llm, 'model_name', '') or getattr(self.llm, 'model', ''))
        model_type = prompt_manager.get_provider_from_model(model_name)
        is_perplexity = 'sonar' in model_name.lower() or 'perplexity' in model_name.lower()
        
        # prompts.py의 시스템 프롬프트 사용
        system_prompt = prompt_manager.get_system_prompt(model_type, use_tools=False)
        
        # RAG 특화 프롬프트 추가
        rag_instruction = (
            "\n\n**Document Retrieval Context**:\n"
            "You have access to retrieved documents. Use them to provide accurate, detailed answers. "
            "Cite document numbers when referencing specific information. "
            "If documents don't contain the answer, clearly state that."
        )
        
        combined_prompt = system_prompt + rag_instruction
        
        # 🔍 DEBUG: 프롬프트 로깅
        logger.info(f"[RAG PROMPT] System prompt length: {len(system_prompt)} chars")
        logger.info(f"[RAG PROMPT] Combined prompt length: {len(combined_prompt)} chars")
        logger.debug(f"[RAG PROMPT] Full prompt:\n{combined_prompt[:500]}...")  # 처음 500자만
        
        # combine_docs_chain에 프롬프트 적용
        doc_prompt = PromptTemplate.from_template(
            combined_prompt + "\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        )
        
        # Perplexity는 RetrievalQA 사용 (Tool 모드 방식)
        if is_perplexity:
            logger.info(f"Using RetrievalQA for Perplexity model: {model_name}")
            self.chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": doc_prompt},
                verbose=True
            )
            logger.info("✅ RetrievalQA chain created (single vector search)")
        else:
            # ConversationalRetrievalChain with rephrase disabled
            self.chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                return_source_documents=True,
                output_key="answer",
                combine_docs_chain_kwargs={"prompt": doc_prompt},
                rephrase_question=False,  # 질문 재작성 비활성화 (벡터 검색 1회)
                verbose=True
            )
            logger.info("✅ ConversationalRetrievalChain created with rephrase_question=False (single vector search)")
        
        logger.info(f"RAG chain created for {model_type}")
        logger.info(f"[RAG CONFIG] Model: {model_name}, Type: {model_type}, Perplexity: {is_perplexity}")
        return self.chain
    

    def can_handle(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Check if query requires document retrieval (rule-based, no LLM call)
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if query needs RAG
        """
        # RAG 모드가 명시적으로 활성화된 경우
        if context and context.get('rag_mode_active'):
            logger.info("RAG mode explicitly active")
            return True
        
        # 문서가 컨텍스트에 있으면 RAG 사용
        if context and context.get('documents'):
            logger.info("Documents available in context")
            return True
        
        # 벡터스토어가 비어있으면 RAG 불가
        try:
            if hasattr(self.vectorstore, '_collection'):
                doc_count = self.vectorstore._collection.count()
                if doc_count == 0:
                    logger.info("No documents in vectorstore")
                    return False
        except:
            pass
        
        # 키워드 기반 판단 (LLM 호출 없음)
        rag_keywords = ['문서', '파일', '내용', '요약', '검색', 'document', 'file', 'search', 'summarize', 'find']
        query_lower = query.lower()
        result = any(keyword in query_lower for keyword in rag_keywords)
        
        logger.info(f"RAG Agent can_handle (rule-based): {result}")
        return result
    
    def _load_top_k(self) -> int:
        """Load top_k from RAGConfigManager (default: 10)"""
        try:
            from core.rag.config.rag_config_manager import RAGConfigManager
            config_manager = RAGConfigManager()
            top_k = config_manager.get_top_k()
            logger.info(f"Loaded top_k={top_k} from RAGConfigManager")
            return top_k
        except Exception as e:
            logger.warning(f"Failed to load top_k from config: {e}")
            return 10  # Default
