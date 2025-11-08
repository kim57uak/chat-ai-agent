"""
Code Chunker
"""

from typing import List
from langchain.schema import Document
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter
from core.logging import get_logger
from .base_chunker import BaseChunker

logger = get_logger("code_chunker")


class CodeChunker(BaseChunker):
    """코드 전용 청킹 (LangChain Language Splitters)"""
    
    LANGUAGE_MAP = {
        "py": Language.PYTHON,
        "js": Language.JS,
        "ts": Language.TS,
        "java": Language.JAVA,
        "cpp": Language.CPP,
        "go": Language.GO,
        "rs": Language.RUST,
        "rb": Language.RUBY,
        "php": Language.PHP,
        "swift": Language.SWIFT,
        "kt": Language.KOTLIN,
        "scala": Language.SCALA,
        "c": Language.C,
        "cs": Language.CSHARP,
        "lua": Language.LUA,
        "md": Language.MARKDOWN,
        "html": Language.HTML,
        "sol": Language.SOL,
    }
    
    def __init__(self, language: str = "python", chunk_size: int = 500, overlap: int = 50):
        """
        Initialize code chunker
        
        Args:
            language: Programming language (python, javascript, etc.)
            chunk_size: Chunk size
            overlap: Overlap size
        """
        self.language = language
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.splitter = self._create_splitter()
        logger.info(f"Code chunker: {language}, size={chunk_size}")
    
    def _create_splitter(self):
        """Create language-specific splitter"""
        try:
            lang_enum = self.LANGUAGE_MAP.get(self.language.lower())
            if not lang_enum:
                logger.warning(f"Unknown language: {self.language}, using default")
                return RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.overlap
                )
            
            return RecursiveCharacterTextSplitter.from_language(
                language=lang_enum,
                chunk_size=self.chunk_size,
                chunk_overlap=self.overlap
            )
        except Exception as e:
            logger.error(f"Failed to create code splitter: {e}")
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.overlap
            )
    
    def chunk(self, text: str, metadata: dict = None) -> List[Document]:
        """Split code into chunks"""
        try:
            chunks = self.splitter.create_documents([text], metadatas=[metadata or {}])
            logger.debug(f"Created {len(chunks)} code chunks")
            return chunks
        except Exception as e:
            logger.error(f"Code chunking failed: {e}")
            return [Document(page_content=text, metadata=metadata or {})]
    
    @property
    def name(self) -> str:
        return f"code_{self.language}"
