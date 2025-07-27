"""도구 사용 채팅 처리를 담당하는 모듈"""
from typing import List, Dict, Any, Tuple
from core.strategies.model_strategy import ModelStrategyFactory
from core.processors.simple_chat_processor import SimpleChatProcessor
import logging
import time

logger = logging.getLogger(__name__)


class ToolChatProcessor:
    """도구 사용 채팅 처리기 - OCP 원칙 적용"""
    
    def __init__(self, tools: List[Any], agent_executor_factory):
        self.tools = tools
        self.agent_executor_factory = agent_executor_factory
        self.agent_executor = None
        self._last_error = ""
    
    def process_chat(self, user_input: str, llm: Any, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """도구를 사용한 채팅"""
        start_time = time.time()
        logger.info(f"🚀 도구 채팅 시작: {user_input[:50]}...")
        
        try:
            # 토큰 제한 오류 방지
            if "context_length_exceeded" in str(self._last_error):
                logger.warning("토큰 제한 오류로 인해 일반 채팅으로 대체")
                return self._fallback_to_simple_chat(user_input, llm)

            # 모델별 전략 선택
            model_name = getattr(llm, 'model_name', str(llm))
            strategy = ModelStrategyFactory.get_strategy(model_name)
            
            logger.info(f"🔧 {strategy.get_model_type()} 전략 사용")
            
            result = strategy.process_tool_chat(
                user_input, llm, self.tools, 
                self.agent_executor_factory, self.agent_executor
            )
            
            elapsed = time.time() - start_time
            logger.info(f"✅ 도구 채팅 완료: {elapsed:.2f}초")
            
            return result

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            self._last_error = error_msg
            logger.error(f"❌ 도구 사용 채팅 오류: {elapsed:.2f}초, 오류: {e}")

            # 특정 오류 처리
            if ("context_length_exceeded" in error_msg or 
                "maximum context length" in error_msg):
                logger.warning("토큰 제한 오류 발생, 일반 채팅으로 대체")
                return self._fallback_to_simple_chat(user_input, llm)
            
            if ("iteration limit" in error_msg or 
                "time limit" in error_msg or
                "Agent stopped" in error_msg):
                logger.warning("에이전트 실행 제한 오류 발생, 일반 채팅으로 대체")
                return self._fallback_to_simple_chat(user_input, llm)

            return self._fallback_to_simple_chat(user_input, llm)
    
    def _fallback_to_simple_chat(self, user_input: str, llm: Any) -> Tuple[str, List]:
        """일반 채팅으로 폴백"""
        simple_processor = SimpleChatProcessor()
        response = simple_processor.process_chat(user_input, llm)
        return response, []