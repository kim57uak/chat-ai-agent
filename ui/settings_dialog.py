from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLineEdit, QLabel, QPushButton
from core.file_utils import save_model_api_key, load_model_api_key, load_last_model

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('환경설정')
        self.setMinimumWidth(350)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel('AI 모델 선택'))
        self.model_combo = QComboBox(self)
        self.model_combo.addItems([
            'gpt-3.5-turbo',
            'gpt-4',
            'claude-2',
            'gemini-1.5-pro',
            'gemini-2.0-flash-exp',
            'gemini-2.5-pro',
            'gemini-2.5-flash'
        ])
        layout.addWidget(self.model_combo)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)

        layout.addWidget(QLabel('API Key'))
        self.api_key_edit = QLineEdit(self)
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_key_edit)

        self.save_button = QPushButton('저장', self)
        layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)

        self.load()

    def load(self):
        last_model = load_last_model()
        idx = self.model_combo.findText(last_model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        self.api_key_edit.setText(load_model_api_key(self.model_combo.currentText()))

    def on_model_changed(self, model):
        self.api_key_edit.setText(load_model_api_key(model))

    def save(self):
        model = self.model_combo.currentText()
        api_key = self.api_key_edit.text()
        save_model_api_key(model, api_key)
        self.accept() 