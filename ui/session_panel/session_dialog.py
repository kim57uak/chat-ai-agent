"""
Session Creation Dialog
새 세션 생성 다이얼로그
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox)
from typing import Dict


class NewSessionDialog(QDialog):
    """새 세션 생성 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("새 세션 생성")
        self.setModal(True)
        self.resize(400, 200)

        layout = QVBoxLayout()

        # 제목 입력
        layout.addWidget(QLabel("세션 제목:"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("예: Python 학습, 여행 계획 등")
        layout.addWidget(self.title_edit)

        # 카테고리 입력
        layout.addWidget(QLabel("카테고리 (선택사항):"))
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("예: 개발, 여행, 업무 등")
        layout.addWidget(self.category_edit)

        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.title_edit.setFocus()

    def get_session_data(self) -> Dict[str, str]:
        """세션 데이터 반환"""
        return {
            "title": self.title_edit.text().strip(),
            "category": self.category_edit.text().strip() or None,
        }
