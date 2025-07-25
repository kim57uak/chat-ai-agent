from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import BaseMessage


class BaseModelStrategy(ABC):
    """AI 모델별 처리 전략 기본 인터페이스"""
    
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self._llm = None
    
    @abstractmethod
    def create_llm(self):
        """LLM 인스턴스 생성"""
        pass
    
    @abstractmethod
    def create_messages(self, user_input: str, system_prompt: str = None) -> List[BaseMessage]:
        """메시지 형식 생성"""
        pass
    
    @abstractmethod
    def process_image_input(self, user_input: str) -> BaseMessage:
        """이미지 입력 처리"""
        pass
    
    @abstractmethod
    def should_use_tools(self, user_input: str) -> bool:
        """도구 사용 여부 결정"""
        pass
    
    @abstractmethod
    def create_agent_executor(self, tools: List):
        """에이전트 실행기 생성"""
        pass
    
    @property
    def llm(self):
        """LLM 인스턴스 반환 (지연 로딩)"""
        if self._llm is None:
            self._llm = self.create_llm()
        return self._llm
    
    def supports_streaming(self) -> bool:
        """스트리밍 지원 여부"""
        return True
    
    def get_default_system_prompt(self) -> str:
        """기본 시스템 프롬프트"""
        return """You are a helpful AI assistant that provides accurate and well-structured responses.
        
**Response Guidelines:**
- Always respond in natural, conversational Korean
- Organize information clearly with headings and bullet points
- Highlight important information using **bold** formatting
- Be friendly, helpful, and accurate
- Use proper markdown table format when creating tables

**TABLE FORMAT RULES**: When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row. Format: |Header1|Header2|Header3|\\n|---|---|---|\\n|Data1|Data2|Data3|. Never use tabs or spaces for table alignment."""