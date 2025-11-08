"""
Batch Processor
"""

from pathlib import Path
from typing import List, Callable, Optional
from core.logging import get_logger

logger = get_logger("batch_processor")


class BatchProcessor:
    """배치 프로세서"""
    
    def __init__(self, storage_manager, embeddings, max_workers: int = 1, chunking_strategy: Optional[str] = None):
        """
        Initialize batch processor
        
        Args:
            storage_manager: RAGStorageManager instance
            embeddings: Embedding model
            max_workers: Max parallel workers (unused, sequential processing)
            chunking_strategy: Override chunking strategy (None for auto)
        """
        self.storage = storage_manager
        self.embeddings = embeddings
        self.chunking_strategy = chunking_strategy
        logger.info(f"Batch processor: sequential mode, strategy={chunking_strategy or 'auto'}")
    
    def process_files(
        self,
        files: List[Path],
        topic_id: str,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        check_cancel: Optional[Callable] = None
    ):
        """
        Process files sequentially
        
        Args:
            files: List of file paths
            topic_id: Topic ID
            on_progress: Progress callback (file_path, current, total)
            on_complete: Complete callback (file_path, doc_id, chunk_count)
            on_error: Error callback (file_path, error)
            check_cancel: Cancel check callback
        """
        total = len(files)
        logger.info(f"Processing {total} files sequentially")
        processed_docs = []
        
        for i, file_path in enumerate(files, 1):
            # Check cancel
            if check_cancel and check_cancel():
                logger.warning(f"Processing cancelled at {i}/{total}")
                # Rollback: delete processed documents
                for doc_id in processed_docs:
                    try:
                        self.storage.delete_document(doc_id)
                        logger.info(f"Rolled back document: {doc_id}")
                    except Exception as e:
                        logger.error(f"Failed to rollback {doc_id}: {e}")
                return
            
            try:
                result = self._process_file(file_path, topic_id)
                if result:
                    processed_docs.append(result['doc_id'])
                
                if on_progress:
                    on_progress(file_path, i, total)
                
                if on_complete and result:
                    on_complete(file_path, result['doc_id'], result['chunk_count'])
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
                if on_error:
                    on_error(file_path, str(e))
        
        logger.info(f"Batch processing completed: {total} files")
    
    def _process_file(self, file_path: Path, topic_id: str) -> dict:
        """Process single file"""
        from core.rag.chunking.chunking_factory import ChunkingFactory
        from core.rag.loaders.document_loader_factory import DocumentLoaderFactory
        
        # 파일 읽기 (DocumentLoaderFactory 사용)
        docs = DocumentLoaderFactory.load_document(str(file_path))
        if not docs:
            raise ValueError(f"Failed to load document: {file_path}")
        
        # 모든 페이지/문서의 텍스트 결합
        text = "\n\n".join([doc.page_content for doc in docs])
        
        # 문서 생성
        doc_id = self.storage.create_document(
            topic_id=topic_id,
            filename=file_path.name,
            file_path=str(file_path),
            file_type=file_path.suffix.lstrip('.').lower(),
            file_size=file_path.stat().st_size
        )
        
        # 청킹
        if self.chunking_strategy:
            logger.info(f"Using manual strategy: {self.chunking_strategy} for {file_path.name}")
            # Code strategy needs language parameter
            if self.chunking_strategy == "code":
                ext = file_path.suffix.lstrip('.').lower()
                chunker = ChunkingFactory.create(self.chunking_strategy, language=ext, embeddings=self.embeddings)
            else:
                chunker = ChunkingFactory.create(self.chunking_strategy, embeddings=self.embeddings)
        else:
            logger.info(f"Using auto strategy for {file_path.name}")
            chunker = ChunkingFactory.get_strategy_for_file(file_path.name)
        
        logger.info(f"Selected chunker: {chunker.name} for {file_path.name}")
        chunks = chunker.chunk(text, metadata={"source": file_path.name})
        
        # 임베딩
        texts = [c.page_content for c in chunks]
        logger.debug(f"Embedding {len(texts)} chunks for {file_path.name}")
        vectors = self.embeddings.embed_documents(texts)
        logger.debug(f"Embedding completed for {file_path.name}")
        
        # 저장
        logger.debug(f"Storing {len(chunks)} chunks to LanceDB for {file_path.name}")
        chunk_ids = self.storage.add_chunks(
            doc_id=doc_id,
            chunks=chunks,
            embeddings=vectors,
            chunking_strategy=chunker.name
        )
        logger.debug(f"Storage completed for {file_path.name}")
        
        logger.info(f"Processed {file_path.name}: {len(chunk_ids)} chunks")
        
        return {
            'doc_id': doc_id,
            'chunk_count': len(chunk_ids),
            'strategy': chunker.name
        }
