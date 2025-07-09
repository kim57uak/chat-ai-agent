from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QFileDialog, QCheckBox, QLabel, QProgressBar, QTextBrowser, QPlainTextEdit
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from core.file_utils import load_config, load_model_api_key, load_last_model
from core.ai_client import AIClient
from core.conversation_history import ConversationHistory
import os
import threading

# 파일 내용 추출 유틸리티
from PyPDF2 import PdfReader
from docx import Document

class AIProcessor(QObject):
    finished = pyqtSignal(str, str)  # sender, text
    error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def process_request(self, api_key, model, messages, user_text=None, agent_mode=False, file_prompt=None):
        """AI 요청 처리 - 메인 스레드에서 실행"""
        
        def _process():
            try:
                if self._cancelled:
                    return
                
                client = AIClient(api_key, model)
                response = None
                sender = 'AI'
                
                if file_prompt:
                    if agent_mode:
                        response = client.agent_chat(file_prompt)
                        sender = '에이전트'
                    else:
                        response = client.chat(messages + [{'role': 'user', 'content': file_prompt}])
                else:
                    if agent_mode:
                        response = client.agent_chat(user_text)
                        sender = '에이전트'
                    else:
                        response = client.chat(messages)
                
                if not self._cancelled and response:
                    self.finished.emit(sender, response)
                elif not self._cancelled:
                    self.error.emit("응답을 생성할 수 없습니다.")
                    
            except Exception as e:
                if not self._cancelled:
                    self.error.emit(f'오류 발생: {str(e)}')
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=_process, daemon=True)
        thread.start()

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

        # 채팅 표시 영역 - QWebEngineView로 교체
        self.chat_display = QWebEngineView(self)
        self.chat_display.setMinimumHeight(400)
        self.chat_messages = []  # HTML 메시지 저장용
        
        # QWebEngineView 초기 HTML 설정
        self.init_web_view()
        
        self.layout.addWidget(self.chat_display, 1)
        
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
        
        # 입력창
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
        
        input_layout.addWidget(self.input_text, 5)
        input_layout.addWidget(self.send_button, 1)
        input_layout.addWidget(self.cancel_button, 1)
        input_layout.addWidget(self.upload_button, 1)

        self.layout.addLayout(input_layout, 0)

        self.send_button.clicked.connect(self.send_message)
        self.cancel_button.clicked.connect(self.cancel_request)
        self.upload_button.clicked.connect(self.upload_file)
        
        # Ctrl+Enter로 전송
        send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.input_text)
        send_shortcut.activated.connect(self.send_message)

        self.messages = []
        self.ai_processor = AIProcessor(self)
        self.request_start_time = None
        
        # AI 프로세서 시그널 연결
        self.ai_processor.finished.connect(self.on_ai_response)
        self.ai_processor.error.connect(self.on_ai_error)
        
        # 타이핑 애니메이션용
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.show_next_line)
        self.typing_lines = []
        self.current_line_index = 0
        self.current_sender = ""
        self.current_message_id = ""
        self.is_typing = False

    def init_web_view(self):
        """웹 브라우저 초기화"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    background-color: #1a1a1a;
                    color: #e8e8e8;
                    font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
                    font-size: 13px;
                    line-height: 1.6;
                    margin: 16px;
                }
                pre {
                    background: #2d2d2d;
                    color: #e8e8e8;
                    padding: 12px;
                    border-radius: 6px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 12px;
                    overflow-x: auto;
                    white-space: pre-wrap;
                }
                .message {
                    margin: 16px 0;
                    padding: 12px;
                    border-radius: 8px;
                }
                .user { background: #2a4d6922; }
                .ai { background: #2d4a2d22; }
                .system { background: #4a3d2a22; }
            </style>
        </head>
        <body>
            <div id="messages"></div>
        </body>
        </html>
        """
        self.chat_display.setHtml(html_template)
    
    def update_model_label(self):
        model = load_last_model()
        self.model_label.setText(f'현재 모델: <b>{model}</b>')

    def send_message(self):
        user_text = self.input_text.toPlainText().strip()
        if not user_text:
            return
        
        # 이전 요청이 진행 중이면 취소
        if hasattr(self, 'ai_processor'):
            self.ai_processor.cancel()
            self.ai_processor = AIProcessor(self)
            self.ai_processor.finished.connect(self.on_ai_response)
            self.ai_processor.error.connect(self.on_ai_error)
        
        self._process_new_message(user_text)
    
    def _process_new_message(self, user_text):
        """새 메시지 처리"""
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
        """AI 요청 시작 - 단순화된 방식"""
        self.set_ui_enabled(False)
        self.show_loading(True)
        
        # 최근 대화 기록 포함하여 전송
        recent_history = self.conversation_history.get_recent_messages(10)
        
        # AI 요청 처리 - 항상 에이전트 모드
        self.ai_processor.process_request(
            api_key, model, recent_history, user_text,
            True, file_prompt
        )
        
        # 타임아웃 제거 - 사용자가 취소 버튼으로 제어
    


    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '파일 선택', '', '모든 파일 (*);;텍스트 파일 (*.txt);;PDF 파일 (*.pdf);;Word 파일 (*.docx)')
        if not file_path:
            return
        
        # 이전 요청이 진행 중이면 취소
        if hasattr(self, 'ai_processor'):
            self.ai_processor.cancel()
            self.ai_processor = AIProcessor(self)
            self.ai_processor.finished.connect(self.on_ai_response)
            self.ai_processor.error.connect(self.on_ai_error)
        
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
            
            from datetime import datetime
            self.request_start_time = datetime.now()
            
            self.append_chat('사용자', f'📎 파일 업로드: {os.path.basename(file_path)}')
            self.append_chat('시스템', '파일 내용을 요약 중입니다...')
            
            prompt = f'다음 파일 내용을 요약해줘:\n\n{content[:3000]}'
            model = load_last_model()
            api_key = load_model_api_key(model)
            self.update_model_label()
            
            self._start_ai_request(api_key, model, None, prompt)
            
        except Exception as e:
            self.append_chat('시스템', f'파일 처리 오류: {e}')

    def cancel_request(self):
        """요청 취소 - 단순화된 방식"""
        print("취소 요청 시작")
        
        # UI 상태 복원
        self.set_ui_enabled(True)
        self.show_loading(False)
        
        # AI 프로세서 취소
        if hasattr(self, 'ai_processor'):
            self.ai_processor.cancel()
        
        self.append_chat('시스템', '요청을 취소했습니다.')
        print("취소 요청 완료")
    
    def on_ai_response(self, sender, text):
        # 응답 시간 계산
        response_time = ""
        if self.request_start_time:
            from datetime import datetime
            elapsed = datetime.now() - self.request_start_time
            response_time = f" (응답시간: {elapsed.total_seconds():.1f}초)"
        
        # 타이핑 애니메이션
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
        self.send_button.setEnabled(enabled)
        self.cancel_button.setVisible(not enabled)
        self.upload_button.setEnabled(enabled)
    
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
            margin: 8px 0;
            padding: 12px;
            background: linear-gradient(135deg, {bg_color}22, {bg_color}11);
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        ">"
            <div style="
                margin: 0 0 6px 0;
                font-weight: 600;
                color: {sender_color};
                font-size: 11px;
                display: flex;
                align-items: center;
                gap: 6px;
            ">
                <span style="font-size: 13px;">{icon}</span>
                <span>{sender}</span>
            </div>
            <div style="
                margin: 0;
                padding-left: 20px;
                line-height: 1.4;
                color: {text_color};
                font-size: 12px;
                word-wrap: break-word;
            ">
                {formatted_text}
            </div>
        </div>
        """
        
        # JavaScript로 메시지 추가
        import json
        js_code = f"""
        var messagesDiv = document.getElementById('messages');
        var messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        messageDiv.innerHTML = {json.dumps(html_message)};
        messagesDiv.appendChild(messageDiv);
        window.scrollTo(0, document.body.scrollHeight);
        """
        self.chat_display.page().runJavaScript(js_code)
    
    def start_optimized_typing(self, sender, text):
        """즉시 메시지 표시"""
        self.append_chat(sender, text)
    
    def show_next_line(self):
        """다음 줄 표시"""
        if self.current_line_index >= len(self.typing_lines):
            self.typing_timer.stop()
            self.is_typing = False
            return
            
        line = self.typing_lines[self.current_line_index]
        formatted_line = self.format_text(line)
        
        # 현재 메시지 컨테이너에 줄 추가
        line_js = f"""
        var contentDiv = document.getElementById('{self.current_message_id}_content');
        var lineDiv = document.createElement('div');
        lineDiv.innerHTML = `{formatted_line.replace('`', '\\`').replace('${', '\\${')}` + '<br>';
        contentDiv.appendChild(lineDiv);
        window.scrollTo(0, document.body.scrollHeight);
        """
        
        self.chat_display.page().runJavaScript(line_js)
        self.current_line_index += 1
    
    def _split_text_for_typing(self, text):
        """타이핑용 텍스트 분할"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if len(line) > 100 or '```' in line or line.startswith('#'):
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                chunks.append(line)
            else:
                current_chunk.append(line)
                current_length += len(line)
                
                if current_length > 200:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return chunks
    
    def format_text(self, text):
        """텍스트 포맷팅 - 확장된 마크다운 지원"""
        import re
        
        # 1. 코드 블록 처리 먼저
        code_blocks = []
        def extract_code_block(match):
            code_content = match.group(1)
            placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
            code_blocks.append(code_content)
            return placeholder
        
        text = re.sub(r'```[^\n]*\n([\s\S]*?)```', extract_code_block, text)
        
        # 2. 인라인 코드 처리
        inline_codes = []
        def extract_inline_code(match):
            code_content = match.group(1)
            placeholder = f"__INLINE_CODE_{len(inline_codes)}__"
            inline_codes.append(code_content)
            return placeholder
        
        text = re.sub(r'`([^`]+)`', extract_inline_code, text)
        
        # 3. HTML 이스케이프 처리 (링크는 제외)
        # 먼저 기존 HTML 태그를 임시로 보호
        import re
        html_tags = []
        def preserve_html_tag(match):
            tag = match.group(0)
            placeholder = f"__HTML_TAG_{len(html_tags)}__"
            html_tags.append(tag)
            return placeholder
        
        # 기존 HTML 태그 보호
        text = re.sub(r'<[^>]+>', preserve_html_tag, text)
        
        # 나머지 < > & 이스케이프
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # 4. 헤딩 처리
        text = re.sub(r'^### (.*?)$', r'<h3 style="color: #81C784; margin: 16px 0 8px 0; font-size: 16px;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2 style="color: #4FC3F7; margin: 20px 0 10px 0; font-size: 18px;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*?)$', r'<h1 style="color: #FFD54F; margin: 24px 0 12px 0; font-size: 20px;">\1</h1>', text, flags=re.MULTILINE)
        
        # 5. 링크 처리
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #4FC3F7; text-decoration: underline;" target="_blank">\1</a>', text)
        text = re.sub(r'(https?://[^\s]+)', r'<a href="\1" style="color: #4FC3F7; text-decoration: underline;" target="_blank">\1</a>', text)
        
        # 6. **굵은글씨** 및 *기울임* 처리
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #FFD54F; font-weight: 600;">\1</strong>', text)
        text = re.sub(r'\*([^*]+)\*', r'<em style="color: #FFA726; font-style: italic;">\1</em>', text)
        
        # 7. 번호 목록 처리
        text = re.sub(r'^(\d+)\. (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #4FC3F7; font-weight: bold; margin-right: 8px;">\1.</span>\2</div>', text, flags=re.MULTILINE)
        
        # 8. 불릿 포인트 처리
        text = re.sub(r'^• (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span>\1</div>', text, flags=re.MULTILINE)
        text = re.sub(r'^- (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span>\1</div>', text, flags=re.MULTILINE)
        
        # 9. 테이블 처리
        lines = text.split('\n')
        table_lines = []
        in_table = False
        for line in lines:
            if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    table_lines.append('<table style="border-collapse: collapse; margin: 12px 0; width: 100%; max-width: 600px;">')
                    in_table = True
                cells = [cell.strip() for cell in line.strip().split('|')[1:-1]]
                row_html = '<tr>' + ''.join(f'<td style="padding: 8px 12px; border: 1px solid #444444; background-color: #2a2a2a;">{cell}</td>' for cell in cells) + '</tr>'
                table_lines.append(row_html)
            else:
                if in_table:
                    table_lines.append('</table>')
                    in_table = False
                table_lines.append(line)
        if in_table:
            table_lines.append('</table>')
        text = '\n'.join(table_lines)
        
        # 10. 인라인 코드 복원
        for i, code_content in enumerate(inline_codes):
            placeholder = f"__INLINE_CODE_{i}__"
            escaped_code = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            code_html = f'<code style="background-color: #2d2d2d; color: #e8e8e8; padding: 2px 6px; border-radius: 3px; font-family: Consolas, Monaco, monospace; font-size: 11px;">{escaped_code}</code>'
            text = text.replace(placeholder, code_html)
        
        # 11. 코드 블록 복원
        for i, code_content in enumerate(code_blocks):
            placeholder = f"__CODE_BLOCK_{i}__"
            code_lines = code_content.strip().split('\n')
            formatted_lines = []
            for line in code_lines:
                escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                escaped_line = escaped_line.replace(' ', '&nbsp;')
                formatted_lines.append(f'<div style="margin: 0; padding: 0; line-height: 1.4;">{escaped_line}</div>')
            
            code_html = f'<div style="background-color: #2d2d2d; border: 1px solid #444444; border-radius: 6px; padding: 12px; margin: 8px 0; font-family: Consolas, Monaco, monospace; font-size: 12px; color: #e8e8e8;">{"".join(formatted_lines)}</div>'
            text = text.replace(placeholder, code_html)
        
        # 12. 보호된 HTML 태그 복원
        for i, tag in enumerate(html_tags):
            placeholder = f"__HTML_TAG_{i}__"
            text = text.replace(placeholder, tag)
        
        # 13. 줄바꿈 처리
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('<br>')
            elif line.startswith('<') or line.startswith('</'):  # HTML 태그는 그대로 유지
                formatted_lines.append(line)
            else:
                formatted_lines.append(f'<div style="margin: 3px 0; line-height: 1.5; color: #e8e8e8;">{line}</div>')
        
        return '\n'.join(formatted_lines)
    
    def scroll_to_bottom(self):
        """스크롤을 맨 아래로"""
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def close(self):
        """위젯 종료 - 단순화된 방식"""
        print("ChatWidget 종료 시작")
        
        try:
            # 타이머 정지
            if hasattr(self, 'typing_timer') and self.typing_timer:
                self.typing_timer.stop()
            
            # AI 프로세서 취소
            if hasattr(self, 'ai_processor'):
                self.ai_processor.cancel()
            
            print("ChatWidget 종료 완료")
            
        except Exception as e:
            print(f"ChatWidget 종료 중 오류: {e}")