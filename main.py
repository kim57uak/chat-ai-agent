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
    
    # Setup signal handling only in main thread
    if threading.current_thread() is threading.main_thread():
        signal_handler = SignalHandler()
    
    # Run application
    runner = AppRunner(app)
    return runner.run()


if __name__ == '__main__':
    sys.exit(main())