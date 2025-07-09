from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QLabel, QTextEdit, 
                             QSplitter, QGroupBox, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from core.mcp import get_mcp_servers, restart_mcp_server, stop_mcp_server, start_mcp_server
from core.mcp_client import mcp_manager
from core.mcp_state import mcp_state
import logging

logger = logging.getLogger(__name__)

class MCPWorker(QObject):
    finished = pyqtSignal(str, bool)  # server_name, success
    error = pyqtSignal(str)

    def __init__(self, action, server_name):
        super().__init__()
        self.action = action
        self.server_name = server_name

    def run(self):
        try:
            if self.action == 'start':
                success = start_mcp_server(self.server_name)
            elif self.action == 'stop':
                success = stop_mcp_server(self.server_name)
            elif self.action == 'restart':
                success = restart_mcp_server(self.server_name)
            else:
                success = False
            
            self.finished.emit(self.server_name, success)
        except Exception as e:
            self.error.emit(f'{self.action} 오류: {e}')

class MCPManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('MCP 서버 관리')
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QListWidget {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333333;
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background-color: #4FC3F7;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QPushButton {
                background-color: #4FC3F7;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
                min-height: 30px;
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
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 8px;
                font-family: 'SF Mono', 'Monaco', monospace;
                font-size: 12px;
                color: #e8e8e8;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #666666;
                border-radius: 3px;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background-color: #4FC3F7;
                border-color: #4FC3F7;
            }
        """)
        
        self.setup_ui()
        self.refresh_servers()
        
        self.thread = None
        self.worker = None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 제목
        title_label = QLabel('MCP 서버 관리')
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 메인 스플리터
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # 왼쪽: 서버 목록
        left_group = QGroupBox('서버 목록')
        left_layout = QVBoxLayout(left_group)
        
        self.server_list = QListWidget()
        self.server_list.itemSelectionChanged.connect(self.on_server_selected)
        left_layout.addWidget(self.server_list)
        
        # 서버 제어 버튼들
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton('시작')
        self.start_button.clicked.connect(self.start_server)
        self.start_button.setStyleSheet("QPushButton { background-color: #66BB6A; }")
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton('중지')
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setStyleSheet("QPushButton { background-color: #F44336; }")
        button_layout.addWidget(self.stop_button)
        
        self.restart_button = QPushButton('재시작')
        self.restart_button.clicked.connect(self.restart_server)
        self.restart_button.setStyleSheet("QPushButton { background-color: #FF9800; }")
        button_layout.addWidget(self.restart_button)
        
        left_layout.addLayout(button_layout)
        
        # 새로고침 버튼
        self.refresh_button = QPushButton('새로고침')
        self.refresh_button.clicked.connect(self.refresh_servers)
        left_layout.addWidget(self.refresh_button)
        
        splitter.addWidget(left_group)
        
        # 오른쪽: 서버 정보 및 도구 목록
        right_group = QGroupBox('서버 정보')
        right_layout = QVBoxLayout(right_group)
        
        # 서버 상태
        self.status_label = QLabel('서버를 선택하세요')
        self.status_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        right_layout.addWidget(self.status_label)
        
        # 도구 목록
        tools_label = QLabel('사용 가능한 도구:')
        right_layout.addWidget(tools_label)
        
        self.tools_text = QTextEdit()
        self.tools_text.setReadOnly(True)
        self.tools_text.setMaximumHeight(200)
        right_layout.addWidget(self.tools_text)
        
        # 서버 설정 정보
        config_label = QLabel('서버 설정:')
        right_layout.addWidget(config_label)
        
        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        right_layout.addWidget(self.config_text)
        
        splitter.addWidget(right_group)
        
        # 스플리터 비율 설정
        splitter.setSizes([300, 500])
        
        # 하단 버튼들
        bottom_layout = QHBoxLayout()
        
        self.auto_start_checkbox = QCheckBox('프로그램 시작 시 자동으로 MCP 서버 시작')
        self.auto_start_checkbox.setChecked(True)
        bottom_layout.addWidget(self.auto_start_checkbox)
        
        bottom_layout.addStretch()
        
        close_button = QPushButton('닫기')
        close_button.clicked.connect(self.accept)
        bottom_layout.addWidget(close_button)
        
        layout.addLayout(bottom_layout)

    def refresh_servers(self):
        """서버 목록 새로고침 (빠른 버전)"""
        self.server_list.clear()
        
        try:
            servers = get_mcp_servers()
            for server_name, server_info in servers.items():
                item = QListWidgetItem(server_name)
                
                # 서버 상태에 따라 아이콘 설정
                status = server_info.get('status', 'unknown')
                enabled = mcp_state.is_server_enabled(server_name)
                
                if status == 'running' and enabled:
                    item.setText(f"🟢 {server_name}")
                elif status == 'stopped' or not enabled:
                    item.setText(f"🔴 {server_name} {'(비활성화됨)' if not enabled else ''}")
                else:
                    item.setText(f"⚪ {server_name}")
                
                item.setData(Qt.ItemDataRole.UserRole, server_info)
                self.server_list.addItem(item)
                
        except Exception as e:
            logger.error(f"서버 목록 새로고침 오류: {e}")
            QMessageBox.warning(self, '오류', f'서버 목록을 가져올 수 없습니다: {e}')

    def on_server_selected(self):
        """서버 선택 시 정보 표시"""
        current_item = self.server_list.currentItem()
        if not current_item:
            return
        
        server_info = current_item.data(Qt.ItemDataRole.UserRole)
        server_name = current_item.text().replace('🟢 ', '').replace('🔴 ', '').replace('⚪ ', '')
        
        # 상태 표시
        status = server_info.get('status', 'unknown')
        enabled = mcp_state.is_server_enabled(server_name)
        
        if status == 'running' and enabled:
            self.status_label.setText(f'🟢 {server_name} - 실행 중')
            self.status_label.setStyleSheet("color: #66BB6A;")
        elif status == 'stopped' or not enabled:
            status_text = '중지됨'
            if not enabled:
                status_text += ' (사용자가 비활성화함)'
            self.status_label.setText(f'🔴 {server_name} - {status_text}')
            self.status_label.setStyleSheet("color: #F44336;")
        else:
            self.status_label.setText(f'⚪ {server_name} - 상태 불명')
            self.status_label.setStyleSheet("color: #FFA726;")
        
        # 도구 목록 표시
        tools = server_info.get('tools', [])
        if tools:
            tools_text = []
            for tool in tools:
                tool_name = tool.get('name', 'Unknown')
                tool_desc = tool.get('description', 'No description')
                tools_text.append(f"• {tool_name}: {tool_desc}")
            self.tools_text.setText('\\n'.join(tools_text))
        else:
            self.tools_text.setText('도구 정보를 가져올 수 없습니다.')
        
        # 설정 정보 표시
        config_info = []
        config_info.append(f"명령어: {server_info.get('command', 'N/A')}")
        config_info.append(f"인수: {' '.join(server_info.get('args', []))}")
        config_info.append(f"자동 시작: {'예' if enabled else '아니오'}")
        
        env = server_info.get('env', {})
        if env:
            config_info.append("환경변수:")
            for key, value in env.items():
                config_info.append(f"  {key}: {value}")
        
        self.config_text.setText('\\n'.join(config_info))

    def start_server(self):
        """서버 시작"""
        self._execute_server_action('start')

    def stop_server(self):
        """서버 중지"""
        self._execute_server_action('stop')

    def restart_server(self):
        """서버 재시작"""
        self._execute_server_action('restart')

    def _execute_server_action(self, action):
        """서버 액션 실행"""
        current_item = self.server_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, '경고', '서버를 선택해주세요.')
            return
        
        server_name = current_item.text().replace('🟢 ', '').replace('🔴 ', '').replace('⚪ ', '').replace('(비활성화됨)', '').strip()
        
        # 상태 메시지 표시
        action_text = {'start': '시작', 'stop': '중지', 'restart': '재시작'}[action]
        self.status_label.setText(f'⏳ {server_name} - {action_text} 중...')
        self.status_label.setStyleSheet("color: #FFA726;")
        
        # 버튼 비활성화
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.restart_button.setEnabled(False)
        
        # 워커 스레드 시작
        self.thread = QThread()
        self.worker = MCPWorker(action, server_name)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_action_finished)
        self.worker.error.connect(self.on_action_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()

    def on_action_finished(self, server_name, success):
        """액션 완료 처리"""
        # 버튼 다시 활성화
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.restart_button.setEnabled(True)
        
        # 서버 목록 새로고침 (먼저 수행)
        self.refresh_servers()
        
        # 결과 메시지 (비블록킹)
        if success:
            action_msg = {
                'start': '시작되었습니다',
                'stop': '중지되었습니다', 
                'restart': '재시작되었습니다'
            }
            current_action = getattr(self.worker, 'action', 'unknown')
            msg = action_msg.get(current_action, '작업이 완료되었습니다')
            self.status_label.setText(f'✅ {server_name} - {msg}')
            self.status_label.setStyleSheet("color: #66BB6A;")
        else:
            self.status_label.setText(f'❌ {server_name} - 작업 실패')
            self.status_label.setStyleSheet("color: #F44336;")

    def on_action_error(self, error_msg):
        """액션 오류 처리"""
        # 버튼 다시 활성화
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.restart_button.setEnabled(True)
        
        # 오류 상태 표시
        self.status_label.setText(f'❌ 오류: {error_msg[:50]}...')
        self.status_label.setStyleSheet("color: #F44336;")
        
        # 서버 목록 새로고침
        self.refresh_servers()

    def closeEvent(self, event):
        """다이얼로그 닫기 시 스레드 정리"""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        event.accept()