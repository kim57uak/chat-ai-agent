"""Application runner with error handling."""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


class AppRunner:
    """Handles application execution and error management."""
    
    def __init__(self, app: QApplication):
        self._app = app
        self._window = None
    
    def run(self) -> int:
        """Run the application with error handling."""
        try:
            self._window = MainWindow()
            self._window.show()
            return self._app.exec()
        except KeyboardInterrupt:
            print("Keyboard interrupt detected, shutting down...")
            self._app.quit()
            return 0
        except Exception as e:
            print(f"Application error: {e}")
            return 1