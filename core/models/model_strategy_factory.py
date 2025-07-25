from typing import Dict, Type
from .base_model_strategy import BaseModelStrategy
from .openai_strategy import OpenAIStrategy
from .gemini_strategy import GeminiStrategy
from .perplexity_strategy import PerplexityStrategy
import logging

logger = logging.getLogger(__name__)


class ModelStrategyFactory:
    """AI 모델 전략 팩토리 - 새로운 모델 추가 시 확장 용이"""
    
    _strategies: Dict[str, Type[BaseModelStrategy]] = {
        'openai': OpenAIStrategy,
        'gemini': GeminiStrategy,
        'perplexity': PerplexityStrategy,
    }
    
    @classmethod
    def create_strategy(cls, api_key: str, model_name: str) -> BaseModelStrategy:
        """모델명에 따라 적절한 전략 생성"""
        strategy_type = cls._determine_strategy_type(model_name)
        strategy_class = cls._strategies.get(strategy_type)
        
        if not strategy_class:
            logger.warning(f"Unknown model type for {model_name}, using OpenAI strategy as fallback")
            strategy_class = OpenAIStrategy
        
        return strategy_class(api_key, model_name)
    
    @classmethod
    def _determine_strategy_type(cls, model_name: str) -> str:
        """모델명으로부터 전략 타입 결정"""
        model_lower = model_name.lower()
        
        if model_lower.startswith("gemini"):
            return 'gemini'
        elif any(keyword in model_lower for keyword in ["sonar", "r1-", "perplexity"]):
            return 'perplexity'
        else:
            return 'openai'  # 기본값
    
    @classmethod
    def register_strategy(cls, strategy_name: str, strategy_class: Type[BaseModelStrategy]):
        """새로운 전략 등록 (확장성)"""
        cls._strategies[strategy_name] = strategy_class
        logger.info(f"New strategy registered: {strategy_name}")
    
    @classmethod
    def get_supported_models(cls) -> Dict[str, Type[BaseModelStrategy]]:
        """지원되는 모델 전략 목록 반환"""
        return cls._strategies.copy()


# 새로운 모델 추가 예시
class ClaudeStrategy(BaseModelStrategy):
    """Claude 모델 전략 (예시)"""
    
    def create_llm(self):
        # Claude LLM 구현
        pass
    
    def create_messages(self, user_input: str, system_prompt: str = None):
        # Claude 메시지 형식 구현
        pass
    
    def process_image_input(self, user_input: str):
        # Claude 이미지 처리 구현
        pass
    
    def should_use_tools(self, user_input: str) -> bool:
        # Claude 도구 사용 결정 로직
        return False
    
    def create_agent_executor(self, tools):
        # Claude 에이전트 구현
        return None


# 새로운 전략 등록 (필요시)
# ModelStrategyFactory.register_strategy('claude', ClaudeStrategy)