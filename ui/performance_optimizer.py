"""
from core.logging import get_logger

logger = get_logger("performance_optimizer")
성능 최적화 모듈 - Windows/macOS 크로스 플랫폼 지원
"""
import platform
import os
from PyQt6.QtCore import QThread, QTimer
from PyQt6.QtWidgets import QApplication


class PerformanceOptimizer:
    """성능 최적화 클래스"""
    
    def __init__(self):
        self.system = platform.system()
        self.is_windows = self.system == "Windows"
        self.is_macos = self.system == "Darwin"
        
    def optimize_webview(self, web_view):
        """웹뷰 성능 최적화"""
        settings = web_view.settings()
        
        # 기본 최적화
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        
        # 플랫폼별 최적화
        if self.is_windows:
            self._optimize_windows_webview(settings, web_view)
        elif self.is_macos:
            self._optimize_macos_webview(settings, web_view)
            
        # 공통 최적화
        self._optimize_common_webview(settings, web_view)
        
    def _optimize_windows_webview(self, settings, web_view):
        """Windows 전용 웹뷰 최적화"""
        try:
            # DirectX 가속 활성화
            settings.setAttribute(settings.WebAttribute.Accelerated2dCanvasEnabled, True)
            settings.setAttribute(settings.WebAttribute.WebGLEnabled, True)
            
            # 캐시 크기 증가 (Windows는 메모리가 많음)
            web_view.page().profile().setHttpCacheMaximumSize(150 * 1024 * 1024)
            
            # Windows 전용 스크롤 최적화
            settings.setAttribute(settings.WebAttribute.ScrollAnimatorEnabled, True)
            
        except (AttributeError, RuntimeError):
            pass
            
    def _optimize_macos_webview(self, settings, web_view):
        """macOS 전용 웹뷰 최적화"""
        try:
            # Metal 가속 활성화
            settings.setAttribute(settings.WebAttribute.Accelerated2dCanvasEnabled, True)
            settings.setAttribute(settings.WebAttribute.WebGLEnabled, True)
            
            # macOS 적정 캐시 크기
            web_view.page().profile().setHttpCacheMaximumSize(100 * 1024 * 1024)
            
            # macOS 네이티브 스크롤
            settings.setAttribute(settings.WebAttribute.ScrollAnimatorEnabled, True)
            
        except (AttributeError, RuntimeError):
            pass
            
    def _optimize_common_webview(self, settings, web_view):
        """공통 웹뷰 최적화"""
        try:
            # 메모리 캐시 사용
            web_view.page().profile().setHttpCacheType(
                web_view.page().profile().HttpCacheType.MemoryHttpCache
            )
            
            # 플러그인 비활성화 (성능 향상)
            settings.setAttribute(settings.WebAttribute.PluginsEnabled, False)
            
            # 자동 이미지 로드 (필요시)
            settings.setAttribute(settings.WebAttribute.AutoLoadImages, True)
            
        except (AttributeError, RuntimeError):
            pass
            
    def get_optimized_css(self):
        """플랫폼별 최적화된 CSS 반환"""
        base_css = """
        /* 기본 성능 최적화 */
        * {
            box-sizing: border-box;
        }
        
        html, body {
            scroll-behavior: smooth;
            -webkit-overflow-scrolling: touch;
            transform: translateZ(0);
            will-change: scroll-position;
        }
        
        #messages {
            contain: layout style paint;
            transform: translateZ(0);
            backface-visibility: hidden;
            perspective: 1000px;
        }
        
        .message {
            contain: layout style;
            transform: translateZ(0);
            will-change: transform;
            transition: transform 0.2s ease;
        }
        
        .message:hover {
            transform: translateZ(0) translateY(-1px);
        }
        """
        
        if self.is_windows:
            return base_css + self._get_windows_css()
        elif self.is_macos:
            return base_css + self._get_macos_css()
        else:
            return base_css
            
    def _get_windows_css(self):
        """Windows 전용 CSS"""
        return """
        /* Windows 애니메이션 최적화 */
        .message {
            animation-duration: 0.3s;
            animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
        }
        """
        
    def _get_macos_css(self):
        """macOS 전용 CSS"""
        return """
        /* macOS 네이티브 스타일 애니메이션 */
        .message {
            animation-duration: 0.25s;
            animation-timing-function: cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }
        
        /* macOS 블러 효과 */
        .message {
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        """
        
    def optimize_application(self, app):
        """애플리케이션 전체 성능 최적화"""
        if not isinstance(app, QApplication):
            return
            
        # 플랫폼별 최적화
        if self.is_windows:
            self._optimize_windows_app(app)
        elif self.is_macos:
            self._optimize_macos_app(app)
            
        # 공통 최적화
        self._optimize_common_app(app)
        
    def _optimize_windows_app(self, app):
        """Windows 애플리케이션 최적화"""
        try:
            # Windows DPI 인식 설정
            app.setAttribute(app.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            app.setAttribute(app.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
            
            # Windows 렌더링 최적화
            app.setAttribute(app.ApplicationAttribute.AA_UseOpenGLES, True)
            
        except (AttributeError, RuntimeError):
            pass
            
    def _optimize_macos_app(self, app):
        """macOS 애플리케이션 최적화"""
        try:
            # Retina 디스플레이 최적화
            app.setAttribute(app.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            app.setAttribute(app.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
            
            # macOS Metal 렌더링
            app.setAttribute(app.ApplicationAttribute.AA_UseSoftwareOpenGL, False)
            
        except (AttributeError, RuntimeError):
            pass
            
    def _optimize_common_app(self, app):
        """공통 애플리케이션 최적화"""
        try:
            # 안티앨리어싱 활성화
            app.setAttribute(app.ApplicationAttribute.AA_SynthesizeTouchForUnhandledMouseEvents, True)
            
            # 압축된 이벤트 사용
            app.setAttribute(app.ApplicationAttribute.AA_CompressHighFrequencyEvents, True)
            
        except (AttributeError, RuntimeError):
            pass
            
    def get_memory_usage(self):
        """메모리 사용량 확인"""
        try:
            import psutil
            process = psutil.Process()
            return {
                'memory_percent': process.memory_percent(),
                'memory_info': process.memory_info(),
                'cpu_percent': process.cpu_percent()
            }
        except ImportError:
            return None
            
    def cleanup_memory(self):
        """메모리 정리"""
        try:
            import gc
            gc.collect()
            
            # 플랫폼별 메모리 정리
            if self.is_windows:
                self._cleanup_windows_memory()
            elif self.is_macos:
                self._cleanup_macos_memory()
                
        except Exception as e:
            logger.debug(f"메모리 정리 오류: {e}")
            
    def _cleanup_windows_memory(self):
        """Windows 메모리 정리"""
        try:
            import ctypes
            # Windows API를 통한 메모리 정리
            ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
        except:
            pass
            
    def _cleanup_macos_memory(self):
        """macOS 메모리 정리"""
        try:
            # macOS 메모리 압축 힌트
            os.system("purge > /dev/null 2>&1 &")
        except:
            pass


# 전역 최적화 인스턴스
performance_optimizer = PerformanceOptimizer()