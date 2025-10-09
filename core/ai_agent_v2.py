from typing import List, Dict, Any, Optional, Tuple
from core.models.model_strategy_factory import ModelStrategyFactory
from core.chat.simple_chat_processor import SimpleChatProcessor
from core.chat.tool_chat_processor import ToolChatProcessor
from core.conversation_history import ConversationHistory
from core.token_tracker import token_tracker
from tools.langchain.langchain_tools import MCPTool, MCPToolRegistry
from mcp.servers.mcp import get_all_mcp_tools
from mcp.tools.tool_manager import tool_manager
from core.logging import get_logger

_logger = get_logger("ai_agent_v2")


class AIAgentV2:
    """리팩토링된 AI 에이전트 - SOLID 원칙 적용"""
    
    logger = _logger
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model_name = model_name
        
        # 전략 패턴으로 모델별 처리 분리
        self.model_strategy = ModelStrategyFactory.create_strategy(api_key, model_name)
        
        # 채팅 처리기들
        self.simple_processor = SimpleChatProcessor(self.model_strategy)
        self.tool_processor = None  # 지연 로딩
        
        # 도구 및 대화 히스토리
        self.tools: List[MCPTool] = []
        self.conversation_history = ConversationHistory()
        
        # 초기화
        self._load_mcp_tools()
        self.conversation_history.load_from_file()
    
    def _load_mcp_tools(self):
        """MCP 도구 로드"""
        try:
            from core.mcp_implementation import mcp_tool_caller
            tool_registry = MCPToolRegistry(mcp_tool_caller)
            
            all_mcp_tools = get_all_mcp_tools()
            if all_mcp_tools:
                self.tools = tool_registry.register_mcp_tools(all_mcp_tools)
                tool_manager.register_tools(all_mcp_tools)
                self.logger.info(f"AI 에이전트에 {len(self.tools)}개 도구 로드됨")
            else:
                self.logger.warning("사용 가능한 MCP 도구가 없습니다")
                
        except Exception as e:
            self.logger.error(f"MCP 도구 로드 실패: {e}")
            self.tools = []
    
    def process_message(self, user_input: str) -> Tuple[str, List]:
        """메시지 처리 - 도구 사용 여부 자동 결정"""
        # 대화 토큰 트래킹 시작
        conversation_id = token_tracker.start_conversation(user_input, self.model_name)
        
        # 사용자 메시지를 히스토리에 추가
        self.conversation_history.add_message("user", user_input)
        
        try:
            # 도구 사용 여부 결정
            should_use_tools = self._should_use_tools(user_input)
            
            if should_use_tools and self.tools:
                response, used_tools = self._process_with_tools(user_input)
            else:
                response, used_tools = self._process_simple(user_input)
            
            # 응답을 히스토리에 추가
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            
            # 대화 토큰 트래킹 종료
            token_tracker.end_conversation(response)
            
            return response, used_tools
            
        except Exception as e:
            self.logger.error(f"메시지 처리 오류: {e}")
            error_response = f"메시지 처리 중 오류가 발생했습니다: {str(e)[:100]}..."
            
            # 오류 시에도 대화 토큰 트래킹 종료
            token_tracker.end_conversation(error_response)
            
            return error_response, []
    
    def process_message_with_history(
        self, 
        user_input: str, 
        conversation_history: List[Dict], 
        force_agent: bool = False
    ) -> Tuple[str, List]:
        """대화 기록을 포함한 메시지 처리"""
        try:
            if force_agent and self.tools:
                return self._process_with_tools(user_input, conversation_history)
            else:
                return self._process_simple(user_input, conversation_history)
                
        except Exception as e:
            self.logger.error(f"히스토리 포함 메시지 처리 오류: {e}")
            return f"메시지 처리 중 오류가 발생했습니다: {str(e)[:100]}...", []
    
    def simple_chat(self, user_input: str) -> str:
        """단순 채팅 (도구 사용 없음)"""
        response, _ = self.simple_processor.process_message(user_input)
        return response
    
    def simple_chat_with_history(self, user_input: str, conversation_history: List[Dict]) -> str:
        """대화 기록을 포함한 단순 채팅"""
        response, _ = self.simple_processor.process_message(user_input, conversation_history)
        return response
    
    def _should_use_tools(self, user_input: str) -> bool:
        """도구 사용 여부 결정"""
        if not self.tools:
            self.logger.info(f"도구가 없어서 도구 사용 안함: {len(self.tools)}개")
            return False
        
        # 도구 정보를 전략에 전달
        if hasattr(self.model_strategy, 'set_tools'):
            self.model_strategy.set_tools(self.tools)
        else:
            self.model_strategy.tools = self.tools
        
        # 모델별 전략에 위임
        result = self.model_strategy.should_use_tools(user_input)
        self.logger.info(f"도구 사용 판단: '{user_input}' -> {result} (도구 {len(self.tools)}개 사용 가능)")
        return result
    
    def _process_with_tools(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """도구를 사용한 처리 - 5단계 대화 히스토리 포함"""
        # 도구 처리기 지연 로딩
        if not self.tool_processor:
            self.tool_processor = ToolChatProcessor(self.model_strategy, self.tools)
        
        # 대화 히스토리가 없으면 내부 히스토리에서 5단계 가져오기
        if not conversation_history:
            conversation_history = self.conversation_history.get_context_messages()
        
        return self.tool_processor.process_message(user_input, conversation_history)
    
    def _process_simple(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """단순 처리 - 5단계 대화 히스토리 포함"""
        # 대화 히스토리가 없으면 내부 히스토리에서 5단계 가져오기
        if not conversation_history:
            conversation_history = self.conversation_history.get_context_messages()
        
        # 단순 채팅에서도 토큰 트래킹 시작 (현재 대화가 없는 경우)
        if not token_tracker.current_conversation:
            token_tracker.start_conversation(user_input, self.model_name)
        
        response, used_tools = self.simple_processor.process_message(user_input, conversation_history)
        return response, used_tools
    
    def get_available_tools(self) -> List[str]:
        """사용 가능한 도구 목록 반환"""
        return [tool.name for tool in self.tools]
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "strategy_type": type(self.model_strategy).__name__,
            "supports_streaming": self.model_strategy.supports_streaming(),
            "tools_count": len(self.tools)
        }