"""
Chat Widget - Refactored with SOLID Principles
채팅 위젯 - SOLID 원칙 적용 리팩토링

Design Patterns Applied:
- Facade Pattern: 복잡한 하위 시스템을 단순한 인터페이스로 제공
- Strategy Pattern: 테마 적용 전략
- Observer Pattern: 이벤트 기반 통신
- Command Pattern: 메시지 처리
- Iterator Pattern: 세션 메시지 페이징
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from core.logging import get_logger
from core.conversation_history import ConversationHistory

# 리팩토링된 컴포넌트들
from ui.components.ai_processor import AIProcessor
from ui.components.file_handler import FileHandler
from ui.components.chat_display import ChatDisplay
from .input_area import InputArea
from .message_handler import MessageHandler
from .session_loader import SessionLoader
from .scroll_manager import ScrollManager
from .theme_applier import ChatThemeApplier

logger = get_logger("chat_widget")


class ChatWidget(QWidget):
    """
    메인 채팅 위젯 - Facade Pattern
    
    복잡한 하위 시스템(입력, 메시지 처리, 세션 로드, 스크롤 등)을
    단순한 인터페이스로 제공
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_closing = False
        
        # 기존 컴포넌트와의 호환성을 위한 속성
        self.uploaded_file_content = None
        self.uploaded_file_name = None
        self.messages = []
        self.current_session_id = None
        
        # 대화 히스토리
        self.conversation_history = ConversationHistory()
        self.conversation_history.load_from_file()
        
        # 컴포넌트 초기화 (Composition over Inheritance)
        self._init_components()
        
        # UI 설정
        self._setup_ui()
        
        # 연결 설정
        self._setup_connections()
        
        # 테마 적용
        self.update_theme()
        
    def _init_components(self):
        """컴포넌트 초기화 - Dependency Injection"""
        # 입력 영역
        self.input_area = InputArea(self)
        
        # 메시지 핸들러
        self.message_handler = MessageHandler(self)
        
        # 세션 로더
        self.session_loader = SessionLoader(self)
        
        # 스크롤 관리자
        self.scroll_manager = ScrollManager(self)
        
        # AI 프로세서 (기존 컴포넌트)
        self.ai_processor = AIProcessor(self)
        
        # 파일 핸들러 (정적 메서드 사용)
        self.file_handler = FileHandler
        
        # 웹 뷰 생성
        self.web_view = QWebEngineView()
        self.page = self.web_view.page()
        self.settings = self.web_view.settings()
        
        # 채팅 디스플레이 (기존 컴포넌트)
        self.chat_display = ChatDisplay(self.web_view)
        
    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # 채팅 디스플레이 (웹 뷰)
        layout.addWidget(self.web_view, 1)
        
        # 입력 영역
        layout.addWidget(self.input_area)
        
        self.setLayout(layout)
        
    def _setup_connections(self):
        """시그널/슬롯 연결 - Observer Pattern"""
        # 입력 영역 → 메시지 핸들러
        self.input_area.send_requested.connect(self._on_send_requested)
        self.input_area.file_upload_requested.connect(self._on_file_upload_requested)
        self.input_area.cancel_requested.connect(self._on_cancel_requested)
        
        # 메시지 핸들러 → UI 업데이트
        self.message_handler.message_sent.connect(self._on_message_sent)
        self.message_handler.ai_request_started.connect(self._on_ai_request_started)
        self.message_handler.error_occurred.connect(self._on_error)
        
        # 세션 로더 → 채팅 디스플레이
        self.session_loader.messages_loaded.connect(self._on_messages_loaded)
        self.session_loader.loading_started.connect(lambda: self.input_area.set_processing(True))
        self.session_loader.loading_finished.connect(lambda: self.input_area.set_processing(False))
        
        # 스크롤 관리자 → 채팅 디스플레이
        self.scroll_manager.scroll_to_bottom_requested.connect(self._scroll_to_bottom)
        self.scroll_manager.load_more_requested.connect(self.session_loader.load_more_messages)
        
        # AI 프로세서 → UI 업데이트
        self.ai_processor.finished.connect(self._on_ai_response)
        self.ai_processor.streaming.connect(self._on_ai_streaming)
        self.ai_processor.streaming_complete.connect(self._on_streaming_complete)
        self.ai_processor.error.connect(self._on_error)
        
        # 파일 업로드는 직접 처리
        
    # === 이벤트 핸들러 ===
    
    def _on_send_requested(self, text: str):
        """메시지 전송 요청"""
        use_tools = self.input_area.is_tool_mode()
        self.message_handler.send_message(text, use_tools)
        self.input_area.clear_input()
        self.input_area.set_processing(True)
        
    def _on_file_upload_requested(self):
        """파일 업로드 요청"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "파일 선택", "", 
            "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf);;Word Files (*.docx *.doc)"
        )
        if file_path:
            content, filename = self.file_handler.process_file(file_path)
            self._on_file_processed(content, filename)
        
    def _on_cancel_requested(self):
        """취소 요청"""
        self.ai_processor.cancel_request()
        self.input_area.set_processing(False)
        
    def _on_message_sent(self, message: dict):
        """메시지 전송 완료"""
        self.chat_display.add_message(message)
        self.scroll_manager.scroll_to_bottom(100)
        
    def _on_ai_request_started(self, api_key: str, model: str, text: str, file_prompt: str):
        """AI 요청 시작"""
        self.ai_processor.process_message(api_key, model, text, file_prompt)
        
    def _on_ai_response(self, response: dict):
        """AI 응답 수신"""
        self.chat_display.add_message(response)
        self.input_area.set_processing(False)
        self.scroll_manager.scroll_to_bottom(100)
        
    def _on_ai_streaming(self, partial_text: str):
        """AI 스트리밍 업데이트"""
        self.chat_display.update_streaming_message(partial_text)
        if self.scroll_manager.should_auto_scroll():
            self.scroll_manager.scroll_to_bottom()
            
    def _on_streaming_complete(self, full_text: str, used_tools: list):
        """스트리밍 완료"""
        self.chat_display.finalize_streaming_message(full_text, used_tools)
        self.input_area.set_processing(False)
        self.scroll_manager.scroll_to_bottom(100)
        
    def _on_error(self, error_msg: str):
        """에러 발생"""
        self.chat_display.show_error(error_msg)
        self.input_area.set_processing(False)
        
    def _on_file_processed(self, content: str, filename: str):
        """파일 처리 완료"""
        self.uploaded_file_content = content
        self.uploaded_file_name = filename
        self.message_handler.set_file_upload(content, filename)
        self.input_area.set_file_info(filename)
        
    def _on_messages_loaded(self, messages: list, prepend: bool):
        """메시지 로드 완료"""
        self.chat_display.display_messages(messages, prepend)
        if not prepend:
            self.scroll_manager.scroll_to_bottom(100)
            
    def _scroll_to_bottom(self):
        """하단으로 스크롤"""
        self.chat_display.scroll_to_bottom()
        
    # === 공개 API ===
    
    def load_session_context(self, session_id: int):
        """세션 컨텍스트 로드 - Facade Pattern"""
        self.current_session_id = session_id
        self.message_handler.set_session(session_id)
        self.session_loader.set_session(session_id)
        self.session_loader.load_initial_messages()
        self.scroll_manager.reset_scroll_state()
        
    def clear_conversation_history(self):
        """대화 히스토리 초기화"""
        self.chat_display.clear()
        self.conversation_history.clear()
        self.message_handler.clear_file_upload()
        self.input_area.set_file_info(None)
        
    def update_theme(self):
        """테마 업데이트 - Strategy Pattern"""
        ChatThemeApplier.apply_to_widget(self)
        if hasattr(self.chat_display, 'update_theme'):
            self.chat_display.update_theme()
            
    def close(self):
        """위젯 종료"""
        self._is_closing = True
        self.ai_processor.cancel_request()
        super().close()
