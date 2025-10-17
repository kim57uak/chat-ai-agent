"""
Dialog Manager
다이얼로그 관리 전담 클래스
"""

from PyQt6.QtWidgets import QFileDialog, QMessageBox
from core.logging import get_logger

logger = get_logger("dialog_manager")


class DialogManager:
    """다이얼로그 관리 전담 클래스"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def open_settings(self):
        """설정 다이얼로그 열기"""
        from ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self.main_window)
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            self.main_window.theme_controller.apply_current_theme()
    
    def open_mcp(self):
        """MCP 임포트 다이얼로그 열기"""
        from ui.mcp_dialog import MCPDialog
        mcp_path, _ = QFileDialog.getOpenFileName(
            self.main_window, 'mcp.json 선택', '', 'JSON 파일 (*.json)'
        )
        if not mcp_path:
            return
        
        try:
            with open('mcp.json', 'w', encoding='utf-8') as f:
                with open(mcp_path, 'r', encoding='utf-8') as src:
                    f.write(src.read())
            dlg = MCPDialog('mcp.json', self.main_window)
            dlg.exec()
        except Exception as e:
            logger.debug(f"MCP 파일 처리 오류: {e}")
    
    def open_mcp_manager(self):
        """MCP 관리자 다이얼로그 열기"""
        from ui.mcp_manager_simple import MCPManagerDialog
        dlg = MCPManagerDialog(self.main_window)
        dlg.exec()
    
    def open_user_prompt(self):
        """유저 프롬프트 다이얼로그 열기"""
        from ui.user_prompt_dialog import UserPromptDialog
        from core.file_utils import load_model_api_key, load_last_model
        from core.ai_client import AIClient
        
        model = load_last_model()
        api_key = load_model_api_key(model)
        
        if not api_key:
            QMessageBox.warning(
                self.main_window, '경고', 
                'API 키가 설정되지 않았습니다. 먼저 환경설정에서 API 키를 입력해주세요.'
            )
            return
        
        ai_client = AIClient(api_key, model)
        dlg = UserPromptDialog(ai_client, self.main_window)
        dlg.exec()
    
    def open_config_path_dialog(self):
        """설정 파일 경로 다이얼로그 열기"""
        from ui.config_path_dialog import ConfigPathDialog
        dlg = ConfigPathDialog(self.main_window)
        dlg.exec()
    
    def show_security_status(self):
        """보안 상태 표시"""
        if self.main_window.auth_manager.is_logged_in():
            remaining_minutes = self.main_window.auth_manager.get_session_remaining_minutes()
            status_text = f"현재 로그인 상태입니다.\n\n"
            status_text += f"세션 남은 시간: {remaining_minutes}분\n"
            status_text += f"자동 로그아웃 시간: {self.main_window.auth_manager.auto_logout_minutes}분"
        else:
            status_text = "로그인되지 않은 상태입니다."
        
        msg_box = QMessageBox(self.main_window)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("보안 상태")
        msg_box.setText(status_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.main_window.theme_controller.apply_dialog_theme(msg_box)
        msg_box.exec()
    
    def show_export_message(self, message: str):
        """내보내기 메시지 표시"""
        QMessageBox.information(self.main_window, '내보내기 완료', message)
