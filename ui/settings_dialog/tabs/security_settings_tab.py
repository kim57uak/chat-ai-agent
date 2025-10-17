"""
Security Settings Tab
보안 설정 탭
"""

from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QCheckBox, QSpinBox, 
                            QGroupBox, QVBoxLayout, QPushButton, QMessageBox, QDialog)
from core.file_utils import load_prompt_config, save_prompt_config
from core.logging import get_logger
from ..base_settings_tab import BaseSettingsTab

logger = get_logger("security_settings_tab")


class SecuritySettingsTab(BaseSettingsTab):
    """보안 설정 탭"""
    
    def create_ui(self):
        """UI 생성"""
        # 자동 로그아웃 설정 그룹
        logout_group = QGroupBox('🔒 자동 로그아웃 설정')
        logout_layout = QVBoxLayout(logout_group)
        logout_layout.setSpacing(12)
        
        self.enable_auto_logout = QCheckBox('자동 로그아웃 사용')
        logout_layout.addWidget(self.enable_auto_logout)
        
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel('로그아웃 시간:'))
        self.logout_timeout_spin = QSpinBox()
        self.logout_timeout_spin.setRange(5, 360)
        self.logout_timeout_spin.setValue(30)
        self.logout_timeout_spin.setSuffix(' 분')
        self.logout_timeout_spin.setMinimumHeight(40)
        timeout_layout.addWidget(self.logout_timeout_spin)
        logout_layout.addLayout(timeout_layout)
        
        self.content_layout.addWidget(logout_group)
        
        # 암호화 상태 그룹
        encryption_group = QGroupBox('🔐 암호화 상태')
        encryption_layout = QVBoxLayout(encryption_group)
        encryption_layout.setSpacing(12)
        
        self.encryption_status_label = QLabel('암호화 상태: 확인 중...')
        encryption_layout.addWidget(self.encryption_status_label)
        
        self.key_version_label = QLabel('키 버전: 확인 중...')
        encryption_layout.addWidget(self.key_version_label)
        
        self.last_login_label = QLabel('마지막 로그인: 확인 중...')
        encryption_layout.addWidget(self.last_login_label)
        
        refresh_button = QPushButton('🔄 상태 새로고침')
        refresh_button.clicked.connect(self.refresh_security_status)
        encryption_layout.addWidget(refresh_button)
        
        self.content_layout.addWidget(encryption_group)
        
        # 보안 작업 그룹
        security_actions_group = QGroupBox('⚙️ 보안 작업')
        security_actions_layout = QVBoxLayout(security_actions_group)
        security_actions_layout.setSpacing(12)
        
        change_password_button = QPushButton('🔑 비밀번호 변경')
        change_password_button.clicked.connect(self.change_password)
        security_actions_layout.addWidget(change_password_button)
        
        reset_encryption_button = QPushButton('🔄 암호화 키 재생성')
        reset_encryption_button.clicked.connect(self.reset_encryption)
        security_actions_layout.addWidget(reset_encryption_button)
        
        self.content_layout.addWidget(security_actions_group)
        
        # 초기 보안 상태 로드
        self.refresh_security_status()
    
    def refresh_security_status(self):
        """보안 상태 새로고침"""
        try:
            import keyring
            import datetime
            
            try:
                salt = keyring.get_password('chat-ai-agent', 'encryption_salt')
                key = keyring.get_password('chat-ai-agent', 'data_encryption_key')
                
                if salt and key:
                    self.encryption_status_label.setText('암호화 상태: ✅ 활성화됨')
                    self.encryption_status_label.setStyleSheet('color: #22c55e; font-weight: 600;')
                else:
                    self.encryption_status_label.setText('암호화 상태: ❌ 비활성화됨')
                    self.encryption_status_label.setStyleSheet('color: #ef4444; font-weight: 600;')
            except Exception:
                self.encryption_status_label.setText('암호화 상태: ❓ 확인 불가')
                self.encryption_status_label.setStyleSheet('color: #f59e0b; font-weight: 600;')
            
            self.key_version_label.setText('키 버전: v1.0 (기본)')
            self.key_version_label.setStyleSheet('color: #6366f1; font-weight: 600;')
            
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.last_login_label.setText(f'마지막 로그인: {current_time} (현재 세션)')
            self.last_login_label.setStyleSheet('color: #8b5cf6; font-weight: 600;')
                
        except Exception as e:
            logger.debug(f"보안 상태 새로고침 오류: {e}")
    
    def change_password(self):
        """비밀번호 변경"""
        reply = QMessageBox.question(
            self,
            '비밀번호 변경',
            '비밀번호를 변경하시겠습니까?\n\n변경 후 새로운 비밀번호로 다시 로그인해야 합니다.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from ui.auth.login_dialog import LoginDialog
                from core.auth.auth_manager import AuthManager
                import keyring
                
                auth_manager = AuthManager()
                keyring.delete_password('chat-ai-agent', 'encryption_salt')
                keyring.delete_password('chat-ai-agent', 'data_encryption_key')
                
                dialog = LoginDialog(auth_manager, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    QMessageBox.information(self, '성공', '비밀번호가 성공적으로 변경되었습니다.')
                    self.refresh_security_status()
                else:
                    QMessageBox.warning(self, '취소', '비밀번호 변경이 취소되었습니다.')
            except Exception as e:
                QMessageBox.critical(self, '오류', f'비밀번호 변경 중 오류가 발생했습니다: {str(e)}')
    
    def reset_encryption(self):
        """암호화 키 재생성"""
        reply = QMessageBox.warning(
            self,
            '암호화 키 재생성',
            '⚠️ 경고: 암호화 키를 재생성하면 기존의 모든 암호화된 데이터가 복구할 수 없게 됩니다.\n\n계속하시겠습니까?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.auth.auth_manager import AuthManager
                from ui.auth.login_dialog import LoginDialog
                import keyring
                
                keyring.delete_password('chat-ai-agent', 'encryption_salt')
                keyring.delete_password('chat-ai-agent', 'data_encryption_key')
                
                auth_manager = AuthManager()
                dialog = LoginDialog(auth_manager, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    QMessageBox.information(self, '성공', '암호화 키가 성공적으로 재생성되었습니다.')
                    self.refresh_security_status()
                else:
                    QMessageBox.warning(self, '취소', '암호화 키 재생성이 취소되었습니다.')
            except Exception as e:
                QMessageBox.critical(self, '오류', f'암호화 키 재생성 중 오류가 발생했습니다: {str(e)}')
    
    def load_settings(self):
        """설정 로드"""
        try:
            prompt_config = load_prompt_config()
            security_settings = prompt_config.get('security_settings', {})
            
            self.enable_auto_logout.setChecked(security_settings.get('enable_auto_logout', True))
            self.logout_timeout_spin.setValue(security_settings.get('logout_timeout_minutes', 30))
        except Exception as e:
            logger.debug(f"보안 설정 로드 오류: {e}")
    
    def save_settings(self):
        """설정 저장"""
        try:
            prompt_config = load_prompt_config()
            
            prompt_config['security_settings'] = {
                'enable_auto_logout': self.enable_auto_logout.isChecked(),
                'logout_timeout_minutes': self.logout_timeout_spin.value()
            }
            
            save_prompt_config(prompt_config)
        except Exception as e:
            logger.debug(f"보안 설정 저장 오류: {e}")
    
    def get_tab_title(self) -> str:
        return '🔒 보안'
