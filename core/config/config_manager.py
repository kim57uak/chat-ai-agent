"""Configuration management following SRP."""

import json
import os
from typing import Dict, Any, Optional
from utils.config_path import config_path_manager


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: str = 'config.json'):
        self._config_path = config_path
        self._resolved_path = None
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self._resolved_path is None:
            self._resolved_path = config_path_manager.get_config_path(self._config_path)
        
        if not self._resolved_path.exists():
            return {}
        
        with open(self._resolved_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save(self, data: Dict[str, Any]) -> None:
        """Save configuration to file."""
        if self._resolved_path is None:
            self._resolved_path = config_path_manager.get_config_path(self._config_path)
        
        with open(self._resolved_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        config = self.load()
        return config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        config = self.load()
        config[key] = value
        self.save(config)