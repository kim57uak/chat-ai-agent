from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import BaseMessage
from core.response_formatter import SystemPromptEnhancer
from ui.prompts import prompt_manager, ModelType


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
    def create_messages(self, user_input: str, system_prompt: str = None, conversation_history: List[Dict] = None) -> List[BaseMessage]:
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
    
    @llm.setter
    def llm(self, value):
        """LLM 인스턴스 설정"""
        self._llm = value
    
    def supports_streaming(self) -> bool:
        """스트리밍 지원 여부"""
        return True
    
    def get_default_system_prompt(self) -> str:
        """기본 시스템 프롬프트 - 공통 프롬프트 사용"""
        base_prompt = prompt_manager.get_system_prompt(ModelType.COMMON.value)
        return SystemPromptEnhancer.enhance_prompt(base_prompt)
    
    def enhance_prompt_with_format(self, prompt: str) -> str:
        """프롬프트에 형식 지침 추가"""
        return SystemPromptEnhancer.enhance_prompt(prompt)
    
    def detect_user_language(self, user_input: str) -> str:
        """사용자 입력 텍스트에서 언어 감지 (원본 텍스트만 사용)"""
        import re
        from core.file_utils import load_config
        
        if not user_input or not isinstance(user_input, str):
            return "en"
        
        # config.json에서 한글 비율 임계값 로드
        try:
            config = load_config()
            korean_threshold = config.get("language_detection", {}).get("korean_threshold", 0.3)
        except:
            korean_threshold = 0.3  # 기본값
        
        # 한글 문자 감지
        korean_chars = len(re.findall(r'[가-힣]', user_input))
        total_chars = len(re.sub(r'\s+', '', user_input))  # 공백 제외
        
        if total_chars == 0:
            return "en"
        
        # 한글 비율이 임계값 이상이면 한국어로 판단
        korean_ratio = korean_chars / total_chars
        return "ko" if korean_ratio >= korean_threshold else "en"