"""Model configuration management."""

from typing import Optional
from .config_manager import ConfigManager


class ModelConfigManager:
    """Manages model-specific configuration."""
    
    def __init__(self, config_manager: ConfigManager):
        self._config = config_manager
    
    def save_api_key(self, model: str, api_key: str) -> None:
        """Save API key for a model."""
        config = self._config.load()
        
        if 'models' not in config:
            config['models'] = {}
        
        if model not in config['models']:
            config['models'][model] = {}
        
        config['models'][model]['api_key'] = api_key
        config['current_model'] = model
        self._config.save(config)
    
    def load_api_key(self, model: str) -> str:
        """Load API key for a model."""
        config = self._config.load()
        models = config.get('models', {})
        model_config = models.get(model, {})
        return model_config.get('api_key', '')
    
    def get_current_model(self) -> str:
        """Get current model."""
        return self._config.get('current_model', 'gpt-3.5-turbo')
    
    def set_current_model(self, model: str) -> None:
        """Set current model."""
        self._config.set('current_model', model)