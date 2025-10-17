"""
Main Window - Refactored
메인 윈도우 - 리팩토링된 버전
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QSplitter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import os

from utils.env_loader import load_user_environment
from ui.chat_widget import ChatWidget
from ui.components.token_usage_display import TokenUsageDisplay
from ui.session_panel import SessionPanel
from mcp.servers.mcp import stop_mcp_servers
from ui.components.status_display import status_display
from ui.memory_manager import memory_manager
from core.session.session_manager import initialize_session_manager
from core.auth.auth_manager import AuthManager
from ui.auth.login_dialog import LoginDialog
from core.logging import get_logger
from core.safe_timer import safe_timer_manager

# 매니저 클래스 import
from .menu_manager import MenuManager
from .theme_controller import ThemeController
from .session_controller import SessionController
from .layout_manager import LayoutManager
from .dialog_manager import DialogManager
from .mcp_initializer import MCPInitializer

logger = get_logger("main_window")


class MainWindow(QMainWindow):
    """메인 윈도우 - 컴포넌트 조합 패턴"""
    
    def __init__(self):
        logger.debug("MainWindow.__init__() 시작")
        super().__init__()
        logger.debug("super().__init__() 완료")
        
        # 통합 타이머
        from ui.unified_timer import get_unified_timer
        self._unified_timer = get_unified_timer()
        
        # 타이머 변수 초기화
        self.session_timer = None
        
        # 인증 시스템 초기화
        from utils.security_config import load_logout_timeout
        logout_timeout = load_logout_timeout()
        self.auth_manager = AuthManager(auto_logout_minutes=logout_timeout)
        
        # 인증 체크
        if not self._check_authentication():
            self.close()
            return
        
        # 환경변수 로드
        logger.debug("환경변수 로드 시작")
        load_user_environment()
        logger.debug("환경변수 로드 완료")
        
        # 매니저 초기화
        self.menu_manager = MenuManager(self)
        self.theme_controller = ThemeController(self)
        self.session_controller = SessionController(self)
        self.layout_manager = LayoutManager(self)
        self.dialog_manager = DialogManager(self)
        self.mcp_initializer = MCPInitializer(self)
        
        # UI 설정
        logger.debug("_setup_window() 시작")
        self._setup_window()
        logger.debug("_setup_window() 완료")
        
        logger.debug("_setup_ui() 시작")
        self._setup_ui()
        logger.debug("_setup_ui() 완료")
        
        # MCP 초기화
        logger.debug("MCP 초기화 시작")
        self.mcp_initializer.initialize()
        logger.debug("MCP 초기화 완료")
        
        logger.debug("MainWindow 초기화 완료")
        
        # 세션 만료 타이머 설정
        self._setup_session_timer()
    
    def _setup_window(self):
        """윈도우 설정"""
        self._update_window_title()
        self.setGeometry(100, 100, 1400, 900)
        
        # 애플리케이션 아이콘 설정
        if os.path.exists('image/app_icon_128.png'):
            self.setWindowIcon(QIcon('image/app_icon_128.png'))
        elif os.path.exists('image/Agentic_AI_transparent.png'):
            self.setWindowIcon(QIcon('image/Agentic_AI_transparent.png'))
        
        self.theme_controller.apply_current_theme()
    
    def _setup_ui(self):
        """UI 구성"""
        logger.debug("_setup_ui: Central widget 생성 시작")
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        logger.debug("_setup_ui: Splitter 생성 시작")
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setChildrenCollapsible(False)
        
        logger.debug("_setup_ui: SessionPanel 생성 시작")
        self.session_panel = SessionPanel(self)
        self.session_panel.session_selected.connect(self.session_controller.on_session_selected)
        self.session_panel.session_created.connect(self.session_controller.on_session_created)
        self.splitter.addWidget(self.session_panel)
        
        logger.debug("_setup_ui: Chat container 생성 시작")
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        logger.debug("_setup_ui: NewsBanner 생성 시작")
        from ui.components.news_banner_simple import NewsBanner
        self.news_banner = NewsBanner(self)
        self.news_banner.setMaximumHeight(44)
        self.news_banner.setContentsMargins(0, 0, 0, 5)
        chat_layout.addWidget(self.news_banner)
        chat_layout.addSpacing(3)
        
        logger.debug("_setup_ui: ChatWidget 생성 시작")
        self.chat_widget = ChatWidget(self)
        self.chat_widget.setMinimumWidth(400)
        chat_layout.addWidget(self.chat_widget)
        
        chat_container.setMinimumWidth(400)
        self.splitter.addWidget(chat_container)
        
        logger.debug("_setup_ui: TokenUsageDisplay 생성 시작")
        self.token_display = TokenUsageDisplay(self)
        self.token_display.setVisible(True)
        self.token_display.setMinimumWidth(250)
        self.token_display.setMaximumWidth(600)
        self.token_display.export_requested.connect(self.dialog_manager.show_export_message)
        self.splitter.addWidget(self.token_display)
        
        # 스플리터 비율 설정
        self.splitter.setSizes([250, 700, 300])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 3)
        self.splitter.setStretchFactor(2, 1)
        
        # 세션 ID 추적 (SessionController와 동기화)
        self.current_session_id = None
        self._auto_session_created = False
        
        # 세션 패널에 메인 윈도우 참조 전달
        self.session_panel.main_window = self
        
        # 스플리터 상태 저장/복원
        self.layout_manager.load_splitter_state()
        self.splitter.splitterMoved.connect(self.layout_manager.save_splitter_state)
        
        layout.addWidget(self.splitter)
        self.setCentralWidget(central_widget)
        
        # 상태 표시 초기화
        status_display.status_updated.emit(status_display.current_status.copy())
        
        logger.debug("_setup_ui: Menu 생성 시작")
        self.menu_manager.create_menu_bar()
        logger.debug("_setup_ui: Menu 생성 완료")
        
        logger.debug("_setup_ui: 저장된 테마 적용 시작")
        self.theme_controller.apply_saved_theme()
        logger.debug("_setup_ui: 저장된 테마 적용 완료")
        
        # 메모리 관리 시작
        memory_manager.start_monitoring()
        memory_manager.memory_warning.connect(self._on_memory_warning)
    
    def _change_theme(self, theme_key: str):
        """테마 변경 (세션 패널에서 호출)"""
        self.theme_controller.change_theme(theme_key)
    
    def _update_window_title(self):
        """창 제목 업데이트"""
        try:
            from ui.styles.theme_manager import theme_manager
            current_theme_key = theme_manager.material_manager.current_theme_key
            available_themes = theme_manager.get_available_material_themes()
            theme_name = available_themes.get(current_theme_key, "Unknown")
            
            session_name = ""
            if hasattr(self, 'session_controller') and self.session_controller.current_session_id:
                from core.session.session_manager import session_manager
                if session_manager:
                    session = session_manager.get_session(self.session_controller.current_session_id)
                    if session:
                        session_name = f" - {session['title']}"
            
            self.setWindowTitle(f'AIChat - {theme_name}{session_name}')
        except Exception as e:
            logger.debug(f"창 제목 업데이트 오류: {e}")
            self.setWindowTitle('AIChat')
    
    def save_message_to_session(self, role: str, content: str, token_count: int = 0, content_html: str = None):
        """메시지 저장 (SessionController에 위임)"""
        self.session_controller.save_message(role, content, token_count, content_html)
        # 메인 윈도우의 current_session_id도 동기화
        self.current_session_id = self.session_controller.current_session_id
        self._auto_session_created = self.session_controller._auto_session_created
    
    def show_mcp_dialog(self):
        """MCP 서버 관리 대화상자 표시"""
        self.dialog_manager.open_mcp_manager()
    
    def _check_authentication(self) -> bool:
        """인증 체크"""
        if os.environ.get('CHAT_AI_TEST_MODE') == '1':
            if self.auth_manager.is_setup_required():
                self.auth_manager.setup_first_time("test_password_123")
            else:
                self.auth_manager.login("test_password_123")
            return True
        
        if not self.auth_manager.is_logged_in():
            login_dialog = LoginDialog(self.auth_manager, self)
            login_dialog.login_successful.connect(self._on_login_successful)
            
            if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
                return False
        else:
            global session_manager
            session_manager = initialize_session_manager(self.auth_manager)
        
        return True
    
    def _on_login_successful(self):
        """로그인 성공 처리"""
        logger.debug("로그인 성공")
        
        from core.session.session_manager import session_manager, set_auth_manager
        if session_manager:
            set_auth_manager(self.auth_manager)
        else:
            from core.session.session_manager import initialize_session_manager
            initialize_session_manager(self.auth_manager)
        
        self._setup_session_timer()
    
    def _setup_session_timer(self):
        """세션 만료 타이머 설정"""
        if self.session_timer is None:
            self.session_timer = safe_timer_manager.create_timer(
                60000, self._check_session_expiry, single_shot=False, parent=self
            )
        if self.session_timer:
            self.session_timer.start()
    
    def _check_session_expiry(self):
        """세션 만료 체크"""
        if not self.auth_manager.is_logged_in():
            self._handle_session_expired()
    
    def _handle_session_expired(self):
        """세션 만료 처리"""
        from PyQt6.QtWidgets import QMessageBox
        
        if self.session_timer is not None:
            self.session_timer.stop()
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("세션 만료")
        msg_box.setText("비활성 상태로 인해 세션이 만료되었습니다.\n다시 로그인해주세요.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.theme_controller.apply_dialog_theme(msg_box)
        msg_box.exec()
        
        self._check_authentication()
    
    def _on_memory_warning(self, memory_percent):
        """메모리 경고 처리"""
        logger.debug(f"메모리 사용률 경고: {memory_percent:.1f}%")
    
    def closeEvent(self, event):
        """애플리케이션 종료 처리"""
        logger.debug("애플리케이션 종료 시작")
        
        try:
            # SafeTimer 정리
            safe_timer_manager.cleanup_all()
            
            # 세션 타이머 정리
            if self.session_timer is not None:
                try:
                    self.session_timer.stop()
                    self.session_timer.deleteLater()
                except:
                    pass
            
            # 메모리 관리 중지
            try:
                memory_manager.stop_monitoring()
            except:
                pass
            
            # 스플리터 상태 저장
            try:
                self.layout_manager.save_splitter_state()
            except:
                pass
            
            # 채팅 위젯 종료
            if hasattr(self, 'chat_widget'):
                try:
                    self.chat_widget.close()
                except:
                    pass
            
            # MCP 서버 종료
            try:
                stop_mcp_servers()
            except:
                pass
            
            # 최종 메모리 정리
            try:
                memory_manager.force_cleanup()
            except:
                pass
            
            # 가비지 컬렉션
            import gc
            gc.collect()
            
        except Exception as e:
            try:
                logger.debug(f"종료 중 오류: {e}")
            except:
                print(f"종료 중 오류: {e}")
        
        event.accept()
        try:
            logger.debug("애플리케이션 종료 완료")
        except:
            print("애플리케이션 종료 완료")
