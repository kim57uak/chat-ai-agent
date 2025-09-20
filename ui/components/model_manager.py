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
        from core.file_utils import load_last_model, load_config
        from core.session_token_manager import session_token_manager
        
        model = load_last_model()
        config = load_config()
        models = config.get('models', {})
        
        # 모델 이모지 가져오기
        model_config = models.get(model, {})
        model_emoji = self._get_model_emoji(model, model_config)
        
        # 모델명만 표시
        self.model_label.setText(f'{model_emoji} {model}')
    
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
        """모델 선택 팝업 표시 - 계층 구조"""
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
                QMenu::separator {
                    height: 1px;
                    background-color: #444444;
                    margin: 4px 0px;
                }
            """)
            
            current_model = load_last_model()
            
            # 모델을 카테고리별로 분류
            categorized_models = self._categorize_models(models)
            
            # 카테고리별로 서브메뉴 생성
            for category, category_models in categorized_models.items():
                if not category_models:
                    continue
                    
                category_info = self._get_category_info(category)
                submenu = menu.addMenu(f"{category_info['emoji']} {category_info['name']} ({len(category_models)}개)")
                submenu.setStyleSheet(menu.styleSheet())
                
                for model_name, model_config in category_models.items():
                    model_emoji = self._get_model_emoji(model_name, model_config)
                    display_name = self._get_model_display_name(model_name, model_config)
                    
                    action = submenu.addAction(f"{model_emoji} {display_name}")
                    if model_name == current_model:
                        action.setText(f"✅ {display_name} (현재)")
                    action.triggered.connect(lambda checked, m=model_name: self.change_model(m))
            
            menu.exec(self.model_label.mapToGlobal(event.pos()))
            
        except Exception as e:
            print(f"모델 팝업 표시 오류: {e}")
    
    def _categorize_models(self, models):
        """모델을 카테고리별로 분류"""
        categories = {
            'openrouter_reasoning': {},
            'openrouter_coding': {},
            'openrouter_multimodal': {},
            'openrouter_meta_llama': {},
            'google': {},
            'perplexity': {},
            'pollinations': {},
            'other': {}
        }
        
        for model_name, model_config in models.items():
            api_key = model_config.get('api_key', '')
            if not (api_key and api_key != 'none'):
                continue
                
            provider = model_config.get('provider', '')
            category = model_config.get('category', '')
            
            if provider == 'openrouter':
                if category == 'reasoning':
                    categories['openrouter_reasoning'][model_name] = model_config
                elif category == 'coding':
                    categories['openrouter_coding'][model_name] = model_config
                elif category == 'multimodal':
                    categories['openrouter_multimodal'][model_name] = model_config
                elif category == 'meta_llama':
                    categories['openrouter_meta_llama'][model_name] = model_config
                else:
                    categories['other'][model_name] = model_config
            elif provider == 'google':
                categories['google'][model_name] = model_config
            elif provider == 'perplexity':
                categories['perplexity'][model_name] = model_config
            elif provider == 'pollinations':
                categories['pollinations'][model_name] = model_config
            else:
                categories['other'][model_name] = model_config
        
        return categories
    
    def _get_category_info(self, category):
        """카테고리 정보 반환"""
        category_map = {
            'openrouter_reasoning': {'emoji': '🧠', 'name': 'OpenRouter 추론 특화'},
            'openrouter_coding': {'emoji': '💻', 'name': 'OpenRouter 코딩 특화'},
            'openrouter_multimodal': {'emoji': '🖼️', 'name': 'OpenRouter 멀티모달'},
            'openrouter_meta_llama': {'emoji': '🦙', 'name': 'OpenRouter Meta Llama'},
            'google': {'emoji': '🔍', 'name': 'Google Gemini'},
            'perplexity': {'emoji': '🔬', 'name': 'Perplexity'},
            'pollinations': {'emoji': '🌸', 'name': 'Pollinations'},
            'other': {'emoji': '🤖', 'name': '기타 모델'}
        }
        return category_map.get(category, {'emoji': '🤖', 'name': category})
    
    def _get_model_emoji(self, model_name, model_config):
        """모델별 이모지 반환"""
        if 'image' in model_name.lower():
            return '🎨'
        elif model_config.get('category') == 'reasoning':
            return '🧠'
        elif model_config.get('category') == 'coding':
            return '💻'
        elif model_config.get('category') == 'multimodal':
            return '🖼️'
        elif model_config.get('category') == 'meta_llama':
            return '🦙'
        elif 'gemini' in model_name.lower():
            return '💎'
        elif 'sonar' in model_name.lower():
            return '🔬'
        elif 'pollinations' in model_name.lower():
            return '🌸'
        else:
            return '🤖'
    
    def _get_model_display_name(self, model_name, model_config):
        """모델 표시명 생성"""
        description = model_config.get('description', '')
        if description:
            # 이모지 제거하고 간단한 설명만 추출
            clean_desc = description.split(' - ')[-1] if ' - ' in description else description
            clean_desc = ''.join(char for char in clean_desc if not char.startswith('�'))
            return f"{model_name.split('/')[-1]} - {clean_desc[:30]}..."
        return model_name
    
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