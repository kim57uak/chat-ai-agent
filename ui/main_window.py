from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMenuBar, QFileDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer
from ui.chat_widget import ChatWidget
from ui.settings_dialog import SettingsDialog
from ui.mcp_dialog import MCPDialog
from ui.mcp_manager_simple import MCPManagerDialog
from mcp.servers.mcp import start_mcp_servers, stop_mcp_servers
from core.ai_client import get_mcp_client
import os

MCP_JSON_PATH = 'mcp.json'  # 임시: 최근 임포트된 mcp.json 경로 저장

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('AI 데스크탑 채팅')
        self.setGeometry(100, 100, 900, 700)
        
        # 어두운 배경 테마 적용
        self.setStyleSheet("""
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
        """)

        # 채팅 위젯 중앙에 배치
        central_widget = QWidget(self)
        central_widget.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.chat_widget = ChatWidget(self)
        layout.addWidget(self.chat_widget)
        self.setCentralWidget(central_widget)

        # 메뉴바 - 환경설정, MCP 확장
        menubar = self.menuBar()
        settings_menu = menubar.addMenu('설정')
        settings_action = QAction('환경설정', self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)

        mcp_action = QAction('MCP 확장 임포트', self)
        mcp_action.triggered.connect(self.open_mcp)
        settings_menu.addAction(mcp_action)
        
        mcp_manager_action = QAction('MCP 서버 관리', self)
        mcp_manager_action.triggered.connect(self.open_mcp_manager)
        settings_menu.addAction(mcp_manager_action)
        
        settings_menu.addSeparator()
        
        clear_history_action = QAction('대화 기록 초기화', self)
        clear_history_action.triggered.connect(self.clear_conversation_history)
        settings_menu.addAction(clear_history_action)
        
        user_prompt_action = QAction('유저 프롬프트 설정', self)
        user_prompt_action.triggered.connect(self.open_user_prompt)
        settings_menu.addAction(user_prompt_action)

        # MCP 서버 비동기 초기화
        QTimer.singleShot(100, self.init_mcp_servers)
        print("MainWindow 초기화 완료")

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
    
    def init_mcp_servers(self):
        """MCP 서버 상태 파일을 읽어서 활성화된 서버만 시작"""
        try:
            import json
            import threading
            
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
                            # 서버 시작 후 도구 라벨 업데이트
                            QTimer.singleShot(1000, self.chat_widget.update_tools_label)
                        else:
                            print("활성화된 MCP 서버가 없습니다")
                    else:
                        print("MCP 서버 상태 파일이 없습니다")
                except Exception as e:
                    print(f"MCP 서버 시작 오류: {e}")
            
            # 별도 스레드에서 실행
            threading.Thread(target=start_servers, daemon=True).start()
                
        except Exception as e:
            print(f"MCP 서버 초기화 오류: {e}")

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()
        self.chat_widget.update_model_label()
        self.chat_widget.update_tools_label()

    def open_mcp(self):
        mcp_path, _ = QFileDialog.getOpenFileName(self, 'mcp.json 선택', '', 'JSON 파일 (*.json)')
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
    
    def open_mcp_manager(self):
        dlg = MCPManagerDialog(self)
        dlg.exec()
        self.chat_widget.update_tools_label()
    
    def clear_conversation_history(self):
        """대화 기록 초기화"""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, '대화 기록 초기화', 
            '모든 대화 기록을 삭제하시겠습니까?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.chat_widget.clear_conversation_history()
    
    def open_user_prompt(self):
        """유저 프롬프트 설정 대화상자 열기"""
        from ui.user_prompt_dialog import UserPromptDialog
        from core.file_utils import load_model_api_key, load_last_model
        from core.ai_client import AIClient
        
        # 현재 모델에 맞는 AI 클라이언트 생성
        model = load_last_model()
        api_key = load_model_api_key(model)
        
        if not api_key:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, '경고', 'API 키가 설정되지 않았습니다. 먼저 환경설정에서 API 키를 입력해주세요.')
            return
        
        ai_client = AIClient(api_key, model)
        dlg = UserPromptDialog(ai_client, self)
        dlg.exec() 