from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_perplexity import ChatPerplexity
from core.perplexity_wrapper import PerplexityWrapper
from core.llm.claude.claude_wrapper import ClaudeWrapper
from core.llm.claude.claude_api_wrapper import ClaudeAPIWrapper
from core.file_utils import load_config, load_prompt_config
import logging


logger = logging.getLogger(__name__)


def _get_ai_parameters():
    """AI 파라미터 설정 로드"""
    prompt_config = load_prompt_config()
    ai_params = prompt_config.get('ai_parameters', {})
    response_settings = prompt_config.get('response_settings', {})
    
    return {
        'temperature': ai_params.get('temperature', 0.1),
        'max_tokens': response_settings.get('max_tokens', 4096),
        'top_p': ai_params.get('top_p', 0.9),
        'top_k': ai_params.get('top_k', 40),
        'frequency_penalty': ai_params.get('frequency_penalty', 0.0),
        'presence_penalty': ai_params.get('presence_penalty', 0.0),
        'stop_sequences': ai_params.get('stop_sequences', [])
    }


class LLMFactory(ABC):
    """LLM 생성을 위한 추상 팩토리"""
    
    @abstractmethod
    def create_llm(self, api_key: str, model_name: str, streaming: bool = False) -> Any:
        pass


class OpenAILLMFactory(LLMFactory):
    """OpenAI LLM 팩토리"""
    
    def create_llm(self, api_key: str, model_name: str, streaming: bool = False) -> ChatOpenAI:
        config = load_config()
        params = _get_ai_parameters()
        
        # OpenRouter 모델인지 확인
        models = config.get('models', {})
        model_config = models.get(model_name, {})
        provider = model_config.get('provider')
        
        # 공통 파라미터
        common_params = {
            'model': model_name,
            'openai_api_key': api_key,
            'temperature': params['temperature'],
            'max_tokens': params['max_tokens'],
            'top_p': params['top_p'],
            'frequency_penalty': params['frequency_penalty'],
            'presence_penalty': params['presence_penalty'],
            'streaming': streaming,
            'request_timeout': 120
        }
        
        # stop_sequences 추가 (있는 경우에만)
        if params['stop_sequences']:
            common_params['stop'] = params['stop_sequences']
        
        if provider == 'openrouter':
            logger.info(f"OpenRouter LLM 생성 - model: {model_name}, temp: {params['temperature']}, max_tokens: {params['max_tokens']}")
            common_params['openai_api_base'] = "https://openrouter.ai/api/v1"
            return ChatOpenAI(**common_params)
        else:
            logger.info(f"OpenAI LLM 생성 - temp: {params['temperature']}, max_tokens: {params['max_tokens']}")
            return ChatOpenAI(**common_params)


class GeminiLLMFactory(LLMFactory):
    """Gemini LLM 팩토리"""
    
    def create_llm(self, api_key: str, model_name: str, streaming: bool = False) -> ChatGoogleGenerativeAI:
        params = _get_ai_parameters()
        
        logger.info(f"Gemini LLM 생성 - temp: {params['temperature']}, max_tokens: {params['max_tokens']}, top_k: {params['top_k']}")
        
        gemini_params = {
            'model': model_name,
            'google_api_key': api_key,
            'temperature': params['temperature'],
            'convert_system_message_to_human': True,
            'max_tokens': params['max_tokens'],
            'top_p': params['top_p'],
            'top_k': params['top_k'],
            'streaming': streaming,
            'request_timeout': 120
        }
        
        # stop_sequences 추가 (있는 경우에만)
        if params['stop_sequences']:
            gemini_params['stop'] = params['stop_sequences']
        
        return ChatGoogleGenerativeAI(**gemini_params)



class PerplexityLLMFactory(LLMFactory):
    """Perplexity LLM 팩토리"""
    
    def create_llm(self, api_key: str, model_name: str, streaming: bool = False) -> PerplexityWrapper:
        params = _get_ai_parameters()
        
        logger.info(f"Perplexity LLM 생성 - model: {model_name}, temp: {params['temperature']}, max_tokens: {params['max_tokens']}")
        
        return PerplexityWrapper(
            model=model_name,
            pplx_api_key=api_key,
            temperature=params['temperature'],
            max_tokens=params['max_tokens'],
            top_p=params['top_p'],
            streaming=streaming,
            request_timeout=120
        )


class ClaudeLLMFactory(LLMFactory):
    """Claude LLM 팩토리"""
    
    def create_llm(self, api_key: str, model_name: str, streaming: bool = False) -> ClaudeWrapper:
        params = _get_ai_parameters()
        
        logger.info(f"Claude LLM 생성 - model: {model_name}, temp: {params['temperature']}, max_tokens: {params['max_tokens']}")
        
        # Claude 모델명을 Bedrock API 형식으로 변환
        bedrock_model_map = {
            "claude-2": "us.anthropic.claude-v2:1",
            "claude-3-haiku": "us.anthropic.claude-3-haiku-20240307-v1:0",
            "claude-3-sonnet": "us.anthropic.claude-3-sonnet-20240229-v1:0",
            "claude-3-opus": "us.anthropic.claude-3-opus-20240229-v1:0",
            "claude-3.5-sonnet": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "claude-3.5-haiku": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
            "claude-4": "us.anthropic.claude-3-5-sonnet-20241022-v2:0"  # fallback
        }
        
        bedrock_model = bedrock_model_map.get(model_name, "us.anthropic.claude-3-haiku-20240307-v1:0")
        
        return ClaudeWrapper(
            model=bedrock_model,
            aws_access_key_id=api_key,
            temperature=params['temperature'],
            max_tokens=params['max_tokens'],
            top_p=params['top_p'],
            streaming=streaming,
            request_timeout=120
        )


class LLMFactoryProvider:
    """LLM 팩토리 제공자"""
    
    _factories = {
        'gemini': GeminiLLMFactory(),
        'openai': OpenAILLMFactory(),
        'perplexity': PerplexityLLMFactory(),
        'anthropic': ClaudeLLMFactory(),
        'claude': ClaudeLLMFactory()
    }
    
    @classmethod
    def get_factory(cls, model_name: str) -> LLMFactory:
        """모델명에 따라 적절한 팩토리 반환"""
        # config.json에서 provider 정보 확인
        config = load_config()
        models = config.get('models', {})
        model_config = models.get(model_name, {})
        provider = model_config.get('provider')
        
        # provider가 명시되어 있으면 우선 사용
        if provider:
            if provider == 'google':
                return cls._factories['gemini']
            elif provider == 'perplexity':
                return cls._factories['perplexity']
            elif provider in ['claude', 'anthropic']:
                return cls._factories['claude']
            elif provider in ['openai', 'openrouter']:
                return cls._factories['openai']  # OpenRouter도 OpenAI 호환 API 사용
        
        # 기존 모델명 기반 매칭 (후방 호환성)
        if model_name.startswith("gemini"):
            return cls._factories['gemini']
        elif "sonar" in model_name and "perplexity" in model_name:
            return cls._factories['perplexity']
        elif "claude" in model_name:
            return cls._factories['claude']
        return cls._factories['openai']
    
    @classmethod
    def create_llm(cls, api_key: str, model_name: str, streaming: bool = False) -> Any:
        """LLM 인스턴스 생성"""
        factory = cls.get_factory(model_name)
        return factory.create_llm(api_key, model_name, streaming)