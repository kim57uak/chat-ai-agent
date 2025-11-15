"""
Base Reranker interface
"""

from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseReranker(ABC):
    """Reranker 기본 인터페이스"""
    
    @abstractmethod
    def rerank(self, query: str, documents: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        문서 재순위화
        
        Args:
            query: 검색 쿼리
            documents: 문서 리스트
            top_k: 반환할 상위 문서 수
            
        Returns:
            (문서, 점수) 튜플 리스트
        """
        pass
