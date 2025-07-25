"""Application initialization and configuration."""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from typing import List


class AppInitializer:
    """Handles application initialization and configuration."""
    
    def __init__(self, args: List[str]):
        self._args = args
        self._app = None
        self._timer = None
    
    def create_application(self) -> QApplication:
        """Create and configure QApplication."""
        self._app = QApplication(self._args)
        self._setup_interrupt_timer()
        return self._app
    
    def _setup_interrupt_timer(self) -> None:
        """Setup timer for keyboard interrupt handling."""
        self._timer = QTimer()
        self._timer.start(500)
        self._timer.timeout.connect(lambda: None)
    
    def get_application(self) -> QApplication:
        """Get the created application instance."""
        return self._app