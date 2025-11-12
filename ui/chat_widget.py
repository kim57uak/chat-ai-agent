from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QHBoxLayout, QFileDialog, QCheckBox, QLabel, QProgressBar, 
                             QTextBrowser, QPlainTextEdit, QComboBox)
from ui.components.modern_progress_bar import ModernProgressBar
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QSize
from PyQt6.QtGui import QFont
import weakref

from core.file_utils import load_config, load_model_api_key, load_last_model
from core.conversation_history import ConversationHistory
from core.logging import get_logger

logger = get_logger("chat_widget")
from core.message_validator import MessageValidator
from core.simple_token_accumulator import token_accumulator

# 리팩토링된 컴포넌트들
from ui.components.ai_processor import AIProcessor
from ui.components.file_handler import FileHandler
from ui.components.chat_display import ChatDisplay
from ui.components.ui_manager import UIManager
from ui.components.model_manager import ModelManager
from ui.components.status_display import status_display
from ui.styles.flat_theme import FlatTheme
from ui.styles.theme_manager import theme_manager
from ui.chat_widget_styles import ChatWidgetStylesMixin
from ui.chat_widget_session import ChatWidgetSessionMixin
from ui.chat_widget_scroll import ChatWidgetScrollMixin
from ui.chat_widget_message import ChatWidgetMessageMixin
from ui.chat_widget_welcome import ChatWidgetWelcomeMixin
from ui.chat_widget_file import ChatWidgetFileMixin

from datetime import datetime
import os


def safe_single_shot(delay, callback, widget=None):
    """안전한 QTimer.singleShot 래퍼 - 위젯 삭제 시 크래시 방지"""
    if widget is not None:
        widget_ref = weakref.ref(widget)
        
        def safe_callback():
            try:
                w = widget_ref()
                if w is not None and not getattr(w, '_is_closing', False):
                    callback()
            except (RuntimeError, AttributeError):
                pass
            except Exception:
                pass
        
        try:
            QTimer.singleShot(delay, safe_callback)
        except RuntimeError:
            pass
    else:
        def safe_callback():
            try:
                callback()
            except (RuntimeError, AttributeError):
                pass
            except Exception:
                pass
        
        try:
            QTimer.singleShot(delay, safe_callback)
        except RuntimeError:
            pass


