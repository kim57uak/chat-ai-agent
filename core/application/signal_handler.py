"""Signal handling for graceful application shutdown."""

import signal
from typing import Callable
from PyQt6.QtWidgets import QApplication


class SignalHandler:
    """Handles system signals for graceful application shutdown."""
    
    def __init__(self, quit_callback: Callable[[], None] = None):
        self._quit_callback = quit_callback or QApplication.quit
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except ValueError:
            # Signal handlers can only be set in main thread
            pass
    
    def _handle_signal(self, signum: int, frame) -> None:
        """Handle received signals."""
        print(f"Signal {signum} received, shutting down gracefully...")
        self._quit_callback()