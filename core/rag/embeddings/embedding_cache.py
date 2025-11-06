"""
Embedding Cache
임베딩 결과 캐싱으로 성능 향상
"""

from typing import List, Optional
from functools import lru_cache
import hashlib
import pickle
from pathlib import Path
from core.logging import get_logger

logger = get_logger("embedding_cache")


class EmbeddingCache:
    """임베딩 캐시 관리"""
    
    def __init__(self, cache_dir: Optional[str] = None, max_memory_cache: int = 1000):
        """
        Initialize embedding cache
        
        Args:
            cache_dir: Disk cache directory (None for memory only)
            max_memory_cache: Max items in memory cache
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.max_memory_cache = max_memory_cache
        self.memory_cache = {}
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Disk cache enabled: {cache_dir}")
        else:
            logger.info("Memory cache only")
    
    def _get_hash(self, text: str) -> str:
        """텍스트 해시 생성"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """
        Get cached embedding
        
        Args:
            text: Input text
            
        Returns:
            Cached embedding or None
        """
        text_hash = self._get_hash(text)
        
        # Memory cache 확인
        if text_hash in self.memory_cache:
            logger.debug(f"Memory cache hit: {text[:50]}")
            return self.memory_cache[text_hash]
        
        # Disk cache 확인
        if self.cache_dir:
            cache_file = self.cache_dir / f"{text_hash}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        embedding = pickle.load(f)
                    
                    # Memory cache에 추가
                    self._add_to_memory(text_hash, embedding)
                    
                    logger.debug(f"Disk cache hit: {text[:50]}")
                    return embedding
                except Exception as e:
                    logger.error(f"Failed to load cache: {e}")
        
        return None
    
    def set(self, text: str, embedding: List[float]):
        """
        Cache embedding
        
        Args:
            text: Input text
            embedding: Embedding vector
        """
        text_hash = self._get_hash(text)
        
        # Memory cache에 추가
        self._add_to_memory(text_hash, embedding)
        
        # Disk cache에 저장
        if self.cache_dir:
            cache_file = self.cache_dir / f"{text_hash}.pkl"
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(embedding, f)
                logger.debug(f"Cached to disk: {text[:50]}")
            except Exception as e:
                logger.error(f"Failed to save cache: {e}")
    
    def _add_to_memory(self, text_hash: str, embedding: List[float]):
        """Memory cache에 추가 (LRU)"""
        if len(self.memory_cache) >= self.max_memory_cache:
            # 가장 오래된 항목 제거
            oldest = next(iter(self.memory_cache))
            del self.memory_cache[oldest]
        
        self.memory_cache[text_hash] = embedding
    
    def clear(self):
        """캐시 전체 삭제"""
        self.memory_cache.clear()
        
        if self.cache_dir and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            logger.info("Cache cleared")
    
    def get_stats(self) -> dict:
        """캐시 통계"""
        stats = {
            "memory_items": len(self.memory_cache),
            "max_memory": self.max_memory_cache
        }
        
        if self.cache_dir and self.cache_dir.exists():
            disk_items = len(list(self.cache_dir.glob("*.pkl")))
            stats["disk_items"] = disk_items
        
        return stats
