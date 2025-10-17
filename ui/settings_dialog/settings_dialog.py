"""
Settings Dialog - Refactored
설정 다이얼로그 - 리팩토링된 버전
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget
from PyQt6.QtCore import Qt
from ui.styles.theme_manager import theme_manager
from .styles import DialogStyleManager, TabStyleManager
from .tabs import (
    AISettingsTab,
    SecuritySettingsTab,
    LengthLimitTab,
    HistorySettingsTab,
    LanguageDetectionTab,
    NewsSettingsTab
)


class SettingsDialog(QDialog):
    """설정 다이얼로그 - Facade 패턴"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 성능 최적화 - 디바운서
        from ui.event_debouncer import get_event_debouncer
        self._debouncer = get_event_debouncer()
        
        self.setWindowTitle('🔧 환경설정')
        self.setMinimumSize(700, 720)
        self.resize(800, 810)
        
        # 탭 딕셔너리
        self.tabs = {}
        
        # UI 초기화
        self._init_ui()
        
        # 설정 로드
        self.load_settings()
        
        # 테마 변경 감지
        if hasattr(theme_manager, 'theme_changed'):
            theme_manager.theme_changed.connect(self.update_theme)
    
    def _init_ui(self):
        """UI 초기화"""
        # 스타일 적용
        self.setStyleSheet(DialogStyleManager.get_dialog_style())
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 제목
        title_label = QLabel('⚙️ 환경설정')
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: 700;
                padding: 16px 0;
                text-align: center;
                color: {theme_manager.material_manager.get_theme_colors().get('text_primary', '#f1f5f9')};
                background: transparent;
            }}
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(TabStyleManager.get_tab_widget_style())
        main_layout.addWidget(self.tab_widget)
        
        # 탭 생성 및 추가
        self._create_tabs()
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton('💾 저장')
        self.save_button.setStyleSheet(DialogStyleManager.get_save_button_style())
        self.save_button.clicked.connect(self.save)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton('❌ 취소')
        self.cancel_button.setStyleSheet(DialogStyleManager.get_cancel_button_style())
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def _create_tabs(self):
        """탭 생성"""
        # 각 탭 인스턴스 생성
        self.tabs['ai'] = AISettingsTab(self)
        self.tabs['security'] = SecuritySettingsTab(self)
        self.tabs['length'] = LengthLimitTab(self)
        self.tabs['history'] = HistorySettingsTab(self)
        self.tabs['language'] = LanguageDetectionTab(self)
        self.tabs['news'] = NewsSettingsTab(self)
        
        # 탭 위젯에 추가
        for tab in self.tabs.values():
            self.tab_widget.addTab(tab, tab.get_tab_title())
    
    def load_settings(self):
        """모든 탭의 설정 로드"""
        for tab in self.tabs.values():
            tab.load_settings()
    
    def save(self):
        """모든 탭의 설정 저장"""
        # 유효성 검증
        for name, tab in self.tabs.items():
            if not tab.validate_settings():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    '유효성 검증 실패',
                    f'{tab.get_tab_title()} 탭의 설정이 올바르지 않습니다.'
                )
                return
        
        # 설정 저장
        for tab in self.tabs.values():
            tab.save_settings()
        
        self.accept()
    
    def update_theme(self):
        """테마 업데이트"""
        self.setStyleSheet(DialogStyleManager.get_dialog_style())
        self.tab_widget.setStyleSheet(TabStyleManager.get_tab_widget_style())
        self.save_button.setStyleSheet(DialogStyleManager.get_save_button_style())
        self.cancel_button.setStyleSheet(DialogStyleManager.get_cancel_button_style())
