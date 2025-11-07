"""
Chat Mode Manager
채팅 모드 관리 및 전환
"""

from enum import Enum
from typing import Optional
from .base_chat_processor import BaseChatProcessor
from .simple_chat_processor import SimpleChatProcessor
from .tool_chat_processor import ToolChatProcessor
from .rag_chat_processor import RAGChatProcessor
from core.logging import get_logger

logger = get_logger("chat_mode_manager")


class ChatMode(Enum):
    """채팅 모드"""
    SIMPLE = "simple"      # LLM만
    TOOL = "tool"          # MCP 도구만
    RAG = "rag"            # RAG + Multi-Agent + MCP (통합)


class ChatModeManager:
    """채팅 모드 관리자"""
    
    def __init__(self, model_strategy):
        """
        Initialize chat mode manager
        
        Args:
            model_strategy: LLM strategy
        """
        self.model_strategy = model_strategy
        self.current_mode = ChatMode.SIMPLE
        self._processors = {}
        
        logger.info("Chat Mode Manager initialized")
    
    def set_mode(self, mode: ChatMode):
        """
        Set chat mode
        
        Args:
            mode: Chat mode to set
        """
        if not isinstance(mode, ChatMode):
            raise ValueError(f"Invalid mode: {mode}")
        
        self.current_mode = mode
        logger.info(f"Chat mode changed to: {mode.value}")
    
    def get_processor(
        self,
        mode: Optional[ChatMode] = None,
        vectorstore=None,
        mcp_client=None,
        tools=None,
        session_id: Optional[int] = None
    ) -> BaseChatProcessor:
        """
        Get chat processor for mode
        
        Args:
            mode: Chat mode (uses current if None)
            vectorstore: Vector store for RAG
            mcp_client: MCP client for tools
            tools: Pre-wrapped tools
            
        Returns:
            Chat processor instance
        """
        mode = mode or self.current_mode
        
        # 캐시 키 생성
        cache_key = f"{mode.value}_{id(vectorstore)}_{id(mcp_client)}"
        
        # 캐시된 프로세서 반환
        if cache_key in self._processors:
            return self._processors[cache_key]
        
        # 새 프로세서 생성
        processor = self._create_processor(mode, vectorstore, mcp_client, tools)
        
        # session_id 설정
        if session_id is not None:
            processor.session_id = session_id
        
        self._processors[cache_key] = processor
        
        return processor
    
    def _create_processor(
        self,
        mode: ChatMode,
        vectorstore,
        mcp_client,
        tools
    ) -> BaseChatProcessor:
        """Create processor for mode"""
        if mode == ChatMode.SIMPLE:
            return SimpleChatProcessor(self.model_strategy)
        
        elif mode == ChatMode.TOOL:
            return ToolChatProcessor(self.model_strategy, tools=tools)
        
        elif mode == ChatMode.RAG:
            return RAGChatProcessor(
                self.model_strategy,
                vectorstore=vectorstore,
                mcp_client=mcp_client,
                tools=tools
            )
        
        else:
            logger.warning(f"Unknown mode: {mode}, using SIMPLE")
            return SimpleChatProcessor(self.model_strategy)
    
    def clear_cache(self):
        """Clear processor cache"""
        self._processors.clear()
        logger.info("Processor cache cleared")
