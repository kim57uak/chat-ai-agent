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
            print("[DEBUG] AppRunner.run() 시작")
            # 테마 미리 로드
            print("[DEBUG] 테마 로드 시작")
            self._load_saved_theme()
            print("[DEBUG] 테마 로드 완료")
            
            print("[DEBUG] MainWindow 생성 시작")
            self._window = MainWindow()
            print("[DEBUG] MainWindow 생성 완료")
            print("[DEBUG] MainWindow.show() 호출")
            self._window.show()
            print("[DEBUG] app.exec() 호출")
            return self._app.exec()
        except KeyboardInterrupt:
            print("Keyboard interrupt detected, shutting down...")
            self._app.quit()
            return 0
        except Exception as e:
            print(f"Application error: {e}")
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
                    print(f"앞서 로드된 테마: {saved_theme}")
        except Exception as e:
            print(f"테마 선로드 오류: {e}")