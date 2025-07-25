"""리팩토링된 채팅 프로세서 - SOLID 원칙 적용"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from core.processors.simple_chat_processor import SimpleChatProcessor
from core.processors.tool_chat_processor import ToolChatProcessor


class ChatProcessor(ABC):
    """채팅 처리를 위한 추상 클래스 - ISP 원칙 적용"""
    
    @abstractmethod
    def process_chat(self, user_input: str, llm: Any, conversation_history: List[Dict] = None) -> str:
        pass


class RefactoredSimpleChatProcessor(ChatProcessor):
    """리팩토링된 단순 채팅 처리기"""
    
    def __init__(self):
        self.processor = SimpleChatProcessor()
    
    def process_chat(self, user_input: str, llm: Any, conversation_history: List[Dict] = None) -> str:
        return self.processor.process_chat(user_input, llm, conversation_history)


class RefactoredToolChatProcessor(ChatProcessor):
    """리팩토링된 도구 사용 채팅 처리기"""
    
    def __init__(self, tools: List[Any], agent_executor_factory):
        self.processor = ToolChatProcessor(tools, agent_executor_factory)
    
    def process_chat(self, user_input: str, llm: Any, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        return self.processor.process_chat(user_input, llm, conversation_history)