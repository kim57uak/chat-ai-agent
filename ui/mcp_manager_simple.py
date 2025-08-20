from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QTextEdit,
    QSplitter,
    QGroupBox,
    QCheckBox,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import logging
import json
import time
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from mcp.servers.mcp import (
        get_mcp_servers,
        restart_mcp_server,
        stop_mcp_server,
        start_mcp_server,
    )
    from mcp.client.mcp_state import mcp_state

    MCP_AVAILABLE = True
except ImportError:
    from mcp.client.mcp_simple import (
        get_mcp_servers,
        restart_mcp_server,
        stop_mcp_server,
        start_mcp_server,
    )
    from mcp.client.mcp_state_simple import mcp_state

    MCP_AVAILABLE = False


class MCPManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MCP 서버 관리")
        self.setGeometry(200, 200, 900, 700)

        # 상태 변수
        self.current_servers = {}
        self.refresh_timer = QTimer()
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self._do_refresh)

        self.setStyleSheet(self._get_dialog_style())

        self.setup_ui()
        # 초기 로딩
        QTimer.singleShot(500, self.refresh_servers)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 제목
        title_label = QLabel("MCP 서버 관리")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: 800;
                font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                padding: 15px 0;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 메인 스플리터
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # 왼쪽: 서버 목록
        left_group = QGroupBox("서버 목록")
        left_layout = QVBoxLayout(left_group)

        self.server_list = QListWidget()
        self.server_list.itemSelectionChanged.connect(self.on_server_selected)
        left_layout.addWidget(self.server_list)

        # 서버 제어 버튼들
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("시작")
        self.start_button.clicked.connect(self.start_server)
        self.start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(150, 255, 150, 0.8), 
                    stop:1 rgba(100, 255, 200, 0.8));
                color: #ffffff;
                border: 2px solid rgba(150, 255, 150, 0.4);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(170, 255, 170, 0.9), 
                    stop:1 rgba(120, 255, 220, 0.9));
                border-color: rgba(150, 255, 150, 0.6);
            }
        """)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(255, 100, 100, 0.8), 
                    stop:1 rgba(255, 150, 100, 0.8));
                color: #ffffff;
                border: 2px solid rgba(255, 100, 100, 0.4);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(255, 120, 120, 0.9), 
                    stop:1 rgba(255, 170, 120, 0.9));
                border-color: rgba(255, 100, 100, 0.6);
            }
        """)
        button_layout.addWidget(self.stop_button)

        self.restart_button = QPushButton("재시작")
        self.restart_button.clicked.connect(self.restart_server)
        self.restart_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(255, 200, 100, 0.8), 
                    stop:1 rgba(255, 150, 200, 0.8));
                color: #ffffff;
                border: 2px solid rgba(255, 200, 100, 0.4);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(255, 220, 120, 0.9), 
                    stop:1 rgba(255, 170, 220, 0.9));
                border-color: rgba(255, 200, 100, 0.6);
            }
        """)
        button_layout.addWidget(self.restart_button)

        left_layout.addLayout(button_layout)

        # 새로고침 버튼
        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.clicked.connect(self.refresh_servers)
        left_layout.addWidget(self.refresh_button)

        splitter.addWidget(left_group)

        # 오른쪽: 서버 정보
        right_group = QGroupBox("서버 정보")
        right_layout = QVBoxLayout(right_group)

        # 서버 상태
        self.status_label = QLabel("서버를 선택하세요")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 700;
                font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                padding: 8px 0;
            }
        """)
        right_layout.addWidget(self.status_label)

        # 도구 목록
        tools_label = QLabel("사용 가능한 도구:")
        tools_label.setStyleSheet("""
            QLabel {
                color: #b0e0b0;
                font-size: 15px;
                font-weight: 700;
                padding: 8px 0;
            }
        """)
        right_layout.addWidget(tools_label)

        self.tools_text = QTextEdit()
        self.tools_text.setReadOnly(True)
        self.tools_text.setMaximumHeight(200)
        right_layout.addWidget(self.tools_text)

        # 서버 설정 정보
        config_label = QLabel("서버 설정:")
        config_label.setStyleSheet("""
            QLabel {
                color: #b0e0b0;
                font-size: 15px;
                font-weight: 700;
                padding: 8px 0;
            }
        """)
        right_layout.addWidget(config_label)

        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        right_layout.addWidget(self.config_text)

        splitter.addWidget(right_group)
        splitter.setSizes([350, 550])

        # 하단 버튼들
        bottom_layout = QHBoxLayout()

        self.auto_start_checkbox = QCheckBox("프로그램 시작 시 자동으로 MCP 서버 시작")
        self.auto_start_checkbox.setChecked(True)
        bottom_layout.addWidget(self.auto_start_checkbox)

        bottom_layout.addStretch()

        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)
        bottom_layout.addWidget(close_button)

        layout.addLayout(bottom_layout)

    def refresh_servers(self):
        """서버 목록 새로고침"""
        self.status_label.setText("⏳ 서버 목록을 불러오는 중...")
        self.status_label.setStyleSheet("color: #FFA726;")
        self.refresh_button.setEnabled(False)

        # 타이머로 지연 실행
        self.refresh_timer.start(100)

    def _do_refresh(self):
        """실제 새로고침 작업"""
        try:
            print("서버 새로고침 시작")
            self.server_list.clear()
            self.current_servers.clear()

            # MCP 서버 상태 가져오기
            servers = get_mcp_servers()

            if not servers:
                self.status_label.setText("설정된 서버가 없습니다")
                self.status_label.setStyleSheet("color: #FFA726;")
                self.refresh_button.setEnabled(True)
                return

            server_count = 0

            for server_name, server_info in servers.items():
                server_count += 1
                item = QListWidgetItem()

                status = server_info.get("status", "unknown")
                tools = server_info.get("tools", [])
                config = server_info.get("config", {})

                # 상태에 따른 아이콘과 색상
                if status == "running":
                    icon = "🟢"
                    status_text = "실행중"
                elif status == "stopped":
                    icon = "🔴"
                    status_text = "중지됨"
                else:
                    icon = "⚠️"
                    status_text = "오류"

                item.setText(f"{icon} {server_name}")
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    {
                        "name": server_name,
                        "config": config,
                        "status": status_text,
                        "tools": tools,
                    },
                )

                self.server_list.addItem(item)
                self.current_servers[server_name] = {
                    "config": config,
                    "status": status_text,
                    "tools": tools,
                }

                # UI 업데이트를 위한 이벤트 처리
                QApplication.processEvents()

            if server_count == 0:
                self.status_label.setText("활성화된 서버가 없습니다")
                self.status_label.setStyleSheet("color: #FFA726;")
            else:
                self.status_label.setText(f"✅ {server_count}개 서버 로드 완료")
                self.status_label.setStyleSheet("color: #66BB6A;")

            print("서버 새로고침 완료")

        except Exception as e:
            print(f"새로고침 오류: {e}")
            self.status_label.setText(f"❌ 오류: {str(e)}")
            self.status_label.setStyleSheet("color: #F44336;")
        finally:
            self.refresh_button.setEnabled(True)

    def on_server_selected(self):
        """서버 선택 시 정보 표시"""
        current_item = self.server_list.currentItem()
        if not current_item:
            return

        data = current_item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        server_name = data["name"]
        server_config = data["config"]
        status = data["status"]
        tools = data["tools"]

        # 상태 표시
        status_color = {
            "실행중": "#66BB6A",
            "중지됨": "#F44336",
            "오류": "#FFA726",
        }.get(status, "#FFA726")

        self.status_label.setText(f"{server_name}: {status}")
        self.status_label.setStyleSheet(f"color: {status_color};")

        # 도구 목록 표시
        if tools:
            tools_text = "\n".join([f"• {tool}" for tool in tools])
        else:
            tools_text = "사용 가능한 도구 정보가 없습니다."
        self.tools_text.setPlainText(tools_text)

        # 설정 정보 표시
        config_text = json.dumps(server_config, indent=2, ensure_ascii=False)
        self.config_text.setPlainText(config_text)

        # 버튼 상태 업데이트
        self.start_button.setEnabled(status != "실행중")
        self.stop_button.setEnabled(status == "실행중")
        self.restart_button.setEnabled(True)

    def start_server(self):
        """서버 시작"""
        current_item = self.server_list.currentItem()
        if not current_item:
            return

        data = current_item.data(Qt.ItemDataRole.UserRole)
        server_name = data["name"]

        try:
            self.status_label.setText(f"⏳ {server_name} 시작 중...")
            self.status_label.setStyleSheet("color: #FFA726;")
            QApplication.processEvents()

            # 서버 시작 로직
            success = start_mcp_server(server_name)

            if success:
                self.status_label.setText(f"✅ {server_name} 시작됨")
                self.status_label.setStyleSheet("color: #66BB6A;")
                QTimer.singleShot(1000, self.refresh_servers)
            else:
                self.status_label.setText(f"❌ {server_name} 시작 실패")
                self.status_label.setStyleSheet("color: #F44336;")

        except Exception as e:
            QMessageBox.warning(self, "오류", f"서버 시작 실패: {str(e)}")

    def stop_server(self):
        """서버 중지"""
        current_item = self.server_list.currentItem()
        if not current_item:
            return

        data = current_item.data(Qt.ItemDataRole.UserRole)
        server_name = data["name"]

        try:
            self.status_label.setText(f"⏳ {server_name} 중지 중...")
            self.status_label.setStyleSheet("color: #FFA726;")
            QApplication.processEvents()

            # 서버 중지 로직
            success = stop_mcp_server(server_name)

            if success:
                self.status_label.setText(f"✅ {server_name} 중지됨")
                self.status_label.setStyleSheet("color: #66BB6A;")
                QTimer.singleShot(1000, self.refresh_servers)
            else:
                self.status_label.setText(f"❌ {server_name} 중지 실패")
                self.status_label.setStyleSheet("color: #F44336;")

        except Exception as e:
            QMessageBox.warning(self, "오류", f"서버 중지 실패: {str(e)}")

    def restart_server(self):
        """서버 재시작"""
        current_item = self.server_list.currentItem()
        if not current_item:
            return

        data = current_item.data(Qt.ItemDataRole.UserRole)
        server_name = data["name"]

        try:
            self.status_label.setText(f"⏳ {server_name} 재시작 중...")
            self.status_label.setStyleSheet("color: #FFA726;")
            QApplication.processEvents()

            # 서버 재시작 로직
            success = restart_mcp_server(server_name)

            if success:
                self.status_label.setText(f"✅ {server_name} 재시작됨")
                self.status_label.setStyleSheet("color: #66BB6A;")
                QTimer.singleShot(2000, self.refresh_servers)
            else:
                self.status_label.setText(f"❌ {server_name} 재시작 실패")
                self.status_label.setStyleSheet("color: #F44336;")

        except Exception as e:
            QMessageBox.warning(self, "오류", f"서버 재시작 실패: {str(e)}")
    
    def _get_dialog_style(self):
        return """
            QDialog {
                background: #5a5a5f;
                color: #ffffff;
                font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 4px 0;
            }
            QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(45, 45, 55, 0.95), 
                    stop:1 rgba(35, 35, 45, 0.95));
                border: 2px solid rgba(100, 200, 255, 0.3);
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 8px;
                margin: 4px 0;
                background: rgba(60, 60, 70, 0.5);
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(100, 200, 255, 0.4), 
                    stop:1 rgba(150, 100, 255, 0.4));
                color: #ffffff;
            }
            QListWidget::item:hover {
                background: rgba(70, 70, 80, 0.7);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(100, 200, 255, 0.8), 
                    stop:1 rgba(150, 100, 255, 0.8));
                color: #ffffff;
                border: 2px solid rgba(100, 200, 255, 0.4);
                border-radius: 10px;
                font-weight: 700;
                font-size: 14px;
                padding: 10px 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(120, 220, 255, 0.9), 
                    stop:1 rgba(170, 120, 255, 0.9));
                border-color: rgba(100, 200, 255, 0.6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(80, 180, 235, 0.7), 
                    stop:1 rgba(130, 80, 235, 0.7));
            }
            QPushButton:disabled {
                background: rgba(55, 65, 81, 0.5);
                color: #6b7280;
                border-color: rgba(100, 100, 100, 0.2);
            }
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(45, 45, 55, 0.95), 
                    stop:1 rgba(35, 35, 45, 0.95));
                border: 2px solid rgba(100, 200, 255, 0.3);
                border-radius: 8px;
                padding: 12px;
                font-family: 'SF Mono', 'Monaco', monospace;
                font-size: 13px;
                color: #e8e8e8;
            }
            QGroupBox {
                color: #ffffff;
                font-size: 15px;
                font-weight: 700;
                border: 2px solid rgba(100, 200, 255, 0.3);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background: #5a5a5f;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid rgba(100, 200, 255, 0.4);
                border-radius: 4px;
                background: rgba(45, 45, 55, 0.8);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(100, 200, 255, 0.8), 
                    stop:1 rgba(150, 100, 255, 0.8));
                border-color: rgba(100, 200, 255, 0.6);
            }
        """
