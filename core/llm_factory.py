from abc import ABC, abstractmethod
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


class LLMFactory(ABC):
    """LLM 생성을 위한 추상 팩토리"""
    
    @abstractmethod
    def create_llm(self, api_key: str, model_name: str) -> Any:
        pass


class OpenAILLMFactory(LLMFactory):
    """OpenAI LLM 팩토리"""
    
    def create_llm(self, api_key: str, model_name: str) -> ChatOpenAI:
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            temperature=0.1,
            max_tokens=4096
        )


class GeminiLLMFactory(LLMFactory):
    """Gemini LLM 팩토리"""
    
    def create_llm(self, api_key: str, model_name: str) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1,
            convert_system_message_to_human=True,
            max_tokens=4096
        )


class LLMFactoryProvider:
    """LLM 팩토리 제공자"""
    
    _factories = {
        'gemini': GeminiLLMFactory(),
        'openai': OpenAILLMFactory()
    }
    
    @classmethod
    def get_factory(cls, model_name: str) -> LLMFactory:
        """모델명에 따라 적절한 팩토리 반환"""
        if model_name.startswith("gemini"):
            return cls._factories['gemini']
        return cls._factories['openai']
    
    @classmethod
    def create_llm(cls, api_key: str, model_name: str) -> Any:
        """LLM 인스턴스 생성"""
        factory = cls.get_factory(model_name)
        return factory.create_llm(api_key, model_name)