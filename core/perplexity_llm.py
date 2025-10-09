import requests
from core.logging import get_logger
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

logger = get_logger("perplexity_llm")


class LLMInterface(ABC):
    """LLM 인터페이스 - 다양한 LLM 구현을 위한 공통 인터페이스"""
    
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """메시지 생성"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """모델명 반환"""
        pass


class PerplexityLLM(LLMInterface):
    """Perplexity API 클라이언트 - 단순하고 확장 가능한 구현"""
    
    DEFAULT_MODEL = "sonar"
    API_URL = "https://api.perplexity.ai/chat/completions"
    DEFAULT_TIMEOUT = 120
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_MAX_TOKENS = 4000
    
    def __init__(self, api_key: str, model_name: str = None):
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.model_name = model_name or self.DEFAULT_MODEL
        self._session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """HTTP 세션 생성 - 연결 재사용으로 성능 향상"""
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        return session
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """메시지 생성 - 메인 API 호출 메서드"""
        # 대화 히스토리 로깅
        logger.info(f"Perplexity에 전달되는 메시지 수: {len(messages)}")
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content_preview = msg.get('content', '')[:100] + '...' if len(msg.get('content', '')) > 100 else msg.get('content', '')
            logger.info(f"메시지 {i+1}: {role} - {content_preview}")
        
        payload = self._build_payload(messages, **kwargs)
        
        try:
            response = self._make_request(payload)
            return self._extract_content(response)
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            raise
    
    def _build_payload(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """API 요청 페이로드 구성"""
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.DEFAULT_TEMPERATURE),
            "max_tokens": kwargs.get("max_tokens", self.DEFAULT_MAX_TOKENS)
        }
        
        # Perplexity는 top_p만 추가 지원
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        
        return payload
    
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP 요청 실행"""
        # 전송되는 메시지 수 로깅
        messages_count = len(payload.get('messages', []))
        logger.info(f"Perplexity API 요청 - 메시지 수: {messages_count}, 모델: {payload.get('model')}")
        
        # 메시지 내용 요약 로깅
        for i, msg in enumerate(payload.get('messages', [])):
            role = msg.get('role')
            content_len = len(msg.get('content', ''))
            logger.info(f"  메시지 {i+1}: {role} ({content_len}자)")
        
        response = self._session.post(
            self.API_URL, 
            json=payload, 
            timeout=self.DEFAULT_TIMEOUT
        )
        if not response.ok:
            logger.error(f"Perplexity API 오류: {response.status_code} - {response.text}")
        response.raise_for_status()
        return response.json()
    
    def _extract_content(self, response: Dict[str, Any]) -> str:
        """응답에서 콘텐츠 추출"""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid response format: {e}")
    
    def get_model_name(self) -> str:
        """모델명 반환"""
        return self.model_name
    
    def _call(self, prompt: str, stop: Optional[list] = None, **kwargs) -> str:
        """LangChain 호환성을 위한 레거시 메서드"""
        messages = [{"role": "user", "content": prompt}]
        return self.generate(messages, **kwargs)
    
    @property
    def _llm_type(self) -> str:
        """LangChain 호환성을 위한 타입 식별자"""
        return "perplexity"