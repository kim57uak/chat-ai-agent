"""
Template Handler
템플릿 처리 전담 클래스 - SRP (Single Responsibility Principle)
"""

from core.logging import get_logger

logger = get_logger("template_handler")


class TemplateHandler:
    """템플릿 처리 전담 클래스"""

    def __init__(self, parent):
        self.parent = parent

    def show_manager(self):
        """템플릿 관리자 표시"""
        try:
            from ui.template_dialog import TemplateDialog

            dialog = TemplateDialog(self.parent)
            dialog.template_selected.connect(self._on_template_selected)
            dialog.exec()
        except Exception as e:
            logger.debug(f"템플릿 관리자 표시 오류: {e}")

    def _on_template_selected(self, content: str):
        """템플릿 선택 시 채팅창에 내용 입력"""
        try:
            main_window = self._find_main_window()
            if not main_window or not hasattr(main_window, "chat_widget"):
                return

            chat_widget = main_window.chat_widget
            if not hasattr(chat_widget, "input_text"):
                return

            self._insert_template(chat_widget.input_text, content)

        except Exception as e:
            logger.debug(f"템플릿 선택 처리 오류: {e}")

    def _insert_template(self, input_text, content):
        """템플릿 내용 삽입"""
        current_text = input_text.toPlainText()
        
        if current_text.strip():
            input_text.setPlainText(current_text + "\n" + content)
        else:
            input_text.setPlainText(content)

        cursor = input_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        input_text.setTextCursor(cursor)
        input_text.setFocus()

    def _find_main_window(self):
        """메인 윈도우 찾기"""
        widget = self.parent
        while widget:
            if widget.__class__.__name__ == "MainWindow":
                return widget
            widget = widget.parent()
        return None
