import sys
import threading
import logging
import os
from core.application import SignalHandler, AppInitializer, AppRunner
from ui.performance_optimizer import performance_optimizer


def main() -> int:
    """Main application entry point."""
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
    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-web-security --disable-features=VizDisplayCompositor'
    os.environ['QT_LOGGING_RULES'] = 'qt.webenginecontext.debug=false'
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Initialize application components
    initializer = AppInitializer(sys.argv)
    app = initializer.create_application()
    
    # Apply performance optimizations
    performance_optimizer.optimize_application(app)

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
        return 1


if __name__ == "__main__":
    sys.exit(main())
