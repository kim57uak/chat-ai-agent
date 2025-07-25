"""File utilities - refactored to follow SRP."""

# Backward compatibility imports
from .config import ConfigManager, ModelConfigManager

# Global instances for backward compatibility
_config_manager = ConfigManager()
_model_config = ModelConfigManager(_config_manager)

# Legacy function wrappers for backward compatibility
def save_config(data):
    """Legacy wrapper for config saving."""
    _config_manager.save(data)

def load_config():
    """Legacy wrapper for config loading."""
    return _config_manager.load()

def save_model_api_key(model, api_key):
    """Legacy wrapper for saving model API key."""
    _model_config.save_api_key(model, api_key)

def load_model_api_key(model):
    """Legacy wrapper for loading model API key."""
    return _model_config.load_api_key(model)

def load_last_model():
    """Legacy wrapper for getting current model."""
    return _model_config.get_current_model()

def save_last_model(model):
    """Legacy wrapper for setting current model."""
    _model_config.set_current_model(model) 