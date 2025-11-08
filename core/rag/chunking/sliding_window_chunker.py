"""
Sliding Window Chunker
"""

from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from core.logging import get_logger
from .base_chunker import BaseChunker

logger = get_logger("sliding_window_chunker")


class SlidingWindowChunker(BaseChunker):
    """슬라이딩 윈도우 청킹 (현재 사용 중)"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        """
        Initialize sliding window chunker
        
        Args:
            chunk_size: Chunk size
            overlap: Overlap size
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len
        )
        logger.info(f"Sliding window chunker: size={chunk_size}, overlap={overlap}")
    
    def chunk(self, text: str, metadata: dict = None) -> List[Document]:
        """Split text into chunks"""
        try:
            chunks = self.splitter.create_documents([text], metadatas=[metadata or {}])
            logger.debug(f"Created {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Chunking failed: {e}")
            return [Document(page_content=text, metadata=metadata or {})]
    
    @property
    def name(self) -> str:
        return "sliding_window"
