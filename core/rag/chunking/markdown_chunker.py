"""
Markdown Chunker
"""

from typing import List
from langchain.schema import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter
from core.logging import get_logger
from .base_chunker import BaseChunker

logger = get_logger("markdown_chunker")


class MarkdownChunker(BaseChunker):
    """마크다운 전용 청킹 (헤더 기반)"""
    
    def __init__(self):
        """Initialize markdown chunker"""
        self.headers_to_split = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split
        )
        logger.info("Markdown chunker initialized")
    
    def chunk(self, text: str, metadata: dict = None) -> List[Document]:
        """Split markdown by headers"""
        try:
            chunks = self.splitter.split_text(text)
            
            # Add metadata
            for chunk in chunks:
                if metadata:
                    chunk.metadata.update(metadata)
            
            logger.debug(f"Created {len(chunks)} markdown chunks")
            return chunks
        except Exception as e:
            logger.error(f"Markdown chunking failed: {e}")
            return [Document(page_content=text, metadata=metadata or {})]
    
    @property
    def name(self) -> str:
        return "markdown"
