from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import BaseMessage
from ui.prompts import prompt_manager, ModelType
from core.file_utils import load_prompt_config


class BaseModelStrategy(ABC):
    """AI 모델별 처리 전략 기본 인터페이스"""
    
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self._llm = None
        self._load_ai_parameters()
    
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
    
    def get_default_system_prompt(self, user_language: str = None) -> str:
        """기본 시스템 프롬프트 - 공통 프롬프트 사용"""
        return prompt_manager.get_system_prompt(ModelType.COMMON.value, use_tools=True, user_language=user_language)
    
    def enhance_prompt_with_format(self, prompt: str) -> str:
        """프롬프트 반환 (포맷 지침은 이미 포함됨)"""
        return prompt
    
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
    
    def _load_ai_parameters(self):
        """AI 파라미터 로드"""
        try:
            config = load_prompt_config()
            self.ai_params = config.get('ai_parameters', {})
        except:
            self.ai_params = {}
    
    def get_model_parameters(self) -> Dict[str, Any]:
        """모델별 지원 파라미터만 반환"""
        params = {}
        provider = self._get_provider()
        
        # 공통 파라미터
        if 'temperature' in self.ai_params:
            params['temperature'] = self.ai_params['temperature']
        if 'max_tokens' in self.ai_params:
            params['max_tokens'] = self.ai_params['max_tokens']
        if 'top_p' in self.ai_params:
            params['top_p'] = self.ai_params['top_p']
        
        # 모델별 파라미터
        if provider in ['openai', 'openrouter']:
            if 'frequency_penalty' in self.ai_params:
                params['frequency_penalty'] = self.ai_params['frequency_penalty']
            if 'presence_penalty' in self.ai_params:
                params['presence_penalty'] = self.ai_params['presence_penalty']
            if 'stop_sequences' in self.ai_params and self.ai_params['stop_sequences']:
                params['stop'] = self.ai_params['stop_sequences']
        
        if provider in ['google', 'openrouter']:
            if 'top_k' in self.ai_params:
                params['top_k'] = self.ai_params['top_k']
            if 'stop_sequences' in self.ai_params and self.ai_params['stop_sequences']:
                params['stop_sequences'] = self.ai_params['stop_sequences']
        
        # perplexity는 temperature, max_tokens, top_p만 지원
        
        return params
    
    def _get_provider(self) -> str:
        """현재 모델의 프로바이더 반환"""
        from core.file_utils import load_config
        try:
            config = load_config()
            model_config = config.get('models', {}).get(self.model_name, {})
            provider = model_config.get('provider', 'unknown')
            # perplexity provider 감지
            if provider == 'perplexity' or 'sonar' in self.model_name.lower():
                return 'perplexity'
            return provider
        except:
            return 'unknown'