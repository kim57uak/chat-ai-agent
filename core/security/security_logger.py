"""
Security Logger
보안 이벤트 로깅 클래스 (Backward Compatibility Wrapper)
"""

from typing import Dict, Any, Optional

from core.logging import unified_logger

class SecurityLogger:
    """보안 이벤트 전용 로거 (하위 호환성 유지)"""
    
    def __init__(self, log_file: Optional[str] = None):
        self._unified = unified_logger
    

    
    def log_login_attempt(self, success: bool, details: Dict[str, Any] = None):
        """로그인 시도 로깅"""
        self._unified.log_login_attempt(success, details)
    
    def log_logout(self, reason: str = "user_initiated"):
        """로그아웃 로깅"""
        self._unified.log_logout(reason)
    
    def log_encryption_event(self, event_type: str, success: bool, details: str = ""):
        """암호화 이벤트 로깅"""
        self._unified.log_encryption_event(event_type, success, details)
    
    def log_security_violation(self, violation_type: str, details: str = ""):
        """보안 위반 로깅"""
        self._unified.log_security_violation(violation_type, details)
    
    def log_session_event(self, event_type: str, details: Dict[str, Any] = None):
        """세션 이벤트 로깅"""
        safe_details = self._unified._sanitize_dict(details) if details else {}
        self._unified.security_logger.info(f"Session {event_type} - {safe_details}")
    
    def log_error_safely(self, error: Exception, context: str = ""):
        """안전한 에러 로깅 (민감한 정보 제외)"""
        self._unified.security_logger.error(f"Security error in {context}: {str(error)}", exc_info=True)


# 전역 보안 로거
security_logger = SecurityLogger()