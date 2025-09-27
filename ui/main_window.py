from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QFileDialog, 
                            QMessageBox, QDockWidget, QSplitter)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, Qt
from ui.chat_widget import ChatWidget
from ui.settings_dialog import SettingsDialog
from ui.mcp_dialog import MCPDialog
from ui.mcp_manager_simple import MCPManagerDialog
from ui.components.token_usage_display import TokenUsageDisplay
from ui.session_panel import SessionPanel
from mcp.servers.mcp import start_mcp_servers, stop_mcp_servers
from ui.components.status_display import status_display
from ui.styles.flat_theme import FlatTheme
from ui.styles.theme_manager import theme_manager
# MaterialThemeType 제거 - 하드코딩 금지
from core.session import session_manager
import os
import json
import threading

class MainWindow(QMainWindow):
    def __init__(self):
        print("[DEBUG] MainWindow.__init__() 시작")
        super().__init__()
        print("[DEBUG] super().__init__() 완료")
        print("[DEBUG] _setup_window() 시작")
        self._setup_window()
        print("[DEBUG] _setup_window() 완료")
        print("[DEBUG] _setup_ui() 시작")
        self._setup_ui()
        print("[DEBUG] _setup_ui() 완료")
        print("[DEBUG] _initialize_mcp() 시작")
        self._initialize_mcp()
        print("[DEBUG] _initialize_mcp() 완료")
        print("MainWindow 초기화 완료")
    
    def _setup_window(self) -> None:
        """Setup main window properties."""
        self._update_window_title()
        self.setGeometry(100, 100, 1400, 900)  # 창 크기 약간 증가
        
        # 애플리케이션 아이콘 설정
        from PyQt6.QtGui import QIcon
        if os.path.exists('image/app_icon_128.png'):
            self.setWindowIcon(QIcon('image/app_icon_128.png'))
        elif os.path.exists('image/Agentic_AI_transparent.png'):
            self.setWindowIcon(QIcon('image/Agentic_AI_transparent.png'))
        
        self._apply_current_theme()
    
    def _setup_ui(self) -> None:
        """Setup UI components."""
        print("[DEBUG] _setup_ui: Central widget 생성 시작")
        # Central widget with splitter
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        print("[DEBUG] _setup_ui: Central widget 생성 완료")
        
        print("[DEBUG] _setup_ui: Splitter 생성 시작")
        # Main splitter for session panel, chat, and token usage
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)  # 핸들 너비 최소화
        self.splitter.setChildrenCollapsible(False)  # 완전히 접히지 않도록
        print("[DEBUG] _setup_ui: Splitter 생성 완료")
        
        # 스플리터 스타일은 테마 적용 시 설정됨
        
        print("[DEBUG] _setup_ui: SessionPanel 생성 시작")
        # Session panel (left)
        self.session_panel = SessionPanel(self)
        print("[DEBUG] _setup_ui: SessionPanel 생성 완료")
        self.session_panel.session_selected.connect(self._on_session_selected)
        self.session_panel.session_created.connect(self._on_session_created)
        self.splitter.addWidget(self.session_panel)
        print("[DEBUG] _setup_ui: SessionPanel 스플리터에 추가 완료")
        
        print("[DEBUG] _setup_ui: Chat container 생성 시작")
        # Chat widget with news banner (center)
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        print("[DEBUG] _setup_ui: Chat container 생성 완료")
        
        print("[DEBUG] _setup_ui: NewsBanner 생성 시작")
        # News banner
        from ui.components.news_banner_simple import NewsBanner
        self.news_banner = NewsBanner(self)
        print("[DEBUG] _setup_ui: NewsBanner 생성 완료")
        self.news_banner.setMaximumHeight(44)
        self.news_banner.setContentsMargins(0, 0, 0, 5)
        chat_layout.addWidget(self.news_banner)
        chat_layout.addSpacing(3)  # 하단 영역과 간격 추가
        print("[DEBUG] _setup_ui: NewsBanner 설정 완료")
        
        print("[DEBUG] _setup_ui: ChatWidget 생성 시작")
        # Chat widget
        self.chat_widget = ChatWidget(self)
        print("[DEBUG] _setup_ui: ChatWidget 생성 완료")
        self.chat_widget.setMinimumWidth(400)  # 최소 너비 설정
        chat_layout.addWidget(self.chat_widget)
        print("[DEBUG] _setup_ui: ChatWidget 레이아웃 추가 완료")
        
        chat_container.setMinimumWidth(400)
        self.splitter.addWidget(chat_container)
        print("[DEBUG] _setup_ui: Chat container 스플리터에 추가 완료")
        
        print("[DEBUG] _setup_ui: TokenUsageDisplay 생성 시작")
        # Token usage display (right)
        self.token_display = TokenUsageDisplay(self)
        print("[DEBUG] _setup_ui: TokenUsageDisplay 생성 완료")
        self.token_display.setVisible(True)  # 기본적으로 표시
        self.token_display.setMinimumWidth(250)  # 최소 너비 설정
        self.token_display.setMaximumWidth(600)  # 최대 너비 설정
        self.token_display.export_requested.connect(self._show_export_message)
        self.splitter.addWidget(self.token_display)
        print("[DEBUG] _setup_ui: TokenUsageDisplay 스플리터에 추가 완료")
        
        print("[DEBUG] _setup_ui: SessionPanel 및 TokenUsageDisplay 생성 완료")
        
        # Set splitter proportions (토큰 패널 기본 표시)
        self.splitter.setSizes([250, 700, 300])
        self.splitter.setStretchFactor(0, 0)  # 세션 패널은 고정 크기
        self.splitter.setStretchFactor(1, 3)  # 채팅창이 가장 많이 늘어남
        self.splitter.setStretchFactor(2, 1)  # 토큰창은 적게 늘어남
        
        # 현재 세션 ID 추적
        self.current_session_id = None
        
        # 자동 세션 생성 플래그
        self._auto_session_created = False
        
        # 세션 패널에 메인 윈도우 참조 전달
        self.session_panel.main_window = self
        
        # 스플리터 상태 저장/복원 기능 추가
        self._load_splitter_state()
        self.splitter.splitterMoved.connect(self._save_splitter_state)
        
        layout.addWidget(self.splitter)
        self.setCentralWidget(central_widget)
        
        # 상태 표시 초기화
        status_display.status_updated.emit(status_display.current_status.copy())
        
        print("[DEBUG] _setup_ui: Menu 생성 시작")
        # Menu
        self._create_menu_bar()
        print("[DEBUG] _setup_ui: Menu 생성 완료")
        
        print("[DEBUG] _setup_ui: 저장된 테마 적용 시작")
        # 저장된 테마 적용
        self._apply_saved_theme()
        print("[DEBUG] _setup_ui: 저장된 테마 적용 완료")
    

    
    def _create_menu_bar(self) -> None:
        """Create the main menu bar."""
        menubar = self.menuBar()
        settings_menu = menubar.addMenu('설정')
        
        # Environment settings
        settings_action = QAction('환경설정', self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)
        
        # MCP actions
        mcp_action = QAction('MCP 확장 임포트', self)
        mcp_action.triggered.connect(self.open_mcp)
        settings_menu.addAction(mcp_action)
        
        mcp_manager_action = QAction('MCP 서버 관리', self)
        mcp_manager_action.triggered.connect(self.open_mcp_manager)
        settings_menu.addAction(mcp_manager_action)
        
        settings_menu.addSeparator()
        
        # Config path setting
        config_path_action = QAction('설정 파일 경로 설정', self)
        config_path_action.triggered.connect(self.open_config_path_dialog)
        settings_menu.addAction(config_path_action)
        
        settings_menu.addSeparator()
        
        # History and prompt actions
        clear_history_action = QAction('대화 기록 초기화', self)
        clear_history_action.triggered.connect(self.clear_conversation_history)
        settings_menu.addAction(clear_history_action)
        
        user_prompt_action = QAction('유저 프롬프트 설정', self)
        user_prompt_action.triggered.connect(self.open_user_prompt)
        settings_menu.addAction(user_prompt_action)
        
        settings_menu.addSeparator()
        

        
        # Session panel toggle
        self.session_panel_action = QAction('세션 패널 표시', self)
        self.session_panel_action.setCheckable(True)
        self.session_panel_action.setChecked(True)  # 기본적으로 활성화
        self.session_panel_action.setShortcut('Ctrl+[')
        self.session_panel_action.triggered.connect(self.toggle_session_panel)
        settings_menu.addAction(self.session_panel_action)
        
        # Token usage toggle
        self.token_usage_action = QAction('토큰 사용량 표시', self)
        self.token_usage_action.setCheckable(True)
        self.token_usage_action.setChecked(True)  # 기본적으로 활성화
        self.token_usage_action.setShortcut('Ctrl+]')
        self.token_usage_action.triggered.connect(self.toggle_token_display)
        settings_menu.addAction(self.token_usage_action)
        
        # Glassmorphism toggle
        self.glassmorphism_action = QAction('글래스모피즘 효과', self)
        self.glassmorphism_action.setCheckable(True)
        self.glassmorphism_action.setChecked(theme_manager.material_manager.is_glassmorphism_enabled())
        self.glassmorphism_action.setShortcut('Ctrl+G')
        self.glassmorphism_action.triggered.connect(self.toggle_glassmorphism)
        settings_menu.addAction(self.glassmorphism_action)
        
        settings_menu.addSeparator()
        
        # Splitter reset action
        reset_layout_action = QAction('레이아웃 초기화', self)
        reset_layout_action.triggered.connect(self.reset_layout)
        settings_menu.addAction(reset_layout_action)
        
        # 테마 메뉴 삭제 - 좌측 패널로 이동
    
    def _initialize_mcp(self) -> None:
        """Initialize MCP servers."""
        # MCP 서버 시작 지연 시간을 약간 늘림
        QTimer.singleShot(200, self._init_mcp_servers)

    def _init_mcp_servers(self) -> None:
        """MCP 서버 상태 파일을 읽어서 활성화된 서버만 시작"""
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
                        # MCP 서버 시작 후 충분한 시간을 두고 도구 라벨 업데이트 삭제
                        print("도구 라벨 업데이트 삭제 - 좌측 패널로 이동")
                    else:
                        print("활성화된 MCP 서버가 없습니다")
                        # 서버가 없을 때도 라벨 업데이트 삭제
                        print("도구 라벨 업데이트 삭제 - 좌측 패널로 이동")
                else:
                    print("MCP 서버 상태 파일이 없습니다")
            except Exception as e:
                print(f"MCP 서버 시작 오류: {e}")
        
        threading.Thread(target=start_servers, daemon=True).start()
    
    # 도구 업데이트 삭제 - 좌측 패널로 이동
    
    def open_settings(self) -> None:
        """Open settings dialog."""
        dlg = SettingsDialog(self)
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            # 설정 저장 후 테마 업데이트
            self._apply_current_theme()
        # 모델 매니저 업데이트 삭제 - 좌측 패널로 이동
    
    def open_mcp(self) -> None:
        """Open MCP import dialog."""
        mcp_path, _ = QFileDialog.getOpenFileName(
            self, 'mcp.json 선택', '', 'JSON 파일 (*.json)'
        )
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
    
    def open_mcp_manager(self) -> None:
        """Open MCP manager dialog."""
        dlg = MCPManagerDialog(self)
        dlg.exec()
        # 도구 라벨 업데이트 삭제 - 좌측 패널로 이동
    
    def show_mcp_dialog(self) -> None:
        """MCP 서버 관리 대화상자 표시"""
        self.open_mcp_manager()
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history with confirmation."""
        reply = QMessageBox.question(
            self, '대화 기록 초기화', 
            '모든 대화 기록을 삭제하시겠습니까?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.chat_widget.clear_conversation_history()
    
    def open_user_prompt(self) -> None:
        """Open user prompt dialog."""
        from ui.user_prompt_dialog import UserPromptDialog
        from core.file_utils import load_model_api_key, load_last_model
        from core.ai_client import AIClient
        
        model = load_last_model()
        api_key = load_model_api_key(model)
        
        if not api_key:
            QMessageBox.warning(
                self, '경고', 
                'API 키가 설정되지 않았습니다. 먼저 환경설정에서 API 키를 입력해주세요.'
            )
            return
        
        ai_client = AIClient(api_key, model)
        dlg = UserPromptDialog(ai_client, self)
        dlg.exec()
    
    def open_config_path_dialog(self) -> None:
        """Open configuration path dialog."""
        from ui.config_path_dialog import ConfigPathDialog
        dlg = ConfigPathDialog(self)
        dlg.exec()
    
    def closeEvent(self, event):
        """애플리케이션 종료 처리"""
        print("애플리케이션 종료 시작")
        
        try:
            # 스플리터 상태 저장
            self._save_splitter_state()
            
            if hasattr(self, 'chat_widget'):
                self.chat_widget.close()
            stop_mcp_servers()
        except Exception as e:
            print(f"종료 중 오류: {e}")
        
        event.accept()
        print("애플리케이션 종료 완료")
    
    # 테마 메뉴 생성 삭제 - 좌측 패널로 이동
    
    def _change_theme(self, theme_key: str):
        """테마 변경"""
        try:
            # 테마 설정
            theme_manager.material_manager.set_theme(theme_key)
            
            # 전체 애플리케이션 스타일시트 업데이트
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                new_stylesheet = theme_manager.get_material_design_stylesheet()
                app.setStyleSheet(new_stylesheet)
                # 메인 윈도우에도 직접 적용
                self.setStyleSheet(new_stylesheet)
            
            self._apply_current_theme()
            
            # 창 제목 업데이트
            self._update_window_title()
            
            # 채팅 위젯의 웹뷰 CSS 업데이트 - 강화된 업데이트
            if hasattr(self, 'chat_widget'):
                print("채팅 위젯 테마 업데이트 시작")
                self.chat_widget.update_theme()
                # 추가 지연 업데이트
                QTimer.singleShot(200, lambda: self.chat_widget.update_theme())
                print("채팅 위젯 테마 업데이트 완료")
            
            # 세션 패널 테마 업데이트
            if hasattr(self, 'session_panel'):
                self.session_panel.update_theme()
            
            # 토큰 패널 테마 업데이트
            if hasattr(self, 'token_display'):
                self.token_display.update_theme()
            
            # 뉴스 배너 테마 업데이트
            if hasattr(self, 'news_banner'):
                self.news_banner.update_theme()
            
            # 스플리터 테마 업데이트
            self._apply_splitter_theme()
            
            # 강제로 전체 위젯 다시 그리기
            self.repaint()
            self.update()
            
            # 지연 시간을 두고 추가 업데이트
            QTimer.singleShot(100, self._delayed_theme_update)
            
        except Exception as e:
            print(f"테마 변경 오류: {e}")
    
    def _delayed_theme_update(self):
        """지연된 테마 업데이트"""
        try:
            # 채팅 위젯 추가 업데이트
            if hasattr(self, 'chat_widget'):
                self.chat_widget.update_theme()
                # 입력 영역 강제 업데이트
                if hasattr(self.chat_widget, 'input_text'):
                    self.chat_widget.input_text.update()
                if hasattr(self.chat_widget, 'input_container'):
                    self.chat_widget.input_container.update()
        except Exception as e:
            print(f"지연된 테마 업데이트 오류: {e}")
    

    
    def _apply_current_theme(self):
        """현재 테마 적용 - 스크롤바 포함"""
        # 전체 애플리케이션에 스타일시트 적용
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            stylesheet = theme_manager.get_material_design_stylesheet()
            app.setStyleSheet(stylesheet)
            # 메인 윈도우에도 직접 적용
            self.setStyleSheet(stylesheet)
        
        # 스플리터 및 스크롤바 스타일 동적 적용
        self._apply_splitter_theme()
    
    def _apply_splitter_theme(self):
        """스플리터 테마 적용 - 세션 패널과 동일한 현대적인 디자인"""
        try:
            colors = theme_manager.material_manager.get_theme_colors()
            primary_color = colors.get('primary', '#bb86fc')
            primary_variant = colors.get('primary_variant', '#3700b3')
            divider_color = colors.get('divider', '#333333')
            surface_color = colors.get('surface', '#1e1e1e')
            
            # 세션 패널과 동일한 스크롤바 및 스플리터 스타일
            splitter_style = f"""
            QSplitter::handle {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {divider_color}, 
                    stop:1 {colors.get('text_secondary', '#888888')});
                border: 1px solid {divider_color};
                border-radius: 6px;
                margin: 2px;
                transition: all 0.3s ease;
            }}
            QSplitter::handle:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {colors.get('text_secondary', '#888888')}, 
                    stop:1 {primary_color});
                border-color: {primary_color};
                transform: translateY(-1px);
            }}
            QSplitter::handle:pressed {{
                background: {primary_variant};
                border-color: {primary_variant};
            }}
            
            /* 스크롤바 스타일 - 세션 패널과 동일 */
            QScrollBar:vertical {{
                background: {colors.get('scrollbar_track', surface_color)};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {colors.get('scrollbar', colors.get('text_secondary', '#b3b3b3'))}, 
                    stop:1 {primary_color});
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {primary_color};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background: {colors.get('scrollbar_track', surface_color)};
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 {colors.get('scrollbar', colors.get('text_secondary', '#b3b3b3'))}, 
                    stop:1 {primary_color});
                border-radius: 4px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {primary_color};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            """
            
            self.splitter.setStyleSheet(splitter_style)
            
        except Exception as e:
            print(f"스플리터 테마 적용 오류: {e}")
    
    def _apply_saved_theme(self):
        """저장된 테마 적용"""
        try:
            current_theme_key = theme_manager.material_manager.current_theme_key
            self._update_window_title()
            
            if hasattr(self, 'chat_widget'):
                self.chat_widget.update_theme()
            
            if hasattr(self, 'session_panel'):
                self.session_panel.update_theme()
        except Exception as e:
            print(f"저장된 테마 적용 오류: {e}")
    
    # 테마 메뉴 체크 상태 업데이트 삭제 - 좌측 패널로 이동
    
    def _update_window_title(self):
        """창 제목을 현재 테마명과 함께 업데이트"""
        try:
            current_theme_key = theme_manager.material_manager.current_theme_key
            available_themes = theme_manager.get_available_material_themes()
            theme_name = available_themes.get(current_theme_key, "Unknown")
            self.setWindowTitle(f'AIAgent - {theme_name}')
        except Exception as e:
            print(f"창 제목 업데이트 오류: {e}")
            self.setWindowTitle('AIAgent')
    
    def toggle_session_panel(self):
        """세션 패널 표시 토글"""
        is_visible = self.session_panel.isVisible()
        self.session_panel.setVisible(not is_visible)
        self.session_panel_action.setChecked(not is_visible)
        
        current_sizes = self.splitter.sizes()
        total_width = sum(current_sizes)
        
        if not is_visible:
            # 세션 패널 표시
            token_width = current_sizes[2] if self.token_display.isVisible() else 0
            self.splitter.setSizes([250, total_width - 250 - token_width, token_width])
        else:
            # 세션 패널 숨김
            token_width = current_sizes[2] if self.token_display.isVisible() else 0
            self.splitter.setSizes([0, total_width - token_width, token_width])
        
        self._save_splitter_state()
    
    def toggle_token_display(self):
        """토큰 사용량 표시 토글"""
        is_visible = self.token_display.isVisible()
        self.token_display.setVisible(not is_visible)
        self.token_usage_action.setChecked(not is_visible)
        
        current_sizes = self.splitter.sizes()
        total_width = sum(current_sizes)
        
        if not is_visible:
            self.token_display.refresh_display()
            # 토큰 창 표시
            session_width = current_sizes[0] if self.session_panel.isVisible() else 0
            token_width = 300
            self.splitter.setSizes([session_width, total_width - session_width - token_width, token_width])
        else:
            # 토큰 창 숨김
            session_width = current_sizes[0] if self.session_panel.isVisible() else 0
            self.splitter.setSizes([session_width, total_width - session_width, 0])
        
        self._save_splitter_state()
    
    def toggle_glassmorphism(self):
        """글래스모피즘 효과 토글"""
        new_state = theme_manager.material_manager.toggle_glassmorphism()
        self.glassmorphism_action.setChecked(new_state)
        
        # 테마 업데이트
        if hasattr(self, 'chat_widget'):
            self.chat_widget.update_theme()
        
        print(f"글래스모피즘 {'ON' if new_state else 'OFF'}")
    
    def _load_splitter_state(self):
        """스플리터 상태 로드"""
        try:
            if os.path.exists('splitter_state.json'):
                with open('splitter_state.json', 'r') as f:
                    state = json.load(f)
                    sizes = state.get('sizes', [250, 950, 0])
                    token_visible = state.get('token_visible', False)
                    session_visible = state.get('session_visible', True)
                    
                    self.splitter.setSizes(sizes)
                    self.token_display.setVisible(token_visible)
                    self.token_usage_action.setChecked(token_visible)
                    self.session_panel.setVisible(session_visible)
                    self.session_panel_action.setChecked(session_visible)
        except Exception as e:
            print(f"스플리터 상태 로드 오류: {e}")
    
    def _save_splitter_state(self):
        """스플리터 상태 저장"""
        try:
            state = {
                'sizes': self.splitter.sizes(),
                'token_visible': self.token_display.isVisible(),
                'session_visible': self.session_panel.isVisible()
            }
            with open('splitter_state.json', 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"스플리터 상태 저장 오류: {e}")
    
    def reset_layout(self):
        """레이아웃 초기화"""
        self.splitter.setSizes([250, 950, 0])
        self.session_panel.setVisible(True)
        self.session_panel_action.setChecked(True)
        self.token_display.setVisible(False)
        self.token_usage_action.setChecked(False)
        self._save_splitter_state()
        print("레이아웃이 초기화되었습니다.")
    
    def _show_export_message(self, message: str):
        """내보내기 메시지 표시"""
        QMessageBox.information(self, '내보내기 완료', message)
    
    def export_current_conversation_pdf(self):
        """현재 대화를 PDF로 내보내기"""
        if not self.current_session_id:
            QMessageBox.warning(self, '경고', '현재 활성된 대화 세션이 없습니다.')
            return
        
        try:
            # 세션 정보 가져오기
            session = session_manager.get_session(self.current_session_id)
            if not session:
                QMessageBox.warning(self, '오류', '세션을 찾을 수 없습니다.')
                return
            
            # 메시지 가져오기 (HTML 포함)
            messages = session_manager.get_session_messages(self.current_session_id, include_html=True)
            if not messages:
                QMessageBox.information(self, '정보', '내보낼 메시지가 없습니다.')
                return
            
            # PDF 내보내기 실행
            from core.pdf_exporter import PDFExporter
            pdf_exporter = PDFExporter(self)
            
            # 메시지 형식 변환 - HTML 콘텐츠 사용
            formatted_messages = []
            for msg in messages:
                # content는 이미 HTML 렌더링된 상태
                content = msg.get('content', '')
                formatted_messages.append({
                    'role': msg.get('role', 'unknown'),
                    'content': content,
                    'timestamp': msg.get('timestamp', '')
                })
            
            success = pdf_exporter.export_conversation_to_pdf(
                formatted_messages, 
                session.get('title', '대화')
            )
            
            if success:
                QMessageBox.information(self, '완료', 'PDF 내보내기가 완료되었습니다.')
            
        except Exception as e:
            print(f"PDF 내보내기 오류: {e}")
            QMessageBox.critical(self, '오류', f'PDF 내보내기 실패: {str(e)}')
    
    def _on_session_selected(self, session_id: int):
        """세션 선택 이벤트 처리 - 안전장치 포함"""
        try:
            # 메인 윈도우의 현재 세션 ID 업데이트
            self.current_session_id = session_id
            self._auto_session_created = True  # 세션이 선택되었으므로 자동 생성 플래그 설정
            
            # 토큰 누적기 세션 설정
            from core.token_accumulator import token_accumulator
            token_accumulator.set_session(session_id)
            
            # 채팅 위젯의 세션 정보 업데이트
            if hasattr(self, 'chat_widget') and hasattr(self.chat_widget, 'update_session_info'):
                self.chat_widget.update_session_info(session_id)
            
            session = session_manager.get_session(session_id)
            if not session:
                QMessageBox.warning(self, '오류', '세션을 찾을 수 없습니다.')
                return
            
            print(f"[SESSION_SELECT] 세션 {session_id} 로드 시도")
            
            # 대용량 세션 체크 (200개 이상 메시지)
            message_count = session.get('message_count', 0)
            if message_count > 200:
                reply = QMessageBox.question(
                    self, '대용량 세션 경고', 
                    f'이 세션에는 {message_count}개의 메시지가 있습니다.\n'
                    f'로드하는데 시간이 걸리고 메모리를 많이 사용할 수 있습니다.\n\n'
                    f'계속 로드하시겠습니까?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    print(f"[SESSION_SELECT] 사용자가 대용량 세션 로드 취소")
                    return
            
            # 채팅 화면 초기화
            if hasattr(self.chat_widget, 'chat_display'):
                self.chat_widget.chat_display.clear_messages()
            
            # 안전한 세션 로드 (타이머로 지연 실행)
            QTimer.singleShot(100, lambda: self._safe_load_session(session_id))
            
            print(f"[SESSION_SELECT] 세션 로드 시작: {session['title']}")
            
        except Exception as e:
            print(f"세션 선택 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def _safe_load_session(self, session_id: int):
        """안전한 세션 로드"""
        try:
            print(f"[SAFE_LOAD] 세션 {session_id} 안전 로드 시작")
            
            # 세션 컨텍스트 로드 (제한된 수량으로)
            if hasattr(self.chat_widget, 'load_session_context'):
                self.chat_widget.load_session_context(session_id)
            
            print(f"[SAFE_LOAD] 세션 {session_id} 안전 로드 완료")
            
        except Exception as e:
            print(f"[SAFE_LOAD] 안전 로드 오류: {e}")
            import traceback
            traceback.print_exc()
            
            # 오류 발생 시 사용자에게 알림
            QMessageBox.critical(
                self, '세션 로드 오류', 
                f'세션을 로드하는 중 오류가 발생했습니다:\n{str(e)}\n\n'
                f'다른 세션을 선택하거나 애플리케이션을 재시작해보세요.'
            )
    
    def _on_session_created(self, session_id: int):
        """새 세션 생성 이벤트 처리"""
        self.current_session_id = session_id
        self._auto_session_created = True  # 세션이 생성되었으므로 자동 생성 플래그 설정
        
        # 토큰 누적기 세션 설정
        from core.token_accumulator import token_accumulator
        token_accumulator.set_session(session_id)
        
        # 채팅 위젯의 세션 정보 업데이트
        if hasattr(self, 'chat_widget') and hasattr(self.chat_widget, 'update_session_info'):
            self.chat_widget.update_session_info(session_id)
        
        # 새 세션이므로 채팅 화면 초기화
        if hasattr(self.chat_widget, 'chat_display'):
            self.chat_widget.chat_display.clear_messages()
        
        # 페이징 변수 초기화
        self.chat_widget.current_session_id = session_id
        self.chat_widget.loaded_message_count = 0
        self.chat_widget.total_message_count = 0
        self.chat_widget.is_loading_more = False
        print(f"새 세션 생성: {session_id}")
    
    def save_message_to_session(self, role: str, content: str, token_count: int = 0, content_html: str = None):
        """메시지를 현재 세션에 저장"""
        print(f"[SAVE_MESSAGE] 시작 - role: {role}, current_session_id: {self.current_session_id}, content 길이: {len(content) if content else 0}")
        
        # 현재 세션이 없으면 자동으로 새 세션 생성
        if not self.current_session_id:
            print(f"[SAVE_MESSAGE] 세션 ID가 없음 - 자동 세션 생성 시도")
            self._create_auto_session()
        
        if self.current_session_id:
            try:
                print(f"[SAVE_MESSAGE] 세션 {self.current_session_id}에 메시지 저장 시도")
                message_id = session_manager.add_message(
                    self.current_session_id, 
                    role, 
                    content, 
                    content_html=content_html,
                    token_count=token_count
                )
                print(f"[SAVE_MESSAGE] 성공 - message_id: {message_id}")
                # 채팅 위젯의 세션 정보 업데이트
                if hasattr(self, 'chat_widget') and hasattr(self.chat_widget, 'update_session_info'):
                    self.chat_widget.update_session_info(self.current_session_id)
                # 세션 패널 새로고침
                self.session_panel.load_sessions()
            except Exception as e:
                print(f"[SAVE_MESSAGE] 오류: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[SAVE_MESSAGE] 실패 - 세션 ID가 여전히 None")
    
    def delete_message_from_session(self, message_id: int) -> bool:
        """세션에서 메시지 삭제"""
        if self.current_session_id:
            try:
                success = message_manager.delete_message(self.current_session_id, message_id)
                if success:
                    # 세션 패널 새로고침
                    self.session_panel.load_sessions()
                return success
            except Exception as e:
                print(f"메시지 삭제 오류: {e}")
                return False
        return False
    
    def _create_auto_session(self):
        """자동 세션 생성"""
        print(f"[AUTO_SESSION] 시작 - _auto_session_created: {self._auto_session_created}")
        if not self._auto_session_created:
            try:
                from datetime import datetime
                title = f"대화 {datetime.now().strftime('%m/%d %H:%M')}"
                print(f"[AUTO_SESSION] 세션 생성 시도 - title: {title}")
                self.current_session_id = session_manager.create_session(title)
                self._auto_session_created = True
                print(f"[AUTO_SESSION] 성공 - session_id: {self.current_session_id}")
                
                # 채팅 위젯의 세션 정보 업데이트
                if hasattr(self, 'chat_widget') and hasattr(self.chat_widget, 'update_session_info'):
                    self.chat_widget.update_session_info(self.current_session_id)
                
                # 세션 패널 새로고침
                self.session_panel.load_sessions()
                # 생성된 세션 선택
                self.session_panel.select_session(self.current_session_id)
            except Exception as e:
                print(f"[AUTO_SESSION] 오류: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[AUTO_SESSION] 이미 생성됨 - current_session_id: {self.current_session_id}")
    
