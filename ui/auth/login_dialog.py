"""
Login Dialog for authentication
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QProgressBar, QFrame, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QIcon
import re
from ui.styles.material_theme_manager import material_theme_manager


class AuthWorker(QThread):
    """인증 작업을 백그라운드에서 처리하는 워커"""
    
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, auth_manager, password, is_setup=False):
        super().__init__()
        self.auth_manager = auth_manager
        self.password = password
        self.is_setup = is_setup
        
    def run(self):
        try:
            if self.is_setup:
                success = self.auth_manager.setup_first_time(self.password)
                message = "계정이 성공적으로 생성되었습니다." if success else "계정 생성에 실패했습니다."
            else:
                success = self.auth_manager.login(self.password)
                message = "로그인 성공" if success else "비밀번호가 올바르지 않습니다."
                
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"오류가 발생했습니다: {str(e)}")


class LoginDialog(QDialog):
    """로그인 다이얼로그"""
    
    login_successful = pyqtSignal()
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.auth_worker = None
        
        self.setWindowTitle("Chat AI Agent - 인증")
        self.setFixedSize(400, 350)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        # 모달 다이얼로그로 설정
        self.setModal(True)
        
        self.setup_ui()
        self.apply_theme_styles()
        
        # 최초 설정 필요한지 확인
        if self.auth_manager.is_setup_required():
            self.switch_to_setup_mode()
        else:
            self.switch_to_login_mode()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 25, 30, 25)
        
        # 제목
        self.title_label = QLabel("로그인")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setMinimumHeight(50)
        self.title_label.setWordWrap(False)
        layout.addWidget(self.title_label)
        
        # 설명 텍스트
        self.description_label = QLabel("비밀번호를 입력하세요")
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setObjectName("descriptionLabel")
        self.description_label.setMinimumHeight(25)
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        # 비밀번호 입력
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password (English only)")
        self.password_input.setMinimumHeight(50)
        self.password_input.returnPressed.connect(self.handle_auth)
        self.password_input.textChanged.connect(lambda: self._filter_non_ascii(self.password_input))
        layout.addWidget(self.password_input)
        
        # 비밀번호 확인 (설정 모드에서만 표시)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Confirm Password (English only)")
        self.confirm_password_input.setMinimumHeight(50)
        self.confirm_password_input.returnPressed.connect(self.handle_auth)
        self.confirm_password_input.textChanged.connect(lambda: self._filter_non_ascii(self.confirm_password_input))
        self.confirm_password_input.hide()
        layout.addWidget(self.confirm_password_input)
        
        # 비밀번호 강도 표시
        self.strength_label = QLabel("")
        self.strength_label.setObjectName("strengthLabel")
        self.strength_label.setMinimumHeight(20)
        self.strength_label.setWordWrap(True)
        self.strength_label.hide()
        layout.addWidget(self.strength_label)
        
        # 비밀번호 표시 체크박스
        self.show_password_cb = QCheckBox("비밀번호 표시")
        self.show_password_cb.setMinimumHeight(25)
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_cb)
        
        # 진행률 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 무한 진행률
        self.progress_bar.setMinimumHeight(8)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setMinimumHeight(32)
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.auth_button = QPushButton("로그인")
        self.auth_button.setMinimumHeight(32)
        self.auth_button.setMinimumWidth(80)
        self.auth_button.clicked.connect(self.handle_auth)
        self.auth_button.setDefault(True)
        button_layout.addWidget(self.auth_button)
        
        layout.addLayout(button_layout)
        
        # 하단 링크
        self.bottom_link = QPushButton("비밀번호를 잊으셨나요?")
        self.bottom_link.setFlat(True)
        self.bottom_link.setMinimumHeight(28)
        self.bottom_link.clicked.connect(self.show_reset_dialog)
        self.bottom_link.setObjectName("linkButton")
        layout.addWidget(self.bottom_link)
        
        # 비밀번호 입력 시 강도 체크
        self.password_input.textChanged.connect(self.check_password_strength)
    
    def apply_theme_styles(self):
        """가독성 최적화된 디자인 적용"""
        colors = material_theme_manager.get_theme_colors()
        is_dark = material_theme_manager.is_dark_theme()
        
        # 테마 색상 사용
        primary = colors.get('primary', '#6366f1')
        primary_variant = colors.get('primary_variant', '#4f46e5')
        background = colors.get('background', '#ffffff')
        text_primary = colors.get('text_primary', '#000000')
        text_secondary = colors.get('text_secondary', '#666666')
        
        # rgba 처리 함수
        def clean_color(color, fallback):
            if 'rgba' in str(color) or 'linear-gradient' in str(color):
                return fallback
            return color
        
        # 가독성 확보를 위한 색상 설정
        surface = clean_color(colors.get('surface', '#2a2a2a' if is_dark else '#f5f5f5'), '#2a2a2a' if is_dark else '#f5f5f5')
        divider = clean_color(colors.get('divider', '#555555' if is_dark else '#d0d0d0'), '#555555' if is_dark else '#d0d0d0')
        
        if is_dark:
            input_bg = surface
            input_text = text_primary if self._is_readable_on_dark(text_primary) else '#ffffff'
            input_border = divider
            button_secondary_bg = self._lighten_color(surface, 0.15)
            button_secondary_text = text_primary if self._is_readable_on_dark(text_primary) else '#ffffff'
            placeholder_color = text_secondary if self._is_readable_on_dark(text_secondary) else '#999999'
        else:
            input_bg = '#ffffff'
            input_text = text_primary if self._is_readable_on_light(text_primary) else '#000000'
            input_border = divider
            button_secondary_bg = surface
            button_secondary_text = text_primary if self._is_readable_on_light(text_primary) else '#000000'
            placeholder_color = text_secondary if self._is_readable_on_light(text_secondary) else '#666666'
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {background};
                border: 1px solid {divider};
            }}
            
            #titleLabel {{
                font-size: 22px;
                font-weight: 600;
                color: {text_primary};
                margin: 8px 0;
                padding: 12px 8px;
                line-height: 1.4;
                min-height: 50px;
            }}
            
            #descriptionLabel {{
                font-size: 14px;
                color: {text_primary};
                margin: 4px 0;
                padding: 2px;
            }}
            
            QLineEdit {{
                padding: 10px 16px;
                border: 2px solid {input_border};
                border-radius: 8px;
                font-size: 14px;
                min-height: 24px;
                background-color: {input_bg};
                color: {input_text};
                selection-background-color: {primary};
                selection-color: white;
            }}
            
            QLineEdit:focus {{
                border-color: {primary};
                outline: none;
            }}
            
            QLineEdit::placeholder {{
                color: {placeholder_color};
            }}
            
            QPushButton {{
                padding: 6px 20px;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
                min-height: 32px;
                line-height: 1.2;
            }}
            
            QPushButton[default="true"] {{
                background-color: {primary};
                color: white;
            }}
            
            QPushButton[default="true"]:hover {{
                background-color: {primary_variant};
            }}
            
            QPushButton:!default {{
                background-color: {button_secondary_bg};
                color: {button_secondary_text};
                border: 2px solid {input_border};
            }}
            
            QPushButton:!default:hover {{
                background-color: {input_border};
                color: {button_secondary_text};
            }}
            
            #linkButton {{
                color: {primary};
                border: none;
                background: transparent;
                padding: 8px;
                font-size: 13px;
            }}
            
            #linkButton:hover {{
                color: {primary_variant};
            }}
            
            #strengthLabel {{
                font-size: 12px;
                margin: 4px 0;
                padding: 4px 8px;
                border-radius: 4px;
                background-color: {surface};
            }}
            
            QCheckBox {{
                font-size: 13px;
                color: {text_primary};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {input_border};
                border-radius: 3px;
                background-color: {input_bg};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {primary};
                border-color: {primary};
            }}
            
            QProgressBar {{
                border: 1px solid {input_border};
                border-radius: 4px;
                background-color: {surface};
                color: {text_primary};
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {primary};
                border-radius: 3px;
            }}
        """)
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """헥스 색상을 RGB로 변환"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return f"{int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}"
        return "99, 102, 241"  # 기본값
    
    def _get_luminance(self, hex_color: str) -> float:
        """색상의 명도 계산"""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                return (0.299 * r + 0.587 * g + 0.114 * b) / 255
        except:
            pass
        return 0.5
    
    def _is_readable_on_dark(self, hex_color: str) -> bool:
        """어두운 배경에서 읽기 가능한 색상인지 확인"""
        return self._get_luminance(hex_color) > 0.5
    
    def _is_readable_on_light(self, hex_color: str) -> bool:
        """밝은 배경에서 읽기 가능한 색상인지 확인"""
        return self._get_luminance(hex_color) < 0.5
    
    def _lighten_color(self, hex_color: str, amount: float) -> str:
        """색상을 밝게 조정"""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                r = min(255, int(int(hex_color[0:2], 16) * (1 + amount)))
                g = min(255, int(int(hex_color[2:4], 16) * (1 + amount)))
                b = min(255, int(int(hex_color[4:6], 16) * (1 + amount)))
                return f'#{r:02x}{g:02x}{b:02x}'
        except:
            pass
        return hex_color
    
    def switch_to_setup_mode(self):
        """최초 설정 모드로 전환"""
        self.title_label.setText("계정 생성")
        self.description_label.setText("새 비밀번호를 설정하세요")
        self.auth_button.setText("계정 생성")
        self.confirm_password_input.show()
        self.strength_label.show()
        self.bottom_link.hide()
        self.setFixedSize(400, 400)  # 높이 증가
        
    def switch_to_login_mode(self):
        """로그인 모드로 전환"""
        self.title_label.setText("로그인")
        self.description_label.setText("비밀번호를 입력하세요")
        self.auth_button.setText("로그인")
        self.confirm_password_input.hide()
        self.strength_label.hide()
        self.bottom_link.show()
        self.setFixedSize(400, 350)  # 높이 증가
    
    def check_password_strength(self, password):
        """비밀번호 강도 검사"""
        if not self.confirm_password_input.isVisible():
            return
            
        if len(password) < 8:
            self.strength_label.setText("⚠️ 비밀번호는 8자 이상이어야 합니다")
            self.strength_label.setStyleSheet("color: #e74c3c;")
            return
        
        score = 0
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        
        if score < 2:
            self.strength_label.setText("🔴 약함")
            self.strength_label.setStyleSheet("color: #e74c3c;")
        elif score < 3:
            self.strength_label.setText("🟡 보통")
            self.strength_label.setStyleSheet("color: #f39c12;")
        else:
            self.strength_label.setText("🟢 강함")
            self.strength_label.setStyleSheet("color: #27ae60;")
    
    def toggle_password_visibility(self, checked):
        """비밀번호 표시/숨김 토글"""
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)
        if self.confirm_password_input.isVisible():
            self.confirm_password_input.setEchoMode(mode)
    
    def validate_input(self):
        """입력 검증"""
        password = self.password_input.text()
        
        if not password:
            self._show_warning("입력 오류", "비밀번호를 입력하세요.")
            return False
        
        if self.confirm_password_input.isVisible():
            # 설정 모드
            if len(password) < 8:
                self._show_warning("입력 오류", "비밀번호는 8자 이상이어야 합니다.")
                return False
            
            confirm_password = self.confirm_password_input.text()
            if password != confirm_password:
                self._show_warning("입력 오류", "비밀번호가 일치하지 않습니다.")
                return False
        
        return True
    
    def handle_auth(self):
        """인증 처리"""
        if not self.validate_input():
            return
        
        password = self.password_input.text()
        is_setup = self.confirm_password_input.isVisible()
        
        # UI 비활성화
        self.set_ui_enabled(False)
        self.progress_bar.show()
        
        # 백그라운드에서 인증 처리
        self.auth_worker = AuthWorker(self.auth_manager, password, is_setup)
        self.auth_worker.finished.connect(self.on_auth_finished)
        self.auth_worker.start()
    
    @pyqtSlot(bool, str)
    def on_auth_finished(self, success, message):
        """인증 완료 처리"""
        self.progress_bar.hide()
        self.set_ui_enabled(True)
        
        if success:
            self.login_successful.emit()
            self.accept()
        else:
            self._show_critical("인증 실패", message)
            self.password_input.clear()
            self.confirm_password_input.clear()
            self.password_input.setFocus()
    
    def set_ui_enabled(self, enabled):
        """UI 활성화/비활성화"""
        self.password_input.setEnabled(enabled)
        self.confirm_password_input.setEnabled(enabled)
        self.auth_button.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)
        self.show_password_cb.setEnabled(enabled)
    
    def show_reset_dialog(self):
        """비밀번호 재설정 다이얼로그 표시"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("비밀번호 재설정")
        msg_box.setText("비밀번호를 재설정하면 기존의 모든 암호화된 데이터가 복구할 수 없게 됩니다.\n\n"
                       "새로운 비밀번호로 재설정하시겠습니까?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        self._apply_messagebox_theme(msg_box)
        
        reply = msg_box.exec()
        if reply == QMessageBox.StandardButton.Yes:
            self.switch_to_setup_mode()
    
    def _apply_messagebox_theme(self, msg_box):
        """메시지박스에 테마 적용"""
        colors = material_theme_manager.get_theme_colors()
        is_dark = material_theme_manager.is_dark_theme()
        
        primary = colors.get('primary', '#6366f1')
        primary_variant = colors.get('primary_variant', '#4f46e5')
        background = colors.get('background', '#ffffff')
        text_primary = colors.get('text_primary', '#000000')
        
        def clean_color(color, fallback):
            if 'rgba' in str(color) or 'linear-gradient' in str(color):
                return fallback
            return color
        
        if is_dark:
            surface = clean_color(colors.get('surface', '#2a2a2a'), '#2a2a2a')
            divider = clean_color(colors.get('divider', '#555555'), '#555555')
        else:
            surface = clean_color(colors.get('surface', '#f5f5f5'), '#f5f5f5')
            divider = clean_color(colors.get('divider', '#d0d0d0'), '#d0d0d0')
        
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {background};
                color: {text_primary};
            }}
            QMessageBox QLabel {{
                color: {text_primary};
                font-size: 14px;
            }}
            QMessageBox QPushButton {{
                background-color: {primary};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {primary_variant};
            }}
            QMessageBox QPushButton:pressed {{
                background-color: {primary_variant};
            }}
        """)
    
    def _show_warning(self, title, message):
        """경고 메시지 표시"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        self._apply_messagebox_theme(msg_box)
        msg_box.exec()
    
    def _show_critical(self, title, message):
        """오류 메시지 표시"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        self._apply_messagebox_theme(msg_box)
        msg_box.exec()
    
    def _filter_non_ascii(self, line_edit):
        """한글 및 비ASCII 문자 필터링"""
        text = line_edit.text()
        cursor_pos = line_edit.cursorPosition()
        filtered = ''.join(c for c in text if ord(c) < 128)
        if text != filtered:
            line_edit.setText(filtered)
            line_edit.setCursorPosition(min(cursor_pos, len(filtered)))
    
    def keyPressEvent(self, event):
        """키 이벤트 처리"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)