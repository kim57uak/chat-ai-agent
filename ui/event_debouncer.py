"""
Event Debouncer
이벤트를 디바운싱하여 불필요한 호출 방지
"""

from PyQt6.QtCore import QTimer, QObject
from typing import Callable, Dict
from core.logging import get_logger

logger = get_logger("event_debouncer")


class EventDebouncer(QObject):
    """이벤트 디바운서"""
    
    def __init__(self):
        super().__init__()
        self._timers: Dict[str, QTimer] = {}
        self._callbacks: Dict[str, Callable] = {}
    
    def debounce(self, key: str, callback: Callable, delay_ms: int = 100):
        """이벤트 디바운싱"""
        # 기존 타이머가 있으면 중지
        if key in self._timers:
            self._timers[key].stop()
        else:
            self._timers[key] = QTimer()
            self._timers[key].setSingleShot(True)
            self._timers[key].timeout.connect(lambda: self._execute(key))
        
        self._callbacks[key] = callback
        self._timers[key].start(delay_ms)
    
    def _execute(self, key: str):
        """콜백 실행"""
        if key in self._callbacks:
            try:
                self._callbacks[key]()
            except Exception as e:
                logger.error(f"Debounced callback error for {key}: {e}")
    
    def cancel(self, key: str):
        """디바운싱 취소"""
        if key in self._timers:
            self._timers[key].stop()
    
    def cleanup(self):
        """정리"""
        for timer in self._timers.values():
            timer.stop()
        self._timers.clear()
        self._callbacks.clear()


# 전역 인스턴스
_event_debouncer = None


def get_event_debouncer() -> EventDebouncer:
    """이벤트 디바운서 인스턴스 반환"""
    global _event_debouncer
    if _event_debouncer is None:
        _event_debouncer = EventDebouncer()
    return _event_debouncer
