"""Application runner with error handling."""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.logging import get_logger

logger = get_logger('app.runner')


class AppRunner:
    """Handles application execution and error management."""
    
    def __init__(self, app: QApplication):
        self._app = app
        self._window = None
    
    def run(self) -> int:
        """Run the application with error handling."""
        try:
            logger.debug("AppRunner starting")
            logger.debug("Loading theme")
            self._load_saved_theme()
            logger.debug("Theme loaded")
            
            logger.debug("Creating MainWindow")
            self._window = MainWindow()
            logger.debug("MainWindow created")
            
            # 로그인 취소 시 종료
            if not hasattr(self._window, 'auth_manager') or not self._window.auth_manager.is_logged_in():
                logger.info("Login cancelled - application exit")
                return 0
            
            logger.debug("Showing MainWindow")
            self._window.show()
            logger.debug("Starting event loop")
            return self._app.exec()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt detected, shutting down")
            self._app.quit()
            return 0
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            return 1
    
    def _load_saved_theme(self):
        """저장된 테마 미리 로드"""
        try:
            import os
            import json
            from ui.styles.theme_manager import theme_manager
            
            theme_file = "theme.json"
            if os.path.exists(theme_file):
                with open(theme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    saved_theme = data.get("current_theme", "material_dark")
                    theme_manager.material_manager.current_theme_key = saved_theme
                    theme_manager.material_manager.themes = data.get("themes", {})
                    logger.debug(f"Theme preloaded: {saved_theme}")
        except Exception as e:
            logger.error(f"Theme preload error: {e}", exc_info=True)