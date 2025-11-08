"""
Progress Tracker
"""

from typing import Dict
from datetime import datetime
from core.logging import get_logger

logger = get_logger("progress_tracker")


class ProgressTracker:
    """진행 상황 추적"""
    
    def __init__(self):
        """Initialize progress tracker"""
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.total_chunks = 0
        self.start_time = None
        self.errors = []
        
    def start(self, total_files: int):
        """Start tracking"""
        self.total_files = total_files
        self.processed_files = 0
        self.failed_files = 0
        self.total_chunks = 0
        self.start_time = datetime.now()
        self.errors = []
        logger.info(f"Progress tracking started: {total_files} files")
    
    def update(self, chunk_count: int = 0):
        """Update progress"""
        self.processed_files += 1
        self.total_chunks += chunk_count
    
    def add_error(self, file_path: str, error: str):
        """Add error"""
        self.failed_files += 1
        self.errors.append({'file': file_path, 'error': error})
        logger.error(f"Error: {file_path} - {error}")
    
    def get_stats(self) -> Dict:
        """Get statistics"""
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'success_rate': (self.processed_files / self.total_files * 100) if self.total_files > 0 else 0,
            'total_chunks': self.total_chunks,
            'elapsed_seconds': elapsed,
            'files_per_second': self.processed_files / elapsed if elapsed > 0 else 0,
            'errors': self.errors
        }
    
    def get_progress_percentage(self) -> float:
        """Get progress percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files + self.failed_files) / self.total_files * 100
    
    def is_complete(self) -> bool:
        """Check if complete"""
        return (self.processed_files + self.failed_files) >= self.total_files
