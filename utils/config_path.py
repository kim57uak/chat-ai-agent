"""Configuration file path utilities for user-configurable paths."""

import os
import sys
import json
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 사용자가 편집해야 하는 설정 파일들
USER_CONFIG_FILES = {'config.json', 'mcp.json', 'news_config.json', 'prompt_config.json'}

class ConfigPathManager:
    """Manages configuration file paths with user-configurable base directory."""
    
    def __init__(self):
        self._base_path = self._get_base_path()
        self._user_config_path = None
        self._load_user_config_path()
    
    def _get_base_path(self) -> Path:
        """Get the base path for the application."""
        if getattr(sys, 'frozen', False):
            print(f"[DEBUG] sys.executable: {sys.executable}")
            print(f"[DEBUG] sys.frozen: {getattr(sys, 'frozen', False)}")
            print(f"[DEBUG] sys._MEIPASS: {getattr(sys, '_MEIPASS', 'Not found')}")
            
            # 여러 경로 시도
            possible_paths = [
                Path(sys.executable).parent.parent / 'Resources',  # Contents/Resources
                Path(sys.executable).parent / 'Resources',         # MacOS/Resources
                Path(sys.executable).parent,                       # MacOS/
                Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else None,  # PyInstaller temp
            ]
            
            for i, base_path in enumerate(possible_paths):
                if base_path and base_path.exists():
                    print(f"[DEBUG] Path {i+1} exists: {base_path}")
                    # theme.json이 있는지 확인
                    if (base_path / 'theme.json').exists():
                        print(f"[DEBUG] Found theme.json at: {base_path}")
                        return base_path
                    else:
                        print(f"[DEBUG] No theme.json at: {base_path}")
                else:
                    print(f"[DEBUG] Path {i+1} does not exist: {base_path}")
            
            # 폴백
            base_path = Path(sys.executable).parent.parent / 'Resources'
            print(f"[DEBUG] Using fallback: {base_path}")
            return base_path
        else:
            # 개발 환경
            base_path = Path(__file__).parent.parent
            print(f"[DEBUG] Development path: {base_path}")
            return base_path
    
    def _load_user_config_path(self):
        """Load user-configured path from settings."""
        # 우선순위: 1) _base_path 2) 사용자 데이터 디렉토리
        possible_settings = [
            self._base_path / 'user_config_path.json',  # 기존 위치 (개발/패키징 모두)
        ]
        
        # 패키징 환경에서 추가 경로 확인
        if getattr(sys, 'frozen', False):
            if os.name == 'nt':  # Windows
                data_dir = Path.home() / "AppData" / "Local" / "ChatAIAgent"
            elif sys.platform == 'darwin':  # macOS
                data_dir = Path.home() / "Library" / "Application Support" / "ChatAIAgent"
            else:  # Linux
                data_dir = Path.home() / ".config" / "chat-ai-agent"
            
            possible_settings.append(data_dir / 'user_config_path.json')
        
        # 존재하는 첫 번째 파일 사용
        for settings_file in possible_settings:
            if settings_file.exists():
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        path_str = data.get('config_path')
                        if path_str and Path(path_str).exists():
                            self._user_config_path = Path(path_str)
                            logger.info(f"Loaded user config from: {settings_file}")
                            return
                except Exception as e:
                    logger.error(f"Failed to load from {settings_file}: {e}")
                    continue
    
    def set_user_config_path(self, path: str) -> bool:
        """Set user configuration path."""
        try:
            config_path = Path(path)
            if not config_path.exists():
                config_path.mkdir(parents=True, exist_ok=True)
            
            self._user_config_path = config_path
            
            # Save to settings file
            settings_file = self._base_path / 'user_config_path.json'
            
            # 패키징 환경에서 _base_path가 읽기 전용이면 대체 경로 사용
            try:
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump({'config_path': str(config_path)}, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved to: {settings_file}")
            except (OSError, PermissionError) as e:
                # 폴백: 사용자 데이터 디렉토리
                if getattr(sys, 'frozen', False):
                    if os.name == 'nt':
                        data_dir = Path.home() / "AppData" / "Local" / "ChatAIAgent"
                    elif sys.platform == 'darwin':
                        data_dir = Path.home() / "Library" / "Application Support" / "ChatAIAgent"
                    else:
                        data_dir = Path.home() / ".config" / "chat-ai-agent"
                    
                    data_dir.mkdir(parents=True, exist_ok=True)
                    settings_file = data_dir / 'user_config_path.json'
                    
                    with open(settings_file, 'w', encoding='utf-8') as f:
                        json.dump({'config_path': str(config_path)}, f, ensure_ascii=False, indent=2)
                    logger.info(f"Saved to fallback: {settings_file}")
                else:
                    raise
            
            return True
        except Exception as e:
            logger.error(f"Failed to set user config path: {e}")
            return False
    
    def get_user_config_path(self) -> Optional[Path]:
        """Get current user configuration path."""
        return self._user_config_path
    
    def get_config_path(self, filename: str, user_writable: bool = True) -> Path:
        """Get the path for a configuration file."""
        # 우선순위: 1) 외부 경로에 파일 존재 2) 내부 경로
        possible_paths = []
        
        # 외부 경로 확인 (파일이 존재하는 경우만)
        if self._user_config_path and filename in USER_CONFIG_FILES:
            user_file_path = self._user_config_path / filename
            if user_file_path.exists():
                possible_paths.append(user_file_path)
        
        # 내부 경로 추가
        base_file_path = self._base_path / filename
        possible_paths.append(base_file_path)
        
        # 존재하는 첫 번째 파일 반환, 없으면 적절한 경로 반환
        for path in possible_paths:
            if path.exists():
                return path
        
        # 파일이 없으면 저장할 적절한 경로 결정
        if filename in USER_CONFIG_FILES and self._user_config_path:
            return self._user_config_path / filename
        else:
            return self._base_path / filename
    
    def ensure_config_exists(self, filename: str, default_content: str = None) -> Path:
        """
        Ensure configuration file exists, create with default content if needed.
        
        Args:
            filename: Name of the configuration file
            default_content: Default content to write if file doesn't exist
        
        Returns:
            Path to the configuration file
        """
        config_path = self.get_config_path(filename, user_writable=True)
        
        if not config_path.exists() and default_content:
            try:
                config_path.write_text(default_content, encoding='utf-8')
                logger.info(f"Created default {filename} at: {config_path}")
            except (OSError, PermissionError) as e:
                logger.error(f"Failed to create {filename}: {e}")
                # Try app directory as fallback
                app_path = self._base_path / filename
                if not app_path.exists():
                    try:
                        app_path.write_text(default_content, encoding='utf-8')
                        logger.info(f"Created default {filename} in app directory: {app_path}")
                        return app_path
                    except (OSError, PermissionError):
                        logger.error(f"Cannot create {filename} anywhere")
        
        return config_path
    
    def get_all_config_locations(self, filename: str) -> list[Path]:
        """Get all possible locations for a configuration file."""
        locations = []
        
        # Add user config path if set
        if self._user_config_path:
            locations.append(self._user_config_path / filename)
        
        # Add base path
        locations.append(self._base_path / filename)
        
        return [path for path in locations if path.exists()]


# Global instance
config_path_manager = ConfigPathManager()