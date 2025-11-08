"""
Chunk Manager
청크 생성 및 관리
"""

from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from core.logging import get_logger

logger = get_logger("chunk_manager")


class ChunkManager:
    """청크 관리자"""
    
    def __init__(
        self, 
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize chunk manager
        
        Args:
            chunk_size: Chunk size in characters
            chunk_overlap: Overlap between chunks
            separators: Custom separators
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 기본 구분자 (한국어 최적화)
        if separators is None:
            separators = [
                "\n\n",  # 단락
                "\n",    # 줄바꿈
                ". ",    # 문장 (영어)
                "。",    # 문장 (일본어)
                ".",     # 마침표
                " ",     # 공백
                ""       # 문자
            ]
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len
        )
        
        logger.info(f"ChunkManager initialized: size={chunk_size}, overlap={chunk_overlap}")
    
    def create_chunks(self, documents: List[Document]) -> List[Document]:
        """
        Create chunks from documents
        
        Args:
            documents: List of documents
            
        Returns:
            List of chunked documents
        """
        if not documents:
            return []
        
        try:
            chunks = self.text_splitter.split_documents(documents)
            
            # 청크 ID 추가
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = f"chunk_{i}"
                chunk.metadata["chunk_index"] = i
            
            logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to create chunks: {e}")
            return []
    
    def create_chunks_with_metadata(
        self, 
        documents: List[Document],
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Create chunks with additional metadata
        
        Args:
            documents: List of documents
            additional_metadata: Additional metadata to add
            
        Returns:
            List of chunked documents with metadata
        """
        chunks = self.create_chunks(documents)
        
        if additional_metadata:
            for chunk in chunks:
                chunk.metadata.update(additional_metadata)
        
        return chunks
    
    def get_chunk_info(self, chunk: Document) -> Dict[str, Any]:
        """
        Get chunk information
        
        Args:
            chunk: Document chunk
            
        Returns:
            Chunk information
        """
        return {
            "chunk_id": chunk.metadata.get("chunk_id"),
            "chunk_index": chunk.metadata.get("chunk_index"),
            "source": chunk.metadata.get("source"),
            "content_length": len(chunk.page_content),
            "metadata": chunk.metadata
        }
    
    def filter_chunks(
        self, 
        chunks: List[Document],
        filter_fn
    ) -> List[Document]:
        """
        Filter chunks by custom function
        
        Args:
            chunks: List of chunks
            filter_fn: Filter function
            
        Returns:
            Filtered chunks
        """
        try:
            filtered = [chunk for chunk in chunks if filter_fn(chunk)]
            logger.info(f"Filtered {len(chunks)} -> {len(filtered)} chunks")
            return filtered
        except Exception as e:
            logger.error(f"Failed to filter chunks: {e}")
            return chunks
    
    def merge_chunks(self, chunks: List[Document]) -> Document:
        """
        Merge multiple chunks into one document
        
        Args:
            chunks: List of chunks
            
        Returns:
            Merged document
        """
        if not chunks:
            return Document(page_content="", metadata={})
        
        # 내용 병합
        merged_content = "\n\n".join([chunk.page_content for chunk in chunks])
        
        # 메타데이터 병합 (첫 번째 청크 기준)
        merged_metadata = chunks[0].metadata.copy()
        merged_metadata["merged_chunks"] = len(chunks)
        merged_metadata["chunk_ids"] = [
            chunk.metadata.get("chunk_id") for chunk in chunks
        ]
        
        return Document(
            page_content=merged_content,
            metadata=merged_metadata
        )
    
    def get_chunk_statistics(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        Get chunk statistics
        
        Args:
            chunks: List of chunks
            
        Returns:
            Statistics dictionary
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_length": 0,
                "min_length": 0,
                "max_length": 0
            }
        
        lengths = [len(chunk.page_content) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_length": sum(lengths) / len(lengths),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "total_characters": sum(lengths)
        }
