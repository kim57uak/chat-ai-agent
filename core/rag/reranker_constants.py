"""
Reranker model constants
"""

from pathlib import Path
import sys

class RerankerConstants:
    """Reranker 모델 상수 관리"""
    
    DEFAULT_MODEL_NAME = "ms-marco-MiniLM-L-12-v2"
    DEFAULT_MODEL_HF_ID = "cross-encoder/ms-marco-MiniLM-L-12-v2"
    DEFAULT_MODEL_SIZE = "128MB"
    DEFAULT_MODEL_LANGUAGE = "한영 혼합"
    
    @staticmethod
    def get_models_base_path() -> Path:
        """모델 기본 경로 반환"""
        if getattr(sys, 'frozen', False):
            if sys.platform == 'darwin':
                base = Path(sys.executable).parent.parent / 'Resources'
            else:
                base = Path(sys.executable).parent
        else:
            base = Path(__file__).parent.parent.parent
        return base / 'models' / 'reranker'
    
    @staticmethod
    def get_default_model_path() -> Path:
        """기본 모델 경로"""
        return RerankerConstants.get_models_base_path() / RerankerConstants.DEFAULT_MODEL_NAME
    
    @classmethod
    def get_available_models(cls):
        """사용 가능한 모델 목록 반환 (기본 모델만)"""
        return [
            {
                "name": f"{cls.DEFAULT_MODEL_NAME} ({cls.DEFAULT_MODEL_LANGUAGE}, 고성능)",
                "model_id": cls.DEFAULT_MODEL_HF_ID,
                "local_name": cls.DEFAULT_MODEL_NAME,
                "size": cls.DEFAULT_MODEL_SIZE,
                "language": cls.DEFAULT_MODEL_LANGUAGE,
                "is_default": True
            }
        ]
