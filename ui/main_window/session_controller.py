"""
Session Controller
세션 관리 전담 클래스
"""

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer
from functools import partial
from core.logging import get_logger
from core.safe_timer import safe_timer_manager

logger = get_logger("session_controller")


class SessionController:
    """세션 관리 전담 클래스"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_session_id = None
        self._auto_session_created = False
        self._session_load_timer = None
        self._scroll_timer = None
    
    def on_session_selected(self, session_id: int):
        """세션 선택 이벤트 처리"""
        try:
            from ui.memory_manager import memory_manager
            memory_manager.light_cleanup()
            
            self.current_session_id = session_id
            self.main_window.current_session_id = session_id
            self.main_window._update_window_title()
            
            from core.token_accumulator import token_accumulator
            token_accumulator.set_session(session_id)
            
            if hasattr(self.main_window, 'chat_widget') and hasattr(self.main_window.chat_widget, 'update_session_info'):
                self.main_window.chat_widget.update_session_info(session_id)
            
            from core.session.session_manager import session_manager
            if not session_manager:
                QMessageBox.warning(self.main_window, '오류', '세션 매니저가 초기화되지 않았습니다.')
                return
            
            session = session_manager.get_session(session_id)
            if not session:
                QMessageBox.warning(self.main_window, '오류', '세션을 찾을 수 없습니다.')
                return
            
            logger.debug(f"[SESSION_SELECT] 세션 {session_id} 로드 시도")
            
            # 페이징 구현으로 대용량 세션 경고 제거
            
            if hasattr(self.main_window.chat_widget, 'chat_display'):
                self.main_window.chat_widget.chat_display.clear_messages()
            
            if self._session_load_timer is not None:
                self._session_load_timer.stop()
                self._session_load_timer.deleteLater()
                self._session_load_timer = None
            
            self._session_load_timer = safe_timer_manager.create_timer(
                100, partial(self._safe_load_session, session_id), single_shot=True, parent=self.main_window
            )
            self._session_load_timer.start()
            
            self._schedule_scroll_to_bottom(1500)
            
            logger.debug(f"[SESSION_SELECT] 세션 로드 시작: {session['title']}")
            
        except Exception as e:
            logger.debug(f"세션 선택 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def _safe_load_session(self, session_id: int):
        """안전한 세션 로드"""
        try:
            logger.debug(f"[SAFE_LOAD] 세션 {session_id} 안전 로드 시작")
            
            if hasattr(self.main_window.chat_widget, 'load_session_context'):
                self.main_window.chat_widget.load_session_context(session_id)
            
            logger.debug(f"[SAFE_LOAD] 세션 {session_id} 안전 로드 완료")
            
            self._schedule_scroll_to_bottom(500)
            
        except Exception as e:
            logger.debug(f"[SAFE_LOAD] 안전 로드 오류: {e}")
            import traceback
            traceback.print_exc()
            
            QMessageBox.critical(
                self.main_window, '세션 로드 오류', 
                f'세션을 로드하는 중 오류가 발생했습니다:\n{str(e)}\n\n'
                f'다른 세션을 선택하거나 애플리케이션을 재시작해보세요.'
            )
    
    def on_session_created(self, session_id: int):
        """새 세션 생성 이벤트 처리"""
        self.current_session_id = session_id
        self.main_window.current_session_id = session_id
        
        # AIClient에 session_id 설정
        if hasattr(self.main_window, 'ai_client') and self.main_window.ai_client:
            self.main_window.ai_client.set_session_id(session_id)
        self._auto_session_created = True
        
        self.main_window._update_window_title()
        
        from core.token_accumulator import token_accumulator
        token_accumulator.set_session(session_id)
        
        if hasattr(self.main_window, 'chat_widget') and hasattr(self.main_window.chat_widget, 'update_session_info'):
            self.main_window.chat_widget.update_session_info(session_id)
        
        if hasattr(self.main_window.chat_widget, 'chat_display'):
            self.main_window.chat_widget.chat_display.clear_messages()
        
        self.main_window.chat_widget.current_session_id = session_id
        self.main_window.chat_widget.loaded_message_count = 0
        self.main_window.chat_widget.total_message_count = 0
        self.main_window.chat_widget.is_loading_more = False
        logger.debug(f"새 세션 생성: {session_id}")
    
    def save_message(self, role: str, content: str, token_count: int = 0, content_html: str = None):
        """메시지를 현재 세션에 저장"""
        logger.debug(f"[SAVE_MESSAGE] 시작 - role: {role}, current_session_id: {self.current_session_id}")
        
        if not self.current_session_id:
            logger.debug(f"[SAVE_MESSAGE] 세션 ID가 없음 - 자동 세션 생성 시도")
            self.create_auto_session()
        
        if self.current_session_id:
            try:
                logger.debug(f"[SAVE_MESSAGE] 세션 {self.current_session_id}에 메시지 저장 시도")
                from core.session.session_manager import session_manager
                if session_manager:
                    message_id = session_manager.add_message(
                        self.current_session_id, 
                        role, 
                        content, 
                        content_html=content_html,
                        token_count=token_count
                    )
                    logger.debug(f"[SAVE_MESSAGE] 성공 - message_id: {message_id}")
                else:
                    logger.debug(f"[SAVE_MESSAGE] 오류 - session_manager가 초기화되지 않음")
                    return
                
                if hasattr(self.main_window, 'chat_widget') and hasattr(self.main_window.chat_widget, 'update_session_info'):
                    self.main_window.chat_widget.update_session_info(self.current_session_id)
                
                self.main_window.session_panel.load_sessions()
            except Exception as e:
                logger.debug(f"[SAVE_MESSAGE] 오류: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.debug(f"[SAVE_MESSAGE] 실패 - 세션 ID가 여전히 None")
    
    def create_auto_session(self):
        """자동 세션 생성"""
        logger.debug(f"[AUTO_SESSION] 시작 - _auto_session_created: {self._auto_session_created}")
        if not self._auto_session_created:
            try:
                from datetime import datetime
                title = f"대화 {datetime.now().strftime('%m/%d %H:%M')}"
                logger.debug(f"[AUTO_SESSION] 세션 생성 시도 - title: {title}")
                from core.session.session_manager import session_manager
                if session_manager:
                    self.current_session_id = session_manager.create_session(title)
                    self.main_window.current_session_id = self.current_session_id
                    
                    # AIClient에 session_id 설정
                    if hasattr(self.main_window, 'ai_client') and self.main_window.ai_client:
                        self.main_window.ai_client.set_session_id(self.current_session_id)
                else:
                    logger.debug(f"[AUTO_SESSION] 오류 - session_manager가 초기화되지 않음")
                    return
                self._auto_session_created = True
                logger.debug(f"[AUTO_SESSION] 성공 - session_id: {self.current_session_id}")
                
                if hasattr(self.main_window, 'chat_widget') and hasattr(self.main_window.chat_widget, 'update_session_info'):
                    self.main_window.chat_widget.update_session_info(self.current_session_id)
                
                self.main_window.session_panel.load_sessions()
                self.main_window.session_panel.select_session(self.current_session_id)
            except Exception as e:
                logger.debug(f"[AUTO_SESSION] 오류: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.debug(f"[AUTO_SESSION] 이미 생성됨 - current_session_id: {self.current_session_id}")
    
    def _schedule_scroll_to_bottom(self, delay_ms: int):
        """지연된 스크롤 예약"""
        if self._scroll_timer is None:
            self._scroll_timer = safe_timer_manager.create_timer(
                delay_ms, self._ensure_scroll_to_bottom, single_shot=True, parent=self.main_window
            )
        if self._scroll_timer:
            self._scroll_timer.start()
    
    def _ensure_scroll_to_bottom(self):
        """채팅 위젯 하단 스크롤 보장"""
        try:
            if hasattr(self.main_window, 'chat_widget') and hasattr(self.main_window.chat_widget, '_scroll_to_bottom'):
                self.main_window.chat_widget._scroll_to_bottom()
                logger.debug("[SESSION_CONTROLLER] 채팅 위젯 하단 스크롤 강제 실행")
        except Exception as e:
            logger.debug(f"[SESSION_CONTROLLER] 하단 스크롤 오류: {e}")
