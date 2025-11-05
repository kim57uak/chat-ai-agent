"""
Chat Widget Session Mixin
채팅 위젯 세션/히스토리 관리 메서드 분리
"""

from core.logging import get_logger
from ui.styles.theme_manager import theme_manager

logger = get_logger("chat_widget_session")


class ChatWidgetSessionMixin:
    """채팅 위젯 세션/히스토리 관리 메서드"""
    
    def load_session_context(self, session_id: int):
        """세션 컨텍스트 로드 (페이징 지원)"""
        try:
            from ui.chat_widget import safe_single_shot
            
            self.current_session_id = session_id
            
            from core.session.session_manager import session_manager
            self.total_message_count = session_manager.get_message_count(session_id)
            
            if hasattr(self.conversation_history, 'clear_session'):
                self.conversation_history.clear_session()
            else:
                self.conversation_history.current_session = []
            self.messages = []
            
            self.chat_display.web_view.page().runJavaScript("document.getElementById('messages').innerHTML = '';")
            
            initial_limit = min(self.initial_load_count, self.total_message_count)
            
            context_messages = session_manager.get_session_messages(session_id, initial_limit, 0)
            self.loaded_message_count = len(context_messages)
            
            logger.debug(f"[CHAT_WIDGET] Loaded {len(context_messages)} messages")
            for i, msg in enumerate(context_messages):
                logger.debug(f"[CHAT_WIDGET] Message {i+1}: role={msg['role']}, id={msg['id']}, timestamp={msg['timestamp'][:19]}")
            
            for msg in context_messages:
                if hasattr(self.conversation_history, 'add_message'):
                    self.conversation_history.add_message(msg['role'], msg['content'])
                self.messages.append(msg)
            
            safe_single_shot(100, lambda: self._display_session_messages(context_messages), self)
            
            if context_messages:
                load_msg = f"💼 세션 로드 완료: {len(context_messages)}개 메시지"
                if self.total_message_count > self.initial_load_count:
                    load_msg += f" (최근 {self.initial_load_count}개만 표시, 전체: {self.total_message_count}개)"
                    load_msg += "\n\n🔼 위로 스크롤하면 이전 메시지를 볼 수 있습니다."
                self.chat_display.append_message('시스템', load_msg)
            
            safe_single_shot(600, self._scroll_to_bottom, self)
            safe_single_shot(1200, self._scroll_to_bottom, self)
            safe_single_shot(2000, self._scroll_to_bottom, self)
            
            self._setup_scroll_listener()
            
            logger.debug(f"[LOAD_SESSION] 세션 컨텍스트 로드 시작: {self.total_message_count}개 메시지 (표시: {len(context_messages)}개)")
            
        except Exception as e:
            logger.debug(f"세션 컨텍스트 로드 오류: {e}")
    
    def _load_pagination_settings(self):
        """페이징 설정 로드"""
        try:
            import json
            import os
            
            config_path = os.path.join(os.getcwd(), 'prompt_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                history_settings = config.get('history_settings', {})
                self.initial_load_count = history_settings.get('initial_load_count', 20)
                self.page_size = history_settings.get('page_size', 10)
                
                logger.debug(f"[PAGINATION] 설정 로드: initial_load_count={self.initial_load_count}, page_size={self.page_size}")
            else:
                self.initial_load_count = 20
                self.page_size = 10
                logger.debug(f"[PAGINATION] 기본값 사용: initial_load_count={self.initial_load_count}, page_size={self.page_size}")
                
        except Exception as e:
            logger.debug(f"[PAGINATION] 설정 로드 오류: {e}")
            self.initial_load_count = 20
            self.page_size = 10
    
    def _display_session_messages(self, messages, prepend=False):
        """세션 메시지들을 화면에 표시"""
        try:
            from ui.chat_widget import safe_single_shot
            
            display_messages = list(reversed(messages)) if prepend else messages
            
            for i, msg in enumerate(display_messages):
                logger.debug(f"[LOAD_SESSION] 메시지 {i+1} 표시: role={msg['role']}, content={msg['content'][:30]}...")
                msg_id = str(msg.get('id', f"session_msg_{i}"))
                timestamp = msg.get('timestamp')
                
                content = msg['content']
                content_html = msg.get('content_html')
                
                if msg['role'] == 'user':
                    self.chat_display.append_message('사용자', content, message_id=msg_id, prepend=prepend, timestamp=timestamp, content_html=content_html)
                elif msg['role'] == 'assistant':
                    self.chat_display.append_message('AI', content, message_id=msg_id, prepend=prepend, timestamp=timestamp, content_html=content_html)
            
            logger.debug(f"[LOAD_SESSION] 세션 메시지 표시 완료: {len(messages)}개")
            
            if not prepend:
                safe_single_shot(1000, self._scroll_to_bottom, self)
                
        except Exception as e:
            logger.debug(f"[LOAD_SESSION] 메시지 표시 오류: {e}")
    
    def load_more_messages(self):
        """더 많은 메시지 로드"""
        if self.is_loading_more or not self.current_session_id:
            return
        
        if self.loaded_message_count >= self.total_message_count:
            logger.debug("[LOAD_MORE] 모든 메시지가 이미 로드됨")
            return
        
        self.is_loading_more = True
        
        try:
            from core.session.session_manager import session_manager
            
            remaining_messages = self.total_message_count - self.loaded_message_count
            load_count = min(self.page_size, remaining_messages)
            offset = self.loaded_message_count
            
            logger.debug(f"[LOAD_MORE] 로드 시도: offset={offset}, limit={load_count}, 로드됨={self.loaded_message_count}, 전체={self.total_message_count}")
            
            older_messages = session_manager.get_session_messages(
                self.current_session_id, load_count, offset
            )
            
            if older_messages:
                for msg in older_messages:
                    if hasattr(self.conversation_history, 'add_message'):
                        self.conversation_history.add_message(msg['role'], msg['content'])
                    self.messages.insert(0, msg)
                
                self._display_session_messages(older_messages, prepend=True)
                self.loaded_message_count += len(older_messages)
                
                logger.debug(f"[LOAD_MORE] {len(older_messages)}개 메시지 추가 로드 (전체: {self.loaded_message_count}/{self.total_message_count})")
                
                if self.loaded_message_count < self.total_message_count:
                    load_msg = f"🔼 {len(older_messages)}개 이전 메시지 로드 완료. 더 보려면 위로 스크롤하세요."
                else:
                    load_msg = f"🎉 모든 메시지를 로드했습니다! (전체 {self.total_message_count}개)"
                
                self.chat_display.append_message('시스템', load_msg, prepend=True)
            
        except Exception as e:
            logger.debug(f"[LOAD_MORE] 오류: {e}")
        finally:
            self.is_loading_more = False
    
    def clear_conversation_history(self):
        """대화 히스토리 초기화"""
        from core.simple_token_accumulator import token_accumulator
        from ui.components.status_display import status_display
        
        if hasattr(self.conversation_history, 'clear_session'):
            self.conversation_history.clear_session()
        else:
            self.conversation_history.current_session = []
        self.messages = []
        
        status_display.reset_session_stats()
        
        token_accumulator.reset()
        logger.debug(f"[ChatWidget] 대화 히스토리 초기화 - 토큰 누적기도 초기화")
        
        from core.token_tracker import token_tracker
        if hasattr(token_tracker, 'current_conversation'):
            token_tracker.current_conversation = None
        if hasattr(token_tracker, 'conversation_history'):
            token_tracker.conversation_history.clear()
        
        main_window = self._find_main_window()
        if main_window and hasattr(main_window, 'current_session_id'):
            main_window.current_session_id = None
            main_window._auto_session_created = False
        
        logger.debug("대화 히스토리가 초기화되었습니다.")
        
        self.chat_display.clear_messages()
    
    def delete_message(self, message_id: str) -> bool:
        """메시지 삭제 - 개선된 세션 ID 찾기"""
        try:
            logger.debug(f"[CHAT_DELETE] 삭제 시작: {message_id}")
            
            try:
                db_message_id = int(message_id)
                logger.debug(f"[CHAT_DELETE] DB 메시지 ID: {db_message_id}")
            except ValueError:
                logger.debug(f"[CHAT_DELETE] 잘못된 메시지 ID 형식: {message_id}")
                return False
            
            from core.session.message_manager import message_manager
            session_id = message_manager.find_session_by_message_id(db_message_id)
            logger.debug(f"[CHAT_DELETE] 메시지로부터 세션 ID 찾음: {session_id}")
            
            if not session_id:
                main_window = self._find_main_window()
                if main_window and hasattr(main_window, 'current_session_id') and main_window.current_session_id:
                    session_id = main_window.current_session_id
                    logger.debug(f"[CHAT_DELETE] 메인 윈도우에서 세션 ID 가져옴: {session_id}")
            
            if not session_id and hasattr(self, 'current_session_id') and self.current_session_id:
                session_id = self.current_session_id
                logger.debug(f"[CHAT_DELETE] 채팅 위젯에서 세션 ID 가져옴: {session_id}")
            
            if not session_id:
                logger.debug(f"[CHAT_DELETE] 세션 ID를 찾을 수 없음")
                return False
            
            logger.debug(f"[CHAT_DELETE] 사용할 세션 ID: {session_id}")
            
            success = message_manager.delete_message(session_id, db_message_id)
            logger.debug(f"[CHAT_DELETE] DB 삭제 결과: {success}")
            
            if success:
                try:
                    self.conversation_history.delete_message(message_id)
                    logger.debug(f"[CHAT_DELETE] 메모리 삭제 완료")
                except Exception as e:
                    logger.debug(f"[CHAT_DELETE] 메모리 삭제 오류: {e}")
                
                main_window = self._find_main_window()
                if main_window and hasattr(main_window, 'session_panel'):
                    main_window.session_panel.load_sessions()
                    logger.debug(f"[CHAT_DELETE] 세션 패널 새로고침 완료")
            
            return success
            
        except Exception as e:
            logger.debug(f"[CHAT_DELETE] 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _find_main_window(self):
        """메인 윈도우 찾기"""
        widget = self
        while widget:
            if widget.__class__.__name__ == 'MainWindow':
                return widget
            widget = widget.parent()
        return None
