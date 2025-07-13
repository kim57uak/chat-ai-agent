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

        self.setStyleSheet(
            """
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
        """
        )

        self.setup_ui()
        # 초기 로딩
        QTimer.singleShot(500, self.refresh_servers)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 제목
        title_label = QLabel("MCP 서버 관리")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
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
        self.start_button.setStyleSheet("QPushButton { background-color: #66BB6A; }")
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setStyleSheet("QPushButton { background-color: #F44336; }")
        button_layout.addWidget(self.stop_button)

        self.restart_button = QPushButton("재시작")
        self.restart_button.clicked.connect(self.restart_server)
        self.restart_button.setStyleSheet("QPushButton { background-color: #FF9800; }")
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
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(self.status_label)

        # 도구 목록
        tools_label = QLabel("사용 가능한 도구:")
        right_layout.addWidget(tools_label)

        self.tools_text = QTextEdit()
        self.tools_text.setReadOnly(True)
        self.tools_text.setMaximumHeight(200)
        right_layout.addWidget(self.tools_text)

        # 서버 설정 정보
        config_label = QLabel("서버 설정:")
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
