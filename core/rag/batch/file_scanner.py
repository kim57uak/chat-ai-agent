"""
File Scanner
"""

from pathlib import Path
from typing import List, Set
from core.logging import get_logger

logger = get_logger("file_scanner")


class FileScanner:
    """파일 스캐너"""
    
    SUPPORTED_EXTENSIONS = {
        # 텍스트
        'txt', 'text', 'log',
        # 문서
        'md', 'markdown', 'rst', 'pdf', 'doc', 'docx',
        # 코드
        'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'cpp', 'c', 'h', 'hpp',
        'go', 'rs', 'rb', 'php', 'swift', 'kt', 'scala', 'cs', 'lua',
        'sh', 'bash', 'zsh', 'sql', 'r', 'm',
        # 웹
        'html', 'htm', 'css', 'scss', 'sass', 'xml', 'json', 'yaml', 'yml',
        # 데이터
        'csv', 'tsv', 'jsonl',
        # 설정
        'ini', 'cfg', 'conf', 'config', 'toml', 'env',
    }
    
    DEFAULT_EXCLUDE = {'node_modules', '.git', 'venv', '__pycache__', '.venv', 'dist', 'build'}
    
    def __init__(self, exclude_patterns: Set[str] = None, max_file_size_mb: int = 50):
        """
        Initialize file scanner
        
        Args:
            exclude_patterns: Patterns to exclude
            max_file_size_mb: Max file size in MB
        """
        self.exclude_patterns = exclude_patterns or self.DEFAULT_EXCLUDE
        self.max_file_size = max_file_size_mb * 1024 * 1024
        logger.info(f"File scanner: max_size={max_file_size_mb}MB, exclude={self.exclude_patterns}")
    
    def scan_folder(self, folder_path: str) -> List[Path]:
        """
        Scan folder for supported files
        
        Args:
            folder_path: Folder path
            
        Returns:
            List of file paths
        """
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            logger.error(f"Invalid folder: {folder_path}")
            return []
        
        files = []
        for file_path in folder.rglob('*'):
            if self._should_include(file_path):
                files.append(file_path)
        
        logger.info(f"Scanned {folder_path}: {len(files)} files found")
        return files
    
    def _should_include(self, file_path: Path) -> bool:
        """Check if file should be included"""
        # 디렉토리 제외
        if not file_path.is_file():
            return False
        
        # 제외 패턴 체크
        for exclude in self.exclude_patterns:
            if exclude in file_path.parts:
                return False
        
        # 확장자 체크
        ext = file_path.suffix.lstrip('.').lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return False
        
        # 파일 크기 체크
        try:
            if file_path.stat().st_size > self.max_file_size:
                logger.warning(f"File too large: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to check file size: {e}")
            return False
        
        return True
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get file information"""
        try:
            stat = file_path.stat()
            return {
                'path': str(file_path),
                'name': file_path.name,
                'extension': file_path.suffix.lstrip('.').lower(),
                'size': stat.st_size,
                'modified': stat.st_mtime
            }
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return None
