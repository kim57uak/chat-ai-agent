"""Configuration file path utilities for packaged applications."""

import os
import sys
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ConfigPathManager:
    """Manages configuration file paths for both development and packaged environments."""
    
    def __init__(self):
        self._base_path = self._get_base_path()
        self._user_config_dir = self._get_user_config_dir()
    
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
    
    def _get_user_config_dir(self) -> Path:
        """Get user-specific configuration directory."""
        if sys.platform == 'darwin':
            config_dir = Path.home() / 'Library' / 'Application Support' / 'ChatAIAgent'
        elif sys.platform == 'win32':
            config_dir = Path(os.environ.get('APPDATA', Path.home())) / 'ChatAIAgent'
        else:
            config_dir = Path.home() / '.config' / 'ChatAIAgent'
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def get_config_path(self, filename: str, user_writable: bool = True) -> Path:
        """
        Get the path for a configuration file.
        
        Args:
            filename: Name of the configuration file
            user_writable: If True, prefer user directory for writable configs
        
        Returns:
            Path to the configuration file
        """
        # Always prefer project directory for mcp.json
        if filename == 'mcp.json':
            project_path = self._base_path / filename
            if project_path.exists():
                return project_path
        
        if user_writable:
            # Check user directory first
            user_path = self._user_config_dir / filename
            if user_path.exists():
                return user_path
            
            # Check if we can write to user directory
            try:
                test_file = self._user_config_dir / '.test'
                test_file.touch()
                test_file.unlink()
                
                # Copy from app bundle if exists
                app_path = self._base_path / filename
                if app_path.exists() and not user_path.exists():
                    import shutil
                    shutil.copy2(app_path, user_path)
                    logger.info(f"Copied {filename} to user directory: {user_path}")
                
                return user_path
            except (OSError, PermissionError):
                logger.warning(f"Cannot write to user directory, using app directory")
        
        # Fall back to app directory
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
        locations = [
            self._user_config_dir / filename,
            self._base_path / filename
        ]
        return [path for path in locations if path.exists()]


# Global instance
config_path_manager = ConfigPathManager()