from typing import List, Dict, Any, Optional, Tuple
from tools.langchain.langchain_tools import create_tool_registry, MCPTool
from core.mcp_implementation import mcp_tool_caller, mcp_server_manager
from mcp.tools.tool_manager import tool_manager
from tools.strategies.tool_decision_strategy import ToolDecisionContext, AIBasedToolDecisionStrategy
from core.conversation_history import ConversationHistory
from core.llm_factory import LLMFactoryProvider
from core.chat_processor import SimpleChatProcessor, ToolChatProcessor
from core.agent_executor_factory import AgentExecutorFactoryProvider
import logging

logger = logging.getLogger(__name__)


class AIAgent:
    """리팩토링된 AI 에이전트 - SOLID 원칙과 디자인 패턴 적용"""

    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model_name = model_name
        
        # Factory 패턴으로 LLM 생성
        self.llm = LLMFactoryProvider.create_llm(api_key, model_name)
        
        # 도구 관리
        self.tool_registry = create_tool_registry(mcp_tool_caller)
        self.tools: List[MCPTool] = []
        self._load_mcp_tools()
        
        # Strategy 패턴으로 도구 결정 전략 설정
        self.tool_decision_context = ToolDecisionContext(AIBasedToolDecisionStrategy())
        
        # 채팅 처리기들
        self.simple_chat_processor = SimpleChatProcessor()
        self.tool_chat_processor = ToolChatProcessor(
            self.tools, 
            AgentExecutorFactoryProvider()
        ) if self.tools else None
        
        # 대화 히스토리
        self.conversation_history = ConversationHistory()
        self.conversation_history.load_from_file()

    def _load_mcp_tools(self):
        """MCP 도구 로드 및 LangChain 도구로 등록"""
        try:
            all_mcp_tools = mcp_tool_caller.get_all_tools()
            if all_mcp_tools:
                self.tools = self.tool_registry.register_mcp_tools(all_mcp_tools)
                tool_manager.register_tools(all_mcp_tools)
                logger.info(f"AI 에이전트에 {len(self.tools)}개 도구 로드됨")
            else:
                logger.warning("사용 가능한 MCP 도구가 없습니다")
        except Exception as e:
            logger.error(f"MCP 도구 로드 실패: {e}")

    def process_message(self, user_input: str) -> Tuple[str, List]:
        """메시지 처리 - AI가 도구 사용 여부 결정"""
        # 사용자 메시지를 히스토리에 추가
        self.conversation_history.add_message("user", user_input)

        if not self.tools:
            response = self.simple_chat_processor.process_chat(
                user_input, self.llm, self.conversation_history.get_recent_messages(10)
            )
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            return response, []

        # AI가 컨텍스트를 분석하여 도구 사용 여부 결정
        use_tools = self.tool_decision_context.should_use_tools(
            user_input, self.tools, self.llm
        )

        if use_tools and self.tool_chat_processor:
            response, used_tools = self.tool_chat_processor.process_chat(
                user_input, self.llm
            )
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            return response, used_tools
        else:
            response = self.simple_chat_processor.process_chat(
                user_input, self.llm, self.conversation_history.get_recent_messages(10)
            )
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            return response, []

    def process_message_with_history(
        self,
        user_input: str,
        conversation_history: List[Dict],
        force_agent: bool = False,
    ) -> Tuple[str, List]:
        """대화 기록을 포함한 메시지 처리"""
        if not self.tools:
            response = self.simple_chat_processor.process_chat(
                user_input, self.llm, conversation_history
            )
            return response, []

        # force_agent가 True면 더 적극적으로 도구 사용 판단
        use_tools = self.tool_decision_context.should_use_tools(
            user_input, self.tools, self.llm, force_agent
        )

        if use_tools and self.tool_chat_processor:
            response, used_tools = self.tool_chat_processor.process_chat(
                user_input, self.llm
            )
            return response, used_tools
        else:
            response = self.simple_chat_processor.process_chat(
                user_input, self.llm, conversation_history
            )
            return response, []

    def simple_chat(self, user_input: str) -> str:
        """단순 채팅 (도구 사용 없음)"""
        # 모델 전략 생성
        from core.models.model_strategy_factory import ModelStrategyFactory
        model_strategy = ModelStrategyFactory.create_strategy(self.api_key, self.model_name)
        
        # SimpleChatProcessor 생성 및 처리
        from core.chat.simple_chat_processor import SimpleChatProcessor
        processor = SimpleChatProcessor(model_strategy)
        response, _ = processor.process_message(user_input)
        return response

    def simple_chat_with_history(
        self, user_input: str, conversation_history: List[Dict]
    ) -> str:
        """대화 기록을 포함한 일반 채팅"""
        # 모델 전략 생성
        from core.models.model_strategy_factory import ModelStrategyFactory
        model_strategy = ModelStrategyFactory.create_strategy(self.api_key, self.model_name)
        
        # SimpleChatProcessor 생성 및 처리
        from core.chat.simple_chat_processor import SimpleChatProcessor
        processor = SimpleChatProcessor(model_strategy)
        response, _ = processor.process_message(user_input, conversation_history)
        return response

    def chat_with_tools(self, user_input: str) -> Tuple[str, List]:
        """도구를 사용한 채팅"""
        if not self.tool_chat_processor:
            return "사용 가능한 도구가 없습니다.", []
        
        return self.tool_chat_processor.process_chat(user_input, self.llm)