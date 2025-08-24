"""
Resource file helper for PyInstaller bundled apps
"""
import os
import sys
import json
from pathlib import Path

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def load_json_config(filename):
    """Load JSON config file from resources"""
    try:
        config_path = get_resource_path(filename)
        print(f"Loading config from: {config_path}")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Config file not found: {config_path}")
            return {}
    except Exception as e:
        print(f"Error loading config {filename}: {e}")
        return {}

def save_json_config(filename, data):
    """Save JSON config file"""
    try:
        # 개발 환경에서는 현재 디렉토리에 저장
        if hasattr(sys, '_MEIPASS'):
            # 번들된 앱에서는 사용자 디렉토리에 저장
            import os
            config_dir = os.path.expanduser("~/Library/Application Support/ChatAIAgent")
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, filename)
        else:
            config_path = filename
            
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Config saved to: {config_path}")
        return True
    except Exception as e:
        print(f"Error saving config {filename}: {e}")
        return False
