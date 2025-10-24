"""
WebView Configurator
웹뷰 설정 전담
"""

from core.logging import get_logger

logger = get_logger("webview_configurator")


class WebViewConfigurator:
    """웹뷰 설정 관리"""
    
    def __init__(self, web_view):
        self.web_view = web_view
    
    def configure(self):
        """웹 브라우저 초기화 - 고급 다크 테마"""
        from ui.styles.theme_manager import theme_manager
        from PyQt6.QtCore import Qt
        
        # CRITICAL: WebEngine 키 이벤트 크래시 방지
        # WebEngine이 키보드 포커스를 받지 못하도록 설정
        self.web_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.web_view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # 웹 보안 설정 완화 (PyQt6 호환)
        settings = self.web_view.settings()
        settings.setAttribute(
            settings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)
        
        # 패키징 환경 디버깅: 개발자 도구 활성화
        try:
            from PyQt6.QtWebEngineCore import QWebEngineSettings
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
            # 개발자 도구 활성화 (패키징 환경에서도 사용 가능)
            self.web_view.page().settings().setAttribute(
                QWebEngineSettings.WebAttribute.DeveloperExtrasEnabled, True
            )
            logger.info("패키징 환경 디버깅 모드 활성화: 우클릭 > Inspect 사용 가능")
        except Exception as e:
            logger.debug(f"개발자 도구 활성화 실패: {e}")

        # PyQt6에서 지원하는 속성만 안전하게 사용
        try:
            settings.setAttribute(
                settings.WebAttribute.AllowRunningInsecureContent, True
            )
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"AllowRunningInsecureContent 설정 실패 (무시됨): {e}")
        
        try:
            settings.setAttribute(
                settings.WebAttribute.PlaybackRequiresUserGesture, False
            )
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"PlaybackRequiresUserGesture 설정 실패 (무시됨): {e}")

        # 웹뷰 배경 설정 (안전한 방식으로 변경)
        try:
            # PyQt6에서 setBackgroundColor 호출 시 크래시 방지
            from PyQt6.QtGui import QColor
            from ui.styles.theme_manager import theme_manager
            
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                bg_color = QColor(colors.get('background', '#121212'))
            else:
                bg_color = QColor('#1a1a1a')
            
            # setBackgroundColor 대신 CSS로 배경색 설정
            # self.web_view.page().setBackgroundColor(bg_color)  # 크래시 원인
            
        except Exception as e:
            logger.debug(f"웹뷰 배경 설정 오류 (무시됨): {e}")
        
        # 성능 최적화 적용
        from ui.performance_optimizer import performance_optimizer
        performance_optimizer.optimize_webview(self.web_view)

        # 스크롤 성능 향상을 위한 추가 설정
        from PyQt6.QtCore import QUrl
        import platform
        
        # 플랫폼별 최적화
        system = platform.system()
        
        # 캐시 설정
        self.web_view.page().profile().setHttpCacheType(
            self.web_view.page().profile().HttpCacheType.MemoryHttpCache
        )
        cache_size = 100 * 1024 * 1024 if system == "Windows" else 50 * 1024 * 1024
        self.web_view.page().profile().setHttpCacheMaximumSize(cache_size)
        
        # 하드웨어 가속 활성화
        try:
            web_settings = self.web_view.settings()
            web_settings.setAttribute(web_settings.WebAttribute.Accelerated2dCanvasEnabled, True)
            web_settings.setAttribute(web_settings.WebAttribute.WebGLEnabled, True)
        except (AttributeError, RuntimeError):
            pass
            
        # 스크롤 최적화
        try:
            web_settings = self.web_view.settings()
            web_settings.setAttribute(web_settings.WebAttribute.ScrollAnimatorEnabled, True)
        except (AttributeError, RuntimeError):
            pass
    
    def handle_console_message(self, level, message, line_number, source_id):
        """자바스크립트 콘솔 메시지 처리 - Mermaid 오류 완전 차단"""
        # Mermaid 관련 모든 오류 메시지 완전 차단
        message_lower = message.lower()
        blocked_keywords = [
            'mermaid', 'syntax error', 'parse error', 'diagram error',
            'version 11.12.0', 'rendering error', 'invalid syntax',
            'diagram syntax', 'mermaid.min.js'
        ]
        
        for keyword in blocked_keywords:
            if keyword in message_lower:
                return  # 완전히 무시
        
        # 일반 메시지만 출력
        logger.debug(f"[JS Console] {message} (line: {line_number})")
