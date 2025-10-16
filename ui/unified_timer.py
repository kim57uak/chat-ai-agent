"""
Unified Timer Manager
여러 타이머를 하나로 통합하여 성능 개선
"""

from PyQt6.QtCore import QTimer, QObject
from typing import Callable, Dict, Optional
from core.logging import get_logger

logger = get_logger("unified_timer")


class UnifiedTimer(QObject):
    """통합 타이머 - 여러 콜백을 하나의 타이머로 관리"""
    
    def __init__(self, interval_ms: int = 100):
        super().__init__()
        self._timer = QTimer()
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._on_timeout)
        
        self._callbacks: Dict[str, Callable] = {}
        self._enabled_callbacks: Dict[str, bool] = {}
        
    def register(self, name: str, callback: Callable, enabled: bool = True):
        """콜백 등록"""
        self._callbacks[name] = callback
        self._enabled_callbacks[name] = enabled
        
        if not self._timer.isActive() and any(self._enabled_callbacks.values()):
            self._timer.start()
    
    def unregister(self, name: str):
        """콜백 제거"""
        if name in self._callbacks:
            del self._callbacks[name]
            del self._enabled_callbacks[name]
        
        if not any(self._enabled_callbacks.values()):
            self._timer.stop()
    
    def enable(self, name: str):
        """콜백 활성화"""
        if name in self._enabled_callbacks:
            self._enabled_callbacks[name] = True
            if not self._timer.isActive():
                self._timer.start()
    
    def disable(self, name: str):
        """콜백 비활성화"""
        if name in self._enabled_callbacks:
            self._enabled_callbacks[name] = False
    
    def _on_timeout(self):
        """타이머 콜백 실행"""
        for name, callback in self._callbacks.items():
            if self._enabled_callbacks.get(name, False):
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Callback {name} error: {e}")
    
    def stop(self):
        """타이머 중지"""
        self._timer.stop()
    
    def cleanup(self):
        """정리"""
        self._timer.stop()
        self._callbacks.clear()
        self._enabled_callbacks.clear()


# 전역 인스턴스
_unified_timer: Optional[UnifiedTimer] = None


def get_unified_timer() -> UnifiedTimer:
    """통합 타이머 인스턴스 반환"""
    global _unified_timer
    if _unified_timer is None:
        _unified_timer = UnifiedTimer()
    return _unified_timer
