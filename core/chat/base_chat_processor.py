from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from core.response_formatter import ResponseFormatter


class BaseChatProcessor(ABC):
    """채팅 처리기 기본 인터페이스"""
    
    def __init__(self, model_strategy):
        self.model_strategy = model_strategy
    
    @abstractmethod
    def process_message(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """메시지 처리"""
        pass
    
    @abstractmethod
    def supports_tools(self) -> bool:
        """도구 지원 여부"""
        pass
    
    def validate_input(self, user_input: str) -> bool:
        """입력 검증"""
        if not user_input:
            return False
        
        # user_input이 문자열이 아닌 경우 처리
        if not isinstance(user_input, str):
            return False
            
        return bool(user_input.strip())
    
    def format_response(self, response: str) -> str:
        """응답 포맷팅 - 모든 AI 모델에 일관된 형식 적용"""
        return ResponseFormatter.format_response(response)