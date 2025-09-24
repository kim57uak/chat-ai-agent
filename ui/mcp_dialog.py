from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QLabel, QTextEdit, QGroupBox, QPushButton
from mcp.servers.mcp import start_mcp_servers, get_all_mcp_tools
from ui.styles.material_theme_manager import material_theme_manager
import json
import os

class MCPDialog(QDialog):
    def __init__(self, mcp_path='mcp.json', parent=None):
        super().__init__(parent)
        self.setWindowTitle('MCP 서버 상태')
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.mcp_path = mcp_path
        self.setStyleSheet(self._get_themed_dialog_style())
        
        layout = QVBoxLayout(self)
        
        # MCP 서버 시작 버튼
        self.start_button = QPushButton('서버 시작')
        self.start_button.clicked.connect(self.start_servers)
        layout.addWidget(self.start_button)
        
        # MCP 서버 설정 표시
        try:
            if os.path.exists(mcp_path):
                with open(mcp_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                servers = config.get('servers', {})
            else:
                servers = {}
            
            if servers:
                server_group = QGroupBox('MCP 서버 설정')
                server_layout = QVBoxLayout()
                for name, info in servers.items():
                    cmd_str = info.get('command', '')
                    args_str = ' '.join(info.get('args', []))
                    label = QLabel(f"<b>{name}</b>: {cmd_str} {args_str}")
                    server_layout.addWidget(label)
                server_group.setLayout(server_layout)
                layout.addWidget(server_group)
        except Exception as e:
            layout.addWidget(QLabel(f'설정 로드 실패: {e}'))
        
        # 도구 목록 표시
        layout.addWidget(QLabel('로드된 도구 목록'))
        self.tools_box = QTextEdit(self)
        self.tools_box.setReadOnly(True)
        layout.addWidget(self.tools_box)
        
        self.update_tools_display()
    
    def start_servers(self):
        """MCP 서버 시작"""
        success = start_mcp_servers(self.mcp_path)
        if success:
            self.start_button.setText('서버 시작됨')
            self.start_button.setEnabled(False)
            self.update_tools_display()
        else:
            self.tools_box.setText('서버 시작 실패')
    
    def update_tools_display(self):
        """MCP 도구 목록 업데이트"""
        try:
            tools = get_all_mcp_tools()
            if tools:
                tool_info = []
                for server_name, server_tools in tools.items():
                    tool_info.append(f"\n📦 {server_name} ({len(server_tools)}개 도구):")
                    for tool in server_tools[:5]:  # 처음 5개만
                        name = tool.get('name', 'Unknown')
                        desc = tool.get('description', '')
                        tool_info.append(f"  • {name}: {desc[:50]}...")
                    if len(server_tools) > 5:
                        tool_info.append(f"  ... 외 {len(server_tools) - 5}개 더")
                self.tools_box.setText('\n'.join(tool_info))
            else:
                self.tools_box.setText('로드된 도구가 없습니다. 서버를 먼저 시작하세요.')
        except Exception as e:
            self.tools_box.setText(f'도구 정보 로드 실패: {e}')
    
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
            QTextEdit {{
                background-color: {colors.get('surface', '#334155')};
                color: {colors.get('text_primary', '#f1f5f9')};
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
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
        """ 