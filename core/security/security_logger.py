"""
Security Logger
보안 이벤트 로깅 클래스
"""

import logging
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class SecurityLogger:
    """보안 이벤트 전용 로거"""
    
    def __init__(self, log_file: Optional[str] = None):
        if log_file is None:
            log_file = self._get_default_log_path()
        
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 보안 전용 로거 설정
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # 핸들러가 이미 있으면 제거
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 파일 핸들러 추가
        handler = logging.FileHandler(self.log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # 상위 로거로 전파 방지
        self.logger.propagate = False
    
    def _get_default_log_path(self) -> str:
        """기본 로그 파일 경로"""
        try:
            from utils.config_path import config_path_manager
            user_path = config_path_manager.get_user_config_path()
            if user_path:
                return str(user_path / "logs" / "security.log")
        except:
            pass
        
        # 폴백 경로
        return str(Path.home() / ".chat-ai-agent" / "logs" / "security.log")
    
    def _sanitize_message(self, message: str) -> str:
        """민감한 정보 제거"""
        # API 키 패턴 제거
        message = re.sub(r'["\']?api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?', 
                        'api_key: [REDACTED]', message, flags=re.IGNORECASE)
        
        # 비밀번호 패턴 제거
        message = re.sub(r'["\']?password["\']?\s*[:=]\s*["\']?[^"\'\\s]{8,}["\']?', 
                        'password: [REDACTED]', message, flags=re.IGNORECASE)
        
        # 토큰 패턴 제거
        message = re.sub(r'["\']?token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_.-]{20,}["\']?', 
                        'token: [REDACTED]', message, flags=re.IGNORECASE)
        
        return message
    
    def log_login_attempt(self, success: bool, details: Dict[str, Any] = None):
        """로그인 시도 로깅"""
        status = "SUCCESS" if success else "FAILED"
        message = f"Login attempt: {status}"
        
        if details:
            safe_details = {k: v for k, v in details.items() 
                          if k not in ['password', 'key', 'token']}
            message += f" - Details: {json.dumps(safe_details)}"
        
        if success:
            self.logger.info(self._sanitize_message(message))
        else:
            self.logger.warning(self._sanitize_message(message))
    
    def log_logout(self, reason: str = "user_initiated"):
        """로그아웃 로깅"""
        message = f"Logout: {reason}"
        self.logger.info(message)
    
    def log_encryption_event(self, event_type: str, success: bool, details: str = ""):
        """암호화 이벤트 로깅"""
        status = "SUCCESS" if success else "FAILED"
        message = f"Encryption {event_type}: {status}"
        
        if details:
            message += f" - {details}"
        
        if success:
            self.logger.info(self._sanitize_message(message))
        else:
            self.logger.error(self._sanitize_message(message))
    
    def log_security_violation(self, violation_type: str, details: str = ""):
        """보안 위반 로깅"""
        message = f"Security violation: {violation_type}"
        
        if details:
            message += f" - {details}"
        
        self.logger.critical(self._sanitize_message(message))
    
    def log_session_event(self, event_type: str, details: Dict[str, Any] = None):
        """세션 이벤트 로깅"""
        message = f"Session {event_type}"
        
        if details:
            safe_details = {k: v for k, v in details.items() 
                          if k not in ['password', 'key', 'token']}
            message += f" - {json.dumps(safe_details)}"
        
        self.logger.info(self._sanitize_message(message))
    
    def log_error_safely(self, error: Exception, context: str = ""):
        """안전한 에러 로깅 (민감한 정보 제외)"""
        error_msg = str(error)
        safe_error = self._sanitize_message(error_msg)
        
        message = f"Security error in {context}: {safe_error}"
        self.logger.error(message)


# 전역 보안 로거
security_logger = SecurityLogger()