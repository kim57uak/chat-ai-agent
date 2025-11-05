"""
Chat Widget Scroll Mixin
채팅 위젯 스크롤 관리 메서드 분리
"""

from PyQt6.QtCore import QTimer
from core.logging import get_logger

logger = get_logger("chat_widget_scroll")


class ChatWidgetScrollMixin:
    """채팅 위젯 스크롤 관리 메서드"""
    
    def _setup_scroll_listener(self):
        """스크롤 이벤트 리스너 설정"""
        try:
            if self._is_closing:
                return
                
            if hasattr(self, 'scroll_check_timer') and self.scroll_check_timer is not None:
                try:
                    self.scroll_check_timer.stop()
                    self.scroll_check_timer.timeout.disconnect()
                    self.scroll_check_timer.deleteLater()
                except RuntimeError:
                    pass
            
            self.scroll_check_timer = QTimer(self)
            self.scroll_check_timer.setSingleShot(False)
            self.scroll_check_timer.timeout.connect(self._check_scroll_position)
            self.scroll_check_timer.start(2000)
            self._timers.append(self.scroll_check_timer)
        except Exception:
            pass
    
    def _check_scroll_position(self):
        """스크롤 위치 체크"""
        try:
            if (self._is_closing or not self.current_session_id or 
                self.is_loading_more or not hasattr(self, 'chat_display_view') or 
                self.chat_display_view is None):
                return
                
            self.chat_display_view.page().runJavaScript(
                "window.scrollY",
                lambda scroll_y: self._handle_scroll_position(scroll_y) if not self._is_closing else None
            )
        except (RuntimeError, AttributeError):
            if hasattr(self, 'scroll_check_timer'):
                try:
                    self.scroll_check_timer.stop()
                except RuntimeError:
                    pass
        except Exception:
            pass
    
    def _handle_scroll_position(self, scroll_y):
        """스크롤 위치 처리"""
        try:
            if scroll_y <= 50 and self.loaded_message_count < self.total_message_count:
                logger.debug(f"[SCROLL_CHECK] 스크롤 맨 위 감지: {scroll_y}, 더 로드 시도")
                self.load_more_messages()
        except RuntimeError as e:
            if "wrapped C/C++ object" in str(e):
                logger.debug(f"스크롤 처리 중 객체 삭제됨: {e}")
            else:
                raise
        except Exception as e:
            logger.debug(f"스크롤 위치 처리 오류: {e}")
    
    def _scroll_to_bottom(self):
        """채팅 화면을 맨 하단으로 스크롤"""
        try:
            self.chat_display_view.page().runJavaScript(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
        except Exception as e:
            pass
