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

def load_prompt_config():
    """Load prompt configuration from prompt_config.json."""
    import json
    from utils.config_path import config_path_manager
    
    try:
        config_path = config_path_manager.get_config_path('prompt_config.json')
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Return default configuration
    return {
        'conversation_settings': {
            'enable_history': True,
            'hybrid_mode': True,
            'user_message_limit': 6,
            'ai_response_limit': 4,
            'ai_response_token_limit': 4000,
            'max_history_pairs': 6,
            'max_tokens_estimate': 8000
        },
        'response_settings': {
            'max_tokens': 4096,
            'max_response_length': 50000,
            'enable_length_limit': False,
            'enable_streaming': True,
            'streaming_chunk_size': 300
        },
        'language_detection': {
            'korean_threshold': 0.1,
            'description': 'Korean character ratio threshold for language detection (0.0-1.0)'
        },
        'theme': {
            'current_theme': 'material_high_contrast'
        },
        'history_settings': {
            'initial_load_count': 50,
            'page_size': 10
        }
    }

def save_prompt_config(config):
    """Save prompt configuration to prompt_config.json."""
    import json
    from utils.config_path import config_path_manager
    
    config_path = config_path_manager.get_config_path('prompt_config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False) 