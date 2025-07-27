import sys
import threading
from core.application import SignalHandler, AppInitializer, AppRunner


def main() -> int:
    """Main application entry point."""
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