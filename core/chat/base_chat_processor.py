from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional


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
        return bool(user_input and user_input.strip())
    
    def format_response(self, response: str) -> str:
        """응답 포맷팅"""
        if not response:
            return response
        
        import re
        # 과도한 줄바꿈 정리
        formatted = re.sub(r"\n{3,}", "\n\n", response)
        # 불규칙한 들여쓰기 정리
        formatted = re.sub(r"\n\s{5,}", "\n    ", formatted)
        return formatted.strip()