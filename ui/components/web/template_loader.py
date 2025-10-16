"""
Template Loader with Caching
템플릿 로더 (캐시 지원)
"""

import os
from pathlib import Path
from typing import Dict, Optional
from core.logging import get_logger

logger = get_logger("template_loader")


class TemplateCache:
    """템플릿 캐시"""
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._enabled = True
    
    def get(self, key: str) -> Optional[str]:
        """캐시에서 템플릿 가져오기"""
        if not self._enabled:
            return None
        return self._cache.get(key)
    
    def set(self, key: str, content: str):
        """캐시에 템플릿 저장"""
        if self._enabled:
            self._cache[key] = content
    
    def clear(self):
        """캐시 초기화"""
        self._cache.clear()
    
    def disable(self):
        """캐시 비활성화 (개발 모드)"""
        self._enabled = False
        self.clear()


# 전역 캐시 인스턴스
_template_cache = TemplateCache()


def load_template(template_name: str, variables: Optional[Dict[str, str]] = None) -> str:
    """
    템플릿 파일 로드 (캐시 지원)
    
    Args:
        template_name: 템플릿 파일명
        variables: 템플릿 변수 딕셔너리
    
    Returns:
        str: 렌더링된 HTML
    """
    cache_key = template_name
    
    # 캐시 확인
    cached = _template_cache.get(cache_key)
    if cached and not variables:
        return cached
    
    # 템플릿 파일 경로
    template_dir = Path(__file__).parent / "templates"
    template_path = template_dir / template_name
    
    if not template_path.exists():
        logger.error(f"템플릿 파일 없음: {template_path}")
        return ""
    
    # 파일 읽기
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 캐시 저장 (변수 없는 경우만)
        if not variables:
            _template_cache.set(cache_key, content)
        
        # 변수 치환
        if variables:
            for key, value in variables.items():
                content = content.replace(f"{{{{ {key} }}}}", str(value))
        
        return content
        
    except Exception as e:
        logger.error(f"템플릿 로드 실패: {e}")
        return ""


def clear_cache():
    """캐시 초기화"""
    _template_cache.clear()


def disable_cache():
    """캐시 비활성화 (개발 모드)"""
    _template_cache.disable()
