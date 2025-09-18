from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
                             QLabel, QPushButton, QSpinBox, QCheckBox, QGroupBox, QTabWidget,
                             QWidget, QScrollArea, QFormLayout, QFrame)
from PyQt6.QtCore import Qt
from core.file_utils import save_model_api_key, load_model_api_key, load_last_model, load_config, save_config
from core.config.ai_model_manager import AIModelManager
from ui.styles.material_theme_manager import material_theme_manager
import json
import os

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('환경설정')
        self.setFixedSize(700, 750)
        self.setStyleSheet(self._get_themed_dialog_style())
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumHeight(620)
        layout.addWidget(self.tab_widget)
        
        # AI 모델 매니저 초기화
        self.model_manager = AIModelManager()
        
        # 탭 생성
        self._create_ai_settings_tab()
        self._create_length_limit_tab()
        self._create_history_settings_tab()
        self._create_language_detection_tab()
        
        # 저장 버튼
        self.save_button = QPushButton('저장', self)
        self.save_button.setFixedHeight(45)
        self.save_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)
        
        self.load()
    
    def _create_ai_settings_tab(self):
        """AI 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # AI 설정 그룹
        ai_group = QGroupBox('AI 모델 설정')
        ai_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        form_layout = QFormLayout(ai_group)
        form_layout.setVerticalSpacing(18)
        form_layout.setHorizontalSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # AI 제공업체 선택
        provider_label = QLabel('AI 제공업체:')
        provider_label.setMinimumWidth(100)
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(['OpenAI', 'Google', 'Claude', 'Perplexity', 'Image Generation'])
        self.provider_combo.setFixedHeight(40)
        self.provider_combo.setMinimumWidth(300)
        form_layout.addRow(provider_label, self.provider_combo)
        
        # 상세 모델 선택
        model_label = QLabel('모델:')
        model_label.setMinimumWidth(100)
        self.model_combo = QComboBox()
        self.model_combo.setFixedHeight(40)
        self.model_combo.setMinimumWidth(300)
        form_layout.addRow(model_label, self.model_combo)
        
        # API Key
        api_label = QLabel('API Key:')
        api_label.setMinimumWidth(100)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setFixedHeight(40)
        self.api_key_edit.setMinimumWidth(300)
        self.api_key_edit.setPlaceholderText('API 키를 입력하세요')
        form_layout.addRow(api_label, self.api_key_edit)
        
        layout.addWidget(ai_group)
        layout.addStretch()
        
        # 이벤트 연결
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        
        self.tab_widget.addTab(widget, "AI 설정")
    
    def _create_length_limit_tab(self):
        """길이 제한 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # 길이 제한 설정 그룹
        limit_group = QGroupBox('응답 길이 제한 설정')
        limit_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        limit_layout = QVBoxLayout(limit_group)
        limit_layout.setSpacing(18)
        
        # 응답 길이 제한 사용
        self.enable_length_limit = QCheckBox('응답 길이 제한 사용')
        self.enable_length_limit.setFixedHeight(35)
        self.enable_length_limit.setStyleSheet('font-size: 13px; padding: 5px;')
        limit_layout.addWidget(self.enable_length_limit)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        limit_layout.addWidget(line)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # 최대 토큰 수
        tokens_label = QLabel('최대 토큰 수:')
        tokens_label.setMinimumWidth(120)
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 4096)
        self.max_tokens_spin.setValue(1500)
        self.max_tokens_spin.setFixedHeight(40)
        self.max_tokens_spin.setMinimumWidth(200)
        self.max_tokens_spin.setSuffix(' tokens')
        form_layout.addRow(tokens_label, self.max_tokens_spin)
        
        # 최대 응답 길이
        length_label = QLabel('최대 응답 길이:')
        length_label.setMinimumWidth(120)
        self.max_response_length_spin = QSpinBox()
        self.max_response_length_spin.setRange(1000, 50000)
        self.max_response_length_spin.setValue(8000)
        self.max_response_length_spin.setFixedHeight(40)
        self.max_response_length_spin.setMinimumWidth(200)
        self.max_response_length_spin.setSuffix(' 문자')
        form_layout.addRow(length_label, self.max_response_length_spin)
        
        limit_layout.addLayout(form_layout)
        layout.addWidget(limit_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, "길이 제한")
    
    def _create_history_settings_tab(self):
        """히스토리 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # 페이징 설정 그룹
        paging_group = QGroupBox('페이징 설정')
        paging_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        paging_form = QFormLayout(paging_group)
        paging_form.setVerticalSpacing(15)
        paging_form.setHorizontalSpacing(15)
        paging_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # 첫 페이지 로딩 개수
        initial_label = QLabel('첫 페이지 로딩 개수:')
        initial_label.setMinimumWidth(140)
        self.initial_load_count_spin = QSpinBox()
        self.initial_load_count_spin.setRange(10, 100)
        self.initial_load_count_spin.setValue(50)
        self.initial_load_count_spin.setFixedHeight(40)
        self.initial_load_count_spin.setMinimumWidth(150)
        self.initial_load_count_spin.setSuffix(' 개')
        paging_form.addRow(initial_label, self.initial_load_count_spin)
        
        # 페이징 개수
        page_label = QLabel('페이징 개수:')
        page_label.setMinimumWidth(140)
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(5, 20)
        self.page_size_spin.setValue(10)
        self.page_size_spin.setFixedHeight(40)
        self.page_size_spin.setMinimumWidth(150)
        self.page_size_spin.setSuffix(' 개')
        paging_form.addRow(page_label, self.page_size_spin)
        
        layout.addWidget(paging_group)
        
        # 하이브리드 대화 히스토리 설정 그룹
        history_group = QGroupBox('하이브리드 대화 히스토리 설정')
        history_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        history_layout = QVBoxLayout(history_group)
        history_layout.setSpacing(15)
        
        self.hybrid_mode = QCheckBox('하이브리드 모드 사용')
        self.hybrid_mode.setFixedHeight(35)
        self.hybrid_mode.setStyleSheet('font-size: 13px; padding: 5px;')
        history_layout.addWidget(self.hybrid_mode)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        history_layout.addWidget(line)
        
        # 폼 레이아웃
        history_form = QFormLayout()
        history_form.setVerticalSpacing(15)
        history_form.setHorizontalSpacing(15)
        history_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # 사용자 메시지 제한
        user_label = QLabel('사용자 메시지 제한:')
        user_label.setMinimumWidth(140)
        self.user_message_limit_spin = QSpinBox()
        self.user_message_limit_spin.setRange(1, 50)
        self.user_message_limit_spin.setValue(10)
        self.user_message_limit_spin.setFixedHeight(40)
        self.user_message_limit_spin.setMinimumWidth(150)
        self.user_message_limit_spin.setSuffix(' 개')
        history_form.addRow(user_label, self.user_message_limit_spin)
        
        # AI 응답 제한
        ai_label = QLabel('AI 응답 제한:')
        ai_label.setMinimumWidth(140)
        self.ai_response_limit_spin = QSpinBox()
        self.ai_response_limit_spin.setRange(1, 50)
        self.ai_response_limit_spin.setValue(10)
        self.ai_response_limit_spin.setFixedHeight(40)
        self.ai_response_limit_spin.setMinimumWidth(150)
        self.ai_response_limit_spin.setSuffix(' 개')
        history_form.addRow(ai_label, self.ai_response_limit_spin)
        
        # AI 응답 토큰 제한
        token_label = QLabel('AI 응답 토큰 제한:')
        token_label.setMinimumWidth(140)
        self.ai_response_token_limit_spin = QSpinBox()
        self.ai_response_token_limit_spin.setRange(1000, 50000)
        self.ai_response_token_limit_spin.setValue(15000)
        self.ai_response_token_limit_spin.setFixedHeight(40)
        self.ai_response_token_limit_spin.setMinimumWidth(150)
        self.ai_response_token_limit_spin.setSuffix(' tokens')
        history_form.addRow(token_label, self.ai_response_token_limit_spin)
        
        history_layout.addLayout(history_form)
        layout.addWidget(history_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, "히스토리 설정")
    
    def _create_language_detection_tab(self):
        """언어 감지 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # 언어 감지 설정 그룹
        lang_group = QGroupBox('언어 감지 설정')
        lang_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        lang_layout = QVBoxLayout(lang_group)
        lang_layout.setSpacing(15)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # 한글 비율 임계값
        threshold_label = QLabel('한글 비율 임계값:')
        threshold_label.setMinimumWidth(120)
        self.korean_threshold_spin = QSpinBox()
        self.korean_threshold_spin.setRange(0, 100)
        self.korean_threshold_spin.setValue(30)
        self.korean_threshold_spin.setFixedHeight(40)
        self.korean_threshold_spin.setMinimumWidth(150)
        self.korean_threshold_spin.setSuffix('%')
        form_layout.addRow(threshold_label, self.korean_threshold_spin)
        
        lang_layout.addLayout(form_layout)
        
        # 설명 라벨
        desc_label = QLabel('한글 비율이 이 값 이상이면 한국어로 인식합니다')
        desc_label.setStyleSheet('color: #888; font-size: 12px; font-style: italic; padding: 10px;')
        lang_layout.addWidget(desc_label)
        
        layout.addWidget(lang_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, "언어 감지")
    
    def _create_tab_widget(self, layout):
        """탭 위젯 생성 헬퍼"""
        from PyQt6.QtWidgets import QWidget
        widget = QWidget()
        widget.setLayout(layout)
        return widget
    
    def on_provider_changed(self, provider):
        """제공업체 변경 처리"""
        self.model_combo.clear()
        
        models_by_category = self.model_manager.get_models_by_category()
        category_models = models_by_category.get(provider, [])
        
        for model in category_models:
            self.model_combo.addItem(model['name'])
            self.model_combo.setItemData(self.model_combo.count() - 1, model['id'])
        
        if self.model_combo.count() > 0:
            first_model_id = self.model_combo.itemData(0)
            if first_model_id:
                self.api_key_edit.setText(load_model_api_key(first_model_id))
    
    def on_model_changed(self, model_name):
        """모델 변경 처리"""
        current_index = self.model_combo.currentIndex()
        model_id = self.model_combo.itemData(current_index)
        
        if model_id:
            self.api_key_edit.setText(load_model_api_key(model_id))
    
    def load(self):
        """설정 로드"""
        # AI 설정 로드
        last_model = load_last_model()
        model_info = self.model_manager.get_model_info(last_model)
        if model_info:
            category = model_info.get('category', 'OpenAI')
            provider_index = self.provider_combo.findText(category)
            if provider_index >= 0:
                self.provider_combo.setCurrentIndex(provider_index)
            
            self.on_provider_changed(category)
            
            for i in range(self.model_combo.count()):
                item_data = self.model_combo.itemData(i)
                if item_data == last_model:
                    self.model_combo.setCurrentIndex(i)
                    break
        else:
            self.on_provider_changed(self.provider_combo.currentText())
        
        current_index = self.model_combo.currentIndex()
        model_id = self.model_combo.itemData(current_index)
        if model_id:
            self.api_key_edit.setText(load_model_api_key(model_id))
        
        # 설정 파일 로드
        config = load_config()
        prompt_config = self._load_prompt_config()
        
        # 응답 길이 제한 설정 (prompt_config에서)
        response_settings = prompt_config.get('response_settings', {})
        self.enable_length_limit.setChecked(response_settings.get('enable_length_limit', True))
        self.max_tokens_spin.setValue(response_settings.get('max_tokens', 1500))
        self.max_response_length_spin.setValue(response_settings.get('max_response_length', 8000))
        
        # 페이징 설정
        paging_settings = prompt_config.get('paging_settings', {})
        self.initial_load_count_spin.setValue(paging_settings.get('initial_load_count', 50))
        self.page_size_spin.setValue(paging_settings.get('page_size', 10))
        
        # 하이브리드 대화 히스토리 설정 (prompt_config에서)
        conversation_settings = prompt_config.get('conversation_settings', {})
        self.hybrid_mode.setChecked(conversation_settings.get('hybrid_mode', True))
        self.user_message_limit_spin.setValue(conversation_settings.get('user_message_limit', 10))
        self.ai_response_limit_spin.setValue(conversation_settings.get('ai_response_limit', 10))
        self.ai_response_token_limit_spin.setValue(conversation_settings.get('ai_response_token_limit', 15000))
        
        # 언어 감지 설정 (prompt_config에서)
        language_settings = prompt_config.get('language_detection', {})
        korean_threshold = language_settings.get('korean_threshold', 0.3)
        self.korean_threshold_spin.setValue(int(korean_threshold * 100))
    
    def _load_prompt_config(self):
        """prompt_config.json 로드"""
        try:
            if os.path.exists('prompt_config.json'):
                with open('prompt_config.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"prompt_config.json 로드 오류: {e}")
        return {}
    
    def _save_prompt_config(self, config):
        """prompt_config.json 저장"""
        try:
            with open('prompt_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"prompt_config.json 저장 오류: {e}")
    
    def save(self):
        """설정 저장"""
        # AI 설정 저장 (config.json)
        current_index = self.model_combo.currentIndex()
        model_id = self.model_combo.itemData(current_index)
        
        if model_id:
            api_key = self.api_key_edit.text()
            save_model_api_key(model_id, api_key)
        
        # config.json에는 AI 설정만 저장 (이미 save_model_api_key로 처리됨)
        
        # prompt_config.json에 모든 설정 저장
        prompt_config = self._load_prompt_config()
        
        # 페이징 설정
        if 'paging_settings' not in prompt_config:
            prompt_config['paging_settings'] = {}
        prompt_config['paging_settings']['initial_load_count'] = self.initial_load_count_spin.value()
        prompt_config['paging_settings']['page_size'] = self.page_size_spin.value()
        prompt_config['paging_settings']['description'] = 'Chat session paging configuration'
        
        # 응답 길이 제한 설정
        if 'response_settings' not in prompt_config:
            prompt_config['response_settings'] = {}
        prompt_config['response_settings']['enable_length_limit'] = self.enable_length_limit.isChecked()
        prompt_config['response_settings']['max_tokens'] = self.max_tokens_spin.value()
        prompt_config['response_settings']['max_response_length'] = self.max_response_length_spin.value()
        
        # 하이브리드 대화 히스토리 설정
        if 'conversation_settings' not in prompt_config:
            prompt_config['conversation_settings'] = {}
        prompt_config['conversation_settings']['hybrid_mode'] = self.hybrid_mode.isChecked()
        prompt_config['conversation_settings']['user_message_limit'] = self.user_message_limit_spin.value()
        prompt_config['conversation_settings']['ai_response_limit'] = self.ai_response_limit_spin.value()
        prompt_config['conversation_settings']['ai_response_token_limit'] = self.ai_response_token_limit_spin.value()
        
        # 언어 감지 설정
        if 'language_detection' not in prompt_config:
            prompt_config['language_detection'] = {}
        prompt_config['language_detection']['korean_threshold'] = self.korean_threshold_spin.value() / 100.0
        prompt_config['language_detection']['description'] = 'Korean character ratio threshold for language detection (0.0-1.0)'
        
        self._save_prompt_config(prompt_config)
        
        self.accept()
    
    def _get_themed_dialog_style(self):
        """테마 스타일 반환"""
        theme = material_theme_manager.get_current_theme()
        colors = theme.get('colors', {})
        
        return f"""
            QDialog {{
                background: {colors.get('background', '#121212')};
                color: {colors.get('text_primary', '#ffffff')};
                font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
            }}
            QTabWidget::pane {{
                border: 2px solid {colors.get('divider', '#333333')};
                border-radius: 8px;
                background: {colors.get('surface', '#1e1e1e')};
            }}
            QTabBar::tab {{
                background: {colors.get('surface', '#1e1e1e')};
                color: {colors.get('text_primary', '#ffffff')};
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {colors.get('primary', '#bb86fc')};
                color: {colors.get('on_primary', '#000000')};
            }}
            QTabBar::tab:hover {{
                background: {colors.get('primary_variant', '#3700b3')};
            }}
            QLabel {{
                color: {colors.get('text_primary', '#ffffff')};
                font-size: 14px;
                font-weight: 600;
                padding: 4px 0;
            }}
            QComboBox {{
                background: {colors.get('surface', '#1e1e1e')};
                color: {colors.get('text_primary', '#ffffff')};
                border: 2px solid {colors.get('primary', '#bb86fc')};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }}
            QComboBox:hover {{
                border-color: {colors.get('primary_variant', '#3700b3')};
            }}
            QLineEdit {{
                background: {colors.get('surface', '#1e1e1e')};
                color: {colors.get('text_primary', '#ffffff')};
                border: 2px solid {colors.get('primary', '#bb86fc')};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                font-weight: 500;
            }}
            QLineEdit:focus {{
                border-color: {colors.get('secondary', '#03dac6')};
            }}
            QSpinBox {{
                background: {colors.get('surface', '#1e1e1e')};
                color: {colors.get('text_primary', '#ffffff')};
                border: 2px solid {colors.get('primary', '#bb86fc')};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }}
            QCheckBox {{
                color: {colors.get('text_primary', '#ffffff')};
                font-size: 14px;
                font-weight: 500;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {colors.get('primary', '#bb86fc')};
                border-radius: 4px;
                background: {colors.get('surface', '#1e1e1e')};
            }}
            QCheckBox::indicator:checked {{
                background: {colors.get('primary', '#bb86fc')};
                border-color: {colors.get('secondary', '#03dac6')};
            }}
            QGroupBox {{
                color: {colors.get('text_primary', '#ffffff')};
                font-size: 15px;
                font-weight: 700;
                border: 2px solid {colors.get('divider', '#333333')};
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background: {colors.get('surface', '#1e1e1e')};
            }}
            QPushButton {{
                background: {colors.get('primary', '#bb86fc')};
                color: {colors.get('on_primary', '#000000')};
                border: 2px solid {colors.get('primary_variant', '#3700b3')};
                border-radius: 10px;
                font-weight: 700;
                font-size: 16px;
                padding: 12px 24px;
            }}
            QPushButton:hover {{
                background: {colors.get('secondary', '#03dac6')};
                color: {colors.get('on_secondary', '#000000')};
                border-color: {colors.get('secondary_variant', '#018786')};
            }}
        """