"""
Session Export Handler
세션 내보내기 처리
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QRadioButton, 
                            QDialogButtonBox, QButtonGroup, QFileDialog, QMessageBox)
from typing import Dict

from core.session import session_manager
from core.session.session_exporter import SessionExporter as CoreExporter
from core.logging import get_logger

logger = get_logger("session_exporter")


class SessionExporter:
    """세션 내보내기 핸들러"""

    def __init__(self, panel):
        self.panel = panel

    def export_session(self):
        """세션 내보내기"""
        if not self.panel.current_session_id:
            return

        session = session_manager.get_session(self.panel.current_session_id)
        if not session:
            return

        # 내보내기 형식 선택 대화상자
        dialog = QDialog(self.panel)
        dialog.setWindowTitle("내보내기 형식 선택")
        dialog.setModal(True)
        dialog.resize(300, 250)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"세션 '{session['title']}'를 내보내기:"))

        # 라디오 버튼 그룹
        button_group = QButtonGroup()

        text_radio = QRadioButton("텍스트 파일 (.txt)")
        html_radio = QRadioButton("HTML 파일 (.html)")
        json_radio = QRadioButton("JSON 파일 (.json)")
        md_radio = QRadioButton("Markdown 파일 (.md)")
        pdf_radio = QRadioButton("PDF 파일 (.pdf)")

        text_radio.setChecked(True)  # 기본 선택

        button_group.addButton(text_radio, 0)
        button_group.addButton(html_radio, 1)
        button_group.addButton(json_radio, 2)
        button_group.addButton(md_radio, 3)
        button_group.addButton(pdf_radio, 4)

        layout.addWidget(text_radio)
        layout.addWidget(html_radio)
        layout.addWidget(json_radio)
        layout.addWidget(md_radio)
        layout.addWidget(pdf_radio)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_format = button_group.checkedId()
            self._export_with_format(session, selected_format)

    def _export_with_format(self, session: Dict, format_id: int):
        """선택된 형식으로 내보내기"""
        try:
            if format_id == 4:  # PDF 내보내기
                self._export_to_pdf(session)
                return

            # 기존 파일 형식 매핑
            formats = {
                0: (".txt", "Text files (*.txt)", CoreExporter.export_to_text),
                1: (".html", "HTML files (*.html)", CoreExporter.export_to_html),
                2: (".json", "JSON files (*.json)", CoreExporter.export_to_json),
                3: (".md", "Markdown files (*.md)", CoreExporter.export_to_markdown),
            }

            ext, file_filter, export_func = formats[format_id]

            # 기본 파일명 생성
            safe_title = "".join(
                c for c in session["title"] if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            default_filename = f"{safe_title}_{session['id']}{ext}"

            # 파일 저장 대화상자
            file_path, _ = QFileDialog.getSaveFileName(
                self.panel, "세션 내보내기", default_filename, file_filter
            )

            if not file_path:
                return

            # 메시지 데이터 가져오기 (HTML 포함)
            messages = session_manager.get_session_messages(
                session["id"], limit=None, include_html=True
            )

            # 내보내기 실행
            success = export_func(session, messages, file_path)

            if success:
                QMessageBox.information(
                    self.panel, "성공", f"세션이 성공적으로 내보내졌습니다:\n{file_path}"
                )
            else:
                QMessageBox.warning(self.panel, "실패", "내보내기에 실패했습니다.")

        except Exception as e:
            logger.error(f"세션 내보내기 오류: {e}")
            QMessageBox.critical(self.panel, "오류", f"내보내기 중 오류가 발생했습니다:\n{e}")

    def _export_to_pdf(self, session: Dict):
        """PDF로 내보내기 - HTML 렌더링된 상태로"""
        try:
            # 메시지 데이터 가져오기 (HTML 포함)
            messages = session_manager.get_session_messages(
                session["id"], limit=None, include_html=True
            )

            if not messages:
                QMessageBox.information(self.panel, "정보", "내보낼 메시지가 없습니다.")
                return

            # PDF 내보내기 실행
            from core.pdf_exporter import PDFExporter

            pdf_exporter = PDFExporter(self.panel)

            # 메시지 형식 변환 - HTML 콘텐츠 사용
            formatted_messages = []
            for msg in messages:
                content = msg.get("content", "")
                formatted_messages.append(
                    {
                        "role": msg.get("role", "unknown"),
                        "content": content,
                        "timestamp": msg.get("timestamp", ""),
                    }
                )

            success = pdf_exporter.export_conversation_to_pdf(
                formatted_messages, session.get("title", "대화")
            )

            if success:
                QMessageBox.information(self.panel, "성공", "PDF 내보내기가 완료되었습니다.")

        except Exception as e:
            logger.error(f"PDF 내보내기 오류: {e}")
            QMessageBox.critical(self.panel, "오류", f"PDF 내보내기 실패: {str(e)}")
