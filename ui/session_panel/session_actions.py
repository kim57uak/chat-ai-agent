"""
Session Actions Handler
세션 액션 처리 (생성, 삭제, 이름변경)
"""

from PyQt6.QtWidgets import QDialog, QMessageBox, QInputDialog
from PyQt6.QtCore import QTimer

from core.session import session_manager
from core.logging import get_logger
from .session_dialog import NewSessionDialog

logger = get_logger("session_actions")


class SessionActions:
    """세션 액션 핸들러"""

    def __init__(self, panel):
        self.panel = panel

    def create_new_session(self):
        """새 세션 생성"""
        dialog = NewSessionDialog(self.panel)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_session_data()
            if not data["title"]:
                QMessageBox.warning(self.panel, "경고", "세션 제목을 입력해주세요.")
                return

            try:
                session_id = session_manager.create_session(
                    title=data["title"], topic_category=data["category"]
                )

                # 메인 윈도우의 현재 세션 ID 업데이트
                if hasattr(self.panel, "main_window") and self.panel.main_window:
                    self.panel.main_window.current_session_id = session_id
                    self.panel.main_window._auto_session_created = True

                # 세션 목록 새로고침 후 선택
                self.panel.load_sessions()
                QTimer.singleShot(50, lambda: self.panel.select_session(session_id))
                self.panel.session_created.emit(session_id)

                QMessageBox.information(
                    self.panel, "성공", f"새 세션 '{data['title']}'이 생성되었습니다."
                )

            except Exception as e:
                logger.error(f"세션 생성 오류: {e}")
                QMessageBox.critical(
                    self.panel, "오류", f"세션 생성 중 오류가 발생했습니다:\n{e}"
                )

    def rename_session(self):
        """세션 이름 변경"""
        if not self.panel.current_session_id:
            return

        session = session_manager.get_session(self.panel.current_session_id)
        if not session:
            return

        new_title, ok = QInputDialog.getText(
            self.panel, "세션 이름 변경", "새 제목:", text=session["title"]
        )

        if ok and new_title.strip():
            try:
                success = session_manager.update_session(
                    self.panel.current_session_id, title=new_title.strip()
                )

                if success:
                    self.panel.load_sessions()
                    QMessageBox.information(self.panel, "성공", "세션 이름이 변경되었습니다.")
                else:
                    QMessageBox.warning(self.panel, "실패", "세션 이름 변경에 실패했습니다.")

            except Exception as e:
                logger.error(f"세션 이름 변경 오류: {e}")
                QMessageBox.critical(
                    self.panel, "오류", f"세션 이름 변경 중 오류가 발생했습니다:\n{e}"
                )

    def delete_session(self):
        """세션 삭제"""
        if not self.panel.current_session_id:
            return

        session = session_manager.get_session(self.panel.current_session_id)
        if not session:
            return

        reply = QMessageBox.question(
            self.panel,
            "세션 삭제",
            f"'{session['title']}' 세션을 삭제하시겠습니까?\n\n"
            f"메시지 {session['message_count']}개가 함께 삭제됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 먼저 UI에서 해당 아이템 제거
                self.panel._remove_session_item(self.panel.current_session_id)

                success = session_manager.delete_session(
                    self.panel.current_session_id, hard_delete=True
                )

                if success:
                    # 메인 윈도우의 현재 세션 ID도 초기화
                    if hasattr(self.panel, "main_window") and self.panel.main_window:
                        if (
                            self.panel.main_window.current_session_id
                            == self.panel.current_session_id
                        ):
                            self.panel.main_window.current_session_id = None
                            self.panel.main_window._auto_session_created = False
                            self.panel.main_window._update_window_title()

                    self.panel.current_session_id = None
                    self.panel.rename_btn.setEnabled(False)
                    self.panel.export_btn.setEnabled(False)
                    self.panel.delete_btn.setEnabled(False)

                    self.panel.load_sessions()
                    QMessageBox.information(self.panel, "성공", "세션이 삭제되었습니다.")
                else:
                    QMessageBox.warning(self.panel, "실패", "세션 삭제에 실패했습니다.")
                    self.panel.load_sessions()

            except Exception as e:
                logger.error(f"세션 삭제 오류: {e}")
                QMessageBox.critical(
                    self.panel, "오류", f"세션 삭제 중 오류가 발생했습니다:\n{e}"
                )
                self.panel.load_sessions()

    def delete_session_by_id(self, session_id: int):
        """세션 ID로 삭제 (아이템에서 호출)"""
        session = session_manager.get_session(session_id)
        if not session:
            return

        reply = QMessageBox.question(
            self.panel,
            "세션 삭제",
            f"'{session['title']}' 세션을 삭제하시겠습니까?\n\n"
            f"메시지 {session['message_count']}개가 함께 삭제됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.panel._remove_session_item(session_id)

                success = session_manager.delete_session(session_id, hard_delete=True)
                if success:
                    if hasattr(self.panel, "main_window") and self.panel.main_window:
                        if self.panel.main_window.current_session_id == session_id:
                            self.panel.main_window.current_session_id = None
                            self.panel.main_window._auto_session_created = False
                            self.panel.main_window._update_window_title()

                    if self.panel.current_session_id == session_id:
                        self.panel.current_session_id = None
                        self.panel.rename_btn.setEnabled(False)
                        self.panel.export_btn.setEnabled(False)
                        self.panel.delete_btn.setEnabled(False)

                    self.panel.load_sessions()
                    QMessageBox.information(self.panel, "성공", "세션이 삭제되었습니다.")
                else:
                    QMessageBox.warning(self.panel, "실패", "세션 삭제에 실패했습니다.")
                    self.panel.load_sessions()
            except Exception as e:
                logger.error(f"세션 삭제 오류: {e}")
                QMessageBox.critical(
                    self.panel, "오류", f"세션 삭제 중 오류가 발생했습니다:\n{e}"
                )
                self.panel.load_sessions()
