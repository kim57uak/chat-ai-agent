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
            # Running as packaged app
            if sys.platform == 'darwin':
                # macOS app bundle
                return Path(sys.executable).parent.parent / 'Resources'
            else:
                # Windows/Linux executable
                return Path(sys.executable).parent
        else:
            # Running in development
            return Path(__file__).parent.parent
    
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
        """
        Get the path for a configuration file.
        
        Args:
            filename: Name of the configuration file
            user_writable: If True, prefer user directory for writable configs
        
        Returns:
            Path to the configuration file
        """
        # Check if this is a user-configurable file
        if filename in USER_CONFIG_FILES and self._user_config_path:
            user_file_path = self._user_config_path / filename
            if user_file_path.exists():
                return user_file_path
            # If user path is set but file doesn't exist, still return user path for creation
            return user_file_path
        
        # For other files or when no user path is set, use base path
        project_path = self._base_path / filename
        return project_path
    
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
        locations = [
            self._user_config_dir / filename,
            self._base_path / filename
        ]
        return [path for path in locations if path.exists()]


# Global instance
config_path_manager = ConfigPathManager()