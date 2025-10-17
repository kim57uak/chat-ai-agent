"""
AI Settings Tab
AI 설정 탭
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QComboBox, QLineEdit, QGroupBox, QVBoxLayout
from core.file_utils import save_model_api_key, load_model_api_key, load_last_model
from core.config.ai_model_manager import AIModelManager
from ..base_settings_tab import BaseSettingsTab


class AISettingsTab(BaseSettingsTab):
    """AI 설정 탭"""
    
    def __init__(self, parent=None):
        self.model_manager = AIModelManager()
        super().__init__(parent)
    
    def create_ui(self):
        """UI 생성"""
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
        
        self.content_layout.addWidget(model_group)
        
        # 이벤트 연결
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
    
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
    
    def load_settings(self):
        """설정 로드"""
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
        
        current_index = self.model_combo.currentIndex()
        model_id = self.model_combo.itemData(current_index)
        if model_id:
            self.api_key_edit.setText(load_model_api_key(model_id))
    
    def save_settings(self):
        """설정 저장"""
        current_index = self.model_combo.currentIndex()
        model_id = self.model_combo.itemData(current_index)
        
        if model_id:
            api_key = self.api_key_edit.text()
            save_model_api_key(model_id, api_key)
    
    def get_tab_title(self) -> str:
        return '🤖 AI 설정'
