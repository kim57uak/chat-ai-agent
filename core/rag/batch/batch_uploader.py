"""
Batch Uploader
통합 배치 업로드 관리자
"""

from pathlib import Path
from typing import Callable, Optional
from core.logging import get_logger
from .file_scanner import FileScanner
from .batch_processor import BatchProcessor
from .progress_tracker import ProgressTracker

logger = get_logger("batch_uploader")


class BatchUploader:
    """배치 업로드 통합 관리자"""
    
    def __init__(self, storage_manager, embeddings, config: dict = None):
        """
        Initialize batch uploader
        
        Args:
            storage_manager: RAGStorageManager instance
            embeddings: Embedding model
            config: Configuration dict
        """
        config = config or {}
        
        self.scanner = FileScanner(
            exclude_patterns=set(config.get('exclude_patterns', [])),
            max_file_size_mb=config.get('max_file_size_mb', 50)
        )
        
        self.processor = BatchProcessor(
            storage_manager,
            embeddings,
            max_workers=config.get('max_workers', 4),
            chunking_strategy=config.get('chunking_strategy')
        )
        
        self.tracker = ProgressTracker()
        logger.info("Batch uploader initialized")
    
    def upload_folder(
        self,
        folder_path: str,
        topic_id: str,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None
    ):
        """
        Upload entire folder
        
        Args:
            folder_path: Folder path
            topic_id: Topic ID
            on_progress: Progress callback (current, total, percentage, stats)
            on_complete: Complete callback (stats)
        """
        # 파일 스캔
        files = self.scanner.scan_folder(folder_path)
        if not files:
            logger.warning(f"No files found in {folder_path}")
            return
        
        # 진행 추적 시작
        self.tracker.start(len(files))
        
        # 콜백 래퍼
        def progress_callback(file_path, current, total):
            self.tracker.update()
            if on_progress:
                stats = self.tracker.get_stats()
                percentage = self.tracker.get_progress_percentage()
                on_progress(current, total, percentage, stats)
        
        def complete_callback(file_path, doc_id, chunk_count):
            self.tracker.update(chunk_count)
        
        def error_callback(file_path, error):
            self.tracker.add_error(str(file_path), error)
        
        # 배치 처리
        self.processor.process_files(
            files,
            topic_id,
            on_progress=progress_callback,
            on_complete=complete_callback,
            on_error=error_callback
        )
        
        # 완료
        stats = self.tracker.get_stats()
        logger.info(f"Upload completed: {stats}")
        
        if on_complete:
            on_complete(stats)
        
        return stats
