"""
설정 파일 유틸리티
config.json과 prompt_config.json을 통합 관리
"""
import json
import os
from typing import Dict, Any

def load_prompt_config() -> Dict[str, Any]:
    """prompt_config.json 로드"""
    try:
        if os.path.exists('prompt_config.json'):
            with open('prompt_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"prompt_config.json 로드 오류: {e}")
    return {}

def get_setting(key: str, default: Any = None) -> Any:
    """통합 설정 조회 (prompt_config.json 우선)"""
    prompt_config = load_prompt_config()
    
    # prompt_config에서 먼저 찾기
    if key in prompt_config:
        return prompt_config[key]
    
    # config.json에서 찾기 (하위 호환성)
    try:
        from core.file_utils import load_config
        config = load_config()
        return config.get(key, default)
    except:
        return default

def get_conversation_settings() -> Dict[str, Any]:
    """대화 설정 조회"""
    return get_setting('conversation_settings', {})

def get_response_settings() -> Dict[str, Any]:
    """응답 설정 조회"""
    return get_setting('response_settings', {})

def get_language_detection_settings() -> Dict[str, Any]:
    """언어 감지 설정 조회"""
    return get_setting('language_detection', {})

def get_paging_settings() -> Dict[str, Any]:
    """페이징 설정 조회"""
    return get_setting('paging_settings', {})