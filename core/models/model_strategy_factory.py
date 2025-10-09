from typing import Dict, Type
from .base_model_strategy import BaseModelStrategy
from .openai_strategy import OpenAIStrategy
from .gemini_strategy import GeminiStrategy
from .gemini_image_strategy import GeminiImageStrategy
from .perplexity_strategy import PerplexityStrategy
from .claude_strategy import ClaudeStrategy
from .pollinations_strategy import PollinationsStrategy
from .openrouter_strategy import OpenRouterStrategy
from core.logging import get_logger

logger = get_logger("model_strategy_factory")


class ModelStrategyFactory:
    """AI 모델 전략 팩토리 - 새로운 모델 추가 시 확장 용이"""
    
    _strategies: Dict[str, Type[BaseModelStrategy]] = {
        'openai': OpenAIStrategy,
        'gemini': GeminiStrategy,
        'gemini_image': GeminiImageStrategy,
        'perplexity': PerplexityStrategy,
        'claude': ClaudeStrategy,
        'anthropic': ClaudeStrategy,
        'pollinations': PollinationsStrategy,
        'openrouter': OpenRouterStrategy,
    }
    
    @classmethod
    def create_strategy(cls, api_key: str, model_name: str) -> BaseModelStrategy:
        """모델명에 따라 적절한 전략 생성"""
        # config.json에서 provider 정보 확인
        from core.file_utils import load_config
        config = load_config()
        models = config.get('models', {})
        model_config = models.get(model_name, {})
        provider = model_config.get('provider')
        
        # provider가 명시되어 있으면 우선 사용
        if provider and provider in cls._strategies:
            strategy_class = cls._strategies[provider]
            logger.info(f"Using provider-based strategy for {model_name}: {provider}")
        else:
            # 모델명 기반 전략 결정
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
        
        if "image-preview" in model_lower and model_lower.startswith("gemini"):
            return 'gemini_image'
        elif model_lower.startswith("gemini"):
            return 'gemini'
        elif any(keyword in model_lower for keyword in ["sonar", "perplexity"]) and not model_lower.startswith(("deepseek/", "qwen/", "meta-llama/", "nvidia/", "moonshotai/")):
            return 'perplexity'
        elif "claude" in model_lower:
            return 'claude'
        elif model_lower.startswith("pollinations-") or "pollinations" in model_lower:
            return 'pollinations'
        elif any(keyword in model_lower for keyword in ["deepseek/", "qwen/", "meta-llama/", "nvidia/", "moonshotai/"]):
            return 'openrouter'
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


# 새로운 모델 추가 시 이 팩토리에 등록하여 사용