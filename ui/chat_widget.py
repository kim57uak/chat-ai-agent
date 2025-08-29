from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QHBoxLayout, QFileDialog, QCheckBox, QLabel, QProgressBar, 
                             QTextBrowser, QPlainTextEdit, QComboBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

from core.file_utils import load_config, load_model_api_key, load_last_model
from core.conversation_history import ConversationHistory
from core.message_validator import MessageValidator

# 리팩토링된 컴포넌트들
from ui.components.ai_processor import AIProcessor
from ui.components.file_handler import FileHandler
from ui.components.chat_display import ChatDisplay
from ui.components.ui_manager import UIManager
from ui.components.model_manager import ModelManager
from ui.components.status_display import status_display
from ui.styles.flat_theme import FlatTheme

from datetime import datetime
import os


class ChatWidget(QWidget):
    """메인 채팅 위젯 - 컴포넌트들을 조합하여 사용 (Composition over Inheritance)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(FlatTheme.get_chat_widget_style())
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(16)
        
        # 대화 히스토리 관리
        self.conversation_history = ConversationHistory()
        self.conversation_history.load_from_file()
        
        # 업로드된 파일 정보
        self.uploaded_file_content = None
        self.uploaded_file_name = None
        self.messages = []
        self.request_start_time = None
        
        self._setup_ui()
        self._setup_components()
        self._setup_connections()
        self._load_previous_conversations()
    
    def _setup_ui(self):
        """UI 구성"""
        # 상단 정보 영역
        info_layout = QHBoxLayout()
        
        self.model_label = QLabel(self)
        self.tools_label = QLabel(self)
        self.status_label = QLabel(self)
        
        # 새로운 플랫 스타일 적용
        styles = FlatTheme.get_info_labels_style()
        self.model_label.setStyleSheet(styles['model_label'])
        self.tools_label.setStyleSheet(styles['tools_label'])
        self.status_label.setStyleSheet(styles['status_label'])
        
        info_layout.addWidget(self.model_label, 1)
        info_layout.addWidget(self.status_label, 0)
        info_layout.addWidget(self.tools_label, 0)
        self.layout.addLayout(info_layout)
        
        # 채팅 표시 영역
        self.chat_display_view = QWebEngineView(self)
        self.chat_display_view.setMinimumHeight(400)
        self.layout.addWidget(self.chat_display_view, 1)
        
        # 로딩 바
        self.loading_bar = QProgressBar(self)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setFixedHeight(3)
        self.loading_bar.hide()
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setStyleSheet(FlatTheme.get_loading_bar_style())
        self.layout.addWidget(self.loading_bar)
        
        # 입력 영역
        self._setup_input_area()
    
    def _setup_input_area(self):
        """입력 영역 설정"""
        input_layout = QHBoxLayout()
        
        # 입력 컨테이너
        input_container = QWidget(self)
        input_container_layout = QHBoxLayout(input_container)
        input_container_layout.setContentsMargins(0, 0, 0, 0)
        input_container_layout.setSpacing(0)
        
        # 모드 토글 버튼
        self.mode_toggle = QPushButton("💬 Ask", self)
        self.mode_toggle.setCheckable(True)
        self.mode_toggle.setChecked(False)
        self.mode_toggle.setStyleSheet(FlatTheme.get_input_area_style()['mode_toggle'])
        
        # 입력창
        self.input_text = QTextEdit(self)
        self.input_text.setMaximumHeight(80)
        self.input_text.setPlaceholderText("메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)")
        self.input_text.setStyleSheet(FlatTheme.get_input_area_style()['input_text'])
        
        # 컨테이너 스타일
        input_container.setStyleSheet(FlatTheme.get_input_area_style()['container'])
        
        input_container_layout.addWidget(self.mode_toggle, 0)
        input_container_layout.addWidget(self.input_text, 1)
        
        # 버튼들
        self.send_button = QPushButton('전송', self)
        self.send_button.setMinimumHeight(80)
        self.send_button.setStyleSheet(FlatTheme.get_input_area_style()['send_button'])
        
        self.cancel_button = QPushButton('취소', self)
        self.cancel_button.setMinimumHeight(80)
        self.cancel_button.setVisible(False)
        self.cancel_button.setStyleSheet(FlatTheme.get_input_area_style()['cancel_button'])
        
        self.upload_button = QPushButton('파일\n업로드', self)
        self.upload_button.setMinimumHeight(80)
        self.upload_button.setStyleSheet(FlatTheme.get_input_area_style()['upload_button'])
        
        input_layout.addWidget(input_container, 5)
        input_layout.addWidget(self.send_button, 1)
        input_layout.addWidget(self.cancel_button, 1)
        input_layout.addWidget(self.upload_button, 1)
        
        self.layout.addLayout(input_layout, 0)
    
    def _setup_components(self):
        """컴포넌트 초기화"""
        # AI 프로세서
        self.ai_processor = AIProcessor(self)
        
        # 채팅 표시
        self.chat_display = ChatDisplay(self.chat_display_view)
        
        # UI 매니저
        self.ui_manager = UIManager(
            self.send_button, 
            self.cancel_button, 
            self.upload_button, 
            self.loading_bar
        )
        
        # 모델 매니저
        self.model_manager = ModelManager(self.model_label, self.tools_label)
    
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
        
        # 상태 표시 연결
        status_display.status_updated.connect(self.update_status_display)
        
        # 모델/도구 라벨 클릭 연결
        self.model_label.mousePressEvent = self.model_manager.show_model_popup
        self.tools_label.mousePressEvent = self.model_manager.show_tools_popup
        
        # 키보드 단축키
        self.input_text.keyPressEvent = self.handle_input_key_press
        send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.input_text)
        send_shortcut.activated.connect(self.send_message)
        
        # 웹뷰 로드 완료
        self.chat_display_view.loadFinished.connect(self._on_webview_loaded)
        
        # 웹뷰 로드 시간 초과 시 대비책
        QTimer.singleShot(2000, self._ensure_welcome_message)
    
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
        QTimer.singleShot(0, self._update_toggle_ui)
    
    def _update_toggle_ui(self):
        """토글 UI 업데이트"""
        try:
            is_agent_mode = self.mode_toggle.isChecked()
            if is_agent_mode:
                self.mode_toggle.setText("🔧 Agent")
                self.input_text.setPlaceholderText("도구를 사용한 메시지 입력... (Enter로 전송, Shift+Enter로 줄바꿈)")
            else:
                self.mode_toggle.setText("💬 Ask")
                self.input_text.setPlaceholderText("메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)")
        except Exception as e:
            print(f"토글 UI 업데이트 오류: {e}")
    
    def send_message(self):
        """메시지 전송"""
        user_text = self.input_text.toPlainText().strip()
        if not user_text:
            return
        
        # 이전 요청 취소
        self.ai_processor.cancel()
        self.ai_processor = AIProcessor(self)
        self.ai_processor.finished.connect(self.on_ai_response)
        self.ai_processor.error.connect(self.on_ai_error)
        self.ai_processor.streaming.connect(self.on_ai_streaming)
        
        self._process_new_message(user_text)
    
    def _process_new_message(self, user_text):
        """새 메시지 처리"""
        self.request_start_time = datetime.now()
        
        self.chat_display.append_message('사용자', user_text)
        self.input_text.clear()
        
        # 사용자 메시지를 히스토리에 즉시 추가 (하이브리드 방식에서는 즉시 추가)
        self.conversation_history.add_message('user', user_text)
        self.messages.append({'role': 'user', 'content': user_text})
        
        model = load_last_model()
        api_key = load_model_api_key(model)
        self.model_manager.update_model_label()
        
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
        
        QTimer.singleShot(0, lambda: self._prepare_and_send_request(api_key, model, user_text, file_prompt))
    
    def _prepare_and_send_request(self, api_key, model, user_text, file_prompt=None):
        """요청 준비 및 전송 - 모든 모델에 하이브리드 히스토리 사용"""
        try:
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
            
            print(f"하이브리드 히스토리 로드됨: {len(validated_history)}개 메시지 (모델: {model})")
            
            try:
                is_agent_mode = self.mode_toggle.isChecked()
                use_agent = is_agent_mode
            except Exception as e:
                print(f"모드 확인 오류: {e}")
                use_agent = False
            
            self.ai_processor.process_request(
                api_key, model, validated_history, user_text,
                agent_mode=use_agent, file_prompt=file_prompt
            )
        except Exception as e:
            print(f"AI 요청 준비 오류: {e}")
            QTimer.singleShot(0, lambda: self.on_ai_error(f"요청 준비 중 오류: {e}"))
    
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
            self.input_text.setPlaceholderText(f"{filename}에 대해 무엇을 알고 싶으신가요? (Enter로 전송)")
            
        except Exception as e:
            self.chat_display.append_message('시스템', f'파일 처리 오류: {e}')
            self.uploaded_file_content = None
            self.uploaded_file_name = None
            self.input_text.setPlaceholderText("메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)")
    
    def cancel_request(self):
        """요청 취소"""
        print("취소 요청 시작")
        
        self.ui_manager.set_ui_enabled(True)
        self.ui_manager.show_loading(False)
        
        if hasattr(self, 'ai_processor'):
            self.ai_processor.cancel()
        
        # 점진적 출력도 취소
        self.chat_display.cancel_progressive_display()
        
        self.chat_display.append_message('시스템', '요청을 취소했습니다.')
        print("취소 요청 완료")
    
    def on_ai_response(self, sender, text, used_tools):
        """AI 응답 처리"""
        print(f"AI 응답 받음 - 길이: {len(text)}자")
        
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
        
        # 토큰 사용량 정보 추가
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
        
        enhanced_text = f"{text}{tools_info}\n\n---\n*🤖 {current_model}{response_time}{token_info}*"
        
        # 표시용 sender 결정
        display_sender = '에이전트' if '에이전트' in sender else 'AI'
        
        self.chat_display.append_message(display_sender, enhanced_text, original_sender=sender, progressive=True)
        
        # AI 응답을 히스토리에 추가 - 토큰 정보 포함
        input_tokens = current_status.get('input_tokens', 0)
        output_tokens = current_status.get('output_tokens', 0)
        total_tokens = current_status.get('total_tokens', 0)
        
        self.conversation_history.add_message(
            'assistant', text, current_model, 
            input_tokens=input_tokens if input_tokens > 0 else None,
            output_tokens=output_tokens if output_tokens > 0 else None,
            total_tokens=total_tokens if total_tokens > 0 else None
        )
        self.conversation_history.save_to_file()
        self.messages.append({'role': 'assistant', 'content': text})
        
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
        enhanced_msg = f"{msg}{error_time}\n\n---\n*🤖 {current_model}{token_info}*" if token_info else f"{msg}{error_time}"
        
        self.chat_display.append_message('시스템', enhanced_msg)
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
            QTimer.singleShot(500, self._load_previous_conversations)
        else:
            # 웹뷰 로드 실패 시에도 웰컴 메시지 표시
            QTimer.singleShot(1000, self._show_welcome_message)
    
    def update_status_display(self, status_data):
        """상태 표시 업데이트"""
        try:
            html_status = status_display.get_status_html()
            self.status_label.setText(html_status)
        except Exception as e:
            print(f"상태 표시 업데이트 오류: {e}")
    
    def _load_previous_conversations(self):
        """이전 대화 로드"""
        try:
            self._welcome_shown = True  # 웰컴 메시지 표시됨 플래그
            self.conversation_history.load_from_file()
            all_messages = self.conversation_history.current_session
            
            if all_messages:
                display_messages = all_messages[-20:] if len(all_messages) > 20 else all_messages
                
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
                            self.chat_display.append_message('사용자', content)
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
                            
                            # 모델 정보가 있으면 표시하고 센더 정보로 모델명 전달
                            if model and model != 'unknown':
                                enhanced_content = f"{content}\n\n---\n*🤖 {model}{token_info}*"
                                # 모델명을 original_sender로 전달하여 포맷팅에 활용
                                self.chat_display.append_message('AI', enhanced_content, original_sender=model)
                            else:
                                enhanced_content = f"{content}\n\n---\n*🤖 AI{token_info}*" if token_info else content
                                self.chat_display.append_message('AI', enhanced_content)
                    
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
                    
                    welcome_msg = f'🚀 **Chat AI Agent에 오신 것을 환영합니다!** 🤖\n\n✨ 저는 다양한 도구를 활용해 여러분을 도와드리는 AI 어시스턴트입니다\n\n🔄 **이전 대화**: {len(unique_messages)}개 메시지 로드됨\n{token_summary}\n\n🎯 **사용 가능한 기능**:\n• 💬 **Ask 모드**: 일반 대화 및 질문\n• 🔧 **Agent 모드**: 외부 도구 활용 (검색, 데이터베이스, API 등)\n• 📎 **파일 업로드**: 문서, 이미지, 데이터 분석\n\n💡 **팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다!'
                    self.chat_display.append_message('시스템', welcome_msg)
                else:
                    # 빈 히스토리일 때도 토큰 통계 표시
                    stats = self.conversation_history.get_stats()
                    total_tokens = stats.get('total_tokens', 0)
                    if total_tokens > 0:
                        self.chat_display.append_message('시스템', f'🎉 안녕하세요! 새로운 대화를 시작합니다 😊\n\n📊 전체 토큰: {total_tokens:,}개\n\n💡 **팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다 📋')
                    else:
                        self.chat_display.append_message('시스템', '🎉 안녕하세요! 새로운 대화를 시작합니다 😊\n\n💡 **팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다 📋')
            else:
                # 빈 히스토리일 때도 토큰 통계 표시
                stats = self.conversation_history.get_stats()
                total_tokens = stats.get('total_tokens', 0)
                if total_tokens > 0:
                    self.chat_display.append_message('시스템', f'🚀 **Chat AI Agent에 오신 것을 환영합니다!** 🤖\n\n✨ 저는 다양한 도구를 활용해 여러분을 도와드리는 AI 어시스턴트입니다\n\n📊 **누적 토큰**: {total_tokens:,}개\n\n🎯 **사용 가능한 기능**:\n• 💬 **Ask 모드**: 일반 대화 및 질문\n• 🔧 **Agent 모드**: 외부 도구 활용 (검색, 데이터베이스, API 등)\n• 📎 **파일 업로드**: 문서, 이미지, 데이터 분석\n\n💡 **팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다!')
                else:
                    self.chat_display.append_message('시스템', '🚀 **Chat AI Agent에 오신 것을 환영합니다!** 🤖\n\n✨ 저는 다양한 도구를 활용해 여러분을 도와드리는 AI 어시스턴트입니다\n\n🎯 **사용 가능한 기능**:\n• 💬 **Ask 모드**: 일반 대화 및 질문\n• 🔧 **Agent 모드**: 외부 도구 활용 (검색, 데이터베이스, API 등)\n• 📎 **파일 업로드**: 문서, 이미지, 데이터 분석\n\n💡 **팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다!')
                
        except Exception as e:
            print(f"대화 기록 로드 오류: {e}")
            # 오류 시에도 토큰 통계 표시 시도
            try:
                stats = self.conversation_history.get_stats()
                total_tokens = stats.get('total_tokens', 0)
                if total_tokens > 0:
                    self.chat_display.append_message('시스템', f'새로운 대화를 시작합니다. 📊 전체 토큰: {total_tokens:,}개\n\n**팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다.')
                else:
                    self.chat_display.append_message('시스템', '새로운 대화를 시작합니다. **팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다.')
            except:
                self.chat_display.append_message('시스템', '새로운 대화를 시작합니다. **팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다.')
    
    def _show_welcome_message(self):
        """웰컴 메시지 표시"""
        try:
            stats = self.conversation_history.get_stats()
            total_tokens = stats.get('total_tokens', 0)
            if total_tokens > 0:
                self.chat_display.append_message('시스템', f'🚀 **Chat AI Agent에 오신 것을 환영합니다!** 🤖\n\n✨ 저는 다양한 도구를 활용해 여러분을 도와드리는 AI 어시스턴트입니다\n\n📊 **누적 토큰**: {total_tokens:,}개\n\n🎯 **사용 가능한 기능**:\n• 💬 **Ask 모드**: 일반 대화 및 질문\n• 🔧 **Agent 모드**: 외부 도구 활용 (검색, 데이터베이스, API 등)\n• 📎 **파일 업로드**: 문서, 이미지, 데이터 분석\n\n💡 **팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다!')
            else:
                self.chat_display.append_message('시스템', '🚀 **Chat AI Agent에 오신 것을 환영합니다!** 🤖\n\n✨ 저는 다양한 도구를 활용해 여러분을 도와드리는 AI 어시스턴트입니다\n\n🎯 **사용 가능한 기능**:\n• 💬 **Ask 모드**: 일반 대화 및 질문\n• 🔧 **Agent 모드**: 외부 도구 활용 (검색, 데이터베이스, API 등)\n• 📎 **파일 업로드**: 문서, 이미지, 데이터 분석\n\n💡 **팁**: 메시지에 마우스를 올리면 복사 버튼이 나타납니다!')
        except Exception as e:
            print(f"웰컴 메시지 표시 오류: {e}")
            self.chat_display.append_message('시스템', '🚀 **Chat AI Agent에 오신 것을 환영합니다!** 🤖')
    
    def _ensure_welcome_message(self):
        """웰컴 메시지 보장 (웹뷰 로드 시간 초과 시 대비책)"""
        try:
            if not hasattr(self, '_welcome_shown'):
                self._welcome_shown = True
                self._show_welcome_message()
        except Exception as e:
            print(f"웰컴 메시지 보장 오류: {e}")
    
    def clear_conversation_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history.clear_session()
        self.conversation_history.save_to_file()
        self.messages = []
        
        # 세션 통계도 초기화
        status_display.reset_session_stats()
        
        print("대화 히스토리가 초기화되었습니다.")
        
        self.chat_display.clear_messages()
    
    def close(self):
        """위젯 종료"""
        print("ChatWidget 종료 시작")
        
        try:
            if hasattr(self, 'ai_processor'):
                self.ai_processor.cancel()
            
            if hasattr(self, 'model_manager'):
                self.model_manager.stop_monitoring()
            
            print("ChatWidget 종료 완료")
            
        except Exception as e:
            print(f"ChatWidget 종료 중 오류: {e}")