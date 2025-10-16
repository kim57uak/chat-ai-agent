"""
Security configuration utility
보안 설정 유틸리티
"""

from core.logging import get_logger

logger = get_logger("security_config")


def load_logout_timeout() -> int:
    """
    설정 파일에서 로그아웃 타임아웃 값 로드
    
    Returns:
        int: 타임아웃 시간(분), 기본값 30분
    """
    try:
        from utils.config_path import config_path_manager
        import json
        
        config_path = config_path_manager.get_config_path('prompt_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        security_settings = config.get('security_settings', {})
        timeout = security_settings.get('logout_timeout_minutes', 30)
        
        logger.info(f"세션 타임아웃 설정: {timeout}분")
        return timeout
        
    except Exception as e:
        logger.warning(f"타임아웃 설정 로드 실패, 기본값 30분 사용: {e}")
        return 30
