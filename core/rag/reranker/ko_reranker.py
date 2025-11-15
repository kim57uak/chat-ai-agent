"""
Korean Reranker implementation
"""

from typing import List, Tuple
from pathlib import Path
from .base_reranker import BaseReranker
from core.logging import get_logger
from core.dynamic_import_resolver import dynamic_import_resolver

logger = get_logger(__name__)

class KoReranker(BaseReranker):
    """한국어 전용 Reranker"""
    
    def __init__(self, model_path: str = None):
        """
        Args:
            model_path: 모델 경로 (None이면 기본 경로 사용)
        """
        self.model = None
        self.model_path = model_path
        self._load_model()
    
    def _load_model(self):
        """모델 로딩"""
        try:
            logger.info("[RERANKER] Starting model load...")
            
            CrossEncoder = dynamic_import_resolver.safe_import(
                'sentence_transformers',
                'CrossEncoder'
            )
            
            if CrossEncoder is None:
                logger.error("[RERANKER] CrossEncoder import failed")
                raise ImportError("CrossEncoder not available")
            
            logger.info("[RERANKER] CrossEncoder imported successfully")
            
            if self.model_path and Path(self.model_path).exists():
                logger.info(f"[RERANKER] Loading from custom path: {self.model_path}")
                self.model = CrossEncoder(self.model_path)
                logger.info(f"[RERANKER] ✓ Model loaded from: {self.model_path}")
            else:
                from core.rag.reranker_constants import RerankerConstants
                default_path = RerankerConstants.get_default_model_path()
                
                logger.info(f"[RERANKER] Checking default path: {default_path}")
                logger.info(f"[RERANKER] Path exists: {default_path.exists()}")
                
                if default_path.exists():
                    logger.info(f"[RERANKER] Loading from local: {default_path}")
                    self.model = CrossEncoder(str(default_path))
                    logger.info(f"[RERANKER] ✓ Model loaded from local: {default_path}")
                else:
                    hf_id = RerankerConstants.DEFAULT_MODEL_HF_ID
                    logger.info(f"[RERANKER] Downloading from HuggingFace: {hf_id}")
                    self.model = CrossEncoder(hf_id)
                    logger.info(f"[RERANKER] ✓ Model downloaded and loaded: {hf_id}")
            
            logger.info("[RERANKER] Model initialization complete")
                    
        except Exception as e:
            logger.error(f"[RERANKER] ✗ Failed to load model: {e}", exc_info=True)
            raise
    
    def rerank(self, query: str, documents: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """문서 재순위화"""
        if not self.model:
            logger.error("[RERANKER] Model not loaded")
            raise RuntimeError("Reranker model not loaded")
        
        if not documents:
            logger.warning("[RERANKER] No documents to rerank")
            return []
        
        logger.info(f"[RERANKER] Starting rerank: query_len={len(query)}, docs={len(documents)}, top_k={top_k}")
        
        try:
            pairs = [[query, doc] for doc in documents]
            logger.debug(f"[RERANKER] Created {len(pairs)} query-document pairs")
            
            scores = self.model.predict(pairs)
            logger.debug(f"[RERANKER] Prediction complete, scores: {scores[:5]}...")
            
            ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
            result = ranked[:top_k]
            
            logger.info(f"[RERANKER] ✓ Reranking complete: returned {len(result)} documents")
            logger.debug(f"[RERANKER] Top scores: {[f'{s:.4f}' for _, s in result[:3]]}")
            
            return result
        except Exception as e:
            logger.error(f"[RERANKER] ✗ Reranking failed: {e}", exc_info=True)
            raise
