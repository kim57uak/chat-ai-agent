from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QHBoxLayout, QFileDialog, QCheckBox, QLabel, QProgressBar, 
                             QTextBrowser, QPlainTextEdit, QComboBox)
from ui.components.modern_progress_bar import ModernProgressBar
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
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


class ChatWidget(QWidget):
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
        input_layout.setSpacing(4)  # 전체 간격 줄임
        
        # 입력 컨테이너
        self.input_container = QWidget(self)
        input_container_layout = QHBoxLayout(self.input_container)
        input_container_layout.setContentsMargins(8, 8, 8, 8)
        input_container_layout.setSpacing(8)
        
        # 모드 토글 버튼
        self.mode_toggle = QPushButton("🧠", self)
        self.mode_toggle.setCheckable(True)
        self.mode_toggle.setChecked(False)
        self.mode_toggle.setFixedHeight(48)  # 5% 더 줄임
        
        # 토글 버튼 호버 효과 스타일 (35% 증가)
        toggle_style = """
        QPushButton {
            background: transparent;
            border: none;
            font-size: 32px;
        }
        QPushButton:hover {
            background: transparent;
            font-size: 43px;
        }
        QPushButton:pressed {
            background: transparent;
            font-size: 30px;
        }
        QPushButton:checked {
            background: transparent;
        }
        """
        self.mode_toggle.setStyleSheet(toggle_style)
        self.mode_toggle.setToolTip("Ask 모드 - 뇌")
        
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
        
        input_container_layout.addWidget(self.mode_toggle, 0, Qt.AlignmentFlag.AlignVCenter)
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
        
        # 메인 레이아웃에 추가
        input_layout.addSpacing(0)  # 왼쪽 간격 제거
        input_layout.addWidget(self.input_container, 1)  # 입력창이 대부분 차지
        input_layout.addWidget(button_container, 0)  # 버튼은 고정 크기
        input_layout.addSpacing(0)  # 오른쪽 간격 제거
        
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
        self.mode_toggle.clicked.connect(self.toggle_mode)
        
        # AI 프로세서 시그널 연결
        self.ai_processor.finished.connect(self.on_ai_response)
        self.ai_processor.error.connect(self.on_ai_error)
        self.ai_processor.streaming.connect(self.on_ai_streaming)
        self.ai_processor.streaming_complete.connect(self.on_streaming_complete)
        self.ai_processor.conversation_completed.connect(self._on_conversation_completed)
        
        # 상태 표시 연결 삭제 - 좌측 패널로 이동
        
        # 모델/도구 라벨 클릭 연결 삭제 - 좌측 패널로 이동
        
        # 키보드 단축키
        self.input_text.keyPressEvent = self.handle_input_key_press
        send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.input_text)
        send_shortcut.activated.connect(self.send_message)
        
        # 템플릿 단축키 삭제 - 좌측 패널로 이동
        
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
    
    def toggle_mode(self):
        """모드 토글"""
        safe_single_shot(0, self._update_toggle_ui, self)
    
    def _update_toggle_ui(self):
        """토글 UI 업데이트"""
        try:
            is_agent_mode = self.mode_toggle.isChecked()
            if is_agent_mode:
                self.mode_toggle.setText("🤖")
                self.mode_toggle.setToolTip("Agent 모드 - 로봇이 도구를 사용합니다")
                self.input_text.setPlaceholderText("도구를 사용한 메시지 입력... (Enter로 전송, Shift+Enter로 줄바꿈)")
            else:
                self.mode_toggle.setText("🧠")
                self.mode_toggle.setToolTip("Ask 모드 - 뇌로 생각합니다")
                self.input_text.setPlaceholderText("메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)")
        except Exception as e:
            logger.debug(f"토글 UI 업데이트 오류: {e}")
    
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
    
    def _process_new_message(self, user_text):
        """새 메시지 처리"""
        self.request_start_time = datetime.now()
        
        # 사용자 입력 시에만 토큰 누적기 초기화 (사용자가 직접 입력한 경우만)
        logger.debug(f"[ChatWidget] 사용자 메시지 입력 - 토큰 누적기 상태 확인")
        # 대화가 비활성 상태일 때만 시작
        if not token_accumulator.conversation_active:
            token_accumulator.start_conversation()
        else:
            logger.debug(f"[ChatWidget] 대화가 이미 진행 중 - 토큰 계속 누적")
        
        # 사용자 메시지를 히스토리에 즉시 추가 (하이브리드 방식에서는 즉시 추가)
        message_id = self.conversation_history.add_message('user', user_text)
        self.messages.append({'role': 'user', 'content': user_text})
        
        # 메인 윈도우에 사용자 메시지 저장 알림
        logger.debug(f"[CHAT_WIDGET] 사용자 메시지 저장 시도: {user_text[:50]}...")
        main_window = self._find_main_window()
        if main_window and hasattr(main_window, 'save_message_to_session'):
            main_window.save_message_to_session('user', user_text, 0)
        else:
            logger.debug(f"[CHAT_WIDGET] MainWindow를 찾을 수 없거나 save_message_to_session 메소드 없음")
        
        self.chat_display.append_message('사용자', user_text, message_id=message_id)
        self.input_text.clear()
        
        # 사용자 메시지 후 맨 하단으로 스크롤 - 더 긴 지연
        safe_single_shot(500, self._scroll_to_bottom, self)
        
        model = load_last_model()
        api_key = load_model_api_key(model)
        # 모델 라벨 업데이트 삭제 - 좌측 패널로 이동
        
        if not api_key:
            self.chat_display.append_message('시스템', 'API Key가 설정되어 있지 않습니다. 환경설정에서 입력해 주세요.')
            return
        
        # 파일 처리
        if self.uploaded_file_content:
            if "[IMAGE_BASE64]" in self.uploaded_file_content:
                combined_prompt = f'{user_text}\n\n{self.uploaded_file_content}'
            else:
                combined_prompt = f'업로드된 파일 ({self.uploaded_file_name})에 대한 사용자 요청: {user_text}\n\n파일 내용:\n{self.uploaded_file_content}'
            
            self._start_ai_request(api_key, model, None, combined_prompt)
            self.uploaded_file_content = None
            self.uploaded_file_name = None
        else:
            self._start_ai_request(api_key, model, user_text)
    
    def _start_ai_request(self, api_key, model, user_text, file_prompt=None):
        """AI 요청 시작"""
        self.ui_manager.set_ui_enabled(False)
        self.ui_manager.show_loading(True)
        
        safe_single_shot(0, lambda: self._prepare_and_send_request(api_key, model, user_text, file_prompt), self)
    
    def _prepare_and_send_request(self, api_key, model, user_text, file_prompt=None):
        """요청 준비 및 전송 - 모든 모델에 하이브리드 히스토리 사용"""
        try:
            # logger 안전 체크
            if 'logger' not in globals():
                from core.logging import get_logger
                global logger
                logger = get_logger("chat_widget")
            # 모든 모델에 대해 하이브리드 방식으로 컨텍스트 메시지 가져오기
            context_messages = self.conversation_history.get_context_messages()
            
            validated_history = []
            # 유효한 메시지만 필터링
            for msg in context_messages:
                if msg.get('content') and msg.get('content').strip():
                    validated_history.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            logger.debug(f"하이브리드 히스토리 로드됨: {len(validated_history)}개 메시지 (모델: {model})")
            
            try:
                is_agent_mode = self.mode_toggle.isChecked()
                use_agent = is_agent_mode
            except Exception as e:
                logger.debug(f"모드 확인 오류: {e}")
                use_agent = False
            
            self.ai_processor.process_request(
                api_key, model, validated_history, user_text,
                agent_mode=use_agent, file_prompt=file_prompt
            )
        except Exception as e:
            try:
                logger.debug(f"AI 요청 준비 오류: {e}")
            except:
                print(f"AI 요청 준비 오류: {e}")
            safe_single_shot(0, lambda: self.on_ai_error(f"요청 준비 중 오류: {e}"), self)
    
    def upload_file(self):
        """파일 업로드"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '파일 선택', '', 
            '모든 파일 (*);;텍스트 파일 (*.txt);;PDF 파일 (*.pdf);;Word 파일 (*.docx *.doc);;Excel 파일 (*.xlsx *.xls);;PowerPoint 파일 (*.pptx *.ppt);;JSON 파일 (*.json);;이미지 파일 (*.jpg *.jpeg *.png *.gif *.bmp *.webp);;CSV 파일 (*.csv)'
        )
        if not file_path:
            return
        
        self.ai_processor.cancel()
        self.ai_processor = AIProcessor(self)
        self.ai_processor.finished.connect(self.on_ai_response)
        self.ai_processor.error.connect(self.on_ai_error)
        self.ai_processor.streaming.connect(self.on_ai_streaming)
        self.ai_processor.conversation_completed.connect(self._on_conversation_completed)
        
        self._process_file_upload(file_path)
    
    def _process_file_upload(self, file_path):
        """파일 업로드 처리"""
        try:
            content, filename = FileHandler.process_file(file_path)
            
            self.chat_display.append_message('사용자', f'📎 파일 업로드: {filename}')
            
            if "[IMAGE_BASE64]" not in content and len(content) > 5000:
                content = content[:5000] + "...(내용 생략)"
            
            self.uploaded_file_content = content
            self.uploaded_file_name = filename
            
            self.chat_display.append_message('시스템', f'파일이 업로드되었습니다. 이제 파일에 대해 무엇을 알고 싶은지 메시지를 입력해주세요.')
            
            # 파일 업로드 후 맨 하단으로 스크롤
            safe_single_shot(300, self._scroll_to_bottom, self)
            safe_single_shot(700, self._scroll_to_bottom, self)
            self.input_text.setPlaceholderText(f"{filename}에 대해 무엇을 알고 싶으신가요? (Enter로 전송)")
            
        except Exception as e:
            self.chat_display.append_message('시스템', f'파일 처리 오류: {e}')
            self.uploaded_file_content = None
            self.uploaded_file_name = None
            self.input_text.setPlaceholderText("메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)")
    
    # 템플릿 관련 메서드 삭제 - 좌측 패널로 이동
    
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
    
    def on_ai_response(self, sender, text, used_tools):
        """AI 응답 처리"""
        logger.debug(f"AI 응답 받음 - 길이: {len(text)}자")
        
        # 응답 시간 계산
        response_time = ""
        if self.request_start_time:
            elapsed = datetime.now() - self.request_start_time
            response_time = f" ({elapsed.total_seconds():.1f}초)"
        
        current_model = load_last_model()
        
        # 사용된 도구 정보
        tools_info = ""
        if '에이전트' in sender and used_tools:
            tool_emojis = self._get_tool_emoji_list(used_tools)
            tools_text = ", ".join([f"{emoji} {tool}" for emoji, tool in tool_emojis])
            tools_info = f"\n\n*사용된 도구: {tools_text}*"
        
        # 토큰 정보 추가
        token_info = ""
        current_status = status_display.current_status
        input_tokens = current_status.get('input_tokens', 0)
        output_tokens = current_status.get('output_tokens', 0)
        total_tokens = current_status.get('total_tokens', 0)
        
        # 토큰 누적기에서 누적 토큰 가져오기
        current_input, current_output, current_total = token_accumulator.get_total()
        if current_total > 0:
            input_tokens = current_input
            output_tokens = current_output
            total_tokens = current_total
        
        # 토큰 정보 표시 - Material Design 스타일 적용
        if total_tokens > 0:
            if input_tokens > 0 and output_tokens > 0:
                token_info = f" | 📊 {total_tokens:,}토큰 (IN:{input_tokens:,} OUT:{output_tokens:,})"
            else:
                token_info = f" | 📊 {total_tokens:,}토큰"
        
        # 테마 색상 가져오기
        colors = theme_manager.material_manager.get_theme_colors() if theme_manager.use_material_theme else {}
        is_light = not theme_manager.material_manager.is_dark_theme() if theme_manager.use_material_theme else False
        text_color = colors.get('on_surface', colors.get('text_primary', '#1a1a1a' if is_light else '#ffffff'))
        text_dim = colors.get('text_secondary', '#666666' if is_light else '#a0a0a0')
        
        # Material Design 스타일 적용된 하단 정보
        enhanced_text = f"{text}{tools_info}\n\n<div class='ai-footer'>\n<div class='ai-info' style='color: {text_dim};'>🤖 {current_model}{response_time}{token_info}</div>\n<div class='ai-warning' style='color: {text_dim};'>⚠️ AI 답변은 부정확할 수 있습니다. 중요한 정보는 반드시 검증하세요.</div>\n</div>"
        
        # 표시용 sender 결정
        display_sender = '에이전트' if '에이전트' in sender else 'AI'
        
        # AI 응답을 히스토리에 추가 - 토큰 정보 포함
        current_status = status_display.current_status
        input_tokens = current_status.get('input_tokens', 0)
        output_tokens = current_status.get('output_tokens', 0)
        total_tokens = current_status.get('total_tokens', 0)
        
        # 토큰 누적기에서 누적 토큰 가져오기
        current_input, current_output, current_total = token_accumulator.get_total()
        if current_total > 0:
            input_tokens = current_input
            output_tokens = current_output
            total_tokens = current_total
        
        ai_message_id = self.conversation_history.add_message(
            'assistant', text, current_model, 
            input_tokens=input_tokens if input_tokens > 0 else None,
            output_tokens=output_tokens if output_tokens > 0 else None,
            total_tokens=total_tokens if total_tokens > 0 else None
        )
        # self.conversation_history.save_to_file()  # JSON 저장 비활성화
        self.messages.append({'role': 'assistant', 'content': text})
        
        # 메인 윈도우에 AI 메시지 저장 알림 (HTML 포함)
        logger.debug(f"[CHAT_WIDGET] AI 메시지 저장 시도: {text[:50]}...")
        main_window = self._find_main_window()
        if main_window and hasattr(main_window, 'save_message_to_session'):
            # AI 메시지는 원본 텍스트를 저장하고 enhanced_text를 HTML로 저장
            main_window.save_message_to_session('assistant', text, total_tokens, enhanced_text)
        else:
            logger.debug(f"[CHAT_WIDGET] MainWindow를 찾을 수 없거나 save_message_to_session 메소드 없음")
        
        self.chat_display.append_message(display_sender, enhanced_text, original_sender=sender, progressive=True, message_id=ai_message_id)
        
        # AI 응답 후 맨 하단으로 스크롤 - 더 적극적으로
        safe_single_shot(800, self._scroll_to_bottom, self)
        
        # 모델 라벨 업데이트 삭제 - 좌측 패널로 이동
        
        self.ui_manager.set_ui_enabled(True)
        self.ui_manager.show_loading(False)
    
    def on_ai_streaming(self, sender, partial_text):
        """스트리밍 처리"""
        pass  # 현재 버전에서는 스트리밍 비활성화
    
    def on_streaming_complete(self, sender, full_text, used_tools):
        """스트리밍 완료 처리"""
        pass  # 현재 버전에서는 스트리밍 비활성화
    
    def on_ai_error(self, msg):
        """AI 오류 처리"""
        error_time = ""
        if self.request_start_time:
            elapsed = datetime.now() - self.request_start_time
            error_time = f" (오류발생시간: {elapsed.total_seconds():.1f}초)"
        
        # 토큰 사용량 정보 추가 (오류 시에도 표시)
        token_info = ""
        current_status = status_display.current_status
        if current_status.get('total_tokens', 0) > 0:
            total_tokens = current_status['total_tokens']
            input_tokens = current_status.get('input_tokens', 0)
            output_tokens = current_status.get('output_tokens', 0)
            if input_tokens > 0 and output_tokens > 0:
                token_info = f" | 📊 {total_tokens:,}토큰 (IN:{input_tokens:,} OUT:{output_tokens:,})"
            else:
                token_info = f" | 📊 {total_tokens:,}토큰"
        
        current_model = load_last_model()
        enhanced_msg = f"{msg}{error_time}\n\n---\n*🤖 {current_model}{token_info}*\n⚠️ *AI 답변은 부정확할 수 있습니다. 중요한 정보는 반드시 검증하세요.*" if token_info else f"{msg}{error_time}"
        
        self.chat_display.append_message('시스템', enhanced_msg)
        
        # 오류 메시지 후 맨 하단으로 스크롤
        safe_single_shot(300, self._scroll_to_bottom, self)
        
        self.ui_manager.set_ui_enabled(True)
        self.ui_manager.show_loading(False)
    
    def _get_tool_emoji_list(self, used_tools):
        """사용된 도구 이모티콘 목록"""
        if not used_tools:
            return []
        
        emoji_map = {
            'search': '🔍', 'web': '🌐', 'url': '🌐', 'fetch': '📄',
            'database': '🗄️', 'mysql': '🗄️', 'sql': '🗄️',
            'travel': '✈️', 'tour': '✈️', 'hotel': '🏨', 'flight': '✈️',
            'map': '🗺️', 'location': '📍', 'geocode': '📍',
            'weather': '🌤️', 'email': '📧', 'file': '📁',
            'excel': '📊', 'chart': '📈', 'image': '🖼️',
            'translate': '🌐', 'api': '🔧'
        }
        
        result = []
        for tool in used_tools:
            tool_name = str(tool).lower()
            emoji = "⚡"
            
            for keyword, e in emoji_map.items():
                if keyword in tool_name:
                    emoji = e
                    break
            
            display_name = str(tool)
            if '.' in display_name:
                display_name = display_name.split('.')[-1]
            
            result.append((emoji, display_name))
        
        return result[:5]
    
    def _on_webview_loaded(self, ok):
        """웹뷰 로드 완료"""
        if ok:
            safe_single_shot(500, self._load_previous_conversations, self)
        else:
            # 웹뷰 로드 실패 시에도 웰컴 메시지 표시
            safe_single_shot(1000, self._show_welcome_message, self)
    
    # 상태 표시 업데이트 삭제 - 좌측 패널로 이동
    
    def _load_previous_conversations(self):
        """이전 대화 로드"""
        try:
            self._welcome_shown = True  # 웰컴 메시지 표시됨 플래그
            self.conversation_history.load_from_file()
            all_messages = self.conversation_history.current_session
            
            if all_messages:
                # 페이징 설정에 따라 초기 로드 개수 결정
                display_messages = all_messages[-self.initial_load_count:] if len(all_messages) > self.initial_load_count else all_messages
                
                unique_contents = set()
                unique_messages = []
                
                for msg in display_messages:
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    
                    if not content or not content.strip():
                        continue
                    
                    content_key = f"{role}:{content[:50]}"
                    if content_key not in unique_contents:
                        unique_contents.add(content_key)
                        unique_messages.append(msg)
                
                if unique_messages:
                    for msg in unique_messages:
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        model = msg.get('model', '')
                        
                        if role == 'user':
                            self.chat_display.append_message('사용자', content, message_id=msg.get('id'))
                        elif role == 'assistant':
                            # 토큰 정보 추출 - 실시간과 동일한 형식
                            token_info = ""
                            input_tokens = msg.get('input_tokens', 0)
                            output_tokens = msg.get('output_tokens', 0)
                            total_tokens = msg.get('total_tokens', 0)
                            
                            # 실시간과 동일한 형식: 전체(인/아웃)
                            if input_tokens > 0 and output_tokens > 0 and total_tokens > 0:
                                token_info = f" | 📊 {total_tokens:,}토큰 (IN:{input_tokens:,} OUT:{output_tokens:,})"
                            elif total_tokens > 0:
                                token_info = f" | 📊 {total_tokens:,}토큰"
                            elif msg.get('token_count', 0) > 0:
                                token_info = f" | 📊 {msg['token_count']:,}토큰"
                            
                            # 테마 색상 가져오기
                            colors = theme_manager.material_manager.get_theme_colors() if theme_manager.use_material_theme else {}
                            is_light = not theme_manager.material_manager.is_dark_theme() if theme_manager.use_material_theme else False
                            text_dim = colors.get('text_secondary', '#666666' if is_light else '#a0a0a0')
                            
                            # 모델 정보가 있으면 표시하고 센더 정보로 모델명 전달
                            if model and model != 'unknown':
                                enhanced_content = f"{content}\n\n<div class='ai-footer'>\n<div class='ai-info' style='color: {text_dim};'>🤖 {model}{token_info}</div>\n</div>"
                                # 모델명을 original_sender로 전달하여 포맷팅에 활용
                                self.chat_display.append_message('AI', enhanced_content, original_sender=model, message_id=msg.get('id'))
                            else:
                                enhanced_content = f"{content}\n\n<div class='ai-footer'>\n<div class='ai-info' style='color: {text_dim};'>🤖 AI{token_info}</div>\n</div>" if token_info else content
                                self.chat_display.append_message('AI', enhanced_content, message_id=msg.get('id'))
                    
                    # 이전 대화 로드 후 웰컴 메시지 표시
                    stats = self.conversation_history.get_stats()
                    total_tokens = stats.get('total_tokens', 0)
                    model_stats = stats.get('model_stats', {})
                    
                    token_summary = f"📊 전체 토큰: {total_tokens:,}개"
                    if model_stats:
                        model_breakdown = []
                        for model, data in model_stats.items():
                            if model != 'unknown':
                                model_breakdown.append(f"{model}: {data['tokens']:,}")
                        if model_breakdown:
                            token_summary += f" ({', '.join(model_breakdown)})"
                    
                    welcome_msg = self._generate_welcome_message(len(unique_messages), token_summary)
                    self.chat_display.append_message('시스템', welcome_msg)
                else:
                    # 빈 히스토리일 때도 토큰 통계 표시
                    stats = self.conversation_history.get_stats()
                    total_tokens = stats.get('total_tokens', 0)
                    welcome_msg = self._generate_welcome_message(0, f"📊 전체 토큰: {total_tokens:,}개" if total_tokens > 0 else None)
                    self.chat_display.append_message('시스템', welcome_msg)
            else:
                # 빈 히스토리일 때도 토큰 통계 표시
                stats = self.conversation_history.get_stats()
                total_tokens = stats.get('total_tokens', 0)
                welcome_msg = self._generate_welcome_message(0, f"📊 누적 토큰: {total_tokens:,}개" if total_tokens > 0 else None)
                self.chat_display.append_message('시스템', welcome_msg)
                
        except Exception as e:
            logger.debug(f"대화 기록 로드 오류: {e}")
            # 오류 시에도 토큰 통계 표시 시도
            try:
                stats = self.conversation_history.get_stats()
                total_tokens = stats.get('total_tokens', 0)
                welcome_msg = self._generate_welcome_message(0, f"📊 전체 토큰: {total_tokens:,}개" if total_tokens > 0 else None)
                self.chat_display.append_message('시스템', welcome_msg)
            except:
                welcome_msg = self._generate_welcome_message(0, None)
                self.chat_display.append_message('시스템', welcome_msg)
    
    def _show_welcome_message(self):
        """웰컴 메시지 표시"""
        try:
            stats = self.conversation_history.get_stats()
            total_tokens = stats.get('total_tokens', 0)
            welcome_msg = self._generate_welcome_message(0, f"📊 누적 토큰: {total_tokens:,}개" if total_tokens > 0 else None)
            self.chat_display.append_message('시스템', welcome_msg)
        except Exception as e:
            logger.debug(f"웰컴 메시지 표시 오류: {e}")
            welcome_msg = self._generate_welcome_message(0, None)
            self.chat_display.append_message('시스템', welcome_msg)
    
    def _ensure_welcome_message(self):
        """웰컴 메시지 보장 (웹뷰 로드 시간 초과 시 대비책)"""
        try:
            if not hasattr(self, '_welcome_shown'):
                self._welcome_shown = True
                self._show_welcome_message()
        except Exception as e:
            logger.debug(f"웰컴 메시지 보장 오류: {e}")
    
    def _generate_welcome_message(self, message_count=0, token_info=None):
        """테마 색상이 적용된 환영 메시지 생성"""
        try:
            # 테마 색상 가져오기
            colors = theme_manager.material_manager.get_theme_colors() if theme_manager.use_material_theme else {}
            primary_color = colors.get('primary', '#bb86fc')
            is_light = not theme_manager.material_manager.is_dark_theme() if theme_manager.use_material_theme else False
            text_color = colors.get('on_surface', colors.get('text_primary', '#1a1a1a' if is_light else '#ffffff'))
            
            # 기본 환영 메시지
            welcome_parts = [
                f'<div style="color: {primary_color}; font-weight: bold; font-size: 1.2em;">🚀 Chat AI Agent에 오신 것을 환영합니다! 🤖</div>',
                '',
                f'<span style="color: {text_color};">✨ 저는 다양한 도구를 활용해 여러분을 도와드리는 AI 어시스턴트입니다</span>',
                ''
            ]
            
            # 이전 대화 정보 추가
            if message_count > 0:
                welcome_parts.append(f'🔄 **이전 대화**: {message_count}개 메시지 로드됨')
            
            # 토큰 정보 추가
            if token_info:
                welcome_parts.append(token_info)
            
            if message_count > 0 or token_info:
                welcome_parts.append('')
            
            # 기능 안내
            welcome_parts.extend([
                f'<div style="color: {primary_color}; font-weight: bold;">🎯 사용 가능한 기능:</div>',
                f'<span style="color: {text_color};">• 💬 **Ask 모드**: 일반 대화 및 질문</span>',
                f'<span style="color: {text_color};">• 🔧 **Agent 모드**: 외부 도구 활용 (검색, 데이터베이스, API 등)</span>',
                f'<span style="color: {text_color};">• 📎 **파일 업로드**: 문서, 이미지, 데이터 분석</span>',
                '',
                f'<span style="color: {text_color};">⚠️ **주의사항**: AI 답변은 부정확할 수 있습니다. 중요한 정보는 반드시 검증하세요.</span>',
                '',
                f'<span style="color: {text_color};">💡 **팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다!</span>'
            ])
            
            return '\n'.join(welcome_parts)
            
        except Exception as e:
            logger.debug(f"환영 메시지 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            # 오류 시 기본 메시지 반환
            return '🚀 **Chat AI Agent에 오신 것을 환영합니다!** 🤖\n\n✨ 저는 다양한 도구를 활용해 여러분을 도와드리는 AI 어시스턴트입니다'
    
    def clear_conversation_history(self):
        """대화 히스토리 초기화"""
        if hasattr(self.conversation_history, 'clear_session'):
            self.conversation_history.clear_session()
        else:
            self.conversation_history.current_session = []
        # self.conversation_history.save_to_file()  # JSON 저장 비활성화
        self.messages = []
        
        # 세션 통계도 초기화
        status_display.reset_session_stats()
        
        # 토큰 누적기 초기화
        token_accumulator.reset()
        logger.debug(f"[ChatWidget] 대화 히스토리 초기화 - 토큰 누적기도 초기화")
        
        # 토큰 트래커도 초기화
        from core.token_tracker import token_tracker
        if hasattr(token_tracker, 'current_conversation'):
            token_tracker.current_conversation = None
        if hasattr(token_tracker, 'conversation_history'):
            token_tracker.conversation_history.clear()
        
        # 메인 윈도우의 현재 세션 ID도 초기화
        main_window = self._find_main_window()
        if main_window and hasattr(main_window, 'current_session_id'):
            main_window.current_session_id = None
            main_window._auto_session_created = False
        
        logger.debug("대화 히스토리가 초기화되었습니다.")
        
        self.chat_display.clear_messages()
    
    def close(self):
        """위젯 종료"""
        self._is_closing = True
        
        try:
            if hasattr(self, 'ai_processor'):
                self.ai_processor.cancel()
            
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
    
    def delete_message(self, message_id: str) -> bool:
        """메시지 삭제 - 개선된 세션 ID 찾기"""
        try:
            logger.debug(f"[CHAT_DELETE] 삭제 시작: {message_id}")
            
            # 메시지 ID를 정수로 변환
            try:
                db_message_id = int(message_id)
                logger.debug(f"[CHAT_DELETE] DB 메시지 ID: {db_message_id}")
            except ValueError:
                logger.debug(f"[CHAT_DELETE] 잘못된 메시지 ID 형식: {message_id}")
                return False
            
            # 1순위: 메시지 ID로부터 직접 세션 찾기 (가장 안정적)
            from core.session.message_manager import message_manager
            session_id = message_manager.find_session_by_message_id(db_message_id)
            logger.debug(f"[CHAT_DELETE] 메시지로부터 세션 ID 찾음: {session_id}")
            
            # 2순위: 메인 윈도우에서 세션 ID 가져오기
            if not session_id:
                main_window = self._find_main_window()
                if main_window and hasattr(main_window, 'current_session_id') and main_window.current_session_id:
                    session_id = main_window.current_session_id
                    logger.debug(f"[CHAT_DELETE] 메인 윈도우에서 세션 ID 가져옴: {session_id}")
            
            # 3순위: 채팅 위젯의 세션 ID
            if not session_id and hasattr(self, 'current_session_id') and self.current_session_id:
                session_id = self.current_session_id
                logger.debug(f"[CHAT_DELETE] 채팅 위젯에서 세션 ID 가져옴: {session_id}")
            
            if not session_id:
                logger.debug(f"[CHAT_DELETE] 세션 ID를 찾을 수 없음")
                return False
            
            logger.debug(f"[CHAT_DELETE] 사용할 세션 ID: {session_id}")
            
            # DB에서 삭제 실행
            success = message_manager.delete_message(session_id, db_message_id)
            logger.debug(f"[CHAT_DELETE] DB 삭제 결과: {success}")
            
            if success:
                # 메모리에서도 삭제
                try:
                    self.conversation_history.delete_message(message_id)
                    logger.debug(f"[CHAT_DELETE] 메모리 삭제 완료")
                except Exception as e:
                    logger.debug(f"[CHAT_DELETE] 메모리 삭제 오류: {e}")
                
                # 세션 패널 새로고침
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
    
    def update_theme(self):
        """테마 업데이트"""
        try:
            # 기존 스타일시트 완전 제거
            self.setStyleSheet("")
            
            # Qt 스타일시트 업데이트
            if theme_manager.use_material_theme:
                self._apply_material_theme_styles()
            else:
                self.setStyleSheet(FlatTheme.get_chat_widget_style())
                self._update_input_text_style()
                if hasattr(self, 'input_container'):
                    self._update_input_container_style(self.input_container)
            
            # 채팅 표시 영역 실시간 업데이트
            if hasattr(self, 'chat_display'):
                self.chat_display.update_theme()
            
            # 로딩바 테마 업데이트
            if hasattr(self, 'loading_bar') and hasattr(self.loading_bar, 'update_theme'):
                self.loading_bar.update_theme()
            
            # 버튼 스타일도 업데이트
            self._update_button_styles()
            
            # 강제로 전체 위젯 다시 그리기
            self.repaint()
            if hasattr(self, 'input_text'):
                self.input_text.repaint()
            if hasattr(self, 'input_container'):
                self.input_container.repaint()
            
            logger.debug("테마 업데이트 완료")
            
        except Exception as e:
            logger.debug(f"테마 업데이트 오류: {e}")
    
    def _update_button_styles(self):
        """버튼 스타일 업데이트"""
        try:
            themed_button_style = self._get_themed_button_style()
            cancel_button_style = self._get_cancel_button_style()
            
            if hasattr(self, 'send_button'):
                self.send_button.setStyleSheet(themed_button_style)
            if hasattr(self, 'upload_button'):
                self.upload_button.setStyleSheet(themed_button_style)
            if hasattr(self, 'cancel_button'):
                self.cancel_button.setStyleSheet(cancel_button_style)
        except Exception as e:
            logger.debug(f"버튼 스타일 업데이트 오류: {e}")
    
    def _get_cancel_button_style(self):
        """취소 버튼 전용 빨간색 테두리 스타일"""
        try:
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                bg_color = colors.get('surface', '#1e1e1e')
                
                return f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: 1px solid #FF5252;
                    border-radius: 12px;
                    font-size: 20px;
                    font-weight: bold;
                    color: #FF5252;
                    padding: 0px;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                }}
                QPushButton:hover {{
                    background-color: #FF5252;
                    color: {bg_color};
                    border-color: #FF5252;
                    font-size: 22px;
                }}
                QPushButton:pressed {{
                    background-color: #D32F2F;
                    transform: scale(0.95);
                    font-size: 18px;
                }}
                QPushButton:disabled {{
                    background-color: {bg_color};
                    border-color: #666666;
                    color: #666666;
                    opacity: 0.5;
                }}
                """
            else:
                return """
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #FF5252;
                    border-radius: 12px;
                    font-size: 20px;
                    font-weight: bold;
                    color: #FF5252;
                }
                QPushButton:hover {
                    background-color: #FF5252;
                    color: #FFFFFF;
                    font-size: 22px;
                }
                QPushButton:pressed {
                    background-color: #D32F2F;
                    font-size: 18px;
                }
                QPushButton:disabled {
                    opacity: 0.5;
                }
                """
        except Exception as e:
            logger.debug(f"취소 버튼 스타일 생성 오류: {e}")
            return """
            QPushButton {
                background-color: transparent;
                border: 1px solid #FF5252;
                color: #FF5252;
            }
            """
    
    def _apply_material_theme_styles(self):
        """재료 테마 스타일 적용"""
        colors = theme_manager.material_manager.get_theme_colors()
        loading_config = theme_manager.material_manager.get_loading_bar_config()
        
        # 채팅 위젯 전체 스타일 - 강제 적용
        widget_style = f"""
        ChatWidget {{
            background-color: {colors.get('background', '#121212')} !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        }}
        QWidget {{
            background-color: {colors.get('background', '#121212')};
            color: {colors.get('text_primary', '#ffffff')};
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        }}
        QWebEngineView {{
            background-color: {colors.get('background', '#121212')} !important;
        }}
        """
        self.setStyleSheet(widget_style)
        
        # 입력 영역 스타일 업데이트
        self._apply_material_input_styles(colors)
        
        # 로딩바 스타일 업데이트
        if hasattr(self, 'loading_bar'):
            loading_style = f"""
            QProgressBar {{
                border: none;
                background-color: {loading_config.get('background', 'rgba(187, 134, 252, 0.1)')};
                border-radius: 8px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background: {loading_config.get('chunk', 'linear-gradient(90deg, #bb86fc 0%, #03dac6 100%)')};
                border-radius: 6px;
            }}
            """
            self.loading_bar.setStyleSheet(loading_style)
    
    def _apply_material_input_styles(self, colors):
        """재료 테마 입력 영역 스타일 적용 - Soft Shadow + Rounded Edge + Gradient Depth"""
        is_dark = theme_manager.is_material_dark_theme()
        shadow_color = "rgba(0,0,0,0.15)" if is_dark else "rgba(0,0,0,0.08)"
        
        # 입력 컨테이너 스타일 - Gradient Depth + Soft Shadow
        container_style = f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 {colors.get('surface', '#1e1e1e')}, 
                stop:1 {colors.get('background', '#121212')});
            border: 2px solid {colors.get('primary', '#bb86fc')};
            border-radius: 20px;
            transition: all 0.3s ease;
        }}
        QWidget:focus-within {{
            border: 3px solid {colors.get('primary', '#bb86fc')};
            transform: translateY(-2px);
        }}
        """
        
        # 투명한 버튼 스타일 - 호버 시 그라데이션 효과
        transparent_button_style = f"""
        QPushButton {{
            background: transparent;
            border: none;
            font-size: 28px;
            border-radius: 14px;
            transition: all 0.3s ease;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 {colors.get('primary', '#bb86fc')}40, 
                stop:1 {colors.get('primary_variant', '#3700b3')}20);
            font-size: 38px;
            transform: translateY(-1px);
        }}
        QPushButton:pressed {{
            background: {colors.get('primary', '#bb86fc')}60;
            font-size: 26px;
            transform: translateY(0px);
        }}
        QPushButton:disabled {{
            background: transparent;
            opacity: 0.5;
        }}
        """
        
        # 드래그 핸들 스타일 - Rounded Edge + Gradient
        drag_handle_style = f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {colors.get('divider', '#666666')}, 
                stop:1 {colors.get('text_secondary', '#888888')});
            border-radius: 6px;
            margin: 2px 20px;
            transition: all 0.3s ease;
        }}
        QWidget:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {colors.get('text_secondary', '#888888')}, 
                stop:1 {colors.get('primary', '#bb86fc')});
            transform: translateY(-1px);
        }}
        """
        
        # 스타일 적용
        if hasattr(self, 'input_container'):
            self.input_container.setStyleSheet(container_style)
        
        if hasattr(self, 'drag_handle'):
            self.drag_handle.setStyleSheet(drag_handle_style)
        
        # 입력창 스타일 업데이트
        self._update_input_text_style(colors)
        
        # 버튼 스타일 업데이트 - 테마 색상 적용
        themed_button_style = self._get_themed_button_style(colors)
        cancel_button_style = self._get_cancel_button_style()
        
        if hasattr(self, 'send_button'):
            self.send_button.setStyleSheet(themed_button_style)
        if hasattr(self, 'upload_button'):
            self.upload_button.setStyleSheet(themed_button_style)
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setStyleSheet(cancel_button_style)
    
    def _on_conversation_completed(self, _):
        """대화 완료 시 토큰 누적기 종료"""
        try:
            # 대화 종료만 처리 (토큰 박스는 표시하지 않음)
            if token_accumulator.end_conversation():
                input_tokens, output_tokens, total_tokens = token_accumulator.get_total()
                logger.debug(f"[ChatWidget] 대화 완룮 - 토큰: {total_tokens:,}개")
            
        except Exception as e:
            logger.debug(f"대화 완룮 처리 오류: {e}")
    
    def load_session_context(self, session_id: int):
        """세션 컨텍스트 로드 (페이징 지원)"""
        try:
            self.current_session_id = session_id
            
            # 전체 메시지 수 조회
            from core.session.session_manager import session_manager
            self.total_message_count = session_manager.get_message_count(session_id)
            
            # 기존 대화 히스토리 초기화
            if hasattr(self.conversation_history, 'clear_session'):
                self.conversation_history.clear_session()
            else:
                self.conversation_history.current_session = []
            self.messages = []
            
            # 채팅 화면 초기화
            self.chat_display.web_view.page().runJavaScript("document.getElementById('messages').innerHTML = '';")
            
            # 설정에서 초기 로드 개수 가져오기
            initial_limit = min(self.initial_load_count, self.total_message_count)
            
            context_messages = session_manager.get_session_messages(session_id, initial_limit, 0)
            self.loaded_message_count = len(context_messages)
            
            logger.debug(f"[CHAT_WIDGET] Loaded {len(context_messages)} messages")
            for i, msg in enumerate(context_messages):
                logger.debug(f"[CHAT_WIDGET] Message {i+1}: role={msg['role']}, id={msg['id']}, timestamp={msg['timestamp'][:19]}")
            
            # 세션 컨텍스트를 대화 히스토리에 로드
            for msg in context_messages:
                if hasattr(self.conversation_history, 'add_message'):
                    self.conversation_history.add_message(msg['role'], msg['content'])
                self.messages.append(msg)
            
            # 메시지 표시
            safe_single_shot(100, lambda: self._display_session_messages(context_messages), self)
            
            # 세션 로드 완료 메시지
            if context_messages:
                load_msg = f"💼 세션 로드 완료: {len(context_messages)}개 메시지"
                if self.total_message_count > self.initial_load_count:
                    load_msg += f" (최근 {self.initial_load_count}개만 표시, 전체: {self.total_message_count}개)"
                    load_msg += "\n\n🔼 위로 스크롤하면 이전 메시지를 볼 수 있습니다."
                self.chat_display.append_message('시스템', load_msg)
            
            # 맨 하단으로 스크롤 - 더 긴 지연 시간
            safe_single_shot(600, self._scroll_to_bottom, self)
            safe_single_shot(1200, self._scroll_to_bottom, self)
            safe_single_shot(2000, self._scroll_to_bottom, self)  # 최종 확인
            
            # 스크롤 이벤트 리스너 추가
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
                # 기본값 사용
                self.initial_load_count = 20
                self.page_size = 10
                logger.debug(f"[PAGINATION] 기본값 사용: initial_load_count={self.initial_load_count}, page_size={self.page_size}")
                
        except Exception as e:
            logger.debug(f"[PAGINATION] 설정 로드 오류: {e}")
            # 기본값 사용
            self.initial_load_count = 20
            self.page_size = 10
    
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
            # 스크롤이 맨 위에 있고 더 로드할 메시지가 있을 때
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
    
    def _find_main_window(self):
        """메인 윈도우 찾기"""
        widget = self
        while widget:
            if widget.__class__.__name__ == 'MainWindow':
                return widget
            widget = widget.parent()
        return None
    
    def _display_session_messages(self, messages, prepend=False):
        """세션 메시지들을 화면에 표시"""
        try:
            # prepend 시에는 역순으로 처리하여 올바른 순서 보장
            display_messages = list(reversed(messages)) if prepend else messages
            
            for i, msg in enumerate(display_messages):
                logger.debug(f"[LOAD_SESSION] 메시지 {i+1} 표시: role={msg['role']}, content={msg['content'][:30]}...")
                msg_id = str(msg.get('id', f"session_msg_{i}"))
                timestamp = msg.get('timestamp')  # DB에서 저장된 timestamp 가져오기
                if msg['role'] == 'user':
                    self.chat_display.append_message('사용자', msg['content'], message_id=msg_id, prepend=prepend, timestamp=timestamp)
                elif msg['role'] == 'assistant':
                    self.chat_display.append_message('AI', msg['content'], message_id=msg_id, prepend=prepend, timestamp=timestamp)
            
            logger.debug(f"[LOAD_SESSION] 세션 메시지 표시 완료: {len(messages)}개")
            
            # prepend가 아닌 경우(일반 로드)에만 하단 스크롤
            if not prepend:
                safe_single_shot(1000, self._scroll_to_bottom, self)
                
        except Exception as e:
            logger.debug(f"[LOAD_SESSION] 메시지 표시 오류: {e}")
    
    def _scroll_to_bottom(self):
        """채팅 화면을 맨 하단으로 스크롤"""
        try:
            self.chat_display_view.page().runJavaScript(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
        except Exception as e:
            pass

    def _update_input_text_style(self, colors=None):
        """입력창 스타일 동적 업데이트"""
        try:
            if theme_manager.use_material_theme and colors:
                # True Gray 테마 특별 처리
                if colors.get('primary') == '#6B7280':  # True Gray 테마 감지
                    input_text_style = f"""
                    QTextEdit {{
                        background-color: #FFFFFF;
                        color: #374151;
                        border: 1px solid {colors.get('divider', '#E5E7EB')};
                        border-radius: 12px;
                        font-size: 15px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        padding: 8px;
                        selection-background-color: {colors.get('primary', '#6B7280')};
                        selection-color: #FFFFFF;
                    }}
                    QTextEdit:focus {{
                        border-color: {colors.get('primary', '#6B7280')};
                        border-width: 2px;
                    }}
                    """
                else:
                    input_text_style = f"""
                    QTextEdit {{
                        background-color: {colors.get('surface', '#1e1e1e')};
                        color: {colors.get('text_primary', '#ffffff')};
                        border: 1px solid {colors.get('divider', '#333333')};
                        border-radius: 12px;
                        font-size: 15px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        padding: 8px;
                        selection-background-color: {colors.get('primary', '#bb86fc')};
                    }}
                    QTextEdit:focus {{
                        border-color: {colors.get('primary', '#bb86fc')};
                    }}
                    """
            elif theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                # True Gray 테마 특별 처리
                if colors.get('primary') == '#6B7280':  # True Gray 테마 감지
                    input_text_style = f"""
                    QTextEdit {{
                        background-color: #FFFFFF;
                        color: #374151;
                        border: 1px solid {colors.get('divider', '#E5E7EB')};
                        border-radius: 12px;
                        font-size: 15px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        padding: 8px;
                        selection-background-color: {colors.get('primary', '#6B7280')};
                        selection-color: #FFFFFF;
                    }}
                    QTextEdit:focus {{
                        border-color: {colors.get('primary', '#6B7280')};
                        border-width: 2px;
                    }}
                    """
                else:
                    input_text_style = f"""
                    QTextEdit {{
                        background-color: {colors.get('surface', '#1e1e1e')};
                        color: {colors.get('text_primary', '#ffffff')};
                        border: 1px solid {colors.get('divider', '#333333')};
                        border-radius: 12px;
                        font-size: 15px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        padding: 8px;
                        selection-background-color: {colors.get('primary', '#bb86fc')};
                    }}
                    QTextEdit:focus {{
                        border-color: {colors.get('primary', '#bb86fc')};
                    }}
                    """
            else:
                input_text_style = FlatTheme.get_input_area_style()['input_text']
            
            self.input_text.setStyleSheet("")
            self.input_text.setStyleSheet(input_text_style)
            
        except Exception as e:
            logger.debug(f"입력창 스타일 업데이트 오류: {e}")
            self.input_text.setStyleSheet(FlatTheme.get_input_area_style()['input_text'])
    
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
    
    def _update_input_container_style(self, container):
        """입력 컴테이너 스타일 동적 업데이트"""
        try:
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                style = f"""
                QWidget {{
                    background-color: {colors.get('surface', '#1e1e1e')};
                    border: 2px solid {colors.get('primary', '#bb86fc')};
                    border-radius: 16px;
                }}
                """
            else:
                style = FlatTheme.get_input_area_style()['container']
            
            container.setStyleSheet(style)
            
        except Exception as e:
            logger.debug(f"입력 컴테이너 스타일 업데이트 오류: {e}")
            container.setStyleSheet(FlatTheme.get_input_area_style()['container'])
    
    def _apply_initial_theme(self):
        """초기 테마 적용"""
        try:
            if theme_manager.use_material_theme:
                self._apply_material_theme_styles()
            else:
                self.setStyleSheet(FlatTheme.get_chat_widget_style())
            logger.debug("초기 테마 적용 완료")
        except Exception as e:
            logger.debug(f"초기 테마 적용 오류: {e}")
    
    def _apply_theme_if_needed(self):
        """필요시 테마 적용"""
        try:
            if theme_manager.use_material_theme:
                self._apply_material_theme_styles()
                if hasattr(self, 'chat_display'):
                    self.chat_display.update_theme()
        except Exception as e:
            logger.debug(f"테마 적용 오류: {e}")
    
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
    
    def _get_themed_button_style(self, colors=None):
        """테마 색상을 적용한 버튼 스타일 생성 - 뉴스 재조회 버튼과 동일한 스타일"""
        try:
            if theme_manager.use_material_theme:
                if not colors:
                    colors = theme_manager.material_manager.get_theme_colors()
                
                bg_color = colors.get('surface', '#1e1e1e')
                primary_color = colors.get('primary', '#bb86fc')
                primary_variant = colors.get('primary_variant', '#3700b3')
                
                # 뉴스 재조회 버튼과 동일한 테두리 스타일
                return f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: 1px solid {primary_color};
                    border-radius: 12px;
                    font-size: 20px;
                    font-weight: bold;
                    color: {primary_color};
                    padding: 0px;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                }}
                QPushButton:hover {{
                    background-color: {primary_color};
                    color: {bg_color};
                    border-color: {primary_color};
                    font-size: 22px;
                }}
                QPushButton:pressed {{
                    background-color: {primary_variant};
                    transform: scale(0.95);
                    font-size: 18px;
                }}
                QPushButton:disabled {{
                    background-color: {bg_color};
                    border-color: #666666;
                    color: #666666;
                    opacity: 0.5;
                }}
                """
            else:
                # Flat 테마 기본 스타일
                return """
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #666666;
                    border-radius: 12px;
                    font-size: 20px;
                    color: #666666;
                }
                QPushButton:hover {
                    background-color: #666666;
                    color: #FFFFFF;
                    font-size: 22px;
                }
                QPushButton:pressed {
                    background-color: #444444;
                    font-size: 18px;
                }
                QPushButton:disabled {
                    opacity: 0.5;
                }
                """
        except Exception as e:
            logger.debug(f"버튼 스타일 생성 오류: {e}")
            return """
            QPushButton {
                background: transparent;
                border: none;
                font-size: 20px;
            }
            QPushButton:hover {
                background: transparent;
                font-size: 22px;
            }
            QPushButton:pressed {
                background: transparent;
                font-size: 18px;
            }
            QPushButton:disabled {
                background: transparent;
            }
            """
    
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
            
            # 설정에서 페이지 크기 사용
            remaining_messages = self.total_message_count - self.loaded_message_count
            load_count = min(self.page_size, remaining_messages)
            # 이미 로드된 메시지 바로 다음부터 로드 (최신부터 역순이므로)
            offset = self.loaded_message_count
            
            logger.debug(f"[LOAD_MORE] 로드 시도: offset={offset}, limit={load_count}, 로드됨={self.loaded_message_count}, 전체={self.total_message_count}")
            
            older_messages = session_manager.get_session_messages(
                self.current_session_id, load_count, offset
            )
            
            if older_messages:
                # 이전 메시지들을 대화 히스토리에 추가
                for msg in older_messages:
                    if hasattr(self.conversation_history, 'add_message'):
                        self.conversation_history.add_message(msg['role'], msg['content'])
                    self.messages.insert(0, msg)
                
                # 화면 상단에 메시지 추가
                self._display_session_messages(older_messages, prepend=True)
                self.loaded_message_count += len(older_messages)
                
                logger.debug(f"[LOAD_MORE] {len(older_messages)}개 메시지 추가 로드 (전체: {self.loaded_message_count}/{self.total_message_count})")
                
                # 로드 완료 메시지
                if self.loaded_message_count < self.total_message_count:
                    load_msg = f"🔼 {len(older_messages)}개 이전 메시지 로드 완료. 더 보려면 위로 스크롤하세요."
                else:
                    load_msg = f"🎉 모든 메시지를 로드했습니다! (전체 {self.total_message_count}개)"
                
                self.chat_display.append_message('시스템', load_msg, prepend=True)
            
        except Exception as e:
            logger.debug(f"[LOAD_MORE] 오류: {e}")
        finally:
            self.is_loading_more = False