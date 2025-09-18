from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
                            QLabel, QPushButton, QSpinBox, QCheckBox, QGroupBox, 
                            QTabWidget, QWidget, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from core.file_utils import save_model_api_key, load_model_api_key, load_last_model, load_prompt_config, save_prompt_config
from core.config.ai_model_manager import AIModelManager
from ui.styles.material_theme_manager import material_theme_manager
import json
import os

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('🔧 환경설정')
        self.setMinimumSize(600, 700)
        self.setStyleSheet(self._get_themed_dialog_style())
        
        # AI 모델 매니저 초기화
        self.model_manager = AIModelManager()
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 제목
        title_label = QLabel('⚙️ 환경설정')
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 800;
                padding: 10px 0;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._get_tab_style())
        main_layout.addWidget(self.tab_widget)
        
        # 탭 생성
        self.create_ai_settings_tab()
        self.create_length_limit_tab()
        self.create_history_settings_tab()
        self.create_language_detection_tab()
        
        # 저장 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton('💾 저장')
        self.save_button.setStyleSheet(self._get_save_button_style())
        self.save_button.clicked.connect(self.save)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton('❌ 취소')
        self.cancel_button.setStyleSheet(self._get_cancel_button_style())
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # 설정 로드
        self.load_settings()
    
    def create_ai_settings_tab(self):
        """AI 설정 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # AI 모델 설정 그룹
        model_group = QGroupBox('🤖 AI 모델 설정')
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(12)
        
        # AI 제공업체 선택
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel('AI 제공업체:'))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(['OpenAI', 'Google', 'Claude', 'Perplexity', 'Image Generation'])
        provider_layout.addWidget(self.provider_combo)
        model_layout.addLayout(provider_layout)
        
        # 상세 모델 선택
        model_detail_layout = QHBoxLayout()
        model_detail_layout.addWidget(QLabel('모델:'))
        self.model_combo = QComboBox()
        model_detail_layout.addWidget(self.model_combo)
        model_layout.addLayout(model_detail_layout)
        
        # API Key 입력
        api_layout = QVBoxLayout()
        api_layout.addWidget(QLabel('🔑 API Key:'))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText('API 키를 입력하세요...')
        api_layout.addWidget(self.api_key_edit)
        model_layout.addLayout(api_layout)
        
        layout.addWidget(model_group)
        layout.addStretch()
        
        # 이벤트 연결
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        
        self.tab_widget.addTab(tab, '🤖 AI 설정')
    
    def create_length_limit_tab(self):
        """길이 제한 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 응답 길이 제한 그룹
        response_group = QGroupBox('📏 응답 길이 제한 설정')
        response_layout = QVBoxLayout(response_group)
        response_layout.setSpacing(12)
        
        self.enable_length_limit = QCheckBox('응답 길이 제한 사용')
        response_layout.addWidget(self.enable_length_limit)
        
        # 최대 토큰 수
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel('최대 토큰 수:'))
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 8192)
        self.max_tokens_spin.setValue(4096)
        self.max_tokens_spin.setSuffix(' tokens')
        self.max_tokens_spin.setMinimumHeight(40)
        token_layout.addWidget(self.max_tokens_spin)
        response_layout.addLayout(token_layout)
        
        # 최대 응답 길이
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel('최대 응답 길이:'))
        self.max_response_length_spin = QSpinBox()
        self.max_response_length_spin.setRange(1000, 100000)
        self.max_response_length_spin.setValue(50000)
        self.max_response_length_spin.setSuffix(' 문자')
        self.max_response_length_spin.setMinimumHeight(40)
        length_layout.addWidget(self.max_response_length_spin)
        response_layout.addLayout(length_layout)
        
        # 스트리밍 설정
        streaming_layout = QVBoxLayout()
        self.enable_streaming = QCheckBox('스트리밍 응답 사용')
        streaming_layout.addWidget(self.enable_streaming)
        
        chunk_layout = QHBoxLayout()
        chunk_layout.addWidget(QLabel('스트리밍 청크 크기:'))
        self.streaming_chunk_size_spin = QSpinBox()
        self.streaming_chunk_size_spin.setRange(50, 1000)
        self.streaming_chunk_size_spin.setValue(300)
        self.streaming_chunk_size_spin.setSuffix(' 문자')
        self.streaming_chunk_size_spin.setMinimumHeight(40)
        chunk_layout.addWidget(self.streaming_chunk_size_spin)
        streaming_layout.addLayout(chunk_layout)
        
        response_layout.addLayout(streaming_layout)
        layout.addWidget(response_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, '📏 길이제한')
    
    def create_history_settings_tab(self):
        """히스토리 설정 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 대화 히스토리 설정 그룹
        history_group = QGroupBox('💬 대화 히스토리 설정')
        history_layout = QVBoxLayout(history_group)
        history_layout.setSpacing(12)
        
        self.enable_history = QCheckBox('대화 히스토리 사용')
        history_layout.addWidget(self.enable_history)
        
        self.hybrid_mode = QCheckBox('하이브리드 모드 사용')
        history_layout.addWidget(self.hybrid_mode)
        
        # 사용자 메시지 제한
        user_limit_layout = QHBoxLayout()
        user_limit_layout.addWidget(QLabel('사용자 메시지 제한:'))
        self.user_message_limit_spin = QSpinBox()
        self.user_message_limit_spin.setRange(1, 50)
        self.user_message_limit_spin.setValue(6)
        self.user_message_limit_spin.setSuffix(' 개')
        self.user_message_limit_spin.setMinimumHeight(40)
        user_limit_layout.addWidget(self.user_message_limit_spin)
        history_layout.addLayout(user_limit_layout)
        
        # AI 응답 제한
        ai_limit_layout = QHBoxLayout()
        ai_limit_layout.addWidget(QLabel('AI 응답 제한:'))
        self.ai_response_limit_spin = QSpinBox()
        self.ai_response_limit_spin.setRange(1, 50)
        self.ai_response_limit_spin.setValue(4)
        self.ai_response_limit_spin.setSuffix(' 개')
        self.ai_response_limit_spin.setMinimumHeight(40)
        ai_limit_layout.addWidget(self.ai_response_limit_spin)
        history_layout.addLayout(ai_limit_layout)
        
        # AI 응답 토큰 제한
        token_limit_layout = QHBoxLayout()
        token_limit_layout.addWidget(QLabel('AI 응답 토큰 제한:'))
        self.ai_response_token_limit_spin = QSpinBox()
        self.ai_response_token_limit_spin.setRange(1000, 50000)
        self.ai_response_token_limit_spin.setValue(4000)
        self.ai_response_token_limit_spin.setSuffix(' tokens')
        self.ai_response_token_limit_spin.setMinimumHeight(40)
        token_limit_layout.addWidget(self.ai_response_token_limit_spin)
        history_layout.addLayout(token_limit_layout)
        
        layout.addWidget(history_group)
        
        # 페이징 설정 그룹
        paging_group = QGroupBox('📄 페이징 설정')
        paging_layout = QVBoxLayout(paging_group)
        paging_layout.setSpacing(12)
        
        # 첫 페이지 로딩 갯수
        initial_layout = QHBoxLayout()
        initial_layout.addWidget(QLabel('첫 페이지 로딩 갯수:'))
        self.initial_load_count_spin = QSpinBox()
        self.initial_load_count_spin.setRange(10, 200)
        self.initial_load_count_spin.setValue(50)
        self.initial_load_count_spin.setSuffix(' 개')
        self.initial_load_count_spin.setMinimumHeight(40)
        initial_layout.addWidget(self.initial_load_count_spin)
        paging_layout.addLayout(initial_layout)
        
        # 페이징 갯수
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel('페이징 갯수:'))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(5, 50)
        self.page_size_spin.setValue(10)
        self.page_size_spin.setSuffix(' 개')
        self.page_size_spin.setMinimumHeight(40)
        page_layout.addWidget(self.page_size_spin)
        paging_layout.addLayout(page_layout)
        
        layout.addWidget(paging_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, '💬 히스토리')
    
    def create_language_detection_tab(self):
        """언어 감지 설정 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 언어 감지 설정 그룹
        language_group = QGroupBox('🌐 언어 감지 설정')
        language_layout = QVBoxLayout(language_group)
        language_layout.setSpacing(12)
        
        # 한글 비율 임계값
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel('한글 비율 임계값:'))
        self.korean_threshold_spin = QSpinBox()
        self.korean_threshold_spin.setRange(0, 100)
        self.korean_threshold_spin.setValue(10)
        self.korean_threshold_spin.setSuffix('%')
        self.korean_threshold_spin.setMinimumHeight(40)
        threshold_layout.addWidget(self.korean_threshold_spin)
        language_layout.addLayout(threshold_layout)
        
        # 설명 라벨
        desc_label = QLabel('한글 비율이 이 값 이상이면 한국어로 인식합니다.')
        desc_label.setStyleSheet('color: #888; font-size: 12px; font-style: italic;')
        language_layout.addWidget(desc_label)
        
        layout.addWidget(language_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, '🌐 언어감지')
    
    def on_provider_changed(self, provider):
        """제공업체 변경 처리"""
        self.model_combo.clear()
        
        models_by_category = self.model_manager.get_models_by_category()
        category_models = models_by_category.get(provider, [])
        
        for model in category_models:
            self.model_combo.addItem(model['name'])
            self.model_combo.setItemData(self.model_combo.count() - 1, model['id'])
        
        # 첫 번째 모델의 API 키 로드
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
    
    def load_settings(self):
        """설정 로드"""
        # AI 모델 설정 로드
        last_model = load_last_model()
        model_info = self.model_manager.get_model_info(last_model)
        
        if model_info:
            category = model_info.get('category', 'OpenAI')
            provider_index = self.provider_combo.findText(category)
            if provider_index >= 0:
                self.provider_combo.setCurrentIndex(provider_index)
            
            self.on_provider_changed(category)
            
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == last_model:
                    self.model_combo.setCurrentIndex(i)
                    break
        else:
            self.on_provider_changed(self.provider_combo.currentText())
        
        # API 키 로드
        current_index = self.model_combo.currentIndex()
        model_id = self.model_combo.itemData(current_index)
        if model_id:
            self.api_key_edit.setText(load_model_api_key(model_id))
        
        # prompt_config.json에서 설정 로드
        prompt_config = load_prompt_config()
        
        # 응답 길이 제한 설정
        response_settings = prompt_config.get('response_settings', {})
        self.enable_length_limit.setChecked(response_settings.get('enable_length_limit', False))
        self.max_tokens_spin.setValue(response_settings.get('max_tokens', 4096))
        self.max_response_length_spin.setValue(response_settings.get('max_response_length', 50000))
        self.enable_streaming.setChecked(response_settings.get('enable_streaming', True))
        self.streaming_chunk_size_spin.setValue(response_settings.get('streaming_chunk_size', 300))
        
        # 히스토리 설정
        conversation_settings = prompt_config.get('conversation_settings', {})
        self.enable_history.setChecked(conversation_settings.get('enable_history', True))
        self.hybrid_mode.setChecked(conversation_settings.get('hybrid_mode', True))
        self.user_message_limit_spin.setValue(conversation_settings.get('user_message_limit', 6))
        self.ai_response_limit_spin.setValue(conversation_settings.get('ai_response_limit', 4))
        self.ai_response_token_limit_spin.setValue(conversation_settings.get('ai_response_token_limit', 4000))
        
        # 페이징 설정
        history_settings = prompt_config.get('history_settings', {})
        self.initial_load_count_spin.setValue(history_settings.get('initial_load_count', 50))
        self.page_size_spin.setValue(history_settings.get('page_size', 10))
        
        # 언어 감지 설정
        language_settings = prompt_config.get('language_detection', {})
        korean_threshold = language_settings.get('korean_threshold', 0.1)
        self.korean_threshold_spin.setValue(int(korean_threshold * 100))
    
    def save(self):
        """설정 저장"""
        # AI 모델 설정 저장
        current_index = self.model_combo.currentIndex()
        model_id = self.model_combo.itemData(current_index)
        
        if model_id:
            api_key = self.api_key_edit.text()
            save_model_api_key(model_id, api_key)
        
        # prompt_config.json에 설정 저장
        prompt_config = load_prompt_config()
        
        # 응답 길이 제한 설정
        prompt_config['response_settings'] = {
            'enable_length_limit': self.enable_length_limit.isChecked(),
            'max_tokens': self.max_tokens_spin.value(),
            'max_response_length': self.max_response_length_spin.value(),
            'enable_streaming': self.enable_streaming.isChecked(),
            'streaming_chunk_size': self.streaming_chunk_size_spin.value()
        }
        
        # 히스토리 설정
        prompt_config['conversation_settings'] = {
            'enable_history': self.enable_history.isChecked(),
            'hybrid_mode': self.hybrid_mode.isChecked(),
            'user_message_limit': self.user_message_limit_spin.value(),
            'ai_response_limit': self.ai_response_limit_spin.value(),
            'ai_response_token_limit': self.ai_response_token_limit_spin.value(),
            'max_history_pairs': self.user_message_limit_spin.value(),
            'max_tokens_estimate': self.ai_response_token_limit_spin.value() * 2
        }
        
        # 페이징 설정
        prompt_config['history_settings'] = {
            'initial_load_count': self.initial_load_count_spin.value(),
            'page_size': self.page_size_spin.value()
        }
        
        # 언어 감지 설정
        prompt_config['language_detection'] = {
            'korean_threshold': self.korean_threshold_spin.value() / 100.0,
            'description': 'Korean character ratio threshold for language detection (0.0-1.0)'
        }
        
        save_prompt_config(prompt_config)
        self.accept()
    
    def _get_themed_dialog_style(self):
        """테마 스타일 반환"""
        theme = material_theme_manager.get_current_theme()
        colors = theme.get('colors', {})
        
        return f"""
            QDialog {{
                background: {colors.get('background', '#121212')};
                color: {colors.get('text_primary', '#ffffff')};
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            }}
            QLabel {{
                color: {colors.get('text_primary', '#ffffff')};
                font-size: 14px;
                font-weight: 600;
                padding: 4px 0;
            }}
            QComboBox, QLineEdit {{
                background: {colors.get('surface', '#1e1e1e')};
                color: {colors.get('text_primary', '#ffffff')};
                border: 2px solid {colors.get('primary', '#bb86fc')};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }}
            QComboBox:hover, QLineEdit:focus {{
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
                padding-right: 40px;
            }}
            QSpinBox:hover {{
                border-color: {colors.get('secondary', '#03dac6')};
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 32px;
                height: 18px;
                border-left: 2px solid {colors.get('divider', '#333333')};
                border-bottom: 1px solid {colors.get('divider', '#333333')};
                border-top-right-radius: 6px;
                background: {colors.get('primary', '#bb86fc')};
            }}
            QSpinBox::up-button:hover {{
                background: {colors.get('secondary', '#03dac6')};
            }}
            QSpinBox::up-button:pressed {{
                background: {colors.get('primary_variant', '#3700b3')};
            }}
            QSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid {colors.get('on_primary', '#000000')};
                width: 0px;
                height: 0px;
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 32px;
                height: 18px;
                border-left: 2px solid {colors.get('divider', '#333333')};
                border-top: 1px solid {colors.get('divider', '#333333')};
                border-bottom-right-radius: 6px;
                background: {colors.get('primary', '#bb86fc')};
            }}
            QSpinBox::down-button:hover {{
                background: {colors.get('secondary', '#03dac6')};
            }}
            QSpinBox::down-button:pressed {{
                background: {colors.get('primary_variant', '#3700b3')};
            }}
            QSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors.get('on_primary', '#000000')};
                width: 0px;
                height: 0px;
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
                font-size: 16px;
                font-weight: 700;
                border: 2px solid {colors.get('divider', '#333333')};
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 20px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background: {colors.get('background', '#121212')};
            }}
        """
    
    def _get_tab_style(self):
        """탭 스타일 반환"""
        theme = material_theme_manager.get_current_theme()
        colors = theme.get('colors', {})
        
        return f"""
            QTabWidget {{
                background: transparent;
                border: none;
            }}
            QTabWidget::pane {{
                background: {colors.get('surface', '#1e1e1e')};
                border: 2px solid {colors.get('divider', '#333333')};
                border-radius: 12px;
                margin-top: 5px;
            }}
            QTabBar::tab {{
                background: {colors.get('background', '#121212')};
                color: {colors.get('text_primary', '#ffffff')};
                border: 2px solid {colors.get('divider', '#333333')};
                padding: 12px 20px;
                margin: 2px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background: {colors.get('primary', '#bb86fc')};
                color: {colors.get('on_primary', '#000000')};
                border-color: {colors.get('secondary', '#03dac6')};
                font-weight: 700;
            }}
            QTabBar::tab:hover {{
                background: {colors.get('primary_variant', '#3700b3')};
                color: {colors.get('on_primary', '#ffffff')};
            }}
        """
    
    def _get_save_button_style(self):
        """저장 버튼 스타일"""
        theme = material_theme_manager.get_current_theme()
        colors = theme.get('colors', {})
        
        return f"""
            QPushButton {{
                background: {colors.get('primary', '#bb86fc')};
                color: {colors.get('on_primary', '#000000')};
                border: 2px solid {colors.get('secondary', '#03dac6')};
                border-radius: 12px;
                font-weight: 700;
                font-size: 16px;
                padding: 15px 30px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: {colors.get('secondary', '#03dac6')};
                color: {colors.get('on_secondary', '#000000')};
                border-color: {colors.get('primary', '#bb86fc')};
            }}
        """
    
    def _get_cancel_button_style(self):
        """취소 버튼 스타일"""
        theme = material_theme_manager.get_current_theme()
        colors = theme.get('colors', {})
        
        return f"""
            QPushButton {{
                background: {colors.get('surface', '#1e1e1e')};
                color: {colors.get('text_primary', '#ffffff')};
                border: 2px solid {colors.get('divider', '#333333')};
                border-radius: 12px;
                font-weight: 600;
                font-size: 16px;
                padding: 15px 30px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: {colors.get('error', '#cf6679')};
                color: {colors.get('on_error', '#000000')};
                border-color: {colors.get('error', '#cf6679')};
            }}
        """