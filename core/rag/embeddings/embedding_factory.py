"""
Embedding Factory
Strategy 패턴: 임베딩 모델 생성
"""

from typing import Optional
from core.logging import get_logger
from .base_embeddings import BaseEmbeddings

logger = get_logger("embedding_factory")


class EmbeddingFactory:
    """임베딩 모델 팩토리"""
    
    @staticmethod
    def create(embedding_type: str, **kwargs) -> BaseEmbeddings:
        """
        Create embedding model
        
        Args:
            embedding_type: Type (local, openai, google, custom)
            **kwargs: Model-specific parameters
            
        Returns:
            BaseEmbeddings instance
        """
        if embedding_type == "local":
            from .korean_embeddings import KoreanEmbeddings
            
            # 사용자 커스텀 모델 우선
            if kwargs.get("use_custom_model") and kwargs.get("custom_model_path"):
                model_path = kwargs.get("custom_model_path")
                logger.info(f"Using custom model: {model_path}")
            else:
                model_path = kwargs.get("model", "exp-models/dragonkue-KoEn-E5-Tiny")
                logger.info(f"Using default model: {model_path}")
            
            cache_folder = kwargs.get("cache_folder")
            enable_cache = kwargs.get("enable_cache", True)
            return KoreanEmbeddings(model_path, cache_folder, enable_cache)
        
        elif embedding_type == "openai":
            from .openai_embeddings import OpenAIEmbeddings
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("OpenAI API key required")
            model = kwargs.get("model", "text-embedding-3-small")
            return OpenAIEmbeddings(api_key, model)
        
        elif embedding_type == "google":
            from .google_embeddings import GoogleEmbeddings
            api_key = kwargs.get("api_key")
            if not api_key:
                raise ValueError("Google API key required")
            model = kwargs.get("model", "embedding-001")
            return GoogleEmbeddings(api_key, model)
        
        elif embedding_type == "custom":
            from .custom_embeddings import CustomEmbeddings
            model_name = kwargs.get("model")
            if not model_name:
                raise ValueError("Model name required for custom embeddings")
            return CustomEmbeddings(model_name, **kwargs)
        
        else:
            raise ValueError(f"Unknown embedding type: {embedding_type}")
