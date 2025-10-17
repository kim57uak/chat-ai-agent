"""
Base Settings Tab
모든 설정 탭의 기본 클래스
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame
from PyQt6.QtCore import Qt


class BaseSettingsTab(QWidget):
    """모든 설정 탭의 기본 클래스 - Template Method 패턴"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """UI 초기화 - 스크롤 영역 자동 생성"""
        # 스크롤 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # 스크롤 내용 위젯
        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)
        
        # 하위 클래스에서 UI 생성
        self.create_ui()
        
        self.content_layout.addStretch()
        
        # 스크롤 영역에 내용 설정
        scroll_area.setWidget(scroll_content)
        
        # 탭에 스크롤 영역 추가
        tab_layout = QVBoxLayout(self)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
    
    def create_ui(self):
        """UI 생성 (하위 클래스에서 구현)"""
        raise NotImplementedError("Subclass must implement create_ui()")
    
    def load_settings(self):
        """설정 로드 (하위 클래스에서 구현)"""
        raise NotImplementedError("Subclass must implement load_settings()")
    
    def save_settings(self):
        """설정 저장 (하위 클래스에서 구현)"""
        raise NotImplementedError("Subclass must implement save_settings()")
    
    def validate_settings(self) -> bool:
        """설정 유효성 검증 (필요시 하위 클래스에서 오버라이드)"""
        return True
    
    def get_tab_title(self) -> str:
        """탭 제목 반환"""
        raise NotImplementedError("Subclass must implement get_tab_title()")
