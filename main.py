import sys
import threading
import logging
from core.application import SignalHandler, AppInitializer, AppRunner


def main() -> int:
    """Main application entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Initialize application components
    initializer = AppInitializer(sys.argv)
    app = initializer.create_application()
    
    # Set application icon
    from PyQt6.QtGui import QIcon
    import os
    if os.path.exists('image/app_icon_128.png'):
        app.setWindowIcon(QIcon('image/app_icon_128.png'))
    elif os.path.exists('image/Agentic_AI_transparent.png'):
        app.setWindowIcon(QIcon('image/Agentic_AI_transparent.png'))
    
    # Setup signal handling only in main thread
    if threading.current_thread() is threading.main_thread():
        signal_handler = SignalHandler()
    
    # Run application
    runner = AppRunner(app)
    return runner.run()


if __name__ == '__main__':
    sys.exit(main())