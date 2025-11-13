import sys
import threading
import logging
import os
import multiprocessing
import signal
import atexit

# 로깅 시스템 초기화 (가장 먼저)
from core.logging import setup_logging
setup_logging()

# PyInstaller 환경에서 데이터 분석 라이브러리 사전 로드
if getattr(sys, 'frozen', False):
    try:
        import pandas.plotting
        import numpy.core
        import matplotlib.pyplot
        import scipy.stats
        import seaborn
        
        sys.modules['pandas.plotting'] = pandas.plotting
        sys.modules['numpy.core'] = numpy.core
        sys.modules['matplotlib.pyplot'] = matplotlib.pyplot
        sys.modules['scipy.stats'] = scipy.stats
        sys.modules['seaborn'] = seaborn
    except Exception:
        pass

from core.application import SignalHandler, AppInitializer, AppRunner
from ui.performance_optimizer import performance_optimizer
from memory_cleanup import memory_cleanup


def qt_message_handler(mode, context, message):
    """Qt 메시지 필터링 - CSS 경고 숨기기 + FATAL 방지"""
    # CSS 관련 경고 메시지 필터링
    if 'Unknown property' in message or 'box-shadow' in message or 'transform' in message or 'transition' in message:
        return
    # CRITICAL: QtFatalMsg를 Critical로 다운그레이드하여 abort() 방지
    if mode == 0:  # QtDebugMsg
        logging.debug(message)
    elif mode == 1:  # QtWarningMsg
        logging.warning(message)
    elif mode == 2:  # QtCriticalMsg
        logging.error(message)
    elif mode == 3:  # QtFatalMsg
        logging.critical(f"[PREVENTED CRASH] {message}")
        # abort() 호출 방지 - 로그만 남기고 계속 실행


def cleanup_resources():
    """리소스 정리 - 최소화"""
    try:
        from core.safe_timer import safe_timer_manager
        safe_timer_manager.cleanup_all()
    except:
        pass
    
    try:
        from mcp.client.mcp_client import mcp_manager
        mcp_manager.close_all()
    except:
        pass


def main() -> int:
    """Main application entry point."""
    # 종료 시 리소스 정리 등록
    atexit.register(cleanup_resources)
    
    # 시그널 핸들러 등록 (SIGABRT 방지)
    def signal_handler(signum, frame):
        cleanup_resources()
        sys.exit(1)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Load user environment variables for packaged apps (Node.js, npm, npx)
    try:
        from utils.env_loader import load_user_environment
        load_user_environment()
        logging.info("환경변수 로더 실행 완료")
    except Exception as e:
        logging.warning(f"환경변수 로더 실행 실패: {e}")
    
    # Remove problematic proxy environment variable for Google API
    if 'EXPERIMENTAL_HTTP_PROXY_SUPPORT' in os.environ:
        del os.environ['EXPERIMENTAL_HTTP_PROXY_SUPPORT']
    
    # Set DNS for tethering environment
    os.environ['GRPC_DNS_RESOLVER'] = 'native'
    os.environ['GRPC_VERBOSITY'] = 'ERROR'
    
    # PyQt6 WebEngine 안정성을 위한 환경 변수 설정
    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-web-security --disable-features=VizDisplayCompositor --no-sandbox --disable-gpu-sandbox --disable-dev-shm-usage'
    os.environ['QT_LOGGING_RULES'] = 'qt.webenginecontext.debug=false;*.debug=false'
    os.environ['QT_FATAL_WARNINGS'] = '0'
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'
    
    # CRITICAL: PyQt6 슬롯 예외를 fatal로 처리하지 않도록 설정
    os.environ['PYQT_FATAL_EXCEPTIONS'] = '0'
    
    # CRITICAL: Prevent Qt event loop conflicts with async logging
    os.environ['PYTHONUNBUFFERED'] = '1'  # Unbuffered output for logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Initialize application components
    initializer = AppInitializer(sys.argv)
    app = initializer.create_application()
    
    # CRITICAL: QtWebEngine 초기화 (QApplication 생성 직후)
    try:
        from PyQt6 import QtWebEngineCore
        # QtWebEngine 초기화 강제 실행
        QtWebEngineCore.QWebEngineProfile.defaultProfile()
        logging.info("QtWebEngine 초기화 완료")
    except Exception as e:
        logging.error(f"QtWebEngine 초기화 실패: {e}")
    
    # Qt 메시지 핸들러 설치 (CSS 경고 숨기기)
    try:
        from PyQt6.QtCore import qInstallMessageHandler
        qInstallMessageHandler(qt_message_handler)
    except Exception as e:
        logging.warning(f"Qt message handler 설치 실패: {e}")
    
    # Apply performance optimizations
    performance_optimizer.optimize_application(app)
    
    # 메모리 자동 정리 시작
    memory_cleanup.start_auto_cleanup()

    # Set application icon with error handling
    try:
        from PyQt6.QtGui import QIcon

        if os.path.exists("image/app_icon_128.png"):
            app.setWindowIcon(QIcon("image/app_icon_128.png"))
        elif os.path.exists("image/Agentic_AI_transparent.png"):
            app.setWindowIcon(QIcon("image/Agentic_AI_transparent.png"))
    except Exception as e:
        logging.warning(f"Failed to set application icon: {e}")

    try:
        # Setup signal handling only in main thread
        if threading.current_thread() is threading.main_thread():
            signal_handler = SignalHandler()

        # Run application
        runner = AppRunner(app)
        return runner.run()
        
    except Exception as e:
        logging.error(f"Application runtime error: {e}")
        import traceback
        traceback.print_exc()
        cleanup_resources()
        return 1
    finally:
        cleanup_resources()


if __name__ == "__main__":
    # PyInstaller freeze 지원 (무한 실행 방지)
    multiprocessing.freeze_support()
    
    # 멀티프로세싱 시작 방법 설정 (macOS 안정성)
    if sys.platform == 'darwin':
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            pass  # 이미 설정됨
    
    try:
        exit_code = main()
        cleanup_resources()
        # CRITICAL: 패키징 환경에서 Python 종료 시 크래시 방지
        if getattr(sys, 'frozen', False):
            os._exit(exit_code)  # Python 종료 프로세스 건너뛰기
        else:
            sys.exit(exit_code)
    except KeyboardInterrupt:
        cleanup_resources()
        if getattr(sys, 'frozen', False):
            os._exit(0)
        else:
            sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        cleanup_resources()
        if getattr(sys, 'frozen', False):
            os._exit(1)
        else:
            sys.exit(1)
