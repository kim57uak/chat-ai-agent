"""
Universal SentenceTransformer Embeddings
설정된 모든 sentence_transformers 모델 지원
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import sys
from core.logging import get_logger
from .base_embeddings import BaseEmbeddings
from .embedding_cache import EmbeddingCache

logger = get_logger("sentence_transformer_embeddings")


class SentenceTransformerEmbeddings(BaseEmbeddings):
    """범용 SentenceTransformer 임베딩 클래스"""
    
    def __init__(self, model_config: Dict[str, Any], cache_folder: Optional[str] = None, enable_cache: bool = True):
        """
        Initialize SentenceTransformer embeddings
        
        Args:
            model_config: 모델 설정 정보 (name, dimension, model_path 등)
            cache_folder: Cache directory
            enable_cache: Enable embedding cache
        """
        self.model_config = model_config
        self.model_name = model_config.get("name", "Unknown Model")
        self.model_path = self._resolve_model_path(model_config)
        self.cache_folder = cache_folder
        self.model = None
        from ..constants import DEFAULT_EMBEDDING_DIMENSION
        self._dimension = model_config.get("dimension", DEFAULT_EMBEDDING_DIMENSION)
        
        # 임베딩 캐시 초기화
        self.embedding_cache = EmbeddingCache(
            cache_dir=cache_folder, 
            max_memory_cache=1000
        ) if enable_cache else None
        
        self._load_model()
        logger.info(f"SentenceTransformer embeddings initialized: {self.model_name} (dimension: {self._dimension})")
    
    def _resolve_model_path(self, model_config: Dict[str, Any]) -> str:
        """모델 경로 결정 (설정 기반)"""
        # 1. model 필드 우선 사용
        if "model" in model_config:
            return model_config["model"]
        
        # 2. model_path 필드 사용
        if "model_path" in model_config:
            return model_config["model_path"]
        
        # 3. 모델 ID 그대로 사용
        return model_config.get("id", "unknown-model")
    
    def _load_model(self):
        """Load embedding model (lazy loading)"""
        logger.info(f"[MODEL_LOAD] Starting model load for: {self.model_name}")
        
        try:
            logger.info(f"[MODEL_LOAD] Step 1: Importing sentence_transformers")
            from sentence_transformers import SentenceTransformer
            logger.info(f"[MODEL_LOAD] Step 1: SUCCESS - sentence-transformers imported")
            
            # 로컬 모델 경로 확인 (기본 모델만)
            logger.info(f"[MODEL_LOAD] Step 2: Resolving model path for: {self.model_path}")
            local_path = self._get_local_model_path()
            if local_path and local_path.exists():
                model_path = str(local_path)
                logger.info(f"[MODEL_LOAD] Step 2: SUCCESS - Using local model: {model_path}")
            else:
                model_path = self.model_path
                logger.info(f"[MODEL_LOAD] Step 2: Using configured model: {model_path}")
            
            # HuggingFace 모델 다운로드 시 자동 재시도
            logger.info(f"[MODEL_LOAD] Step 3: Creating SentenceTransformer instance")
            try:
                self.model = SentenceTransformer(
                    model_path,
                    cache_folder=self.cache_folder
                )
                logger.info(f"[MODEL_LOAD] Step 3: SUCCESS - SentenceTransformer created: {model_path}")
            except Exception as download_error:
                logger.error(f"[MODEL_LOAD] Step 3: FAILED - {type(download_error).__name__}: {download_error}")
                
                # 잘못된 모델 ID 형식 자동 수정 시도
                if "_" in model_path and "/" not in model_path:
                    corrected_path = model_path.replace("_", "/", 1)
                    logger.info(f"[MODEL_LOAD] Step 3b: Retry with corrected path: {corrected_path}")
                    try:
                        self.model = SentenceTransformer(
                            corrected_path,
                            cache_folder=self.cache_folder
                        )
                        self.model_path = corrected_path
                        logger.info(f"[MODEL_LOAD] Step 3b: SUCCESS - Model loaded with corrected path")
                    except Exception as retry_error:
                        logger.error(f"[MODEL_LOAD] Step 3b: FAILED - {type(retry_error).__name__}: {retry_error}")
                        raise download_error
                else:
                    raise download_error
            
            # 실제 차원 확인 및 업데이트
            logger.info(f"[MODEL_LOAD] Step 4: Testing model with sample text")
            test_embedding = self.model.encode("test", convert_to_numpy=True)
            actual_dimension = len(test_embedding)
            logger.info(f"[MODEL_LOAD] Step 4: SUCCESS - Test embedding created (dimension: {actual_dimension})")
            
            if actual_dimension != self._dimension:
                logger.warning(f"[MODEL_LOAD] Dimension mismatch: config={self._dimension}, actual={actual_dimension}")
                self._dimension = actual_dimension
            
            logger.info(f"[MODEL_LOAD] COMPLETE: Model fully loaded and tested (dimension: {self._dimension})")
            
        except ImportError as ie:
            logger.error(f"[MODEL_LOAD] IMPORT_ERROR: sentence-transformers not available: {ie}")
            logger.error(f"[MODEL_LOAD] Check if sentence-transformers is installed: pip install sentence-transformers")
            self.model = None
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"[MODEL_LOAD] {error_type}: Failed to load model '{self.model_path}': {error_msg}")
            
            # 상세 에러 분석
            if "not a valid model identifier" in error_msg:
                logger.error(f"[MODEL_LOAD] Model '{self.model_path}' not found on HuggingFace Hub")
                logger.info(f"[MODEL_LOAD] Available alternatives: jinaai/jina-embeddings-v2-base-en, sentence-transformers/all-MiniLM-L6-v2")
            elif "private repository" in error_msg:
                logger.error(f"[MODEL_LOAD] Model '{self.model_path}' requires authentication")
                logger.info(f"[MODEL_LOAD] Run 'huggingface-cli login' or set HF_TOKEN environment variable")
            elif "No such file or directory" in error_msg:
                logger.error(f"[MODEL_LOAD] Local model file not found: {self.model_path}")
            elif "Permission denied" in error_msg:
                logger.error(f"[MODEL_LOAD] Permission denied accessing: {self.model_path}")
            else:
                logger.error(f"[MODEL_LOAD] Unexpected error type: {error_type}")
                logger.info(f"[MODEL_LOAD] Hint: HuggingFace model IDs should use '/' format (e.g., 'jinaai/jina-embeddings-v2-base-en')")
            
            self.model = None
    
    def _get_local_model_path(self) -> Optional[Path]:
        """로컬 모델 경로 반환 (기본 모델만)"""
        try:
            from ..constants import DEFAULT_EMBEDDING_MODEL
            # 기본 모델인지 확인 (경로에 기본 모델명이 포함되면 기본 모델)
            if DEFAULT_EMBEDDING_MODEL not in self.model_path:
                logger.info(f"Not a default model, skipping local path: {self.model_path}")
                return None
            
            logger.info(f"Default model detected, checking local path: {self.model_path}")
            
            if getattr(sys, 'frozen', False):
                # 패키징된 앱 - 실제 실행 위치 기반
                if sys.platform == 'darwin':
                    base_path = Path(sys.executable).parent.parent / 'Resources'
                else:
                    base_path = Path(sys.executable).parent
            else:
                # 개발 환경
                base_path = Path(__file__).parent.parent.parent.parent
            
            model_path = base_path / "models" / "embeddings" / DEFAULT_EMBEDDING_MODEL
            
            # 경로 존재 여부 로깅
            if model_path.exists():
                logger.info(f"Found local model at: {model_path}")
            else:
                logger.warning(f"Local model not found at: {model_path}")
            
            return model_path if model_path.exists() else None
        except Exception as e:
            logger.error(f"Error resolving local model path: {e}")
            return None
    
    def embed_documents(self, texts: List[str], check_cancel: Optional[callable] = None) -> List[List[float]]:
        """
        Embed multiple documents with caching and cancellation support
        
        Args:
            texts: List of text documents
            check_cancel: Optional cancellation check function
            
        Returns:
            List of embedding vectors
        """
        if not self.model:
            logger.warning("Model not available, returning zero vectors")
            return [[0.0] * self._dimension for _ in texts]
        
        # 취소 확인
        if check_cancel and check_cancel():
            logger.info("Embedding cancelled by user")
            return [[0.0] * self._dimension for _ in texts]
        
        try:
            if not self.embedding_cache:
                # 캐시 비활성화 - 배치 처리로 취소 확인
                if len(texts) > 10:  # 큰 배치는 분할 처리
                    batch_size = 10
                    all_embeddings = []
                    for i in range(0, len(texts), batch_size):
                        if check_cancel and check_cancel():
                            logger.info(f"Embedding cancelled at batch {i//batch_size + 1}")
                            return [[0.0] * self._dimension for _ in texts]
                        
                        batch = texts[i:i + batch_size]
                        batch_embeddings = self.model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
                        all_embeddings.extend(batch_embeddings.tolist())
                    return all_embeddings
                else:
                    embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                    return embeddings.tolist()
            
            # 캐시에서 검색
            results = []
            to_embed = []
            to_embed_indices = []
            
            for i, text in enumerate(texts):
                if check_cancel and check_cancel():
                    logger.info("Embedding cancelled during cache check")
                    return [[0.0] * self._dimension for _ in texts]
                
                cached = self.embedding_cache.get(text)
                if cached:
                    results.append(cached)
                else:
                    results.append(None)
                    to_embed.append(text)
                    to_embed_indices.append(i)
            
            # 캐시 미스: 새로 임베딩
            if to_embed:
                if check_cancel and check_cancel():
                    logger.info("Embedding cancelled before processing")
                    return [[0.0] * self._dimension for _ in texts]
                
                new_embeddings = self.model.encode(to_embed, convert_to_numpy=True, show_progress_bar=False).tolist()
                
                for idx, embedding in zip(to_embed_indices, new_embeddings):
                    results[idx] = embedding
                    self.embedding_cache.set(texts[idx], embedding)
                
                logger.debug(f"Cache miss: {len(to_embed)}/{len(texts)} texts")
            else:
                logger.debug(f"Cache hit: {len(texts)}/{len(texts)} texts")
            
            return results
            
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return [[0.0] * self._dimension for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query with caching
        
        Args:
            text: Query text
            
        Returns:
            Embedding vector
        """
        if not self.model:
            logger.warning("Model not available, returning zero vector")
            return [0.0] * self._dimension
        
        try:
            # 캐시 확인
            if self.embedding_cache:
                cached = self.embedding_cache.get(text)
                if cached:
                    logger.debug(f"Cache hit for query: {text[:50]}")
                    return cached
            
            # 임베딩 생성
            embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            result = embedding.tolist()
            
            # 캐시 저장
            if self.embedding_cache:
                self.embedding_cache.set(text, result)
            
            logger.debug(f"Embedded query: {text[:50]}")
            return result
            
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            return [0.0] * self._dimension
    
    @property
    def dimension(self) -> int:
        """
        Get embedding dimension
        
        Returns:
            Dimension size
        """
        return self._dimension
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information
        
        Returns:
            Model info dictionary
        """
        return {
            "model_name": self.model_name,
            "model_path": self.model_path,
            "dimension": self._dimension,
            "cache_enabled": self.embedding_cache is not None,
            "model_config": self.model_config
        }