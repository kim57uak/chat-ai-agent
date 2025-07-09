from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMenuBar, QFileDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer
from ui.chat_widget import ChatWidget
from ui.settings_dialog import SettingsDialog
from ui.mcp_dialog import MCPDialog
from ui.mcp_manager_dialog import MCPManagerDialog
from core.mcp import start_mcp_servers, stop_mcp_servers
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

        # 채팅창 오픈 시 MCP 서버 자동 기동
        if os.path.exists(MCP_JSON_PATH):
            try:
                start_mcp_servers(MCP_JSON_PATH)
                print(f"MCP 서버 시작: {MCP_JSON_PATH}")
            except Exception as e:
                print(f"MCP 서버 시작 실패: {e}")

    def closeEvent(self, event):
        """애플리케이션 종료 처리 - 안전한 비동기 종료"""
        print("애플리케이션 종료 시작")
        
        # 즉시 이벤트 수락하고 비동기로 종료 처리
        event.accept()
        
        # 비동기로 종료 작업 시작
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._perform_cleanup)
    
    def _perform_cleanup(self):
        """실제 정리 작업 수행"""
        try:
            # 1. 채팅 위젯 종룄 신호
            if hasattr(self, 'chat_widget') and self.chat_widget:
                self.chat_widget.close()
                print("채팅 위젯 종룄 신호 전송")
        except Exception as e:
            print(f"채팅 위젯 종룄 오류: {e}")
        
        try:
            # 2. MCP 서버 종료
            stop_mcp_servers()
            print("MCP 서버 종료 완료")
        except Exception as e:
            print(f"MCP 서버 종료 오류: {e}")
        
        # 3. 지연된 종룄
        QTimer.singleShot(1000, self._final_exit)
    
    def _final_exit(self):
        """최종 종룄"""
        try:
            from PyQt6.QtCore import QThreadPool
            QThreadPool.globalInstance().waitForDone(1000)
            print("애플리케이션 정리 완료")
        except Exception as e:
            print(f"최종 정리 오류: {e}")
        
        # 강제 종룄
        import sys
        sys.exit(0)

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()
        self.chat_widget.update_model_label()

    def open_mcp(self):
        mcp_path, _ = QFileDialog.getOpenFileName(self, 'mcp.json 선택', '', 'JSON 파일 (*.json)')
        if not mcp_path:
            return
        # 임포트된 mcp.json 경로를 임시 저장
        with open('mcp.json', 'w', encoding='utf-8') as f:
            with open(mcp_path, 'r', encoding='utf-8') as src:
                f.write(src.read())
        try:
            start_mcp_servers('mcp.json')
            print("MCP 서버 재시작 완료")
        except Exception as e:
            print(f"MCP 서버 재시작 실패: {e}")
        dlg = MCPDialog('mcp.json', self)
        dlg.exec()
    
    def open_mcp_manager(self):
        dlg = MCPManagerDialog(self)
        dlg.exec()
    
    def clear_conversation_history(self):
        """대화 기록 초기화"""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, 
            '대화 기록 초기화', 
            '모든 대화 기록을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.chat_widget.conversation_history.clear_session()
            self.chat_widget.conversation_history.save_to_file()
            self.chat_widget.chat_display.clear()
            
            # 시스템 메시지 표시
            self.chat_widget.append_chat('시스템', '대화 기록이 초기화되었습니다.')
    
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