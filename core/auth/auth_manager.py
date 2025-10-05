"""
Authentication Manager for user login and session management.
"""

import time
from typing import Optional, Callable
from ..security.encryption_manager import EncryptionManager
from ..security.memory_security import memory_security
from ..security.security_logger import security_logger


class AuthManager:
    """Manages user authentication and session state."""
    
    def __init__(self, auto_logout_minutes: int = 30):
        self.encryption_manager = EncryptionManager()
        self.auto_logout_minutes = auto_logout_minutes
        self.last_activity_time: Optional[float] = None
        self.on_logout_callback: Optional[Callable] = None
        
    def set_logout_callback(self, callback: Callable):
        """세션 만료 시 호출될 콜백 함수 설정"""
        self.on_logout_callback = callback
        
    def is_setup_required(self) -> bool:
        """최초 설정이 필요한지 확인"""
        return self.encryption_manager.is_setup_required()
        
    def setup_first_time(self, password: str) -> bool:
        """
        최초 비밀번호 설정
        
        Args:
            password: 사용자 비밀번호
            
        Returns:
            bool: 설정 성공 여부
        """
        if not self._validate_password(password):
            return False
            
        success = self.encryption_manager.setup_first_time(password)
        if success:
            self._update_activity()
            
        return success
        
    def login(self, password: str) -> bool:
        """
        사용자 로그인
        
        Args:
            password: 사용자 비밀번호
            
        Returns:
            bool: 로그인 성공 여부
        """
        try:
            # 이미 로그인된 상태라면 로그아웃 후 진행
            if self.encryption_manager.is_logged_in():
                self.logout()
                
            success = self.encryption_manager.login(password)
            
            # 보안 로깅
            security_logger.log_login_attempt(success, {'timestamp': time.time()})
            
            if success:
                self._update_activity()
            
            # 비밀번호 메모리에서 즉시 제거
            memory_security.clear_sensitive_data('password')
            
            return success
            
        except Exception as e:
            security_logger.log_error_safely(e, "login")
            memory_security.clear_sensitive_data('password')
            return False
        
    def logout(self, reason: str = "user_initiated"):
        """사용자 로그아웃"""
        try:
            # 보안 로깅
            security_logger.log_logout(reason)
            
            self.encryption_manager.logout()
            self.last_activity_time = None
            
            # 메모리 정리
            memory_security.force_garbage_collection()
            
            # 전역 설정 캐시 클리어 (있다면)
            try:
                from ..security.encrypted_config import EncryptedConfig
                # 전역 인스턴스가 있다면 캐시 클리어
                # 이는 예시이고 실제로는 설정 객체를 직접 관리해야 함
            except:
                pass
                
        except Exception as e:
            security_logger.log_error_safely(e, "logout")
        
    def is_logged_in(self) -> bool:
        """로그인 상태 확인 (세션 만료 체크 포함)"""
        if not self.encryption_manager.is_logged_in():
            return False
            
        # 세션 만료 체크
        if self._is_session_expired():
            self._handle_session_expired()
            return False
            
        return True
        
    def update_activity(self):
        """사용자 활동 시간 업데이트"""
        if self.encryption_manager.is_logged_in():
            self._update_activity()
            
    def reset_password(self, new_password: str) -> bool:
        """
        비밀번호 재설정 (기존 데이터는 복구 불가)
        
        Args:
            new_password: 새로운 비밀번호
            
        Returns:
            bool: 재설정 성공 여부
        """
        if not self._validate_password(new_password):
            return False
            
        success = self.encryption_manager.reset_password(new_password)
        if success:
            self._update_activity()
            
        return success
        
    def encrypt_data(self, data: str) -> bytes:
        """데이터 암호화"""
        if not self.is_logged_in():
            raise RuntimeError("Not logged in")
            
        self._update_activity()
        return self.encryption_manager.encrypt_data(data)
        
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """데이터 복호화"""
        if not self.is_logged_in():
            raise RuntimeError("Not logged in")
            
        self._update_activity()
        return self.encryption_manager.decrypt_data(encrypted_data)
        
    def get_session_remaining_minutes(self) -> int:
        """세션 남은 시간 (분)"""
        if not self.last_activity_time:
            return 0
            
        elapsed = time.time() - self.last_activity_time
        remaining = (self.auto_logout_minutes * 60) - elapsed
        return max(0, int(remaining / 60))
        
    def _validate_password(self, password: str) -> bool:
        """비밀번호 유효성 검증"""
        if not password or len(password) < 8:
            return False
            
        # 최소 요구사항: 8자 이상
        # 추가 요구사항은 필요에 따라 구현
        return True
        
    def _update_activity(self):
        """활동 시간 업데이트"""
        self.last_activity_time = time.time()
        
    def _is_session_expired(self) -> bool:
        """세션 만료 여부 확인"""
        if not self.last_activity_time:
            return True
            
        elapsed = time.time() - self.last_activity_time
        return elapsed > (self.auto_logout_minutes * 60)
        
    def _handle_session_expired(self):
        """세션 만료 처리"""
        security_logger.log_session_event("expired", {'auto_logout_minutes': self.auto_logout_minutes})
        self.logout("session_expired")
        if self.on_logout_callback:
            self.on_logout_callback()