from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QFileDialog, QMessageBox
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer
from ui.chat_widget import ChatWidget
from ui.settings_dialog import SettingsDialog
from ui.mcp_dialog import MCPDialog
from ui.mcp_manager_simple import MCPManagerDialog
from mcp.servers.mcp import start_mcp_servers, stop_mcp_servers
from ui.components.status_display import status_display
import os
import json
import threading

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()
        self._initialize_mcp()
        print("MainWindow 초기화 완료")
    
    def _setup_window(self) -> None:
        """Setup main window properties."""
        self.setWindowTitle('AI 데스크탑 채팅')
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet(self._get_dark_theme())
    
    def _setup_ui(self) -> None:
        """Setup UI components."""
        # Central widget
        central_widget = QWidget(self)
        central_widget.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Chat widget
        self.chat_widget = ChatWidget(self)
        layout.addWidget(self.chat_widget)
        self.setCentralWidget(central_widget)
        
        # 상태 표시 초기화
        status_display.status_updated.emit(status_display.current_status.copy())
        
        # Menu
        self._create_menu_bar()
    
    def _get_dark_theme(self) -> str:
        """Get dark theme stylesheet."""
        return """
            QMainWindow {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #2a2a2a;
                color: #ffffff;
                border-bottom: 1px solid #444444;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #444444;
            }
            QMenu {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #444444;
            }
            QMenu::item:selected {
                background-color: #444444;
            }
        """
    
    def _create_menu_bar(self) -> None:
        """Create the main menu bar."""
        menubar = self.menuBar()
        settings_menu = menubar.addMenu('설정')
        
        # Environment settings
        settings_action = QAction('환경설정', self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)
        
        # MCP actions
        mcp_action = QAction('MCP 확장 임포트', self)
        mcp_action.triggered.connect(self.open_mcp)
        settings_menu.addAction(mcp_action)
        
        mcp_manager_action = QAction('MCP 서버 관리', self)
        mcp_manager_action.triggered.connect(self.open_mcp_manager)
        settings_menu.addAction(mcp_manager_action)
        
        settings_menu.addSeparator()
        
        # History and prompt actions
        clear_history_action = QAction('대화 기록 초기화', self)
        clear_history_action.triggered.connect(self.clear_conversation_history)
        settings_menu.addAction(clear_history_action)
        
        user_prompt_action = QAction('유저 프롬프트 설정', self)
        user_prompt_action.triggered.connect(self.open_user_prompt)
        settings_menu.addAction(user_prompt_action)
    
    def _initialize_mcp(self) -> None:
        """Initialize MCP servers."""
        # MCP 서버 시작 지연 시간을 약간 늘림
        QTimer.singleShot(200, self._init_mcp_servers)

    def _init_mcp_servers(self) -> None:
        """MCP 서버 상태 파일을 읽어서 활성화된 서버만 시작"""
        def start_servers():
            try:
                state_file = 'mcp_server_state.json'
                if os.path.exists(state_file):
                    with open(state_file, 'r', encoding='utf-8') as f:
                        server_states = json.load(f)
                    
                    enabled_servers = [name for name, enabled in server_states.items() if enabled]
                    if enabled_servers:
                        print(f"활성화된 MCP 서버 시작: {enabled_servers}")
                        start_mcp_servers()
                        # MCP 서버 시작 후 충분한 시간을 두고 도구 라벨 업데이트
                        QTimer.singleShot(1500, self._update_tools_with_retry)
                    else:
                        print("활성화된 MCP 서버가 없습니다")
                        # 서버가 없을 때도 라벨 업데이트
                        QTimer.singleShot(500, self.chat_widget.model_manager.update_tools_label)
                else:
                    print("MCP 서버 상태 파일이 없습니다")
            except Exception as e:
                print(f"MCP 서버 시작 오류: {e}")
        
        threading.Thread(target=start_servers, daemon=True).start()
    
    def _update_tools_with_retry(self) -> None:
        """도구 업데이트를 재시도와 함께 수행"""
        def update_with_retry(attempt=1, max_attempts=3):
            try:
                self.chat_widget.model_manager.update_tools_label()
                print(f"도구 라벨 업데이트 성공 (시도 {attempt})")
            except Exception as e:
                print(f"도구 라벨 업데이트 실패 (시도 {attempt}): {e}")
                if attempt < max_attempts:
                    QTimer.singleShot(800, lambda: update_with_retry(attempt + 1, max_attempts))
        
        update_with_retry()
    
    def open_settings(self) -> None:
        """Open settings dialog."""
        dlg = SettingsDialog(self)
        dlg.exec()
        self.chat_widget.model_manager.update_model_label()
        self.chat_widget.model_manager.update_tools_label()
    
    def open_mcp(self) -> None:
        """Open MCP import dialog."""
        mcp_path, _ = QFileDialog.getOpenFileName(
            self, 'mcp.json 선택', '', 'JSON 파일 (*.json)'
        )
        if not mcp_path:
            return
        
        try:
            with open('mcp.json', 'w', encoding='utf-8') as f:
                with open(mcp_path, 'r', encoding='utf-8') as src:
                    f.write(src.read())
            dlg = MCPDialog('mcp.json', self)
            dlg.exec()
        except Exception as e:
            print(f"MCP 파일 처리 오류: {e}")
    
    def open_mcp_manager(self) -> None:
        """Open MCP manager dialog."""
        dlg = MCPManagerDialog(self)
        dlg.exec()
        self.chat_widget.model_manager.update_tools_label()
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history with confirmation."""
        reply = QMessageBox.question(
            self, '대화 기록 초기화', 
            '모든 대화 기록을 삭제하시겠습니까?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.chat_widget.clear_conversation_history()
    
    def open_user_prompt(self) -> None:
        """Open user prompt dialog."""
        from ui.user_prompt_dialog import UserPromptDialog
        from core.file_utils import load_model_api_key, load_last_model
        from core.ai_client import AIClient
        
        model = load_last_model()
        api_key = load_model_api_key(model)
        
        if not api_key:
            QMessageBox.warning(
                self, '경고', 
                'API 키가 설정되지 않았습니다. 먼저 환경설정에서 API 키를 입력해주세요.'
            )
            return
        
        ai_client = AIClient(api_key, model)
        dlg = UserPromptDialog(ai_client, self)
        dlg.exec()
    
    def closeEvent(self, event):
        """애플리케이션 종료 처리"""
        print("애플리케이션 종료 시작")
        
        try:
            if hasattr(self, 'chat_widget'):
                self.chat_widget.close()
            stop_mcp_servers()
        except Exception as e:
            print(f"종료 중 오류: {e}")
        
        event.accept()
        print("애플리케이션 종료 완료") 