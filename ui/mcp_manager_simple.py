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
from ui.styles.material_theme_manager import material_theme_manager
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

        self.setStyleSheet(self._get_themed_dialog_style())

        self.setup_ui()
        # 초기 로딩
        QTimer.singleShot(500, self.refresh_servers)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 제목
        title_label = QLabel("MCP 서버 관리")
        title_label.setStyleSheet(self._get_title_style())
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
        self.start_button.setStyleSheet(self._get_start_button_style())
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setStyleSheet(self._get_stop_button_style())
        button_layout.addWidget(self.stop_button)

        self.restart_button = QPushButton("재시작")
        self.restart_button.clicked.connect(self.restart_server)
        self.restart_button.setStyleSheet(self._get_restart_button_style())
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
        self.status_label.setStyleSheet(self._get_status_label_style())
        right_layout.addWidget(self.status_label)

        # 도구 목록
        tools_label = QLabel("사용 가능한 도구:")
        tools_label.setStyleSheet(self._get_section_label_style())
        right_layout.addWidget(tools_label)

        self.tools_text = QTextEdit()
        self.tools_text.setReadOnly(True)
        self.tools_text.setMaximumHeight(200)
        right_layout.addWidget(self.tools_text)

        # 서버 설정 정보
        config_label = QLabel("서버 설정:")
        config_label.setStyleSheet(self._get_section_label_style())
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
        theme = material_theme_manager.get_current_theme()
        colors = theme.get('colors', {})
        self.status_label.setStyleSheet(f"color: {colors.get('warning', '#FFA726')};")
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
                theme = material_theme_manager.get_current_theme()
                colors = theme.get('colors', {})
                self.status_label.setStyleSheet(f"color: {colors.get('warning', '#FFA726')};")
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
                        "config": server_info,  # 전체 서버 정보 저장
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
                theme = material_theme_manager.get_current_theme()
                colors = theme.get('colors', {})
                self.status_label.setStyleSheet(f"color: {colors.get('warning', '#FFA726')};")
            else:
                self.status_label.setText(f"✅ {server_count}개 서버 로드 완료")
                theme = material_theme_manager.get_current_theme()
                colors = theme.get('colors', {})
                self.status_label.setStyleSheet(f"color: {colors.get('success', '#66BB6A')};")

            print("서버 새로고침 완료")

        except Exception as e:
            print(f"새로고침 오류: {e}")
            self.status_label.setText(f"❌ 오류: {str(e)}")
            theme = material_theme_manager.get_current_theme()
            colors = theme.get('colors', {})
            self.status_label.setStyleSheet(f"color: {colors.get('error', '#F44336')};")
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
        theme = material_theme_manager.get_current_theme()
        colors = theme.get('colors', {})
        status_color = {
            "실행중": colors.get('success', '#66BB6A'),
            "중지됨": colors.get('error', '#F44336'),
            "오류": colors.get('warning', '#FFA726'),
        }.get(status, colors.get('warning', '#FFA726'))

        self.status_label.setText(f"{server_name}: {status}")
        self.status_label.setStyleSheet(f"color: {status_color};")

        # 도구 목록 표시
        if tools:
            tools_text = "\n".join([f"• {tool}" for tool in tools])
        else:
            tools_text = "사용 가능한 도구 정보가 없습니다."
        self.tools_text.setPlainText(tools_text)

        # 설정 정보 표시
        if server_config:
            # 서버 설정을 보기 좋게 포맷팅
            config_display = {
                "명령어": server_config.get('command', 'N/A'),
                "인수": server_config.get('args', []),
                "환경변수": server_config.get('env', {}),
                "상태": status,
                "서버 타입": server_config.get('server_type', 'unknown')
            }
            config_text = json.dumps(config_display, indent=2, ensure_ascii=False)
        else:
            config_text = "설정 정보를 불러올 수 없습니다."
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
            theme = material_theme_manager.get_current_theme()
            colors = theme.get('colors', {})
            self.status_label.setStyleSheet(f"color: {colors.get('warning', '#FFA726')};")
            QApplication.processEvents()

            # 서버 시작 로직
            success = start_mcp_server(server_name)

            if success:
                self.status_label.setText(f"✅ {server_name} 시작됨")
                theme = material_theme_manager.get_current_theme()
                colors = theme.get('colors', {})
                self.status_label.setStyleSheet(f"color: {colors.get('success', '#66BB6A')};")
                QTimer.singleShot(1000, self.refresh_servers)
            else:
                self.status_label.setText(f"❌ {server_name} 시작 실패")
                theme = material_theme_manager.get_current_theme()
                colors = theme.get('colors', {})
                self.status_label.setStyleSheet(f"color: {colors.get('error', '#F44336')};")

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
            theme = material_theme_manager.get_current_theme()
            colors = theme.get('colors', {})
            self.status_label.setStyleSheet(f"color: {colors.get('warning', '#FFA726')};")
            QApplication.processEvents()

            # 서버 중지 로직
            success = stop_mcp_server(server_name)

            if success:
                self.status_label.setText(f"✅ {server_name} 중지됨")
                theme = material_theme_manager.get_current_theme()
                colors = theme.get('colors', {})
                self.status_label.setStyleSheet(f"color: {colors.get('success', '#66BB6A')};")
                QTimer.singleShot(1000, self.refresh_servers)
            else:
                self.status_label.setText(f"❌ {server_name} 중지 실패")
                theme = material_theme_manager.get_current_theme()
                colors = theme.get('colors', {})
                self.status_label.setStyleSheet(f"color: {colors.get('error', '#F44336')};")

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
            theme = material_theme_manager.get_current_theme()
            colors = theme.get('colors', {})
            self.status_label.setStyleSheet(f"color: {colors.get('warning', '#FFA726')};")
            QApplication.processEvents()

            # 서버 재시작 로직
            success = restart_mcp_server(server_name)

            if success:
                self.status_label.setText(f"✅ {server_name} 재시작됨")
                theme = material_theme_manager.get_current_theme()
                colors = theme.get('colors', {})
                self.status_label.setStyleSheet(f"color: {colors.get('success', '#66BB6A')};")
                QTimer.singleShot(2000, self.refresh_servers)
            else:
                self.status_label.setText(f"❌ {server_name} 재시작 실패")
                theme = material_theme_manager.get_current_theme()
                colors = theme.get('colors', {})
                self.status_label.setStyleSheet(f"color: {colors.get('error', '#F44336')};")

        except Exception as e:
            QMessageBox.warning(self, "오류", f"서버 재시작 실패: {str(e)}")
    
    def _get_themed_dialog_style(self):
        from ui.styles.theme_manager import theme_manager
        colors = theme_manager.material_manager.get_theme_colors()
        
        return f"""
            QDialog {{
                background-color: {colors.get('background', '#1e293b')};
                color: {colors.get('text_primary', '#f1f5f9')};
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                border: none;
            }}
            QLabel {{
                color: {colors.get('text_primary', '#f1f5f9')};
                font-size: 14px;
                font-weight: 500;
                padding: 4px 0;
                background: transparent;
            }}
            QListWidget {{
                background-color: {colors.get('surface', '#334155')};
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                color: {colors.get('text_primary', '#f1f5f9')};
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 6px;
                margin: 2px 0;
                background-color: {colors.get('surface_variant', '#475569')};
            }}
            QListWidget::item:selected {{
                background-color: {colors.get('primary', '#6366f1')};
                color: {colors.get('on_primary', '#ffffff')};
            }}
            QListWidget::item:hover {{
                background-color: {colors.get('primary_variant', '#4f46e5')};
                color: {colors.get('on_primary', '#ffffff')};
            }}
            QPushButton {{
                background-color: {colors.get('primary', '#6366f1')};
                color: {colors.get('on_primary', '#ffffff')};
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                padding: 10px 20px;
                margin: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors.get('primary_variant', '#4f46e5')};
            }}
            QPushButton:pressed {{
                background-color: {colors.get('primary_dark', '#3730a3')};
            }}
            QPushButton:disabled {{
                background-color: {colors.get('surface_variant', '#475569')};
                color: {colors.get('text_secondary', '#94a3b8')};
            }}
            QTextEdit {{
                background-color: {colors.get('surface', '#334155')};
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 8px;
                padding: 12px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 13px;
                color: {colors.get('text_primary', '#f1f5f9')};
            }}
            QTextEdit:focus {{
                border-color: {colors.get('primary', '#6366f1')};
            }}
            QGroupBox {{
                color: {colors.get('text_primary', '#f1f5f9')};
                font-size: 16px;
                font-weight: 600;
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: {colors.get('surface', 'rgba(51, 65, 85, 0.5)')};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 4px 12px;
                background-color: {colors.get('primary', '#6366f1')};
                color: {colors.get('on_primary', '#ffffff')};
                border-radius: 4px;
                font-weight: 600;
                font-size: 14px;
            }}
            QCheckBox {{
                color: {colors.get('text_primary', '#f1f5f9')};
                font-size: 14px;
                font-weight: 500;
                spacing: 8px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 3px;
                background-color: {colors.get('surface', '#334155')};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors.get('primary', '#6366f1')};
                border-color: {colors.get('primary', '#6366f1')};
            }}
            QCheckBox::indicator:hover {{
                border-color: {colors.get('primary', '#6366f1')};
            }}
        """
    
    def _get_title_style(self):
        theme = material_theme_manager.get_current_theme()
        colors = theme.get('colors', {})
        
        return f"""
            QLabel {{
                color: {colors.get('text_primary', '#ffffff')};
                font-size: 18px;
                font-weight: 800;
                font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                padding: 15px 0;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
        """
    
    def _get_start_button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(76, 175, 80, 0.8), 
                    stop:1 rgba(139, 195, 74, 0.8));
                color: #ffffff;
                border: 2px solid rgba(76, 175, 80, 0.4);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(102, 187, 106, 0.9), 
                    stop:1 rgba(156, 204, 101, 0.9));
                border-color: rgba(76, 175, 80, 0.6);
            }
        """
    
    def _get_stop_button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(244, 67, 54, 0.8), 
                    stop:1 rgba(255, 87, 34, 0.8));
                color: #ffffff;
                border: 2px solid rgba(244, 67, 54, 0.4);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(229, 115, 115, 0.9), 
                    stop:1 rgba(255, 138, 101, 0.9));
                border-color: rgba(244, 67, 54, 0.6);
            }
        """
    
    def _get_restart_button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(255, 193, 7, 0.8), 
                    stop:1 rgba(255, 152, 0, 0.8));
                color: #ffffff;
                border: 2px solid rgba(255, 193, 7, 0.4);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(255, 213, 79, 0.9), 
                    stop:1 rgba(255, 183, 77, 0.9));
                border-color: rgba(255, 193, 7, 0.6);
            }
        """
    
    def _get_status_label_style(self):
        theme = material_theme_manager.get_current_theme()
        colors = theme.get('colors', {})
        
        return f"""
            QLabel {{
                color: {colors.get('text_primary', '#ffffff')};
                font-size: 16px;
                font-weight: 700;
                font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                padding: 8px 0;
            }}
        """
    
    def _get_section_label_style(self):
        theme = material_theme_manager.get_current_theme()
        colors = theme.get('colors', {})
        
        return f"""
            QLabel {{
                color: {colors.get('secondary', '#03dac6')};
                font-size: 15px;
                font-weight: 700;
                padding: 8px 0;
            }}
        """