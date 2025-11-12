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
from core.token_tracking import get_unified_tracker, ChatModeType
from core.token_tracker import token_tracker, StepType
from core.logging import get_logger
import time

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
    
    def set_session_id(self, session_id: int):
        """Set session ID for token tracking"""
        self.session_id = session_id
    
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
        
        # Python REPL Agent
        try:
            from core.agents.python_repl_agent import PythonREPLAgent
            python_agent = PythonREPLAgent(llm=self.model_strategy.llm)
            agents.append(python_agent)
            logger.info("Python REPL Agent initialized")
        except Exception as e:
            logger.warning(f"Python REPL Agent initialization failed: {e}")
        
        # Pandas Agent
        try:
            from core.agents.pandas_agent import PandasAgent
            pandas_agent = PandasAgent(llm=self.model_strategy.llm)
            agents.append(pandas_agent)
            logger.info("Pandas Agent initialized")
        except Exception as e:
            logger.warning(f"Pandas Agent initialization failed: {e}")
        
        # File System Agent
        try:
            from core.agents.filesystem_agent import FileSystemAgent
            fs_agent = FileSystemAgent(llm=self.model_strategy.llm)
            agents.append(fs_agent)
            logger.info("File System Agent initialized")
        except Exception as e:
            logger.warning(f"File System Agent initialization failed: {e}")
        
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
            # Unified tracker 시작
            start_time = time.time()
            unified_tracker = None
            try:
                from core.security.secure_path_manager import secure_path_manager
                db_path = secure_path_manager.get_database_path()
                unified_tracker = get_unified_tracker(db_path)
                
                # 세션 ID 가져오기
                unified_tracker.start_conversation(
                    mode=ChatModeType.RAG,
                    model=self.model_strategy.model_name,
                    session_id=self.session_id
                )
                logger.info(f"RAG mode unified tracker started: session={self.session_id}")
            except Exception as e:
                logger.error(f"Unified tracker initialization failed: {e}")
                unified_tracker = None
            
            # 토큰 트래킹 시작
            token_tracker.start_step(StepType.INITIAL_PROMPT, "RAG Chat Processing")
            
            if not self.validate_input(user_input):
                return "유효하지 않은 입력입니다.", []
            
            if not self.agents:
                logger.warning("No agents available, using simple response")
                return self._simple_response(user_input), []
            
            # Context 구성 (모델명 포함)
            context = {
                "conversation_history": conversation_history,
                "model_name": self.model_strategy.model_name,
                "unified_tracker": unified_tracker,
                "llm": self.model_strategy.llm  # Agent가 모델명 추출용
            }
            
            # RAG Agent 먼저 실행
            token_tracker.start_step(StepType.TOOL_EXECUTION, "RAG Agent Execution")
            
            rag_agent = None
            for agent in self.agents:
                if 'RAG' in agent.get_name():
                    rag_agent = agent
                    break
            
            if rag_agent:
                logger.info("Executing RAG Agent first")
                rag_result = rag_agent.execute(user_input, context)
                response = rag_result.output
                logger.info(f"RAG Agent response length: {len(response)}")
            else:
                logger.warning("No RAG Agent found, using orchestrator")
                response = self.orchestrator.execute_parallel_optimized(user_input, context)
            
            # unified_tracker에서 토큰 정보 추출
            agent_tokens = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            if unified_tracker and hasattr(unified_tracker, 'current_conversation'):
                conv = unified_tracker.current_conversation
                if conv:
                    agent_tokens["input_tokens"] = conv.total_input
                    agent_tokens["output_tokens"] = conv.total_output
                    agent_tokens["total_tokens"] = conv.total_tokens
            
            token_tracker.end_step(
                StepType.TOOL_EXECUTION,
                "Multi-Agent Execution",
                input_text=user_input,
                output_text=response,
                additional_info=agent_tokens
            )
            
            used_tools = []
            
            token_tracker.end_step(
                StepType.FINAL_RESPONSE,
                "RAG Chat Response",
                input_text=user_input,
                output_text=response,
                additional_info=agent_tokens
            )
            
            # Unified tracker 종료
            if unified_tracker:
                unified_tracker.end_conversation()
            
            return self.format_response(response), used_tools
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"RAG chat processing error: {error_msg}")
            
            # 병렬 실행 타임아웃 오류 처리
            if "futures unfinished" in error_msg:
                logger.warning("병렬 실행 타임아웃, 단일 Agent로 재시도")
                try:
                    response = self.orchestrator.run(user_input, context)
                    return self.format_response(response), []
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
            
            # 사용자 친화적 메시지
            return "요청을 처리하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.", []
    
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
