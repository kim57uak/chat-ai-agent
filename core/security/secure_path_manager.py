"""
Secure Path Manager for encrypted data storage
암호화된 데이터 저장을 위한 보안 경로 관리자
"""

import os
import sys
from pathlib import Path
from typing import Optional
from core.logging import get_logger

logger = get_logger("secure_path_manager")


class SecurePathManager:
    """보안 데이터 저장을 위한 경로 관리자"""
    
    def __init__(self):
        self._app_base_path = self._get_app_base_path()
        self._user_data_path = self._get_user_data_path()
        
    def _get_app_base_path(self) -> Path:
        """앱 기본 경로 반환 (패키징 고려)"""
        if getattr(sys, 'frozen', False):
            # 패키징된 앱
            if sys.platform == 'darwin':  # macOS
                # .app/Contents/MacOS/executable -> .app/Contents/Resources
                app_path = Path(sys.executable).parent.parent / 'Resources'
                if not app_path.exists():
                    # 폴백: executable과 같은 디렉토리
                    app_path = Path(sys.executable).parent
            else:  # Windows/Linux
                app_path = Path(sys.executable).parent
            
            logger.info(f"Packaged app base path: {app_path}")
            return app_path
        else:
            # 개발 환경
            app_path = Path(__file__).parent.parent.parent
            logger.info(f"Development app base path: {app_path}")
            return app_path
    
    def _get_user_data_path(self) -> Path:
        """사용자 데이터 저장 경로 반환"""
        try:
            from utils.config_path import config_path_manager
            user_path = config_path_manager.get_user_config_path()
            if user_path and user_path.exists():
                logger.info(f"User data path: {user_path}")
                return user_path
        except Exception as e:
            logger.warning(f"Failed to get user config path: {e}")
        
        # 폴백: 기본 경로
        if os.name == 'nt':
            base_dir = Path.home() / "AppData" / "Local" / "ChatAIAgent"
        elif sys.platform == 'darwin':
            base_dir = Path.home() / "Library" / "Application Support" / "ChatAIAgent"
        else:
            base_dir = Path.home() / ".config" / "chat-ai-agent"
        
        base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Default data path: {base_dir}")
        return base_dir
    
    def get_secure_database_path(self, filename: str = "chat_sessions_encrypted.db") -> Path:
        """보안 데이터베이스 파일 경로 반환"""
        # db 서브폴더에 저장
        db_path = self._user_data_path / "db" / filename
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Secure database path: {db_path}")
        return db_path
    
    def get_database_path(self) -> str:
        """데이터베이스 경로 반환 (문자열)"""
        return str(self.get_secure_database_path())
    
    def get_secure_config_path(self, filename: str = "config_encrypted.json") -> Path:
        """보안 설정 파일 경로 반환"""
        # 항상 사용자 데이터 디렉토리에 저장 (보안상 중요)
        config_path = self._user_data_path / filename
        logger.info(f"Secure config path: {config_path}")
        return config_path
    
    def get_app_config_path(self, filename: str) -> Path:
        """앱 설정 파일 경로 반환 (읽기 전용)"""
        # 패키징된 앱에서는 앱 내부, 개발 환경에서는 프로젝트 루트
        config_path = self._app_base_path / filename
        logger.info(f"App config path: {config_path}")
        return config_path
    
    def get_writable_config_path(self, filename: str) -> Path:
        """쓰기 가능한 설정 파일 경로 반환"""
        # 사용자가 수정할 수 있는 설정은 사용자 데이터 디렉토리에
        config_path = self._user_data_path / filename
        
        # 앱 내부에 기본 파일이 있으면 복사
        app_config = self._app_base_path / filename
        if app_config.exists() and not config_path.exists():
            try:
                import shutil
                config_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(app_config, config_path)
                logger.info(f"Copied default config from {app_config} to {config_path}")
            except Exception as e:
                logger.warning(f"Failed to copy default config: {e}")
        
        return config_path
    
    def ensure_secure_directory(self) -> bool:
        """보안 디렉토리 생성 및 권한 설정"""
        try:
            self._user_data_path.mkdir(parents=True, exist_ok=True)
            
            # Unix 계열에서 디렉토리 권한 설정 (소유자만 접근)
            if os.name != 'nt':
                os.chmod(self._user_data_path, 0o700)
                logger.info(f"Set secure permissions for {self._user_data_path}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to ensure secure directory: {e}")
            return False
    
    def get_backup_path(self, original_path: Path) -> Path:
        """백업 파일 경로 생성"""
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{original_path.stem}_backup_{timestamp}{original_path.suffix}"
        return original_path.parent / backup_name
    
    def is_path_secure(self, path: Path) -> bool:
        """경로가 보안상 안전한지 확인"""
        try:
            # 사용자 데이터 디렉토리 내부인지 확인
            path.resolve().relative_to(self._user_data_path.resolve())
            return True
        except ValueError:
            # 사용자 데이터 디렉토리 외부
            logger.warning(f"Insecure path detected: {path}")
            return False
    
    def get_migration_info(self) -> dict:
        """마이그레이션 정보 반환"""
        return {
            'app_base_path': str(self._app_base_path),
            'user_data_path': str(self._user_data_path),
            'is_packaged': getattr(sys, 'frozen', False),
            'platform': sys.platform,
            'secure_directory_exists': self._user_data_path.exists()
        }


# 전역 인스턴스
secure_path_manager = SecurePathManager()