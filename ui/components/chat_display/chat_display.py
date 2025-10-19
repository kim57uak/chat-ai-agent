"""
Chat Display - Refactored
채팅 디스플레이 - 리팩토링된 버전
"""

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from ui.components.progressive_display import ProgressiveDisplay
from core.logging import get_logger

from .html_template_builder import HtmlTemplateBuilder
from .webview_configurator import WebViewConfigurator
from .message_renderer import MessageRenderer
from .theme_manager import ThemeManager as ChatThemeManager
from .link_handler import LinkHandler

logger = get_logger("chat_display")


class ChatDisplay:
    """채팅 표시를 담당하는 클래스 (SRP) - Facade 패턴"""

    def __init__(self, web_view: QWebEngineView):
        self.web_view = web_view
        self.progressive_display = ProgressiveDisplay(web_view)
        
        # UI 설정 로드
        self._load_ui_settings()
        
        # 컴포넌트 초기화
        self.html_builder = HtmlTemplateBuilder(web_view)
        self.webview_config = WebViewConfigurator(web_view)
        self.message_renderer = MessageRenderer(
            web_view, 
            self.progressive_display,
            self.progressive_enabled,
            self.delay_per_line,
            self.initial_delay
        )
        self.theme_mgr = ChatThemeManager(web_view)
        
        # 링크 핸들러 설정
        self._setup_link_handler()
        
        # 웹뷰 초기화
        self.init_web_view()

    def _load_ui_settings(self):
        """UI 설정 로드"""
        try:
            from core.file_utils import load_config

            config = load_config()
            ui_settings = config.get("ui_settings", {})
            progressive_settings = ui_settings.get("progressive_display", {})

            self.progressive_enabled = progressive_settings.get("enabled", True)
            self.delay_per_line = progressive_settings.get("delay_per_line", 30)
            self.initial_delay = progressive_settings.get("initial_delay", 100)
        except Exception as e:
            # 설정 로드 실패 시 기본값 사용
            self.progressive_enabled = True
            self.delay_per_line = 30
            self.initial_delay = 100

    def init_web_view(self):
        """웹 브라우저 초기화"""
        # 웹뷰 설정
        self.webview_config.configure()
        
        # 콘솔 메시지 캡처
        self.web_view.page().javaScriptConsoleMessage = self.webview_config.handle_console_message
        
        # HTML 템플릿 로드
        self.html_builder.load_html_template()

    def _setup_link_handler(self):
        """링크 클릭 핸들러 안전 설정"""
        try:
            # 웹 채널 안전 설정
            self.channel = QWebChannel()
            self.link_handler = LinkHandler()
            self.channel.registerObject("pyqt_bridge", self.link_handler)
            self.web_view.page().setWebChannel(self.channel)
            logger.debug("웹 채널 설정 완료")
            
        except Exception as e:
            logger.debug(f"웹 채널 설정 오류: {e}")
            # 채널 설정 실패 시 기본 핸들러만 생성
            self.link_handler = LinkHandler()
    
    def set_auth_manager(self, auth_manager):
        """AuthManager 설정"""
        if hasattr(self, 'link_handler'):
            self.link_handler.auth_manager = auth_manager

    def set_chat_widget(self, chat_widget):
        """채팅 위젯 참조 설정"""
        self.link_handler.chat_widget = chat_widget
    
    def set_auth_manager_from_main(self, main_window):
        """MainWindow에서 AuthManager 설정"""
        if hasattr(main_window, 'auth_manager'):
            self.set_auth_manager(main_window.auth_manager)

    def append_message(
        self,
        sender,
        text,
        original_sender=None,
        progressive=False,
        message_id=None,
        prepend=False,
        timestamp=None,
    ):
        """메시지 추가 - MessageRenderer에 위임"""
        return self.message_renderer.append_message(
            sender, text, original_sender, progressive, 
            message_id, prepend, timestamp
        )

    def clear_messages(self):
        """메시지 초기화"""
        self.progressive_display.cancel_current_display()
        self.init_web_view()

    def cancel_progressive_display(self):
        """점진적 출력 취소"""
        self.progressive_display.cancel_current_display()
    
    def is_dark_theme(self) -> bool:
        """현재 테마가 다크 테마인지 확인"""
        return self.theme_mgr.is_dark_theme()
    
    def update_theme(self):
        """테마 업데이트"""
        self.theme_mgr.update_theme()
    
    def handle_console_message(self, level, message, line_number, source_id):
        """콘솔 메시지 처리 - WebViewConfigurator에 위임"""
        self.webview_config.handle_console_message(level, message, line_number, source_id)
