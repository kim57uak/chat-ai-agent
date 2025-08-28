from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLineEdit, QLabel, QPushButton, QSpinBox, QCheckBox, QGroupBox, QHBoxLayout
from core.file_utils import save_model_api_key, load_model_api_key, load_last_model, load_config, save_config
from core.config.ai_model_manager import AIModelManager
from ui.styles.flat_theme import FlatTheme

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('환경설정')
        self.setMinimumWidth(450)
        self.setStyleSheet(self._get_dialog_style())
        layout = QVBoxLayout(self)
        
        # AI 모델 매니저 초기화
        self.model_manager = AIModelManager()

        # AI 제공업체 선택
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel('AI 제공업체:'))
        self.provider_combo = QComboBox(self)
        self.provider_combo.addItems(['OpenAI', 'Google', 'Claude', 'Perplexity', 'Image Generation'])
        provider_layout.addWidget(self.provider_combo)
        layout.addLayout(provider_layout)
        
        # 상세 모델 선택
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel('모델:'))
        self.model_combo = QComboBox(self)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # 이벤트 연결
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
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
        
        # 하이브리드 대화 히스토리 설정 그룹
        history_group = QGroupBox('하이브리드 대화 히스토리 설정')
        history_layout = QVBoxLayout(history_group)
        
        self.hybrid_mode = QCheckBox('하이브리드 모드 사용')
        history_layout.addWidget(self.hybrid_mode)
        
        history_layout.addWidget(QLabel('사용자 메시지 제한 (1-50):'))
        self.user_message_limit_spin = QSpinBox()
        self.user_message_limit_spin.setRange(1, 50)
        self.user_message_limit_spin.setValue(10)
        history_layout.addWidget(self.user_message_limit_spin)
        
        history_layout.addWidget(QLabel('AI 응답 제한 (1-50):'))
        self.ai_response_limit_spin = QSpinBox()
        self.ai_response_limit_spin.setRange(1, 50)
        self.ai_response_limit_spin.setValue(10)
        history_layout.addWidget(self.ai_response_limit_spin)
        
        history_layout.addWidget(QLabel('AI 응답 토큰 제한 (1000-50000):'))
        self.ai_response_token_limit_spin = QSpinBox()
        self.ai_response_token_limit_spin.setRange(1000, 50000)
        self.ai_response_token_limit_spin.setValue(15000)
        history_layout.addWidget(self.ai_response_token_limit_spin)
        
        layout.addWidget(history_group)
        
        # 언어 감지 설정 그룹
        language_group = QGroupBox('언어 감지 설정')
        language_layout = QVBoxLayout(language_group)
        
        language_layout.addWidget(QLabel('한글 비율 임계값 (0.0-1.0):'))
        self.korean_threshold_spin = QSpinBox()
        self.korean_threshold_spin.setRange(0, 100)
        self.korean_threshold_spin.setValue(30)
        self.korean_threshold_spin.setSuffix('%')
        language_layout.addWidget(self.korean_threshold_spin)
        
        language_layout.addWidget(QLabel('한글 비율이 이 값 이상이면 한국어로 인식'))
        
        layout.addWidget(language_group)

        self.save_button = QPushButton('저장', self)
        layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)

        self.load()
    
    def on_provider_changed(self, provider):
        """Handle provider selection change."""
        self.model_combo.clear()
        
        models_by_category = self.model_manager.get_models_by_category()
        category_models = models_by_category.get(provider, [])
        
        for model in category_models:
            self.model_combo.addItem(model['name'])
            self.model_combo.setItemData(self.model_combo.count() - 1, model['id'])
        
        # Load API key for first model if available
        if self.model_combo.count() > 0:
            first_model_id = self.model_combo.itemData(0)
            if first_model_id:
                self.api_key_edit.setText(load_model_api_key(first_model_id))

    def load(self):
        last_model = load_last_model()
        
        # Find provider for the last model
        model_info = self.model_manager.get_model_info(last_model)
        if model_info:
            category = model_info.get('category', 'OpenAI')
            
            # Set provider
            provider_index = self.provider_combo.findText(category)
            if provider_index >= 0:
                self.provider_combo.setCurrentIndex(provider_index)
            
            # Populate models for this provider
            self.on_provider_changed(category)
            
            # Find and select the specific model
            for i in range(self.model_combo.count()):
                item_data = self.model_combo.itemData(i)
                if item_data == last_model:
                    self.model_combo.setCurrentIndex(i)
                    break
        else:
            # Default to first provider and model
            self.on_provider_changed(self.provider_combo.currentText())
        
        # Load API key
        current_index = self.model_combo.currentIndex()
        model_id = self.model_combo.itemData(current_index)
        if model_id:
            self.api_key_edit.setText(load_model_api_key(model_id))
        
        # 응답 길이 제한 설정 로드
        config = load_config()
        response_settings = config.get('response_settings', {})
        
        self.enable_length_limit.setChecked(response_settings.get('enable_length_limit', True))
        self.max_tokens_spin.setValue(response_settings.get('max_tokens', 1500))
        self.max_response_length_spin.setValue(response_settings.get('max_response_length', 8000))
        
        # 하이브리드 대화 히스토리 설정 로드
        conversation_settings = config.get('conversation_settings', {})
        
        self.hybrid_mode.setChecked(conversation_settings.get('hybrid_mode', True))
        self.user_message_limit_spin.setValue(conversation_settings.get('user_message_limit', 10))
        self.ai_response_limit_spin.setValue(conversation_settings.get('ai_response_limit', 10))
        self.ai_response_token_limit_spin.setValue(conversation_settings.get('ai_response_token_limit', 15000))
        
        # 언어 감지 설정 로드
        language_settings = config.get('language_detection', {})
        korean_threshold = language_settings.get('korean_threshold', 0.3)
        self.korean_threshold_spin.setValue(int(korean_threshold * 100))

    def on_model_changed(self, model_name):
        """Handle model selection change."""
        current_index = self.model_combo.currentIndex()
        model_id = self.model_combo.itemData(current_index)
        
        if model_id:
            self.api_key_edit.setText(load_model_api_key(model_id))

    def save(self):
        current_index = self.model_combo.currentIndex()
        model_id = self.model_combo.itemData(current_index)
        
        if not model_id:
            return
            
        api_key = self.api_key_edit.text()
        save_model_api_key(model_id, api_key)
        
        # 응답 길이 제한 설정 저장
        config = load_config()
        if 'response_settings' not in config:
            config['response_settings'] = {}
        
        config['response_settings']['enable_length_limit'] = self.enable_length_limit.isChecked()
        config['response_settings']['max_tokens'] = self.max_tokens_spin.value()
        config['response_settings']['max_response_length'] = self.max_response_length_spin.value()
        
        # 하이브리드 대화 히스토리 설정 저장
        if 'conversation_settings' not in config:
            config['conversation_settings'] = {}
        
        config['conversation_settings']['hybrid_mode'] = self.hybrid_mode.isChecked()
        config['conversation_settings']['user_message_limit'] = self.user_message_limit_spin.value()
        config['conversation_settings']['ai_response_limit'] = self.ai_response_limit_spin.value()
        config['conversation_settings']['ai_response_token_limit'] = self.ai_response_token_limit_spin.value()
        
        # 언어 감지 설정 저장
        if 'language_detection' not in config:
            config['language_detection'] = {}
        
        config['language_detection']['korean_threshold'] = self.korean_threshold_spin.value() / 100.0
        config['language_detection']['description'] = 'Korean character ratio threshold for language detection (0.0-1.0)'
        
        save_config(config)
        self.accept()
    
    def _get_dialog_style(self):
        return """
            QDialog {
                background: #5a5a5f;
                color: #ffffff;
                font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 4px 0;
            }
            QComboBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(45, 45, 55, 0.95), 
                    stop:1 rgba(35, 35, 45, 0.95));
                color: #ffffff;
                border: 2px solid rgba(100, 200, 255, 0.3);
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: rgba(100, 200, 255, 0.5);
            }
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(45, 45, 55, 0.95), 
                    stop:1 rgba(35, 35, 45, 0.95));
                color: #ffffff;
                border: 2px solid rgba(100, 200, 255, 0.3);
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit:focus {
                border-color: rgba(100, 200, 255, 0.6);
            }
            QSpinBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(45, 45, 55, 0.95), 
                    stop:1 rgba(35, 35, 45, 0.95));
                color: #ffffff;
                border: 2px solid rgba(100, 200, 255, 0.3);
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid rgba(100, 200, 255, 0.4);
                border-radius: 4px;
                background: rgba(45, 45, 55, 0.8);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(100, 200, 255, 0.8), 
                    stop:1 rgba(150, 100, 255, 0.8));
                border-color: rgba(100, 200, 255, 0.6);
            }
            QGroupBox {
                color: #ffffff;
                font-size: 15px;
                font-weight: 700;
                border: 2px solid rgba(100, 200, 255, 0.3);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background: #5a5a5f;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(100, 200, 255, 0.8), 
                    stop:1 rgba(150, 100, 255, 0.8));
                color: #ffffff;
                border: 2px solid rgba(100, 200, 255, 0.4);
                border-radius: 10px;
                font-weight: 700;
                font-size: 16px;
                padding: 12px 24px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(120, 220, 255, 0.9), 
                    stop:1 rgba(170, 120, 255, 0.9));
                border-color: rgba(100, 200, 255, 0.6);
            }
        """ 