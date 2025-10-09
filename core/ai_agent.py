# 하위 호환성을 위한 래퍼 클래스
# 기존 코드가 계속 작동하도록 하면서 새로운 리팩토링된 구조를 사용

from .ai_agent_v2 import AIAgentV2
from core.logging import get_logger

logger = get_logger("ai_agent")


class AIAgent:
    """AI 에이전트 - 하위 호환성 유지를 위한 래퍼 클래스"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        # 새로운 리팩토링된 에이전트 사용
        self._agent_v2 = AIAgentV2(api_key, model_name)
        
        # 기존 속성들 호환성 유지
        self.api_key = api_key
        self.model_name = model_name
        self.llm = self._agent_v2.model_strategy.llm
        self.tools = self._agent_v2.tools
        self.conversation_history = self._agent_v2.conversation_history
        
        logger.info(f"AI 에이전트 초기화 완료 (리팩토링된 버전): {model_name}")
    
    def process_message(self, user_input: str):
        """메시지 처리 - 기존 인터페이스 유지"""
        return self._agent_v2.process_message(user_input)
    
    def process_message_with_history(self, user_input: str, conversation_history, force_agent: bool = False):
        """대화 기록을 포함한 메시지 처리 - 기존 인터페이스 유지"""
        return self._agent_v2.process_message_with_history(user_input, conversation_history, force_agent)
    
    def simple_chat(self, user_input: str) -> str:
        """단순 채팅 - 기존 인터페이스 유지"""
        return self._agent_v2.simple_chat(user_input)
    
    def simple_chat_with_history(self, user_input: str, conversation_history):
        """대화 기록을 포함한 단순 채팅 - 기존 인터페이스 유지"""
        return self._agent_v2.simple_chat_with_history(user_input, conversation_history)
    
    def chat_with_tools(self, user_input: str):
        """도구를 사용한 채팅 - 기존 인터페이스 유지"""
        if not self.tools:
            return "사용 가능한 도구가 없습니다.", []
        
        response, used_tools = self._agent_v2._process_with_tools(user_input)
        return response, used_tools
    
    # 기존 메서드들의 호환성 유지를 위한 위임
    def _should_use_tools(self, user_input: str, force_agent: bool = False) -> bool:
        """도구 사용 여부 결정 - 기존 인터페이스 유지"""
        return self._agent_v2._should_use_tools(user_input)
    
    def _create_llm(self):
        """LLM 생성 - 기존 인터페이스 유지"""
        return self._agent_v2.model_strategy.llm
    
    def _load_mcp_tools(self):
        """MCP 도구 로드 - 기존 인터페이스 유지"""
        # 이미 v2에서 처리됨
        pass
    
    def _process_image_input(self, user_input: str):
        """이미지 입력 처리 - 기존 인터페이스 유지"""
        return self._agent_v2.model_strategy.process_image_input(user_input)
    
    def _convert_history_to_messages(self, conversation_history):
        """대화 기록을 메시지로 변환 - 기존 인터페이스 유지"""
        return self._agent_v2.simple_processor._convert_history_to_messages(conversation_history)
    
    # 추가 호환성 메서드들
    def get_available_tools(self):
        """사용 가능한 도구 목록 반환"""
        return self._agent_v2.get_available_tools()
    
    def get_model_info(self):
        """모델 정보 반환"""
        return self._agent_v2.get_model_info()
    
    # 기존 복잡한 메서드들은 단순화하여 호환성 유지
    def _gemini_tool_chat(self, user_input: str):
        """Gemini 도구 채팅 - 단순화된 호환성 버전"""
        return self._agent_v2._process_with_tools(user_input)
    
    def _perplexity_tool_chat(self, user_input: str):
        """Perplexity 도구 채팅 - 단순화된 호환성 버전"""
        return self._agent_v2._process_with_tools(user_input)
    
    def _create_agent_executor(self):
        """에이전트 실행기 생성 - 호환성 유지"""
        if self._agent_v2.tool_processor:
            return self._agent_v2.tool_processor._agent_executor
        return None
    
    def _format_response(self, text: str) -> str:
        """응답 포맷팅 - 호환성 유지"""
        return self._agent_v2.simple_processor.format_response(text)
    
    def _generate_final_response(self, user_input: str, tool_result: str):
        """최종 응답 생성 - 호환성 유지"""
        if self._agent_v2.tool_processor:
            return self._agent_v2.tool_processor._generate_final_response(user_input, tool_result)
        return "도구 처리기가 초기화되지 않았습니다."