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
        self._ensure_writable_resources()
        return self._app
    
    def _ensure_writable_resources(self) -> None:
        """앱 내부 Resources 폴더의 JSON 파일에 쓰기 권한 보장."""
        try:
            import sys
            import os
            from pathlib import Path
            
            if getattr(sys, 'frozen', False):
                # 패키징된 앱에서만 실행
                resources_path = Path(sys.executable).parent.parent / 'Resources'
                if resources_path.exists():
                    json_files = list(resources_path.glob('*.json'))
                    for json_file in json_files:
                        try:
                            # 현재 권한 확인
                            current_mode = os.stat(json_file).st_mode & 0o777
                            # 모든 사용자 읽기/쓰기 권한 (666)
                            if current_mode != 0o666:
                                os.chmod(json_file, 0o666)
                        except (OSError, PermissionError):
                            pass  # 권한 변경 실패 시 무시
        except Exception:
            pass  # 초기화 실패를 앱 실행에 영향주지 않음
    
    def _setup_interrupt_timer(self) -> None:
        """Setup timer for keyboard interrupt handling."""
        self._timer = QTimer()
        self._timer.start(500)
        self._timer.timeout.connect(lambda: None)
    
    def get_application(self) -> QApplication:
        """Get the created application instance."""
        return self._app