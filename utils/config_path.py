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
        settings_file = self._base_path / 'user_config_path.json'
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    path_str = data.get('config_path')
                    if path_str and Path(path_str).exists():
                        self._user_config_path = Path(path_str)
            except Exception as e:
                logger.error(f"Failed to load user config path: {e}")
    
    def set_user_config_path(self, path: str) -> bool:
        """Set user configuration path."""
        try:
            config_path = Path(path)
            if not config_path.exists():
                config_path.mkdir(parents=True, exist_ok=True)
            
            self._user_config_path = config_path
            
            # Save to settings file
            settings_file = self._base_path / 'user_config_path.json'
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump({'config_path': str(config_path)}, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to set user config path: {e}")
            return False
    
    def get_user_config_path(self) -> Optional[Path]:
        """Get current user configuration path."""
        return self._user_config_path
    
    def get_config_path(self, filename: str, user_writable: bool = True) -> Path:
        """Get the path for a configuration file."""
        print(f"[DEBUG] Getting path for: {filename}")
        print(f"[DEBUG] User config path: {self._user_config_path}")
        print(f"[DEBUG] Base path: {self._base_path}")
        
        # 외부 경로 확인
        if self._user_config_path:
            user_file_path = self._user_config_path / filename
            print(f"[DEBUG] Checking user file: {user_file_path} (exists: {user_file_path.exists()})")
            if user_file_path.exists():
                print(f"[DEBUG] Using user file: {user_file_path}")
                return user_file_path
        
        # 내부 경로 사용
        base_file_path = self._base_path / filename
        print(f"[DEBUG] Using base file: {base_file_path} (exists: {base_file_path.exists()})")
        return base_file_path
    
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