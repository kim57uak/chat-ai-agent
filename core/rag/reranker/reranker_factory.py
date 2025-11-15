"""
Reranker Factory
"""

from typing import Optional
from .base_reranker import BaseReranker
from .ko_reranker import KoReranker
from core.rag.reranker_constants import RerankerConstants
from core.logging import get_logger

logger = get_logger(__name__)

class RerankerFactory:
    """Reranker 팩토리"""
    
    @staticmethod
    def create_reranker(model_name: str = None, model_path: Optional[str] = None) -> BaseReranker:
        """
        Reranker 생성
        
        Args:
            model_name: 모델 이름 (None이면 기본 모델)
            model_path: 모델 경로
            
        Returns:
            BaseReranker 인스턴스
        """
        if model_name is None:
            model_name = RerankerConstants.DEFAULT_MODEL_NAME
        
        logger.info(f"[RERANKER FACTORY] Creating reranker: model={model_name}, path={model_path}")
        
        # 모델 경로 결정
        if model_path is None:
            from pathlib import Path
            base_path = RerankerConstants.get_models_base_path()
            model_path = str(base_path / model_name)
            logger.info(f"[RERANKER FACTORY] Using default path: {model_path}")
        
        reranker = KoReranker(model_path)
        logger.info(f"[RERANKER FACTORY] ✓ Reranker created successfully")
        
        return reranker
    
    @staticmethod
    def get_available_models():
        """사용 가능한 모델 목록 반환"""
        return RerankerConstants.get_available_models()
