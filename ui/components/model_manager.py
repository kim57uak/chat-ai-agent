from PyQt6.QtWidgets import QLabel, QMenu
from PyQt6.QtCore import Qt, QTimer


class ModelManager:
    """모델 관리를 담당하는 클래스 (SRP)"""
    
    def __init__(self, model_label: QLabel, tools_label: QLabel):
        self.model_label = model_label
        self.tools_label = tools_label
        self.tools_update_timer = QTimer()
        self.tools_update_timer.timeout.connect(self.update_tools_label)
        
        self._setup_labels()
        self._start_tools_monitoring()
    
    def _setup_labels(self):
        """라벨 초기 설정"""
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
        
        self.update_model_label()
        self.tools_label.setText('🔧 도구 확인중...')
        self.tools_label.setVisible(True)
    
    def _start_tools_monitoring(self):
        """도구 모니터링 시작"""
        QTimer.singleShot(1500, self.update_tools_label)
        QTimer.singleShot(3000, lambda: self.tools_update_timer.start(10000))
    
    def update_model_label(self):
        """모델 라벨 업데이트"""
        from core.file_utils import load_last_model
        from core.session_token_manager import session_token_manager
        
        model = load_last_model()
        
        # 세션 토큰 정보 추가
        total_input, total_output, total_tokens = session_token_manager.get_session_total_tokens()
        
        if total_tokens > 0:
            token_info = f" | 📊 세션: {total_tokens:,}토큰 (IN:{total_input:,} OUT:{total_output:,})"
            self.model_label.setText(f'🤖 {model}{token_info}')
        else:
            self.model_label.setText(f'🤖 {model} | 📊 세션: 0토큰')
    
    def update_tools_label(self):
        """도구 라벨 업데이트"""
        try:
            from mcp.servers.mcp import get_all_mcp_tools
            tools = get_all_mcp_tools()
            tool_count = len(tools) if tools else 0
            
            if tool_count > 0:
                text = f'🔧 {tool_count}개 도구 활성화'
            else:
                text = '🔧 도구 없음'
            
            self.tools_label.setText(text)
            
        except Exception as e:
            self.tools_label.setText('🔧 도구 상태 불명')
            print(f"도구 라벨 업데이트 오류: {e}")
    
    def show_model_popup(self, event):
        """모델 선택 팝업 표시"""
        try:
            from core.file_utils import load_config, save_last_model, load_last_model
            
            config = load_config()
            models = config.get('models', {})
            
            if not models:
                return
            
            menu = QMenu()
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
                # Pollinations 모델은 API 키가 필요 없으므로 항상 표시
                api_key = model_config.get('api_key', '')
                if (api_key and api_key != 'none') or model_name == 'pollinations-image':
                    emoji = "🎨" if model_name == 'pollinations-image' else "🤖"
                    action = menu.addAction(f"{emoji} {model_name}")
                    if model_name == current_model:
                        action.setText(f"✅ {model_name} (현재)")
                    action.triggered.connect(lambda checked, m=model_name: self.change_model(m))
            
            menu.exec(self.model_label.mapToGlobal(event.pos()))
            
        except Exception as e:
            print(f"모델 팝업 표시 오류: {e}")
    
    def change_model(self, model_name):
        """모델 변경"""
        try:
            from core.file_utils import save_last_model
            save_last_model(model_name)
            self.update_model_label()
            print(f"모델 변경: {model_name}")
        except Exception as e:
            print(f"모델 변경 오류: {e}")
    
    def show_tools_popup(self, event):
        """도구 목록 팝업 표시"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            from mcp.servers.mcp import get_all_mcp_tools
            
            tools = get_all_mcp_tools()
            
            if not tools:
                QMessageBox.information(
                    None, 
                    "도구 상태", 
                    "활성화된 MCP 도구가 없습니다.\n\n설정 > MCP 서버 관리에서 서버를 활성화하세요."
                )
                return
            
            self._show_tools_menu(event, tools)
            
        except Exception as e:
            print(f"도구 팝업 표시 오류: {e}")
    
    def _show_tools_menu(self, event, tools):
        """도구 메뉴 표시"""
        try:
            menu = QMenu()
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
                    server_name = 'Tools'
                else:
                    tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                    server_name = tool.server_name if hasattr(tool, 'server_name') else 'Tools'
                
                if server_name not in servers:
                    servers[server_name] = []
                servers[server_name].append(tool_name)
            
            # 메뉴 항목 추가
            for server_name, tool_names in servers.items():
                menu.addAction(f"📦 {server_name} ({len(tool_names)}개)")
                for tool_name in tool_names[:5]:
                    menu.addAction(f"  • {tool_name}")
                if len(tool_names) > 5:
                    menu.addAction(f"  ... 외 {len(tool_names)-5}개")
                menu.addSeparator()
            
            from PyQt6.QtGui import QCursor
            menu.exec(QCursor.pos())
            
        except Exception as e:
            print(f"도구 메뉴 표시 오류: {e}")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        if self.tools_update_timer:
            self.tools_update_timer.stop()