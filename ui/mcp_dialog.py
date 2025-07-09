from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QLabel, QTextEdit, QGroupBox, QPushButton
from core.mcp import start_mcp_servers, get_all_mcp_tools
import json
import os

class MCPDialog(QDialog):
    def __init__(self, mcp_path='mcp.json', parent=None):
        super().__init__(parent)
        self.setWindowTitle('MCP 서버 상태')
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.mcp_path = mcp_path
        
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