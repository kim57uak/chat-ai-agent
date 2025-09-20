"""템플릿 빠른 선택 바"""
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, 
                            QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.template_manager import template_manager
from ui.styles.theme_manager import theme_manager


class TemplateQuickBar(QWidget):
    """템플릿 빠른 선택 바"""
    
    template_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(40)
        self._setup_ui()
        self._load_quick_templates()
        template_manager.templates_changed.connect(self._load_quick_templates)
    
    def _setup_ui(self):
        """UI 구성"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 라벨
        self.label = QLabel("📋 빠른 템플릿:")
        layout.addWidget(self.label)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameStyle(QFrame.Shape.NoFrame)
        
        # 버튼 컨테이너
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(5)
        
        scroll.setWidget(self.button_container)
        layout.addWidget(scroll, 1)
        
        # 관리 버튼
        self.manage_btn = QPushButton("⚙️")
        self.manage_btn.setMaximumWidth(30)
        self.manage_btn.setToolTip("템플릿 관리")
        self.manage_btn.clicked.connect(self._open_template_manager)
        layout.addWidget(self.manage_btn)
        
        # 테마 적용
        self._apply_theme()
    
    def _load_quick_templates(self):
        """빠른 템플릿 로드"""
        # 기존 버튼 제거
        for i in reversed(range(self.button_layout.count())):
            child = self.button_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # 즐겨찾기 템플릿 추가
        favorites = template_manager.get_favorite_templates()
        for template in favorites[:5]:  # 최대 5개
            btn = QPushButton(template.name)
            btn.setMaximumHeight(30)
            self._apply_button_theme(btn)
            btn.clicked.connect(lambda checked, t=template: self._use_template(t))
            self.button_layout.addWidget(btn)
        
        # 스트레치 추가
        self.button_layout.addStretch()
    
    def _use_template(self, template):
        """템플릿 사용"""
        content = template_manager.use_template(template.name)
        if content:
            self.template_selected.emit(content)
    
    def _open_template_manager(self):
        """템플릿 관리자 열기"""
        from ui.template_dialog import TemplateDialog
        
        dialog = TemplateDialog(self)
        dialog.template_selected.connect(self.template_selected.emit)
        dialog.exec()
    
    def _apply_theme(self):
        """테마 적용"""
        if theme_manager.use_material_theme:
            colors = theme_manager.material_manager.get_theme_colors()
            
            # 라벨 스타일
            self.label.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    color: {colors.get('text_secondary', '#b3b3b3')};
                    font-size: 12px;
                }}
            """)
            
            # 관리 버튼 스타일
            self.manage_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.get('surface', '#1e1e1e')};
                    color: {colors.get('text_primary', '#ffffff')};
                    border: 1px solid {colors.get('divider', '#333333')};
                    border-radius: 15px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {colors.get('primary', '#bb86fc')};
                    color: {colors.get('on_primary', '#000000')};
                }}
            """)
            
            # 전체 배경
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {colors.get('background', '#121212')};
                }}
            """)
        else:
            # Flat 테마
            self.label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    color: #b0b0b0;
                    font-size: 12px;
                }
            """)
            
            self.manage_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3a;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 15px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
            """)
    
    def _apply_button_theme(self, btn):
        """버튼에 테마 적용"""
        if theme_manager.use_material_theme:
            colors = theme_manager.material_manager.get_theme_colors()
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.get('secondary', '#03dac6')};
                    color: {colors.get('on_secondary', '#000000')};
                    border: 1px solid {colors.get('secondary_variant', '#018786')};
                    border-radius: 15px;
                    padding: 5px 10px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {colors.get('secondary_variant', '#018786')};
                    color: {colors.get('on_secondary', '#000000')};
                }}
            """)
        else:
            # Flat 테마
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(150, 255, 150, 0.2);
                    color: #b0e0b0;
                    border: 1px solid rgba(150, 255, 150, 0.3);
                    border-radius: 15px;
                    padding: 5px 10px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: rgba(170, 255, 170, 0.3);
                    color: #ffffff;
                }
            """)
    
    def update_theme(self):
        """테마 업데이트"""
        self._apply_theme()
        self._load_quick_templates()  # 버튼들도 다시 로드해서 테마 적용