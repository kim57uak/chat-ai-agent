"""
RAG Chat Processor
RAG + Multi-Agent + MCP 통합 채팅 처리기
"""

from typing import List, Dict, Tuple, Optional
from .base_chat_processor import BaseChatProcessor
from core.agents.multi_agent_orchestrator import MultiAgentOrchestrator
from core.agents.hybrid_analyzer import HybridAnalyzer
from core.agents.rag_agent import RAGAgent
from core.agents.mcp_agent import MCPAgent
from core.logging import get_logger

logger = get_logger("rag_chat_processor")


class RAGChatProcessor(BaseChatProcessor):
    """RAG + Multi-Agent 통합 채팅 처리기"""
    
    def __init__(
        self, 
        model_strategy,
        vectorstore=None,
        mcp_client=None,
        tools: Optional[List] = None
    ):
        """
        Initialize RAG chat processor
        
        Args:
            model_strategy: LLM strategy
            vectorstore: Vector store for RAG
            mcp_client: MCP client for tools
            tools: Pre-wrapped tools
        """
        super().__init__(model_strategy)
        self.vectorstore = vectorstore
        self.mcp_client = mcp_client
        self.tools = tools or []
        
        # Agents 초기화
        self.agents = self._initialize_agents()
        
        # Orchestrator 초기화
        self.orchestrator = MultiAgentOrchestrator(
            llm=model_strategy.llm,
            agents=self.agents
        )
        
        # Hybrid Analyzer 초기화
        self.analyzer = HybridAnalyzer(
            llm=model_strategy.llm,
            agents=self.agents
        )
        
        logger.info(f"RAG Chat Processor initialized with {len(self.agents)} agents")
    
    def _initialize_agents(self) -> List:
        """Initialize available agents"""
        agents = []
        
        # RAG Agent (vectorstore 있을 때만)
        if self.vectorstore:
            rag_agent = RAGAgent(
                llm=self.model_strategy.llm,
                vectorstore=self.vectorstore
            )
            agents.append(rag_agent)
            logger.info("RAG Agent initialized")
        
        # MCP Agent (mcp_client 있을 때만)
        if self.mcp_client or self.tools:
            mcp_agent = MCPAgent(
                llm=self.model_strategy.llm,
                mcp_client=self.mcp_client,
                tools=self.tools
            )
            agents.append(mcp_agent)
            logger.info("MCP Agent initialized")
        
        return agents
    
    def process_message(
        self, 
        user_input: str, 
        conversation_history: List[Dict] = None
    ) -> Tuple[str, List]:
        """
        Process message with RAG + Multi-Agent
        
        Args:
            user_input: User query
            conversation_history: Conversation history
            
        Returns:
            (response, used_tools)
        """
        try:
            if not self.validate_input(user_input):
                return "유효하지 않은 입력입니다.", []
            
            if not self.agents:
                logger.warning("No agents available, using simple response")
                return self._simple_response(user_input), []
            
            # Context 구성
            context = {
                "conversation_history": conversation_history,
                "model_name": self.model_strategy.model_name
            }
            
            # Orchestrator 실행 (LLM이 자동으로 Agent 선택)
            response = self.orchestrator.run(user_input, context)
            
            # 사용된 도구 추출 (향후 확장)
            used_tools = []
            
            return self.format_response(response), used_tools
            
        except Exception as e:
            logger.error(f"RAG chat processing error: {e}")
            return f"처리 중 오류가 발생했습니다: {str(e)[:100]}", []
    
    def supports_tools(self) -> bool:
        """도구 지원 여부"""
        return len(self.agents) > 0
    
    def _simple_response(self, user_input: str) -> str:
        """Fallback: Simple LLM response"""
        try:
            from langchain.schema import HumanMessage
            response = self.model_strategy.llm.invoke([HumanMessage(content=user_input)])
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Simple response failed: {e}")
            return "죄송합니다. 응답을 생성할 수 없습니다."
