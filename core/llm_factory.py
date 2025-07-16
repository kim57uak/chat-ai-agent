from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_perplexity import ChatPerplexity
from core.file_utils import load_config
import logging


logger = logging.getLogger(__name__)


class LLMFactory(ABC):
    """LLM 생성을 위한 추상 팩토리"""
    
    @abstractmethod
    def create_llm(self, api_key: str, model_name: str, streaming: bool = False) -> Any:
        pass


class OpenAILLMFactory(LLMFactory):
    """OpenAI LLM 팩토리"""
    
    def create_llm(self, api_key: str, model_name: str, streaming: bool = False) -> ChatOpenAI:
        config = load_config()
        response_settings = config.get("response_settings", {})
        max_tokens = response_settings.get("max_tokens", 4000)  # 대용량 응답 지원
        
        logger.info(f"OpenAI LLM 생성 - streaming: {streaming}, max_tokens: {max_tokens}")
        
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            temperature=0.1,
            max_tokens=max_tokens,
            streaming=streaming,
            request_timeout=120  # 대용량 응답을 위한 타임아웃 증가
        )


class GeminiLLMFactory(LLMFactory):
    """Gemini LLM 팩토리"""
    
    def create_llm(self, api_key: str, model_name: str, streaming: bool = False) -> ChatGoogleGenerativeAI:
        config = load_config()
        response_settings = config.get("response_settings", {})
        max_tokens = response_settings.get("max_tokens", 4000)  # 대용량 응답 지원
        
        logger.info(f"Gemini LLM 생성 - streaming: {streaming}, max_tokens: {max_tokens}")
        
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1,
            convert_system_message_to_human=True,
            max_tokens=max_tokens,
            streaming=streaming,
            request_timeout=120  # 대용량 응답을 위한 타임아웃 증가
        )



class PerplexityLLMFactory(LLMFactory):
    """Perplexity LLM 팩토리"""
    
    def create_llm(self, api_key: str, model_name: str, streaming: bool = False) -> ChatPerplexity:
        config = load_config()
        response_settings = config.get("response_settings", {})
        max_tokens = response_settings.get("max_tokens", 4000)
        
        logger.info(f"Perplexity LLM 생성 - model: {model_name}, max_tokens: {max_tokens}")
        
        return ChatPerplexity(
            model=model_name,
            pplx_api_key=api_key,
            temperature=0.1,
            max_tokens=max_tokens,
            streaming=streaming,
            request_timeout=120
        )


class LLMFactoryProvider:
    """LLM 팩토리 제공자"""
    
    _factories = {
        'gemini': GeminiLLMFactory(),
        'openai': OpenAILLMFactory(),
        'perplexity': PerplexityLLMFactory()
    }
    
    @classmethod
    def get_factory(cls, model_name: str) -> LLMFactory:
        """모델명에 따라 적절한 팩토리 반환"""
        if model_name.startswith("gemini"):
            return cls._factories['gemini']
        elif "sonar" in model_name or "r1-" in model_name or "perplexity" in model_name:
            return cls._factories['perplexity']
        return cls._factories['openai']
    
    @classmethod
    def create_llm(cls, api_key: str, model_name: str, streaming: bool = False) -> Any:
        """LLM 인스턴스 생성"""
        factory = cls.get_factory(model_name)
        return factory.create_llm(api_key, model_name, streaming)