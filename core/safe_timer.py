"""안전한 타이머 관리 모듈 - SIGABRT 크래시 방지"""

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from typing import List, Callable
import weakref
import sys
import traceback


class SafeTimerManager(QObject):
    """안전한 타이머 관리자"""
    
    # 예외 발생 시그널 (UI에서 처리 가능)
    exception_occurred = pyqtSignal(str, str)  # (callback_name, error_message)
    
    def __init__(self):
        super().__init__()
        self._timers: List[QTimer] = []
        self._is_closing = False
    
    def create_timer(self, interval: int, callback: Callable, single_shot: bool = False, parent: QObject = None) -> QTimer:
        """안전한 타이머 생성"""
        if self._is_closing:
            return None
            
        try:
            timer = QTimer(parent or self)
            timer.setSingleShot(single_shot)
            timer.setInterval(interval)
            
            # weakref로 콜백 래핑 + 로깅 예외 격리
            if parent:
                parent_ref = weakref.ref(parent)
                def safe_callback():
                    try:
                        p = parent_ref()
                        if p is not None and not getattr(p, '_is_closing', False):
                            callback()
                    except (RuntimeError, AttributeError):
                        try:
                            timer.stop()
                        except:
                            pass
                    except Exception:
                        # CRITICAL: 모든 예외를 완전히 삼킴 - Qt로 전파 방지
                        try:
                            exc_info = sys.exc_info()
                            error_msg = f"{exc_info[0].__name__}: {exc_info[1]}"
                            callback_name = callback.__name__ if hasattr(callback, '__name__') else 'unknown'
                            
                            # 콘솔에 상세 로그
                            print(f"[TIMER ERROR] {callback_name}: {error_msg}", file=sys.stderr)
                            traceback.print_exception(*exc_info, file=sys.stderr)
                            
                            # UI 알림용 시그널 발생 (선택적)
                            self.exception_occurred.emit(callback_name, error_msg)
                        except:
                            pass
            else:
                def safe_callback():
                    try:
                        if not self._is_closing:
                            callback()
                    except (RuntimeError, AttributeError):
                        try:
                            timer.stop()
                        except:
                            pass
                    except Exception:
                        # CRITICAL: 모든 예외를 완전히 삼킴 - Qt로 전파 방지
                        try:
                            exc_info = sys.exc_info()
                            error_msg = f"{exc_info[0].__name__}: {exc_info[1]}"
                            callback_name = callback.__name__ if hasattr(callback, '__name__') else 'unknown'
                            
                            # 콘솔에 상세 로그
                            print(f"[TIMER ERROR] {callback_name}: {error_msg}", file=sys.stderr)
                            traceback.print_exception(*exc_info, file=sys.stderr)
                            
                            # UI 알림용 시그널 발생 (선택적)
                            self.exception_occurred.emit(callback_name, error_msg)
                        except:
                            pass
            
            timer.timeout.connect(safe_callback)
            self._timers.append(timer)
            return timer
            
        except Exception:
            return None
    
    def cleanup_all(self):
        """모든 타이머 정리"""
        self._is_closing = True
        
        for timer in self._timers[:]:
            try:
                if timer and not timer.isNull():
                    timer.stop()
                    timer.timeout.disconnect()
                    timer.deleteLater()
            except RuntimeError:
                pass
        
        self._timers.clear()


# 전역 타이머 매니저
safe_timer_manager = SafeTimerManager()