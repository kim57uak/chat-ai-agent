from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLineEdit, QLabel, QPushButton, QSpinBox, QCheckBox, QGroupBox
from core.file_utils import save_model_api_key, load_model_api_key, load_last_model, load_config, save_config

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
        
        # 응답 길이 제한 설정 그룹
        response_group = QGroupBox('응답 길이 제한 설정')
        response_layout = QVBoxLayout(response_group)
        
        self.enable_length_limit = QCheckBox('응답 길이 제한 사용')
        response_layout.addWidget(self.enable_length_limit)
        
        response_layout.addWidget(QLabel('최대 토큰 수 (1-4096):'))
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 4096)
        self.max_tokens_spin.setValue(1500)
        response_layout.addWidget(self.max_tokens_spin)
        
        response_layout.addWidget(QLabel('최대 응답 길이 (문자 수):'))
        self.max_response_length_spin = QSpinBox()
        self.max_response_length_spin.setRange(1000, 50000)
        self.max_response_length_spin.setValue(8000)
        response_layout.addWidget(self.max_response_length_spin)
        
        layout.addWidget(response_group)

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
        
        # 응답 길이 제한 설정 로드
        config = load_config()
        response_settings = config.get('response_settings', {})
        
        self.enable_length_limit.setChecked(response_settings.get('enable_length_limit', True))
        self.max_tokens_spin.setValue(response_settings.get('max_tokens', 1500))
        self.max_response_length_spin.setValue(response_settings.get('max_response_length', 8000))

    def on_model_changed(self, model):
        self.api_key_edit.setText(load_model_api_key(model))

    def save(self):
        model = self.model_combo.currentText()
        api_key = self.api_key_edit.text()
        save_model_api_key(model, api_key)
        
        # 응답 길이 제한 설정 저장
        config = load_config()
        if 'response_settings' not in config:
            config['response_settings'] = {}
        
        config['response_settings']['enable_length_limit'] = self.enable_length_limit.isChecked()
        config['response_settings']['max_tokens'] = self.max_tokens_spin.value()
        config['response_settings']['max_response_length'] = self.max_response_length_spin.value()
        
        save_config(config)
        self.accept() 