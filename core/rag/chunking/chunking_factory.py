"""
Chunking Factory
"""

from typing import Optional
from core.logging import get_logger
from .base_chunker import BaseChunker

logger = get_logger("chunking_factory")


class ChunkingFactory:
    """청킹 전략 팩토리"""
    
    @staticmethod
    def create(strategy: str, **kwargs) -> BaseChunker:
        """
        Create chunking strategy
        
        Args:
            strategy: Strategy name (sliding_window, semantic, code, markdown)
            **kwargs: Strategy-specific parameters
            
        Returns:
            BaseChunker instance
        """
        if strategy == "sliding_window":
            from .sliding_window_chunker import SlidingWindowChunker
            chunk_size = kwargs.get("chunk_size", 500)
            overlap = kwargs.get("overlap", 100)
            return SlidingWindowChunker(chunk_size, overlap)
        
        elif strategy == "semantic":
            from .semantic_chunker import SemanticChunker
            embeddings = kwargs.get("embeddings")
            if not embeddings:
                raise ValueError("Embeddings required for semantic chunking")
            threshold_type = kwargs.get("threshold_type", "percentile")
            threshold = kwargs.get("threshold", 95)
            return SemanticChunker(embeddings, threshold_type, threshold)
        
        elif strategy == "code":
            from .code_chunker import CodeChunker
            language = kwargs.get("language", "python")
            chunk_size = kwargs.get("chunk_size", 500)
            overlap = kwargs.get("overlap", 50)
            return CodeChunker(language, chunk_size, overlap)
        
        elif strategy == "markdown":
            from .markdown_chunker import MarkdownChunker
            return MarkdownChunker()
        
        else:
            logger.warning(f"Unknown strategy: {strategy}, using sliding_window")
            from .sliding_window_chunker import SlidingWindowChunker
            return SlidingWindowChunker()
    
    @staticmethod
    def get_strategy_for_file(filename: str, **kwargs) -> BaseChunker:
        """
        Auto-select strategy based on file extension
        
        Args:
            filename: File name
            **kwargs: Strategy parameters
            
        Returns:
            BaseChunker instance
        """
        ext = filename.lower().split('.')[-1]
        
        # Code files
        code_extensions = ['py', 'js', 'ts', 'java', 'cpp', 'c', 'go', 'rs', 'rb', 'php', 'swift', 'kt', 'scala', 'cs', 'lua', 'html', 'sol']
        if ext in code_extensions:
            logger.info(f"Auto-selected code chunking for {filename} (ext={ext})")
            return ChunkingFactory.create("code", language=ext, **kwargs)
        
        # Markdown
        if ext in ['md', 'markdown']:
            logger.info(f"Auto-selected markdown chunking for {filename}")
            return ChunkingFactory.create("markdown", **kwargs)
        
        # Default: sliding window
        logger.info(f"Auto-selected sliding_window chunking for {filename} (ext={ext})")
        return ChunkingFactory.create("sliding_window", **kwargs)
