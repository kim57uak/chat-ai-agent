"""
Session Security Manager
세션 보안 관리 클래스
"""

import time
import psutil
from core.logging import get_logger
from typing import Optional, Callable
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

logger = get_logger("session_security")


class SessionSecurityManager(QObject):
    """세션 보안 관리자"""
    
    # 시그널
    auto_logout_triggered = pyqtSignal()
    system_lock_detected = pyqtSignal()
    
    def __init__(self, auth_manager=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.last_activity_time = time.time()
        self.auto_logout_enabled = True
        self.auto_logout_minutes = self._load_timeout_from_config()
        self.system_lock_check_enabled = True
        
        # 타이머 설정
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self._check_auto_logout)
        self.activity_timer.start(60000)  # 1분마다 체크
        
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self._check_system_lock)
        self.system_timer.start(5000)  # 5초마다 체크
        
        # 활동 감지 설정
        self._setup_activity_monitoring()
    
    def _setup_activity_monitoring(self):
        """사용자 활동 모니터링 설정"""
        try:
            app = QApplication.instance()
            if app:
                app.installEventFilter(self)
        except Exception as e:
            logger.error(f"활동 모니터링 설정 실패: {e}")
    
    def eventFilter(self, obj, event):
        """이벤트 필터로 사용자 활동 감지"""
        # 마우스, 키보드 이벤트 시 활동 시간 업데이트
        if event.type() in [2, 3, 4, 5, 6, 7]:  # 마우스/키보드 이벤트
            self.update_activity()
        return False
    
    def update_activity(self):
        """사용자 활동 시간 업데이트"""
        self.last_activity_time = time.time()
    
    def set_auto_logout_settings(self, enabled: bool, minutes: int):
        """자동 로그아웃 설정"""
        self.auto_logout_enabled = enabled
        self.auto_logout_minutes = minutes
        logger.info(f"자동 로그아웃 설정: {enabled}, {minutes}분")
    
    def _check_auto_logout(self):
        """자동 로그아웃 체크"""
        if not self.auto_logout_enabled or not self.auth_manager:
            return
        
        if not self.auth_manager.is_logged_in():
            return
        
        inactive_time = time.time() - self.last_activity_time
        inactive_minutes = inactive_time / 60
        
        if inactive_minutes >= self.auto_logout_minutes:
            logger.info(f"비활성 시간 초과로 자동 로그아웃: {inactive_minutes:.1f}분")
            self.auto_logout_triggered.emit()
    
    def _check_system_lock(self):
        """시스템 잠금 상태 체크"""
        if not self.system_lock_check_enabled or not self.auth_manager:
            return
        
        try:
            # macOS에서 화면 잠금 감지
            import subprocess
            result = subprocess.run(['pmset', '-g', 'ps'], 
                                  capture_output=True, text=True, timeout=2)
            
            if 'sleep' in result.stdout.lower():
                logger.info("시스템 잠금 감지됨")
                self.system_lock_detected.emit()
                
        except Exception:
            # 시스템 잠금 감지 실패는 무시
            pass
    
    def force_logout(self):
        """강제 로그아웃"""
        if self.auth_manager and self.auth_manager.is_logged_in():
            logger.info("강제 로그아웃 실행")
            self.auth_manager.logout()
    
    def prevent_multiple_instances(self) -> bool:
        """다중 실행 방지"""
        try:
            app_name = "chat-ai-agent"
            current_pid = psutil.Process().pid
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] == current_pid:
                        continue
                    
                    cmdline = proc.info.get('cmdline', [])
                    if any(app_name in str(cmd) for cmd in cmdline):
                        logger.warning(f"다른 인스턴스 감지: PID {proc.info['pid']}")
                        return False
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"다중 실행 체크 실패: {e}")
            return True  # 체크 실패 시 실행 허용
    
    def cleanup(self):
        """정리 작업"""
        try:
            if self.activity_timer:
                self.activity_timer.stop()
            if self.system_timer:
                self.system_timer.stop()
        except Exception as e:
            logger.error(f"세션 보안 정리 실패: {e}")


# 전역 세션 보안 매니저
session_security = None

def get_session_security_manager(auth_manager=None):
    """세션 보안 매니저 싱글톤 반환"""
    global session_security
    if session_security is None:
        session_security = SessionSecurityManager(auth_manager)
    return session_security