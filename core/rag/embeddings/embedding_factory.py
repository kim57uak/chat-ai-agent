"""
Embedding Factory
Strategy 패턴: 임베딩 모델 생성
"""

from typing import Optional
from core.logging import get_logger
from .base_embeddings import BaseEmbeddings
from ..constants import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIMENSION, DEFAULT_EMBEDDING_PATH

logger = get_logger("embedding_factory")


class EmbeddingFactory:
    """임베딩 모델 팩토리"""
    
    @staticmethod
    def create_embeddings(model_id: Optional[str] = None) -> BaseEmbeddings:
        """
        현재 모델 기반 임베딩 생성
        
        Args:
            model_id: 모델 ID (None이면 현재 모델 사용)
            
        Returns:
            BaseEmbeddings instance
        """
        try:
            from .embedding_model_manager import EmbeddingModelManager
            manager = EmbeddingModelManager()
            
            if model_id is None:
                model_id = manager.get_current_model()
            
            model_info = manager.get_model_info(model_id)
            if not model_info:
                logger.warning(f"Model {model_id} not found, using default")
                model_id = manager.DEFAULT_MODEL
                model_info = manager.get_model_info(model_id)
            
            provider = model_info.get("provider", "sentence_transformers")
            
            if provider == "sentence_transformers":
                # 범용 SentenceTransformer 임베딩 사용
                from .sentence_transformer_embeddings import SentenceTransformerEmbeddings
                
                # 모델 설정 정보 준비
                model_config = {
                    "id": model_id,
                    "name": model_info.get("name", model_id),
                    "dimension": model_info.get("dimension", DEFAULT_EMBEDDING_DIMENSION),
                    "description": model_info.get("description", ""),
                    "provider": provider
                }
                
                # 추가 설정이 있으면 포함
                if "model_path" in model_info:
                    model_config["model_path"] = model_info["model_path"]
                
                return SentenceTransformerEmbeddings(model_config)
            
            elif provider == "openai":
                from .openai_embeddings import OpenAIEmbeddings
                # API 키는 config.json에서 가져오기
                from core.file_utils import load_config
                config = load_config()
                api_key = config.get("models", {}).get("openai", {}).get("api_key")
                if not api_key:
                    raise ValueError("OpenAI API key not configured")
                return OpenAIEmbeddings(api_key, model_id)
            
            elif provider == "google":
                from .google_embeddings import GoogleEmbeddings
                from core.file_utils import load_config
                config = load_config()
                api_key = config.get("models", {}).get("google", {}).get("api_key")
                if not api_key:
                    raise ValueError("Google API key not configured")
                return GoogleEmbeddings(api_key, model_id)
            
            else:
                logger.warning(f"Unknown provider {provider}, using sentence_transformers fallback")
                from .sentence_transformer_embeddings import SentenceTransformerEmbeddings
                
                # 폴백 모델 설정
                fallback_config = {
                    "id": DEFAULT_EMBEDDING_MODEL,
                    "name": "한국어 E5-Tiny (Fallback)",
                    "dimension": DEFAULT_EMBEDDING_DIMENSION,
                    "provider": "sentence_transformers"
                }
                return SentenceTransformerEmbeddings(fallback_config)
                
        except Exception as e:
            logger.error(f"Failed to create embeddings for {model_id}: {e}")
            # 폴백: 기본 모델
            from .sentence_transformer_embeddings import SentenceTransformerEmbeddings
            
            try:
                from .embedding_model_manager import EmbeddingModelManager
                manager = EmbeddingModelManager()
                fallback_config = {
                    "id": DEFAULT_EMBEDDING_MODEL,
                    "name": "한국어 E5-Tiny (Emergency Fallback)",
                    "dimension": DEFAULT_EMBEDDING_DIMENSION,
                    "provider": "sentence_transformers"
                }
                return SentenceTransformerEmbeddings(fallback_config)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                # 최후의 수단: 기존 KoreanEmbeddings
                from .korean_embeddings import KoreanEmbeddings
                return KoreanEmbeddings()
    
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
            from .sentence_transformer_embeddings import SentenceTransformerEmbeddings
            
            # 모델 설정 준비
            model_path = kwargs.get("model", DEFAULT_EMBEDDING_PATH)
            
            model_config = {
                "id": model_path,
                "name": kwargs.get("name", "Local Model"),
                "dimension": kwargs.get("dimension", DEFAULT_EMBEDDING_DIMENSION),
                "provider": "sentence_transformers",
                "model_path": model_path
            }
            
            # 사용자 커스텀 모델 처리
            if kwargs.get("use_custom_model") and kwargs.get("custom_model_path"):
                model_config["model_path"] = kwargs.get("custom_model_path")
                model_config["name"] = f"Custom: {kwargs.get('custom_model_path')}"
                logger.info(f"Using custom model: {model_config['model_path']}")
            
            return SentenceTransformerEmbeddings(
                model_config,
                cache_folder=kwargs.get("cache_folder"),
                enable_cache=kwargs.get("enable_cache", True)
            )
        
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
    
    @staticmethod
    def get_current_embeddings() -> BaseEmbeddings:
        """현재 설정된 임베딩 모델 반환"""
        return EmbeddingFactory.create_embeddings()
