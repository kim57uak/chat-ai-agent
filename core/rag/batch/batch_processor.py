"""
Batch Processor
"""

from pathlib import Path
from typing import List, Callable, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from core.logging import get_logger

logger = get_logger("batch_processor")


class BatchProcessor(QObject):
    """배치 프로세서 (병렬 처리, Thread-safe)"""
    
    # Thread-safe signals
    progress_signal = pyqtSignal(object, int, int)  # file_path, current, total
    complete_signal = pyqtSignal(object, str, int)  # file_path, doc_id, chunk_count
    error_signal = pyqtSignal(object, str)  # file_path, error
    
    def __init__(self, storage_manager, embeddings, max_workers: int = 1, chunking_strategy: Optional[str] = None):
        """
        Initialize batch processor
        
        Args:
            storage_manager: RAGStorageManager instance
            embeddings: Embedding model
            max_workers: Max parallel workers (FORCED to 1 for SQLite)
            chunking_strategy: Override chunking strategy (None for auto)
        """
        super().__init__()
        self.storage = storage_manager
        self.embeddings = embeddings
        self.chunking_strategy = chunking_strategy
        self.max_workers = 1  # SQLite 안정성을 위해 강제 순차 처리
        logger.info(f"Batch processor: sequential mode (workers=1), strategy={chunking_strategy or 'auto'}")
    
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
        Process files in parallel (Thread-safe)
        
        Args:
            files: List of file paths
            topic_id: Topic ID
            on_progress: Progress callback (file_path, current, total)
            on_complete: Complete callback (file_path, doc_id, chunk_count)
            on_error: Error callback (file_path, error)
            check_cancel: Cancel check callback
        
        Note:
            Callbacks are invoked via Qt signals for thread safety
        """
        # Connect callbacks to signals
        if on_progress:
            self.progress_signal.connect(on_progress)
        if on_complete:
            self.complete_signal.connect(on_complete)
        if on_error:
            self.error_signal.connect(on_error)
        total = len(files)
        logger.info(f"Processing {total} files sequentially (SQLite safe mode)")
        processed_docs = []
        completed = 0
        
        # Sequential processing (no ThreadPoolExecutor)
        for file_path in files:
            # Check cancel
            if check_cancel and check_cancel():
                logger.warning(f"Processing cancelled at {completed}/{total}")
                # Rollback
                for doc_id in processed_docs:
                    try:
                        self.storage.delete_document(doc_id)
                        logger.info(f"Rolled back: {doc_id}")
                    except Exception as e:
                        logger.error(f"Rollback failed for {doc_id}: {e}")
                return
            
            try:
                result = self._process_file(file_path, topic_id, check_cancel)
                if result:
                    processed_docs.append(result['doc_id'])
                    completed += 1
                    
                    # Thread-safe: Signal 사용
                    if on_progress:
                        self.progress_signal.emit(file_path, completed, total)
                    
                    if on_complete:
                        self.complete_signal.emit(file_path, result['doc_id'], result['chunk_count'])
            
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to process {file_path}: {error_msg}")
                
                # DB 손상 오류 처리
                if "database disk image is malformed" in error_msg or "database is locked" in error_msg:
                    logger.warning(f"Database error detected, skipping file: {file_path.name}")
                
                # Thread-safe: Signal 사용
                if on_error:
                    self.error_signal.emit(file_path, error_msg)
        
        logger.info(f"Batch processing completed: {completed}/{total} files")
        
        # Disconnect signals
        if on_progress:
            self.progress_signal.disconnect(on_progress)
        if on_complete:
            self.complete_signal.disconnect(on_complete)
        if on_error:
            self.error_signal.disconnect(on_error)
    
    def _process_file(self, file_path: Path, topic_id: str, check_cancel: Optional[Callable] = None) -> dict:
        """Process single file with cancellation support"""
        from core.rag.chunking.chunking_factory import ChunkingFactory
        from core.rag.loaders.document_loader_factory import DocumentLoaderFactory
        
        # 취소 확인
        if check_cancel and check_cancel():
            logger.info(f"File processing cancelled: {file_path.name}")
            return None
        
        # 파일 읽기 (DocumentLoaderFactory 사용)
        docs = DocumentLoaderFactory.load_document(str(file_path))
        if not docs:
            raise ValueError(f"Failed to load document: {file_path}")
        
        # 취소 확인
        if check_cancel and check_cancel():
            logger.info(f"File processing cancelled after loading: {file_path.name}")
            return None
        
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
        
        try:
            # 취소 확인
            if check_cancel and check_cancel():
                logger.info(f"File processing cancelled before chunking: {file_path.name}")
                self.storage.delete_document(doc_id)  # 생성된 문서 삭제
                return None
            
            # 청킹
            if self.chunking_strategy:
                logger.info(f"Using manual strategy: {self.chunking_strategy} for {file_path.name}")
                # Code strategy needs language parameter
                if self.chunking_strategy == "code":
                    ext = file_path.suffix.lstrip('.').lower()
                    logger.info(f"Creating code chunker with language: {ext}")
                    chunker = ChunkingFactory.create(self.chunking_strategy, language=ext)
                elif self.chunking_strategy == "semantic":
                    logger.info(f"Creating semantic chunker")
                    chunker = ChunkingFactory.create(self.chunking_strategy, embeddings=self.embeddings)
                else:
                    logger.info(f"Creating {self.chunking_strategy} chunker")
                    chunker = ChunkingFactory.create(self.chunking_strategy)
            else:
                logger.info(f"Using auto strategy for {file_path.name}")
                chunker = ChunkingFactory.get_strategy_for_file(file_path.name)
            
            logger.info(f"Selected chunker: {chunker.name} for {file_path.name}")
            chunks = chunker.chunk(text, metadata={"source": file_path.name})
            
            # 취소 확인
            if check_cancel and check_cancel():
                logger.info(f"File processing cancelled before embedding: {file_path.name}")
                self.storage.delete_document(doc_id)
                return None
            
            # 임베딩 (취소 확인 전달)
            texts = [c.page_content for c in chunks]
            logger.debug(f"Embedding {len(texts)} chunks for {file_path.name}")
            vectors = self.embeddings.embed_documents(texts, check_cancel=check_cancel)
            logger.debug(f"Embedding completed for {file_path.name}")
            
            # 취소 확인
            if check_cancel and check_cancel():
                logger.info(f"File processing cancelled before storage: {file_path.name}")
                self.storage.delete_document(doc_id)
                return None
            
            # 저장 (청킹 전략 포함)
            logger.debug(f"Storing {len(chunks)} chunks to LanceDB for {file_path.name}")
            chunk_ids = self.storage.add_chunks(
                doc_id=doc_id,
                chunks=chunks,
                embeddings=vectors,
                chunking_strategy=chunker.name
            )
            logger.debug(f"Storage completed for {file_path.name} with strategy: {chunker.name}")
            
            # 문서 메타데이터에도 청킹 전략 업데이트
            self.storage.topic_db.conn.execute(
                "UPDATE documents SET chunking_strategy = ? WHERE id = ?",
                (chunker.name, doc_id)
            )
            self.storage.topic_db.conn.commit()
            logger.debug(f"Updated document chunking_strategy to: {chunker.name}")
            
            logger.info(f"Processed {file_path.name}: {len(chunk_ids)} chunks")
            
            return {
                'doc_id': doc_id,
                'chunk_count': len(chunk_ids),
                'strategy': chunker.name
            }
        
        except Exception as e:
            # 오류 발생 시 문서 삭제
            try:
                self.storage.delete_document(doc_id)
                logger.info(f"Cleaned up document after error: {doc_id}")
            except Exception as cleanup_error:
                # DB 오류는 무시
                if "database" not in str(cleanup_error).lower():
                    logger.error(f"Failed to cleanup document {doc_id}: {cleanup_error}")
            raise e
