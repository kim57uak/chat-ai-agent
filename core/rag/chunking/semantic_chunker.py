"""
Semantic Chunker
"""

from typing import List
from langchain.schema import Document
from core.logging import get_logger
from .base_chunker import BaseChunker

logger = get_logger("semantic_chunker")


class SemanticChunker(BaseChunker):
    """의미 기반 청킹 (LangChain SemanticChunker)"""
    
    def __init__(self, embeddings, threshold_type: str = "percentile", threshold: float = 95):
        """
        Initialize semantic chunker
        
        Args:
            embeddings: Embedding model
            threshold_type: percentile, standard_deviation, interquartile
            threshold: Threshold value
        """
        self.embeddings = embeddings
        self.threshold_type = threshold_type
        self.threshold = threshold
        self.splitter = None
        self._load_splitter()
        logger.info(f"Semantic chunker: {threshold_type}={threshold}")
    
    def _load_splitter(self):
        """Load semantic splitter"""
        try:
            from langchain_experimental.text_splitter import SemanticChunker
            self.splitter = SemanticChunker(
                self.embeddings,
                breakpoint_threshold_type=self.threshold_type,
                breakpoint_threshold_amount=self.threshold
            )
        except ImportError:
            logger.error("langchain-experimental not installed")
            self.splitter = None
        except Exception as e:
            logger.error(f"Failed to load semantic chunker: {e}")
            self.splitter = None
    
    def chunk(self, text: str, metadata: dict = None) -> List[Document]:
        """Split text into semantic chunks"""
        if not self.splitter:
            logger.warning("Semantic chunker not available, using simple split")
            return [Document(page_content=text, metadata=metadata or {})]
        
        try:
            chunks = self.splitter.create_documents([text], metadatas=[metadata or {}])
            logger.debug(f"Created {len(chunks)} semantic chunks")
            return chunks
        except Exception as e:
            logger.error(f"Semantic chunking failed: {e}")
            return [Document(page_content=text, metadata=metadata or {})]
    
    @property
    def name(self) -> str:
        return "semantic"