class ChatWidget(ChatWidgetStylesMixin, ChatWidgetSessionMixin, ChatWidgetScrollMixin, ChatWidgetMessageMixin, ChatWidgetWelcomeMixin, ChatWidgetFileMixin, QWidget):
    """메인 채팅 위젯 - 컴포넌트들을 조합하여 사용 (Composition over Inheritance)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_closing = False
        self._timers = []
        
        # 성능 최적화 - 통합 타이머
        from ui.unified_timer import get_unified_timer
        self._unified_timer = get_unified_timer()
        
        # 스크롤 상태 추적
        self._user_is_scrolling = False
        self._last_scroll_time = 0
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)
        
        self.conversation_history = ConversationHistory()
        self.conversation_history.load_from_file()
        
        self.uploaded_file_content = None
        self.uploaded_file_name = None
        self.messages = []
        self.request_start_time = None
        
        self.current_session_id = None
        self.loaded_message_count = 0
        self.total_message_count = 0
        self.is_loading_more = False
        
        self._load_pagination_settings()
        
        self._setup_ui()
        self._setup_components()
        self._setup_connections()
        self._load_previous_conversations()
        
        safe_single_shot(100, self._apply_initial_theme, self)
        safe_single_shot(500, self._apply_theme_if_needed, self)
    
    def _setup_ui(self):
        """UI 구성 - 상단 정보 영역 삭제"""
        # 상단 정보 영역 삭제 - 좌측 패널로 이동
        pass
        
        # 채팅 표시 영역
        self.chat_display_view = QWebEngineView(self)
        self.chat_display_view.setMinimumHeight(400)
        self.layout.addWidget(self.chat_display_view, 1)
        
        # 현대적인 로딩 바
        self.loading_bar = ModernProgressBar(self)
        self.loading_bar.hide()
        self.layout.addWidget(self.loading_bar)
        
        # 입력 영역
        self._setup_input_area()
    
    def _setup_input_area(self):
        """입력 영역 설정"""
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # 모드 선택 콤보박스 (입력창 밖으로 이동)
        self.mode_combo = QComboBox(self)
        self.mode_combo.addItem("💬 Ask", "simple")
        self.mode_combo.addItem("🔧 Agent", "tool")
        self.mode_combo.addItem("🧠 RAG", "rag")
        self.mode_combo.setCurrentIndex(0)
        self.mode_combo.setFixedSize(150, 114)  # 버튼과 동일한 높이
        
        # 드롭다운 폭을 선택 영역과 정확히 동일하게
        self.mode_combo.view().setFixedWidth(150)
        self.mode_combo.setStyleSheet("""
            QComboBox QAbstractItemView {
                width: 150px;
                min-width: 150px;
                max-width: 150px;
                padding: 0px;
                margin: 0px;
                border: 1px solid #555555;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px;
                margin: 0px;
            }
        """)
        
        self.mode_combo.currentIndexChanged.connect(self._on_mode_combo_changed)
        self._update_mode_combo_style()
        
        # 입력 컨테이너
        self.input_container = QWidget(self)
        input_container_layout = QHBoxLayout(self.input_container)
        input_container_layout.setContentsMargins(4, 4, 4, 4)
        input_container_layout.setSpacing(4)
        
        # 드래그 핸들
        self.drag_handle = QWidget(self)
        self.drag_handle.setFixedHeight(8)
        self.drag_handle.setCursor(Qt.CursorShape.SizeVerCursor)
        self.drag_handle.setStyleSheet("""
            QWidget {
                background-color: #666666;
                border-radius: 4px;
                margin: 2px 20px;
            }
            QWidget:hover {
                background-color: #888888;
            }
        """)
        self.drag_handle.mousePressEvent = self._start_drag
        self.drag_handle.mouseMoveEvent = self._handle_drag
        self.drag_handle.mouseReleaseEvent = self._end_drag
        self._dragging = False
        self._drag_start_y = 0
        self._original_height = 57
        
        # 입력창
        self.input_text = QTextEdit(self)
        self.input_text.setFixedHeight(57)
        self.input_text.setPlaceholderText("메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)")
        self._update_input_text_style()
        
        # 컨테이너 스타일
        self._update_input_container_style(self.input_container)
        
        input_container_layout.addWidget(self.input_text, 1)
        
        # 오른쪽 버튼 컨테이너
        button_container = QWidget(self)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(2)  # 버튼 간격 줄임
        
        # 버튼들 - 테마 색상 적용된 이모지 버튼
        themed_button_style = self._get_themed_button_style()
        cancel_button_style = self._get_cancel_button_style()
        
        self.send_button = QPushButton('🚀', self)
        self.send_button.setFixedSize(114, 114)
        self.send_button.setStyleSheet(themed_button_style)
        self.send_button.setToolTip("전송")
        
        # 템플릿 버튼 삭제 - 좌측 패널로 이동
        
        self.upload_button = QPushButton('📎', self)
        self.upload_button.setFixedSize(114, 114)
        self.upload_button.setStyleSheet(themed_button_style)
        self.upload_button.setToolTip("파일")
        
        self.cancel_button = QPushButton('❌', self)
        self.cancel_button.setFixedSize(114, 114)
        self.cancel_button.setVisible(False)
        self.cancel_button.setStyleSheet(cancel_button_style)
        self.cancel_button.setToolTip("취소")
        
        # 버튼 순서: 전송 / 파일
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.cancel_button)
        
        # 메인 레이아웃에 추가: 모드 | 입력창 | 버튼
        input_layout.addWidget(self.mode_combo, 0)  # 모드 선택
        input_layout.addWidget(self.input_container, 1)  # 입력창이 대부분 차지
        input_layout.addWidget(button_container, 0)  # 버튼은 고정 크기
        
        # 드래그 핸들과 입력 영역을 수직 레이아웃으로 배치
        input_with_handle = QVBoxLayout()
        input_with_handle.setContentsMargins(0, 0, 0, 0)
        input_with_handle.setSpacing(0)
        input_with_handle.addWidget(self.drag_handle)
        input_with_handle.addLayout(input_layout)
        
        self.layout.addLayout(input_with_handle, 0)
    
    def _setup_components(self):
        """컴포넌트 초기화"""
        # AI 프로세서
        self.ai_processor = AIProcessor(self)
        
        # 채팅 표시
        self.chat_display = ChatDisplay(self.chat_display_view)
        self.chat_display.set_chat_widget(self)
        
        # UI 매니저
        self.ui_manager = UIManager(
            self.send_button, 
            self.cancel_button, 
            self.upload_button,
            None,  # template_button 제거
            self.loading_bar
        )
        
        # 모델 매니저 삭제 - 좌측 패널로 이동
        pass
    
    def _setup_connections(self):
        """시그널 연결"""
        # 버튼 연결
        self.send_button.clicked.connect(self.send_message)
        self.cancel_button.clicked.connect(self.cancel_request)
        self.upload_button.clicked.connect(self.upload_file)
        
        # AI 프로세서 시그널 연결
        self.ai_processor.finished.connect(self.on_ai_response)
        self.ai_processor.error.connect(self.on_ai_error)
        self.ai_processor.streaming.connect(self.on_ai_streaming)
        self.ai_processor.streaming_complete.connect(self.on_streaming_complete)
        self.ai_processor.conversation_completed.connect(self._on_conversation_completed)
        
        # 상태 표시 연결 삭제 - 좌측 패널로 이동
        
        # 모델/도구 라벨 클릭 연결 삭제 - 좌측 패널로 이동
        
        # 키 이벤트 처리
        self.input_text.keyPressEvent = self.handle_input_key_press
        
        # 웹뷰 로드 완료
        self.chat_display_view.loadFinished.connect(self._on_webview_loaded)
        
        # 웹뷰 로드 시간 초과 시 대비책
        safe_single_shot(2000, self._ensure_welcome_message, self)
    
    def handle_input_key_press(self, event):
        """입력창 키 이벤트 처리"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                QTextEdit.keyPressEvent(self.input_text, event)
            else:
                self.send_message()
        else:
            QTextEdit.keyPressEvent(self.input_text, event)
    
    def _on_mode_combo_changed(self, index):
        """모드 콤보박스 변경 핸들러"""
        mode_value = self.mode_combo.itemData(index)
        logger.info(f"Chat mode changed to: {mode_value}")
        
        # 모드에 따라 placeholder 변경
        if mode_value == "simple":
            self.input_text.setPlaceholderText("메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)")
        elif mode_value == "tool":
            self.input_text.setPlaceholderText("도구를 사용한 메시지 입력... (Enter로 전송, Shift+Enter로 줄바꿈)")
        elif mode_value == "rag":
            self.input_text.setPlaceholderText("RAG 모드: 문서 검색 + 도구 사용... (Enter로 전송, Shift+Enter로 줄바꿈)")
    
    def send_message(self):
        """메시지 전송"""
        user_text = self.input_text.toPlainText().strip()
        if not user_text:
            return
        
        # 새 AI 프로세서 생성 (토큰 누적기는 초기화하지 않음)
        self.ai_processor.cancel()
        self.ai_processor = AIProcessor(self)
        self.ai_processor.finished.connect(self.on_ai_response)
        self.ai_processor.error.connect(self.on_ai_error)
        self.ai_processor.streaming.connect(self.on_ai_streaming)
        self.ai_processor.conversation_completed.connect(self._on_conversation_completed)
        
        self._process_new_message(user_text)
    
    def cancel_request(self):
        """요청 취소"""
        logger.debug("취소 요청 시작")
        
        self.ui_manager.set_ui_enabled(True)
        self.ui_manager.show_loading(False)
        
        if hasattr(self, 'ai_processor'):
            self.ai_processor.cancel()
        
        # 점진적 출력도 취소
        self.chat_display.cancel_progressive_display()
        
        self.chat_display.append_message('시스템', '요청을 취소했습니다.')
        
        # 취소 메시지 후 맨 하단으로 스크롤
        safe_single_shot(300, self._scroll_to_bottom, self)
        
        logger.debug("취소 요청 완료")
    
    def on_ai_streaming(self, sender, partial_text):
        """스트리밍 처리"""
        pass  # 현재 버전에서는 스트리밍 비활성화
    
    def on_streaming_complete(self, sender, full_text, used_tools):
        """스트리밍 완료 처리"""
        pass  # 현재 버전에서는 스트리밍 비활성화
    
    def _on_webview_loaded(self, ok):
        """웹뷰 로드 완료"""
        if ok:
            safe_single_shot(500, self._load_previous_conversations, self)
        else:
            # 웹뷰 로드 실패 시에도 웰컴 메시지 표시
            safe_single_shot(1000, self._show_welcome_message, self)
    
    # 상태 표시 업데이트 삭제 - 좌측 패널로 이동
    
    def close(self):
        """위젯 종료 (리소스 정리)"""
        self._is_closing = True
        
        try:
            if hasattr(self, 'ai_processor'):
                self.ai_processor.cancel()
                if hasattr(self.ai_processor, 'shutdown'):
                    self.ai_processor.shutdown()
            
            # 모든 타이머 정리
            for timer in getattr(self, '_timers', []):
                try:
                    if timer and not timer.isNull():
                        timer.stop()
                        timer.timeout.disconnect()
                        timer.deleteLater()
                except RuntimeError:
                    pass
            
            if hasattr(self, 'scroll_check_timer'):
                try:
                    if self.scroll_check_timer and not self.scroll_check_timer.isNull():
                        self.scroll_check_timer.stop()
                        self.scroll_check_timer.timeout.disconnect()
                        self.scroll_check_timer.deleteLater()
                        self.scroll_check_timer = None
                except RuntimeError:
                    pass
            
            self._timers.clear()
            
        except Exception:
            pass
    
    def _on_conversation_completed(self, _):
        """대화 완료 시 토큰 누적기 종료"""
        try:
            # 대화 종료만 처리 (토큰 박스는 표시하지 않음)
            if token_accumulator.end_conversation():
                input_tokens, output_tokens, total_tokens = token_accumulator.get_total()
                logger.debug(f"[ChatWidget] 대화 완룮 - 토큰: {total_tokens:,}개")
            
        except Exception as e:
            logger.debug(f"대화 완룮 처리 오류: {e}")
    
    def _update_mode_toggle_style(self):
        """모드 토글 스타일 동적 업데이트"""
        try:
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                style = f"""
                QPushButton {{
                    background-color: {colors.get('surface', '#1e1e1e')};
                    color: {colors.get('text_primary', '#ffffff')};
                    border: 1px solid {colors.get('divider', '#333333')};
                    border-radius: 12px;
                    padding: 6px 18px;
                    font-size: 40px;
                    font-weight: 700;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    min-width: 100px;
                    max-width: 100px;
                    margin-right: 8px;
                    margin-left: 12px;
                }}
                QPushButton:hover {{
                    background-color: {colors.get('surface', '#1e1e1e')};
                    color: {colors.get('text_primary', '#ffffff')};
                    font-size: 44px;
                }}
                QPushButton:checked {{
                    background-color: {colors.get('surface', '#1e1e1e')};
                    color: {colors.get('text_primary', '#ffffff')};
                }}
                """
            else:
                style = FlatTheme.get_input_area_style()['mode_toggle']
            
            # 호버 효과 유지를 위해 스타일 업데이트 비활성화
            pass
            
        except Exception as e:
            logger.debug(f"모드 토글 스타일 업데이트 오류: {e}")
            self.mode_toggle.setStyleSheet(FlatTheme.get_input_area_style()['mode_toggle'] + "font-size: 48px;")
    
    def _start_drag(self, event):
        """드래그 시작"""
        self._dragging = True
        self._drag_start_y = event.globalPosition().y()
        self._original_height = self.input_text.height()
    
    def _handle_drag(self, event):
        """드래그 처리"""
        if self._dragging:
            delta_y = self._drag_start_y - event.globalPosition().y()
            new_height = int(max(57, min(300, self._original_height + delta_y)))
            self.input_text.setFixedHeight(new_height)
    
    def _end_drag(self, event):
        """드래그 종료"""
        self._dragging = False
    
    def show_progress_bar(self):
        """프로그레스바 표시"""
        if hasattr(self, "loading_bar"):
            self.loading_bar.show()

    def hide_progress_bar(self):
        """프로그레스바 숨김"""
        if hasattr(self, "loading_bar"):
            self.loading_bar.hide()
