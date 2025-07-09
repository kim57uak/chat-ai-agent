from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QFileDialog, QCheckBox, QLabel, QProgressBar, QTextBrowser
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from core.file_utils import load_config, load_model_api_key, load_last_model
from core.ai_client import AIClient
from core.conversation_history import ConversationHistory
import os

from PyQt6.QtCore import Qt

# 파일 내용 추출 유틸리티
from PyPDF2 import PdfReader
from docx import Document

# 전역 스레드 관리 - 자동 삭제 방지
_active_threads = []

def cleanup_all_threads():
    """모든 활성 스레드 정리"""
    global _active_threads
    print(f"전역 스레드 정리 시작: {len(_active_threads)}개")
    
    for thread in _active_threads[:]:
        try:
            if thread and thread.isRunning():
                thread.quit()
                if not thread.wait(2000):
                    thread.terminate()
                    thread.wait(1000)
        except:
            pass
    
    _active_threads.clear()
    print("전역 스레드 정리 완료")

class AIWorker(QObject):
    finished = pyqtSignal(str, str)  # sender, text
    error = pyqtSignal(str)
    cancelled = pyqtSignal()
    progress = pyqtSignal(str)  # 진행 상황 알림

    def __init__(self, api_key, model, messages, user_text=None, agent_mode=False, file_prompt=None):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.messages = messages
        self.user_text = user_text
        self.agent_mode = agent_mode
        self.file_prompt = file_prompt
        self._cancelled = False
        self._client = None

    def cancel(self):
        """워커 취소 - 안전한 방식"""
        self._cancelled = True
        # 클라이언트가 있으면 정리
        if self._client:
            try:
                del self._client
            except:
                pass
        self._client = None

    def run(self):
        """워커 실행 - 메인 스레드 안전 처리"""
        try:
            if self._cancelled:
                return
            
            # AI 클라이언트 초기화
            self._client = AIClient(self.api_key, self.model)
            
            if self._cancelled:
                return
            
            # 응답 생성
            response = None
            sender = 'AI'
            
            if self.file_prompt:
                if self._cancelled:
                    return
                    
                if self.agent_mode:
                    response = self._client.agent_chat(self.file_prompt)
                    sender = '에이전트'
                else:
                    response = self._client.chat(self.messages + [{'role': 'user', 'content': self.file_prompt}])
            else:
                if self._cancelled:
                    return
                    
                if self.agent_mode:
                    response = self._client.agent_chat(self.user_text)
                    sender = '에이전트'
                else:
                    response = self._client.chat(self.messages)
            
            # 결과 전송 - 메인 스레드에서 안전하게
            if not self._cancelled and response:
                from PyQt6.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(self, "_emit_finished", Qt.ConnectionType.QueuedConnection,
                                       sender, response)
            elif not self._cancelled:
                QMetaObject.invokeMethod(self, "_emit_error", Qt.ConnectionType.QueuedConnection,
                                       "응답을 생성할 수 없습니다.")
                
        except Exception as e:
            if not self._cancelled:
                error_msg = f'오류 발생: {str(e)}'
                print(f"AIWorker 오류: {error_msg}")
                from PyQt6.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(self, "_emit_error", Qt.ConnectionType.QueuedConnection,
                                       error_msg)
        finally:
            # 정리 작업
            if self._client:
                try:
                    del self._client
                except:
                    pass
            self._client = None
    
    def _emit_finished(self, sender, response):
        """메인 스레드에서 완료 시그널 발송"""
        if not self._cancelled:
            self.finished.emit(sender, response)
    
    def _emit_error(self, error_msg):
        """메인 스레드에서 오류 시그널 발송"""
        if not self._cancelled:
            self.error.emit(error_msg)

class ChatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1a1a1a;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 대화 히스토리 관리
        self.conversation_history = ConversationHistory()
        self.conversation_history.load_from_file()

        # 현재 모델명 표시 라벨
        self.model_label = QLabel(self)
        self.model_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.model_label.setStyleSheet("""
            QLabel {
                color: #4FC3F7;
                font-size: 12px;
                font-weight: bold;
                padding: 10px;
                background-color: #1a1a1a;
            }
        """)
        self.layout.addWidget(self.model_label)
        self.update_model_label()

        # 채팅 표시 영역 (QTextBrowser로 변경하여 HTML 렌더링 개선)
        self.chat_display = QTextBrowser(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setOpenExternalLinks(True)
        
        # 개선된 어두운 테마 스타일
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: #1e1e1e;
                color: #e8e8e8;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 16px;
                font-family: 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                line-height: 1.6;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 10px;
                border: none;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777777;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # 깜박이는 커서 CSS 추가
        self.chat_display.document().setDefaultStyleSheet("""
            @keyframes blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0; }
            }
        """)
        
        self.layout.addWidget(self.chat_display)
        
        # 로딩 표시
        self.loading_bar = QProgressBar(self)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.hide()
        self.loading_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #4FC3F7;
                border-radius: 3px;
            }
        """)
        self.layout.addWidget(self.loading_bar)

        input_layout = QHBoxLayout()
        
        # 입력창을 QTextEdit으로 변경 (3줄 높이)
        self.input_text = QTextEdit(self)
        self.input_text.setMaximumHeight(80)
        self.input_text.setPlaceholderText("메시지를 입력하세요... (Ctrl+Enter로 전송)")
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        
        self.send_button = QPushButton('전송', self)
        self.send_button.setMinimumHeight(80)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4FC3F7;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #29B6F6;
            }
            QPushButton:pressed {
                background-color: #0288D1;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        
        self.cancel_button = QPushButton('취소', self)
        self.cancel_button.setMinimumHeight(80)
        self.cancel_button.setVisible(False)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
        """)
        
        self.upload_button = QPushButton('파일\n업로드', self)
        self.upload_button.setMinimumHeight(80)
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #66BB6A;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        
        self.agent_checkbox = QCheckBox('에이전트\n모드', self)
        self.agent_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #666666;
                border-radius: 3px;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background-color: #FFA726;
                border-color: #FFA726;
            }
        """)
        
        input_layout.addWidget(self.input_text, 4)  # 입력창이 더 넓게
        input_layout.addWidget(self.send_button, 1)
        input_layout.addWidget(self.cancel_button, 1)
        input_layout.addWidget(self.upload_button, 1)
        input_layout.addWidget(self.agent_checkbox, 1)

        self.layout.addLayout(input_layout)

        self.send_button.clicked.connect(self.send_message)
        self.cancel_button.clicked.connect(self.cancel_request)
        self.upload_button.clicked.connect(self.upload_file)
        
        # Ctrl+Enter로 전송
        send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.input_text)
        send_shortcut.activated.connect(self.send_message)

        self.messages = []  # 세션별 대화 내역 (기존 호환성 유지)
        self.thread = None
        self.worker = None
        self.request_start_time = None  # 요청 시작 시간
        
        # 최적화된 타이핑 애니메이션용
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.show_next_line)
        self.typing_chunks = []
        self.current_chunk_index = 0
        self.current_sender = ""
        self.current_message_id = ""
        self.is_typing = False

    def update_model_label(self):
        model = load_last_model()
        self.model_label.setText(f'현재 모델: <b>{model}</b>')

    def send_message(self):
        user_text = self.input_text.toPlainText().strip()
        if not user_text:
            return
        
        # 이전 요청이 진행 중이면 취소
        if self.thread and self.thread.isRunning():
            self.cancel_request()
            # 잠시 대기 후 새 요청 처리
            QTimer.singleShot(500, lambda: self._process_new_message(user_text))
            return
        
        self._process_new_message(user_text)
    
    def _process_new_message(self, user_text):
        """새 메시지 처리"""
        # 요청 시작 시간 기록
        from datetime import datetime
        self.request_start_time = datetime.now()
        
        self.append_chat('사용자', user_text)
        self.input_text.clear()
        
        # 히스토리에 사용자 메시지 추가
        self.conversation_history.add_message('user', user_text)
        self.messages.append({'role': 'user', 'content': user_text})

        model = load_last_model()
        api_key = load_model_api_key(model)
        self.update_model_label()
        if not api_key:
            self.append_chat('시스템', 'API Key가 설정되어 있지 않습니다. 환경설정에서 입력해 주세요.')
            return
        
        self._start_ai_request(api_key, model, user_text)
    
    def _start_ai_request(self, api_key, model, user_text, file_prompt=None):
        """AI 요청 시작 - 전역 스레드 관리"""
        self.set_ui_enabled(False)
        self.show_loading(True)
        
        # 최근 대화 기록 포함하여 전송
        recent_history = self.conversation_history.get_recent_messages(10)
        
        # 새 쓰레드와 워커 생성
        self.thread = QThread()
        self.worker = AIWorker(
            api_key, model, recent_history, user_text, 
            self.agent_checkbox.isChecked(), file_prompt
        )
        self.worker.moveToThread(self.thread)
        
        # 전역 리스트에 추가하여 자동 삭제 방지
        _active_threads.append(self.thread)
        
        # 시그널 연결
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_ai_response)
        self.worker.error.connect(self.on_ai_error)
        self.worker.cancelled.connect(self.on_ai_cancelled)
        self.worker.progress.connect(self.on_ai_progress)
        
        # 정리 시그널 연결
        self.worker.finished.connect(self._cleanup_thread)
        self.worker.error.connect(self._cleanup_thread)
        self.worker.cancelled.connect(self._cleanup_thread)
        
        # 쓰레드 시작
        self.thread.start()
        
        # 타임아웃 설정 (30초)
        QTimer.singleShot(30000, self._check_timeout)
    
    def _cleanup_thread(self):
        """쓰레드 정리 - 전역 리스트에서 제거"""
        # 전역 리스트에서 제거
        if self.thread and self.thread in _active_threads:
            _active_threads.remove(self.thread)
        
        # 참조 제거
        self.worker = None
        self.thread = None
    
    def _check_timeout(self):
        """타임아웃 체크"""
        if self.thread and self.thread.isRunning():
            self.append_chat('시스템', '요청 시간이 초과되었습니다. 다시 시도해주세요.')
            self.cancel_request()
    
    def on_ai_progress(self, message):
        """진행 상황 표시"""
        # 로딩바 텍스트 업데이트 (선택사항)
        pass

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '파일 선택', '', '모든 파일 (*);;텍스트 파일 (*.txt);;PDF 파일 (*.pdf);;Word 파일 (*.docx)')
        if not file_path:
            return
        
        # 이전 요청이 진행 중이면 취소
        if self.thread and self.thread.isRunning():
            self.cancel_request()
            QTimer.singleShot(500, lambda: self._process_file_upload(file_path))
            return
        
        self._process_file_upload(file_path)
    
    def _process_file_upload(self, file_path):
        """파일 업로드 처리"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif ext == '.pdf':
                reader = PdfReader(file_path)
                content = "\n".join(page.extract_text() or '' for page in reader.pages)
            elif ext == '.docx':
                doc = Document(file_path)
                content = "\n".join([p.text for p in doc.paragraphs])
            else:
                self.append_chat('시스템', '지원하지 않는 파일 형식입니다.')
                return
            
            # 파일 요약 시작 시간 기록
            from datetime import datetime
            self.request_start_time = datetime.now()
            
            self.append_chat('사용자', f'📎 파일 업로드: {os.path.basename(file_path)}')
            self.append_chat('시스템', '파일 내용을 요약 중입니다...')
            
            prompt = f'다음 파일 내용을 요약해줘:\n\n{content[:3000]}'  # 길이 제한
            model = load_last_model()
            api_key = load_model_api_key(model)
            self.update_model_label()
            
            self._start_ai_request(api_key, model, None, prompt)
            
        except Exception as e:
            self.append_chat('시스템', f'파일 처리 오류: {e}')

    def cancel_request(self):
        """요청 취소 - 전역 스레드 관리"""
        print("취소 요청 시작")
        
        # UI 상태 먼저 복원
        self.set_ui_enabled(True)
        self.show_loading(False)
        
        # 워커 취소 신호
        if self.worker:
            self.worker.cancel()
        
        # 쓰레드 종료 신호만 전송
        if self.thread and self.thread.isRunning():
            self.thread.quit()
        
        # 정리는 _cleanup_thread에서 처리
        self._cleanup_thread()
        
        self.append_chat('시스템', '요청을 취소했습니다.')
        print("취소 요청 완료")
    
    def on_ai_cancelled(self):
        """취소 완료 처리"""
        # UI 상태는 cancel_request에서 이미 복원됨
        # 중복 처리 방지
        pass
    
    def on_ai_response(self, sender, text):
        # 응답 시간 계산
        response_time = ""
        if self.request_start_time:
            from datetime import datetime
            elapsed = datetime.now() - self.request_start_time
            response_time = f" (응답시간: {elapsed.total_seconds():.1f}초)"
        
        # 최적화된 타이핑 애니메이션
        self.start_optimized_typing(sender, text + response_time)
        
        # 히스토리에 AI 응답 추가
        self.conversation_history.add_message('assistant', text)
        self.conversation_history.save_to_file()
        
        self.messages.append({'role': 'assistant', 'content': text})
        self.set_ui_enabled(True)
        self.show_loading(False)

    def on_ai_error(self, msg):
        # 오류 시에도 응답 시간 표시
        error_time = ""
        if self.request_start_time:
            from datetime import datetime
            elapsed = datetime.now() - self.request_start_time
            error_time = f" (오류발생시간: {elapsed.total_seconds():.1f}초)"
        
        self.append_chat('시스템', msg + error_time)
        self.set_ui_enabled(True)
        self.show_loading(False)

    def set_ui_enabled(self, enabled):
        # 입력창은 항상 활성화, 전송 버튼만 비활성화
        self.send_button.setEnabled(enabled)
        self.cancel_button.setVisible(not enabled)
        self.upload_button.setEnabled(enabled)
        self.agent_checkbox.setEnabled(enabled)
    
    def show_loading(self, show):
        """로딩 상태 표시/숨김"""
        if show:
            self.loading_bar.show()
        else:
            self.loading_bar.hide()

    def append_chat(self, sender, text):
        """채팅 메시지를 예쁘게 표시"""
        # 발신자별 스타일
        if sender == '사용자':
            bg_color = '#2a4d69'
            border_color = '#4FC3F7'
            text_color = '#ffffff'
            icon = '💬'
            sender_color = '#4FC3F7'
        elif sender in ['AI', '에이전트']:
            bg_color = '#2d4a2d'
            border_color = '#66BB6A'
            text_color = '#ffffff'
            icon = '🤖'
            sender_color = '#66BB6A'
        else:
            bg_color = '#4a3d2a'
            border_color = '#FFA726'
            text_color = '#ffffff'
            icon = '⚙️'
            sender_color = '#FFA726'
        
        formatted_text = self.format_text(text)
        
        html_message = f"""
        <div style="
            margin: 16px 0;
            padding: 16px;
            background: linear-gradient(135deg, {bg_color}22, {bg_color}11);
            border-left: 4px solid {border_color};
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        ">
            <div style="
                margin: 0 0 12px 0;
                font-weight: 600;
                color: {sender_color};
                font-size: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <span style="font-size: 15px;">{icon}</span>
                <span>{sender}</span>
            </div>
            <div style="
                margin: 0;
                padding-left: 24px;
                line-height: 1.7;
                color: {text_color};
                font-size: 12px;
                word-wrap: break-word;
            ">
                {formatted_text}
            </div>
        </div>
        """
        
        self.chat_display.append(html_message)
        self.scroll_to_bottom()
    
    def start_optimized_typing(self, sender, text):
        """간단한 타이핑 애니메이션"""
        if self.is_typing:
            return
            
        self.is_typing = True
        self.current_sender = sender
        
        # 짧은 응답은 즉시 표시
        if len(text) < 500:
            self.append_chat(sender, text)
            self.is_typing = False
            return
            
        # 긴 응답은 청크 단위로 분할
        self.typing_chunks = self._split_text_for_typing(text)
        self.current_chunk_index = 0
        
        # 발신자 헤더 먼저 표시
        if sender == '사용자':
            color = '#4FC3F7'
            icon = '👤'
        elif sender in ['AI', '에이전트']:
            color = '#66BB6A'
            icon = '🤖'
        else:
            color = '#FFA726'
            icon = '⚙️'
            
        header_html = f"""
        <div style="margin: 20px 0 10px 0; font-weight: bold; color: {color}; font-size: 16px;">
            {icon} {sender}
        </div>
        """
        
        self.chat_display.append(header_html)
        self.typing_timer.start(200)  # 200ms 간격
    
    def show_next_line(self):
        """다음 청크 표시"""
        if self.current_chunk_index >= len(self.typing_chunks):
            self.typing_timer.stop()
            self.is_typing = False
            return
            
        chunk = self.typing_chunks[self.current_chunk_index]
        formatted_chunk = self.format_text(chunk)
        
        # QTextBrowser는 JavaScript를 지원하지 않으므로 직접 HTML 추가
        self.chat_display.append(f"<div style='margin: 5px 0; color: #ffffff;'>{formatted_chunk}</div>")
        self.current_chunk_index += 1
        
        # 스크롤을 맨 아래로
        self.scroll_to_bottom()
    
    def append_chat_simple(self, sender, text):
        """간단한 메시지 추가 (타이핑용)"""
        # 발신자별 스타일 적용
        if sender == '사용자':
            color = '#64B5F6'
            bg_color = '#1E3A5F'
            icon = '👤'
        elif sender in ['AI', '에이전트']:
            color = '#81C784'
            bg_color = '#2E5D31'
            icon = '🤖'
        else:
            color = '#FFB74D'
            bg_color = '#5D4037'
            icon = '⚙️'
        
        html_message = f"""
        <div style="margin: 8px 0; padding: 12px; border-left: 4px solid {color}; background-color: {bg_color}; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
            <div style="margin: 0 0 8px 0; font-weight: bold; color: {color}; font-size: 13px;">
                {icon} {sender}
            </div>
            <div style="margin: 0; padding-left: 15px; line-height: 1.5; color: #e0e0e0; font-size: 12px;">
                {text}<span style="opacity: 0.7;">▌</span>
            </div>
        </div>
        """
        
        self.chat_display.append(html_message)
    
    def append_typing_message(self, sender, text):
        """타이핑용 메시지 추가"""
        # 발신자별 스타일 적용
        if sender == '사용자':
            color = '#64B5F6'
            bg_color = '#1E3A5F'
            icon = '👤'
        elif sender in ['AI', '에이전트']:
            color = '#81C784'
            bg_color = '#2E5D31'
            icon = '🤖'
        else:
            color = '#FFB74D'
            bg_color = '#5D4037'
            icon = '⚙️'
        
        # 초기 빈 메시지
        html_message = f"""
        <div id="typing-{self.current_message_id}" style="margin: 8px 0; padding: 12px; border-left: 4px solid {color}; background-color: {bg_color}; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
            <div style="margin: 0 0 8px 0; font-weight: bold; color: {color}; font-size: 13px;">
                {icon} {sender}
            </div>
            <div id="typing-content-{self.current_message_id}" style="margin: 0; padding-left: 15px; line-height: 1.5; color: #e0e0e0; font-size: 12px;">
                <span style="opacity: 0.5;">▌</span>
            </div>
        </div>
        """
        
        self.chat_display.append(html_message)
    
    def update_typing_message(self, sender, text):
        """사용하지 않음"""
        pass
    
    def _split_text_for_typing(self, text):
        """타이핑용 텍스트 분할 - 성능 최적화"""
        # 짧은 줄들은 묶어서 처리
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 100자 이상이거나 코드 블록이면 단독 처리
            if len(line) > 100 or '```' in line or line.startswith('#'):
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                chunks.append(line)
            else:
                current_chunk.append(line)
                current_length += len(line)
                
                # 200자마다 청크 분할
                if current_length > 200:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return chunks
    
    def format_text(self, text):
        """텍스트 포맷팅 - 예쁘고 가독성 좋게"""
        import re
        
        # HTML 이스케이프 처리
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # 코드 블록 처리 - 어두운 테마에 맞게
        def replace_code_block(match):
            code_content = match.group(1).strip()
            # HTML 이스케이프 되돌리기
            code_content = code_content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            return f'''
            <div style="
                background: linear-gradient(135deg, #2d2d2d, #1a1a1a);
                border: 1px solid #444444;
                border-radius: 8px;
                padding: 16px;
                margin: 12px 0;
                font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
                font-size: 13px;
                color: #e8e8e8;
                overflow-x: auto;
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
            ">
                <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">{code_content}</pre>
            </div>
            '''
        
        # 코드 블록 처리
        text = re.sub(r'```[^\n]*\n([\s\S]*?)```', replace_code_block, text)
        text = re.sub(r'```([\s\S]*?)```', replace_code_block, text)
        
        # **굵은글씨** 
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff; font-weight: 600;">\1</strong>', text)
        
        # *기울임글씨*
        text = re.sub(r'\*(.*?)\*', r'<em style="color: #cccccc; font-style: italic;">\1</em>', text)
        
        # URL 링크 처리 - 예쁘게
        text = re.sub(r'(https?://[^\s<>"]+)', r'<a href="\1" style="color: #64B5F6; text-decoration: none; border-bottom: 1px dotted #64B5F6;">\1</a>', text)
        
        # `인라인 코드` - 어두운 테마에 맞게
        text = re.sub(r'`([^`\n]+)`', r'<code style="background: linear-gradient(135deg, #3a3a3a, #2a2a2a); color: #ffeb3b; padding: 3px 6px; font-family: monospace; border-radius: 4px; font-size: 13px; border: 1px solid #555555;">\1</code>', text)
        
        # 리스트 스타일링
        text = re.sub(r'^- (.*?)$', r'<div style="margin: 4px 0; padding-left: 16px;"><span style="color: #81C784; font-weight: bold;">•</span> <span style="margin-left: 8px;">\1</span></div>', text, flags=re.MULTILINE)
        text = re.sub(r'^(\d+)\. (.*?)$', r'<div style="margin: 4px 0; padding-left: 16px;"><span style="color: #FFB74D; font-weight: bold;">\1.</span> <span style="margin-left: 8px;">\2</span></div>', text, flags=re.MULTILINE)
        
        # 제목 스타일링
        text = re.sub(r'^### (.*?)$', r'<h3 style="color: #FFB74D; font-size: 16px; font-weight: 600; margin: 16px 0 8px 0; border-bottom: 2px solid #FFB74D; padding-bottom: 4px;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2 style="color: #81C784; font-size: 18px; font-weight: 600; margin: 20px 0 10px 0; border-bottom: 2px solid #81C784; padding-bottom: 6px;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*?)$', r'<h1 style="color: #64B5F6; font-size: 20px; font-weight: 700; margin: 24px 0 12px 0; border-bottom: 3px solid #64B5F6; padding-bottom: 8px;">\1</h1>', text, flags=re.MULTILINE)
        
        # 단락 구분 및 들여쓰기 처리
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('<br><br>')  # 빈 줄은 단락 구분
            elif line.startswith('- ') or line.startswith('• '):
                formatted_lines.append(f'<div style="margin: 8px 0 4px 20px;">{line}</div>')
            elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                formatted_lines.append(f'<div style="margin: 8px 0 4px 20px;">{line}</div>')
            elif line.startswith('#'):
                formatted_lines.append(f'<div style="margin: 16px 0 8px 0;">{line}</div>')
            else:
                formatted_lines.append(f'<div style="margin: 6px 0; line-height: 1.6;">{line}</div>')
        
        return ''.join(formatted_lines)
    
    def scroll_to_bottom(self):
        """스크롤을 맨 아래로"""
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def close(self):
        """위젯 종료 - 전역 스레드 관리"""
        print("ChatWidget 종료 시작")
        
        try:
            # 타이머 정지
            if hasattr(self, 'typing_timer') and self.typing_timer:
                self.typing_timer.stop()
            
            # 워커 취소 신호만 전송
            if hasattr(self, 'worker') and self.worker:
                try:
                    self.worker.cancel()
                except:
                    pass
            
            # 쓰레드 종료 신호만 전송
            if hasattr(self, 'thread') and self.thread:
                try:
                    if self.thread.isRunning():
                        self.thread.quit()
                except:
                    pass
            
            # 정리
            self._cleanup_thread()
            
            print("ChatWidget 종료 완료")
            
        except Exception as e:
            print(f"ChatWidget 종료 중 오류: {e}") 