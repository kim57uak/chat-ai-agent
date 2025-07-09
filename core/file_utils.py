import json
import os

CONFIG_PATH = 'config.json'

def save_config(data):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_model_api_key(model, api_key):
    config = load_config()
    if 'models' not in config:
        config['models'] = {}
    
    if model not in config['models']:
        config['models'][model] = {}
    
    config['models'][model]['api_key'] = api_key
    config['current_model'] = model
    save_config(config)

def load_model_api_key(model):
    config = load_config()
    models = config.get('models', {})
    model_config = models.get(model, {})
    return model_config.get('api_key', '')

def load_last_model():
    config = load_config()
    return config.get('current_model', 'gpt-3.5-turbo') 