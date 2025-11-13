"""
새로운 청킹 전략 추가 예시 - 기존 코드 수정 없음
"""

from typing import List
from langchain.schema import Document
from core.logging import get_logger
from .base_chunker import BaseChunker

logger = get_logger("table_chunker")


class TableChunker(BaseChunker):
    """테이블 전용 청킹 전략 (새로 추가)"""
    
    def __init__(self, max_rows_per_chunk: int = 50):
        self.max_rows = max_rows_per_chunk
        logger.info(f"Table chunker: max_rows={max_rows_per_chunk}")
    
    def chunk(self, text: str, metadata: dict = None) -> List[Document]:
        """테이블을 행 단위로 청킹"""
        lines = text.strip().split('\n')
        chunks = []
        
        current_chunk = []
        for line in lines:
            current_chunk.append(line)
            
            if len(current_chunk) >= self.max_rows:
                chunk_text = '\n'.join(current_chunk)
                chunks.append(Document(
                    page_content=chunk_text,
                    metadata=metadata or {}
                ))
                current_chunk = []
        
        # 마지막 청크
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(Document(
                page_content=chunk_text,
                metadata=metadata or {}
            ))
        
        logger.debug(f"Created {len(chunks)} table chunks")
        return chunks
    
    @property
    def name(self) -> str:
        return "table"