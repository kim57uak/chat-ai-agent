from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QFileDialog, QCheckBox, QLabel, QProgressBar, QTextBrowser, QPlainTextEdit, QComboBox
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
    finished = pyqtSignal(str, str, list)  # sender, text, used_tools
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
                # 대화 히스토리를 클라이언트에 설정
                if messages:
                    client.conversation_history = messages
                    print(f"[디버그] 히스토리 설정: {len(messages)}개")
                
                response = None
                sender = 'AI'
                used_tools = []
                
                if file_prompt:
                    if agent_mode:
                        print(f"[DEBUG] 파일 프롬프트 에이전트 모드로 처리")
                        result = client.agent_chat(file_prompt)
                        if isinstance(result, tuple):
                            response, used_tools = result
                            print(f"[DEBUG] 파일 프롬프트 에이전트 응답 완료, 사용된 도구: {used_tools}")
                        else:
                            response = result
                            used_tools = []
                        sender = '에이전트'
                    else:
                        print(f"[DEBUG] 파일 프롬프트 단순 채팅 모드로 처리")
                        response = client.simple_chat(file_prompt)
                        sender = 'AI'
                        used_tools = []
                else:
                    if agent_mode:
                        print(f"[DEBUG] 에이전트 모드로 처리: {user_text[:50]}...")
                        result = client.agent_chat(user_text)
                        if isinstance(result, tuple):
                            response, used_tools = result
                            print(f"[DEBUG] 에이전트 응답 완료, 사용된 도구: {used_tools}")
                        else:
                            response = result
                            used_tools = []
                        sender = '에이전트'
                    else:
                        print(f"[DEBUG] 단순 채팅 모드로 처리: {user_text[:50]}...")
                        response = client.simple_chat(user_text)
                        sender = 'AI'
                        used_tools = []
                
                if not self._cancelled and response:
                    self.finished.emit(sender, response, used_tools)
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
        print(f"[디버그] 초기 히스토리 로드: {len(self.conversation_history.current_session)}개")
        
        # 업로드된 파일 정보 저장
        self.uploaded_file_content = None
        self.uploaded_file_name = None

        # 상단 정보 영역 (모델명 + 도구 상태)
        info_layout = QHBoxLayout()
        
        # 현재 모델명 표시 라벨 (클릭 가능)
        self.model_label = QLabel(self)
        self.model_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.model_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model_label.setStyleSheet("""
            QLabel {
                color: rgb(163,135,215);
                font-size: 12px;
                font-weight: bold;
                padding: 10px;
                background-color: #1a1a1a;
            }
            QLabel:hover {
                background-color: #2a2a2a;
                border-radius: 4px;
            }
        """)
        self.model_label.mousePressEvent = self.show_model_popup
        
        # 도구 상태 표시 라벨 (클릭 가능)
        self.tools_label = QLabel(self)
        self.tools_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.tools_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tools_label.setStyleSheet("""
            QLabel {
                color: rgb(135,163,215);
                font-size: 12px;
                font-weight: bold;
                padding: 10px;
                background-color: #1a1a1a;
            }
            QLabel:hover {
                background-color: #2a2a2a;
                border-radius: 4px;
            }
        """)
        self.tools_label.mousePressEvent = self.show_tools_popup
        
        info_layout.addWidget(self.model_label, 1)
        info_layout.addWidget(self.tools_label, 0)
        self.layout.addLayout(info_layout)
        
        self.update_model_label()
        self.update_tools_label()
        
        # 도구 상태 주기적 갱신 타이머 (초기 지연 후 시작)
        self.tools_update_timer = QTimer()
        self.tools_update_timer.timeout.connect(self.update_tools_label)
        QTimer.singleShot(10000, lambda: self.tools_update_timer.start(15000))  # 10초 후 시작, 15초마다 갱신

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
                background-color: rgb(163,135,215);
                border-radius: 3px;
            }
        """)
        self.layout.addWidget(self.loading_bar)

        input_layout = QHBoxLayout()
        
        # 입력창 컸테이너 (모드 선택과 함께)
        input_container = QWidget(self)
        input_container_layout = QHBoxLayout(input_container)
        input_container_layout.setContentsMargins(0, 0, 0, 0)
        input_container_layout.setSpacing(0)
        
        # 모드 선택 콤보박스 (입력창 내부 왼쪽)
        self.mode_combo = QComboBox(self)
        self.mode_combo.addItems(["Ask", "Agent"])
        self.mode_combo.setCurrentText("Ask")
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: transparent;
                color: #888888;
                border: none;
                border-right: 1px solid #444444;
                border-radius: 0px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
                min-width: 45px;
                max-width: 45px;
                outline: none;
            }
            QComboBox:focus {
                border: none;
                border-right: 1px solid #444444;
                outline: none;
            }
            QComboBox:hover {
                color: #ffffff;
                background-color: rgba(255,255,255,0.05);
            }
            QComboBox::drop-down {
                border: none;
                width: 12px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid #888888;
                margin-right: 3px;
            }
            QComboBox:hover::down-arrow {
                border-top: 3px solid #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: #ffffff;
                selection-background-color: rgb(163,135,215);
                border: 1px solid #444444;
                border-radius: 4px;
            }
        """)
        
        # 입력창
        self.input_text = QTextEdit(self)
        self.input_text.setMaximumHeight(80)
        self.input_text.setPlaceholderText("메시지를 입력하세요... (Ctrl+Enter로 전송)")
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-size: 12px;
                padding: 10px;
            }
        """)
        
        # 컸테이너 스타일
        input_container.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 6px;
            }
        """)
        
        # 컸테이너에 위젯 추가
        input_container_layout.addWidget(self.mode_combo, 0)
        input_container_layout.addWidget(self.input_text, 1)
        
        # 모드 변경 시 플레이스홀더 업데이트
        self.mode_combo.currentTextChanged.connect(self.update_placeholder)
        
        self.send_button = QPushButton('전송', self)
        self.send_button.setMinimumHeight(80)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(163,135,215);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgb(143,115,195);
            }
            QPushButton:pressed {
                background-color: rgb(123,95,175);
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
                background-color: rgb(135,163,215);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgb(115,143,195);
            }
            QPushButton:pressed {
                background-color: rgb(95,123,175);
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        
        input_layout.addWidget(input_container, 5)
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
        
        # 웹뷰 로드 완료 후 이전 대화 로드
        self.chat_display.loadFinished.connect(self._on_webview_loaded)
    
    def update_placeholder(self):
        """모드에 따라 플레이스홀더 업데이트"""
        current_mode = self.mode_combo.currentText()
        if current_mode == "Ask":
            self.input_text.setPlaceholderText("단순 질의를 입력하세요... (Ctrl+Enter로 전송)")
        else:
            self.input_text.setPlaceholderText("도구 사용 가능한 메시지를 입력하세요... (Ctrl+Enter로 전송)")

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
                    white-space: pre;
                    tab-size: 4;
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
            <script>
                function copyCode(codeId) {
                    const codeElement = document.getElementById(codeId);
                    const text = codeElement.textContent;
                    
                    if (navigator.clipboard && window.isSecureContext) {
                        navigator.clipboard.writeText(text).then(() => {
                            showCopySuccess(event.target);
                        }).catch(err => {
                            fallbackCopy(text, event.target);
                        });
                    } else {
                        fallbackCopy(text, event.target);
                    }
                }
                
                function fallbackCopy(text, button) {
                    const textarea = document.createElement('textarea');
                    textarea.value = text;
                    textarea.style.position = 'fixed';
                    textarea.style.opacity = '0';
                    document.body.appendChild(textarea);
                    textarea.select();
                    
                    try {
                        document.execCommand('copy');
                        showCopySuccess(button);
                    } catch (err) {
                        button.textContent = '실패';
                        button.style.background = '#F44336';
                        setTimeout(() => {
                            button.textContent = '복사';
                            button.style.background = '#444';
                        }, 1500);
                    } finally {
                        document.body.removeChild(textarea);
                    }
                }
                
                function showCopySuccess(button) {
                    button.textContent = '복사됨!';
                    button.style.background = '#4CAF50';
                    setTimeout(() => {
                        button.textContent = '복사';
                        button.style.background = '#444';
                    }, 1500);
                }
            </script>
        </head>
        <body>
            <div id="messages"></div>
        </body>
        </html>
        """
        self.chat_display.setHtml(html_template)
    
    def update_model_label(self):
        model = load_last_model()
        self.model_label.setText(f'현재 모델: <b>{model}</b> 📋')
    
    def show_model_popup(self, event):
        """사용 가능한 모델 목록 팝업 표시"""
        try:
            from PyQt6.QtWidgets import QMenu
            from core.file_utils import load_config, save_last_model
            
            config = load_config()
            models = config.get('models', {})
            
            if not models:
                return
            
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 8px 16px;
                    border-radius: 2px;
                }
                QMenu::item:selected {
                    background-color: rgb(163,135,215);
                }
            """)
            
            current_model = load_last_model()
            
            for model_name, model_config in models.items():
                if model_config.get('api_key'):  # API 키가 있는 모델만 표시
                    action = menu.addAction(f"🤖 {model_name}")
                    if model_name == current_model:
                        action.setText(f"✅ {model_name} (현재)")
                    action.triggered.connect(lambda checked, m=model_name: self.change_model(m))
            
            # 라벨 위치에서 팝업 표시
            menu.exec(self.model_label.mapToGlobal(event.pos()))
            
        except Exception as e:
            print(f"모델 팝업 표시 오류: {e}")
    
    def change_model(self, model_name):
        """모델 변경"""
        try:
            from core.file_utils import save_last_model
            save_last_model(model_name)
            self.update_model_label()
            self.append_chat('시스템', f'모델이 {model_name}으로 변경되었습니다.')
            print(f"[디버그] 모델 변경: {model_name}")
        except Exception as e:
            print(f"모델 변경 오류: {e}")
            self.append_chat('시스템', f'모델 변경 중 오류가 발생했습니다: {e}')
    
    def update_tools_label(self):
        """활성화된 도구 수 표시 업데이트"""
        try:
            from mcp.servers.mcp import get_all_mcp_tools
            tools = get_all_mcp_tools()
            tool_count = len(tools) if tools else 0
            
            if tool_count > 0:
                self.tools_label.setText(f'🔧 {tool_count}개 도구 활성화')
            else:
                self.tools_label.setText('🔧 도구 없음')
        except Exception as e:
            self.tools_label.setText('🔧 도구 상태 불명')
    
    def show_tools_popup(self, event):
        """활성화된 도구 목록 팝업 표시"""
        try:
            from PyQt6.QtWidgets import QMenu
            from mcp.servers.mcp import get_all_mcp_tools
            
            tools = get_all_mcp_tools()
            if not tools:
                return
            
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 6px 12px;
                    border-radius: 2px;
                }
                QMenu::item:selected {
                    background-color: #444444;
                }
            """)
            
            # 서버별로 도구 그룹화
            servers = {}
            for tool in tools:
                if isinstance(tool, str):
                    tool_name = tool
                    server_name = 'Unknown'
                else:
                    # MCPTool 객체의 속성 접근
                    tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                    server_name = tool.server_name if hasattr(tool, 'server_name') else 'Unknown'
                
                if server_name not in servers:
                    servers[server_name] = []
                servers[server_name].append(tool_name)
            
            for server_name, tool_names in servers.items():
                menu.addAction(f"📦 {server_name} ({len(tool_names)}개)")
                for tool_name in tool_names[:5]:  # 최대 5개만 표시
                    menu.addAction(f"  • {tool_name}")
                if len(tool_names) > 5:
                    menu.addAction(f"  ... 외 {len(tool_names)-5}개")
                menu.addSeparator()
            
            # 라벨 위치에서 팝업 표시
            menu.exec(self.tools_label.mapToGlobal(event.pos()))
            
        except Exception as e:
            print(f"도구 팝업 표시 오류: {e}")

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
        self.conversation_history.save_to_file()  # 즉시 저장
        self.messages.append({'role': 'user', 'content': user_text})
        print(f"[디버그] 사용자 메시지 히스토리에 추가: {user_text[:50]}...")

        model = load_last_model()
        api_key = load_model_api_key(model)
        self.update_model_label()
        if not api_key:
            self.append_chat('시스템', 'API Key가 설정되어 있지 않습니다. 환경설정에서 입력해 주세요.')
            return
        
        # 업로드된 파일이 있으면 파일 내용과 함께 분석
        if self.uploaded_file_content:
            # 이미지 파일인지 확인
            if "[IMAGE_BASE64]" in self.uploaded_file_content:
                # 이미지의 경우 사용자 요청과 이미지 데이터를 직접 결합
                combined_prompt = f'{user_text}\n\n{self.uploaded_file_content}'
                print(f"[디버그] 이미지 프롬프트 생성, 길이: {len(combined_prompt)}")
                print(f"[디버그] 종료 태그 확인: {'[/IMAGE_BASE64]' in combined_prompt}")
            else:
                # 일반 파일의 경우 기존 방식 유지
                combined_prompt = f'업로드된 파일 ({self.uploaded_file_name})에 대한 사용자 요청: {user_text}\n\n파일 내용:\n{self.uploaded_file_content}'
            
            self._start_ai_request(api_key, model, None, combined_prompt)
            # 파일 내용 초기화
            self.uploaded_file_content = None
            self.uploaded_file_name = None
        else:
            self._start_ai_request(api_key, model, user_text)
    
    def _start_ai_request(self, api_key, model, user_text, file_prompt=None):
        """모드에 따라 AI 요청 시작"""
        self.set_ui_enabled(False)
        self.show_loading(True)
        
        # 최신 대화 히스토리 가져오기 (파일에서 다시 로드)
        self.conversation_history.load_from_file()
        recent_history = self.conversation_history.get_recent_messages(10)
        print(f"[디버그] 전달할 히스토리: {len(recent_history)}개")
        for i, msg in enumerate(recent_history[-3:]):
            print(f"  [{i}] {msg.get('role', 'unknown')}: {msg.get('content', '')[:50]}...")
        
        # 모드에 따라 에이전트 사용 여부 결정
        current_mode = self.mode_combo.currentText()
        use_agent = (current_mode == "Agent")
        print(f"[DEBUG] 선택된 모드: {current_mode}, 에이전트 사용: {use_agent}")
        
        self.ai_processor.process_request(
            api_key, model, recent_history, user_text,
            use_agent, file_prompt
        )
    
    def old_start_ai_request(self, api_key, model, user_text, file_prompt=None):
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
        file_path, _ = QFileDialog.getOpenFileName(self, '파일 선택', '', '모든 파일 (*);;텍스트 파일 (*.txt);;PDF 파일 (*.pdf);;Word 파일 (*.docx *.doc);;Excel 파일 (*.xlsx *.xls);;PowerPoint 파일 (*.pptx *.ppt);;JSON 파일 (*.json);;이미지 파일 (*.jpg *.jpeg *.png *.gif *.bmp *.webp);;CSV 파일 (*.csv)')
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
            content = ""
            
            if ext == '.txt':
                # 다양한 encoding 시도
                for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin-1', 'utf-8-sig']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    content = f"텍스트 파일: {os.path.basename(file_path)}\n인코딩을 읽을 수 없습니다."
            elif ext == '.pdf':
                reader = PdfReader(file_path)
                content = "\n".join(page.extract_text() or '' for page in reader.pages)
            elif ext in ['.docx', '.doc']:
                doc = Document(file_path)
                content = "\n".join([p.text for p in doc.paragraphs])
            elif ext in ['.xlsx', '.xls']:
                try:
                    import pandas as pd
                    df = pd.read_excel(file_path)
                    content = f"파일 정보: {os.path.basename(file_path)}\n열 수: {len(df.columns)}, 행 수: {len(df)}\n\n데이터 미리보기:\n{df.head(10).to_string()}"
                except ImportError:
                    content = f"Excel 파일: {os.path.basename(file_path)}\n(pandas 라이브러리가 필요합니다. pip install pandas openpyxl)"
            elif ext in ['.pptx', '.ppt']:
                try:
                    from pptx import Presentation
                    prs = Presentation(file_path)
                    slides_text = []
                    for i, slide in enumerate(prs.slides, 1):
                        slide_text = f"슬라이드 {i}:\n"
                        for shape in slide.shapes:
                            if hasattr(shape, "text") and shape.text.strip():
                                slide_text += shape.text + "\n"
                        slides_text.append(slide_text)
                    content = "\n\n".join(slides_text)
                except ImportError:
                    content = f"PowerPoint 파일: {os.path.basename(file_path)}\n(python-pptx 라이브러리가 필요합니다. pip install python-pptx)"
            elif ext == '.json':
                import json
                # JSON 파일도 다중 인코딩 지원
                for encoding in ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            data = json.load(f)
                        content = f"JSON 파일 내용:\n{json.dumps(data, indent=2, ensure_ascii=False)}"
                        break
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                else:
                    content = f"JSON 파일: {os.path.basename(file_path)}\n파일을 읽을 수 없습니다."
            elif ext == '.csv':
                try:
                    import pandas as pd
                    # 다양한 encoding 시도
                    for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin-1']:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding)
                            content = f"CSV 파일 정보: {os.path.basename(file_path)}\n열 수: {len(df.columns)}, 행 수: {len(df)}\n\n데이터 미리보기:\n{df.head(10).to_string()}"
                            break
                        except UnicodeDecodeError:
                            continue
                except ImportError:
                    # pandas 없을 때 기본 처리
                    for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin-1']:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                lines = f.readlines()[:10]
                                content = f"CSV 파일: {os.path.basename(file_path)}\n미리보기 (10줄):\n{''.join(lines)}"
                                break
                        except UnicodeDecodeError:
                            continue
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                import base64
                try:
                    # 이미지를 base64로 인코딩
                    with open(file_path, 'rb') as img_file:
                        img_data = base64.b64encode(img_file.read()).decode('utf-8')
                    
                    # 이미지 정보 추가 (선택사항)
                    img_info = ""
                    try:
                        from PIL import Image
                        img = Image.open(file_path)
                        img_info = f"\n이미지 정보: {img.size[0]}x{img.size[1]} 픽셀, 모드: {img.mode}"
                    except (ImportError, ModuleNotFoundError):
                        pass
                    
                    content = f"[IMAGE_BASE64]{img_data}[/IMAGE_BASE64]\n이미지 파일: {os.path.basename(file_path)}{img_info}"
                    print(f"[디버그] 이미지 콘텐츠 생성 완료, 길이: {len(content)}")
                    print(f"[디버그] 종료 태그 위치: {content.rfind('[/IMAGE_BASE64]')}")
                    
                except Exception as e:
                    file_size = os.path.getsize(file_path)
                    content = f"이미지 파일: {os.path.basename(file_path)}\n파일 크기: {file_size:,} bytes\n이미지 처리 오류: {str(e)}"
            else:
                # 지원하지 않는 파일도 기본 텍스트로 읽기 시도
                for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin-1']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        content = f"파일: {os.path.basename(file_path)}\n파일 읽기 오류: {str(e)}"
                        break
            
            self.append_chat('사용자', f'📎 파일 업로드: {os.path.basename(file_path)}')
            
            # 이미지 파일의 경우 자르지 않음 (태그 보존)
            if "[IMAGE_BASE64]" not in content and len(content) > 5000:
                content = content[:5000] + "...(내용 생략)"
            
            # 파일 내용을 임시 저장
            self.uploaded_file_content = content
            self.uploaded_file_name = os.path.basename(file_path)
            print(f"[디버그] 업로드된 파일 내용 길이: {len(content)}")
            if "[IMAGE_BASE64]" in content:
                print(f"[디버그] 이미지 데이터 포함 확인")
                print(f"[디버그] 종료 태그 위치: {content.rfind('[/IMAGE_BASE64]')}")
            
            # 사용자에게 프롬프트 입력 안내
            self.append_chat('시스템', f'파일이 업로드되었습니다. 이제 파일에 대해 무엇을 알고 싶은지 메시지를 입력해주세요.')
            self.input_text.setPlaceholderText(f"{self.uploaded_file_name}에 대해 무엇을 알고 싶으신가요?")
            
        except Exception as e:
            self.append_chat('시스템', f'파일 처리 오류: {e}')
            # 오류 시 파일 내용 초기화
            self.uploaded_file_content = None
            self.uploaded_file_name = None
            self.input_text.setPlaceholderText("메시지를 입력하세요... (Ctrl+Enter로 전송)")

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
    
    def on_ai_response(self, sender, text, used_tools):
        # 응답 시간 계산
        response_time = ""
        if self.request_start_time:
            from datetime import datetime
            elapsed = datetime.now() - self.request_start_time
            response_time = f" (응답시간: {elapsed.total_seconds():.1f}초)"
        
        # 도구 사용 시 이모티콘 추가
        tool_emoji = self._get_tool_emoji(used_tools)
        if tool_emoji:
            sender = f"{sender} {tool_emoji}"
        
        # 테이블 감지 - 응답시간을 테이블과 분리
        if '|' in text and ('---' in text or text.count('|') > 4):
            # 테이블이 포함된 경우 응답시간을 별도로 표시
            self.start_optimized_typing(sender, text)
            if response_time:
                self.append_chat('시스템', f'처리 완료{response_time}')
        else:
            # 일반 텍스트는 기존 방식
            self.start_optimized_typing(sender, text + response_time)
        
        # 히스토리에 AI 응답 추가
        self.conversation_history.add_message('assistant', text)
        self.conversation_history.save_to_file()
        print(f"[디버그] AI 응답 히스토리에 저장됨: {text[:50]}...")
        
        self.messages.append({'role': 'assistant', 'content': text})
        self.set_ui_enabled(True)
        self.show_loading(False)
    
    def _get_tool_emoji(self, used_tools):
        """사용된 도구에 따라 이모티콘 반환 (동적 매핑)"""
        if not used_tools:
            return ""
        
        # 도구 이름 키워드 기반 이모티콘 매핑
        emoji_map = {
            'search': '🔍',
            'web': '🌐', 
            'url': '🌐',
            'fetch': '📄',
            'database': '🗄️',
            'mysql': '🗄️',
            'sql': '🗄️',
            'travel': '✈️',
            'tour': '✈️',
            'hotel': '🏨',
            'flight': '✈️',
            'map': '🗺️',
            'location': '📍',
            'geocode': '📍',
            'weather': '🌤️',
            'email': '📧',
            'file': '📁',
            'excel': '📊',
            'chart': '📈',
            'image': '🖼️',
            'translate': '🌐',
            'api': '🔧'
        }
        
        # 첫 번째 도구의 이름에서 키워드 찾기
        tool_name = str(used_tools[0]).lower() if used_tools else ""
        
        for keyword, emoji in emoji_map.items():
            if keyword in tool_name:
                return emoji
        
        # 매핑되지 않은 도구의 기본 이모티콘
        return "⚡"

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
            bg_color = 'rgba(163,135,215,0.15)'
            border_color = 'rgb(163,135,215)'
            text_color = '#ffffff'
            icon = '💬'
            sender_color = 'rgb(163,135,215)'
        elif sender in ['AI', '에이전트'] or '에이전트' in sender:
            bg_color = 'rgba(135,163,215,0.15)'
            border_color = 'rgb(135,163,215)'
            text_color = '#ffffff'
            icon = '🤖'
            sender_color = 'rgb(135,163,215)'
        else:
            bg_color = 'rgba(215,163,135,0.15)'
            border_color = 'rgb(215,163,135)'
            text_color = '#ffffff'
            icon = '⚙️'
            sender_color = 'rgb(215,163,135)'
        
        formatted_text = self.format_text(text)
        
        html_message = f"""
        <div style="
            margin: 12px 0;
            padding: 16px;
            background: linear-gradient(135deg, {bg_color}33, {bg_color}11);
            border-radius: 12px;
            border-left: 4px solid {border_color};
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        ">
            <div style="
                margin: 0 0 12px 0;
                font-weight: 700;
                color: {sender_color};
                font-size: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">
                <span style="font-size: 16px;">{icon}</span>
                <span>{sender}</span>
            </div>
            <div style="
                margin: 0;
                padding-left: 24px;
                line-height: 1.6;
                color: {text_color};
                font-size: 13px;
                word-wrap: break-word;
                font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
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
        """텍스트 포맷팅 - HTML 파일 기준"""
        import re
        
        # 코드 블록 처리
        def format_code_block(match):
            import uuid
            lang = match.group(1).strip() if match.group(1) else 'code'
            code = match.group(2)
            code_id = f"code_{uuid.uuid4().hex[:8]}"
            
            # 들여쓰기 정리
            lines = code.split('\n')
            if lines and lines[0].strip() == '':
                lines = lines[1:]
            if lines and lines[-1].strip() == '':
                lines = lines[:-1]
            
            if lines:
                min_indent = float('inf')
                for line in lines:
                    if line.strip():
                        indent = len(line) - len(line.lstrip())
                        min_indent = min(min_indent, indent)
                
                if min_indent != float('inf') and min_indent > 0:
                    lines = [line[min_indent:] if len(line) > min_indent else line for line in lines]
                
                code = '\n'.join(lines)
            
            return f'<div style="background-color: #1e1e1e; border: 1px solid #444444; border-radius: 6px; margin: 12px 0; overflow: hidden;"><div style="background-color: #2d2d2d; padding: 6px 12px; font-size: 11px; color: #888888; border-bottom: 1px solid #444444; display: flex; justify-content: space-between; align-items: center;"><span>{lang}</span><button onclick="copyCode(\'{code_id}\')" style="background: #444; border: none; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 10px; cursor: pointer; opacity: 0.7; transition: opacity 0.2s;" onmouseover="this.style.opacity=\'1\'" onmouseout="this.style.opacity=\'0.7\'">복사</button></div><pre id="{code_id}" style="background: none; color: #f8f8f2; padding: 16px; margin: 0; font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.4; overflow-x: auto; white-space: pre;">{code}</pre></div>'
        
        # 코드 블록 처리 (복사 버튼 포함)
        text = re.sub(r'```([^\n]*)\n([\s\S]*?)```', format_code_block, text)
        
        # 헤딩 처리
        text = re.sub(r'^# (.*?)$', r'<h1 style="color: #ffffff; margin: 20px 0 10px 0; font-size: 20px; font-weight: 600;">\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2 style="color: #eeeeee; margin: 16px 0 8px 0; font-size: 18px; font-weight: 600;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.*?)$', r'<h3 style="color: #dddddd; margin: 14px 0 7px 0; font-size: 16px; font-weight: 600;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^#### (.*?)$', r'<h4 style="color: #cccccc; margin: 12px 0 6px 0; font-size: 14px; font-weight: 600;">\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^##### (.*?)$', r'<h5 style="color: #bbbbbb; margin: 10px 0 5px 0; font-size: 13px; font-weight: 600;">\1</h5>', text, flags=re.MULTILINE)
        text = re.sub(r'^###### (.*?)$', r'<h6 style="color: #aaaaaa; margin: 8px 0 4px 0; font-size: 12px; font-weight: 600;">\1</h6>', text, flags=re.MULTILINE)
        
        # 굵은 글씨
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff; font-weight: 600;">\1</strong>', text)
        
        # 번호 목록
        text = re.sub(r'^(\d+)\. (.*?)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #aaaaaa; margin-right: 6px;">\1.</span>\2</div>', text, flags=re.MULTILINE)
        
        # 불릿 포인트
        text = re.sub(r'^[•\-\*] (.*?)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #aaaaaa; margin-right: 6px;">•</span>\1</div>', text, flags=re.MULTILINE)
        
        # 인라인 코드
        text = re.sub(r'`([^`]+)`', r'<code style="background-color: #2d2d2d; color: #f8f8f2; padding: 3px 6px; border-radius: 4px; font-family: Consolas, Monaco, monospace; font-size: 13px; border: 1px solid #444444;">\1</code>', text)
        
        # 링크
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #bbbbbb; text-decoration: underline;" target="_blank">\1</a>', text)
        
        # 테이블 처리
        def format_table(table_text):
            lines = table_text.strip().split('\n')
            table_lines = [line for line in lines if '|' in line and line.strip()]
            
            if len(table_lines) < 2:
                return table_text
            
            # 테이블 HTML 생성
            html = '<table style="border-collapse: collapse; width: 100%; margin: 12px 0; background-color: #2a2a2a; border-radius: 6px; overflow: hidden;">'
            
            # 최대 열 수 계산
            max_cols = max(len([cell.strip() for cell in line.split('|') if cell.strip()]) for line in table_lines if '---' not in line and '===' not in line)
            
            for i, line in enumerate(table_lines):
                # 구분선 건너뛰기
                if '---' in line or '===' in line:
                    continue
                    
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if not cells:
                    continue
                
                # 헤더 행 처리
                if i == 0:
                    html += '<tr style="background-color: #3a3a3a;">'
                    for j, cell in enumerate(cells):
                        # 빈 셀이면 colspan 적용
                        if not cell and j > 0:
                            continue
                        colspan = 1
                        # 다음 셀들이 비어있으면 colspan 증가
                        for k in range(j + 1, len(cells)):
                            if not cells[k]:
                                colspan += 1
                            else:
                                break
                        # 마지막 열까지 확장
                        if j + colspan < max_cols:
                            remaining = max_cols - (j + colspan)
                            if remaining > 0 and all(not cells[l] if l < len(cells) else True for l in range(j + colspan, min(len(cells), max_cols))):
                                colspan += remaining
                        
                        html += f'<th style="padding: 12px; border: 1px solid #555; color: #ffffff; font-weight: 600; text-align: left;" colspan="{colspan}">{cell}</th>'
                    html += '</tr>'
                else:
                    html += '<tr style="background-color: #2a2a2a;">'
                    for j, cell in enumerate(cells):
                        # 빈 셀이면 colspan 적용
                        if not cell and j > 0:
                            continue
                        colspan = 1
                        # 다음 셀들이 비어있으면 colspan 증가
                        for k in range(j + 1, len(cells)):
                            if not cells[k]:
                                colspan += 1
                            else:
                                break
                        
                        html += f'<td style="padding: 10px; border: 1px solid #555; color: #cccccc;" colspan="{colspan}">{cell}</td>'
                    html += '</tr>'
            
            html += '</table>'
            return html
        
        # 테이블 감지 및 처리
        if '|' in text and ('---' in text or text.count('|') > 4):
            text = format_table(text)
            return text
        
        # 일반 텍스트 줄바꿈 처리
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('<br>')
            elif line.startswith('<'):
                formatted_lines.append(line)
            else:
                formatted_lines.append(f'<div style="margin: 2px 0; line-height: 1.4; color: #cccccc;">{line}</div>')
        
        return '\n'.join(formatted_lines)
    
    def scroll_to_bottom(self):
        """스크롤을 맨 아래로"""
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def _on_webview_loaded(self, ok):
        """웹뷰 로드 완료 후 이전 대화 로드"""
        if ok:
            QTimer.singleShot(500, self._load_previous_conversations)
    
    def _load_previous_conversations(self):
        """이전 대화 내용 10개 로드"""
        try:
            print(f"[디버그] 히스토리 로드 시도 - 전체 메시지: {len(self.conversation_history.current_session)}개")
            recent_messages = self.conversation_history.get_recent_messages(10)
            print(f"[디버그] 최근 메시지 가져오기: {len(recent_messages) if recent_messages else 0}개")
            
            if recent_messages:
                for i, msg in enumerate(recent_messages):
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    print(f"[디버그] 메시지 {i}: role={role}, content={content[:50]}...")
                    
                    if role == 'user' and content.strip():
                        self.append_chat('사용자', content)
                    elif role == 'assistant' and content.strip():
                        self.append_chat('AI', content)
                
                print(f"[디버그] 이전 대화 {len(recent_messages)}개 로드 완료")
            else:
                print(f"[디버그] 로드할 이전 대화 없음")
        except Exception as e:
            print(f"[디버그] 이전 대화 로드 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_conversation_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history.clear_session()
        self.conversation_history.save_to_file()
        self.messages = []
        print("[디버그] 대화 히스토리가 초기화되었습니다.")
        
        # 웹뷰도 초기화
        self.init_web_view()
    
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
        
        # 타이머 정지
        if hasattr(self, 'tools_update_timer'):
            self.tools_update_timer.stop()