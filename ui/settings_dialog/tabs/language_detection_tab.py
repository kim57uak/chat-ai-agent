"""
Language Detection Tab
언어 감지 설정 탭
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSpinBox, QGroupBox, QVBoxLayout
from core.file_utils import load_prompt_config, save_prompt_config
from ..base_settings_tab import BaseSettingsTab


class LanguageDetectionTab(BaseSettingsTab):
    """언어 감지 설정 탭"""
    
    def create_ui(self):
        """UI 생성"""
        # 언어 감지 설정 그룹
        language_group = QGroupBox('🌐 언어 감지 설정')
        language_layout = QVBoxLayout(language_group)
        language_layout.setSpacing(12)
        
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel('한글 비율 임계값:'))
        self.korean_threshold_spin = QSpinBox()
        self.korean_threshold_spin.setRange(0, 100)
        self.korean_threshold_spin.setValue(10)
        self.korean_threshold_spin.setSuffix('%')
        self.korean_threshold_spin.setMinimumHeight(40)
        threshold_layout.addWidget(self.korean_threshold_spin)
        language_layout.addLayout(threshold_layout)
        
        desc_label = QLabel('한글 비율이 이 값 이상이면 한국어로 인식합니다.')
        desc_label.setStyleSheet('color: #888; font-size: 12px; font-style: italic;')
        language_layout.addWidget(desc_label)
        
        self.content_layout.addWidget(language_group)
    
    def load_settings(self):
        """설정 로드"""
        prompt_config = load_prompt_config()
        language_settings = prompt_config.get('language_detection', {})
        korean_threshold = language_settings.get('korean_threshold', 0.1)
        self.korean_threshold_spin.setValue(int(korean_threshold * 100))
    
    def save_settings(self):
        """설정 저장"""
        prompt_config = load_prompt_config()
        
        prompt_config['language_detection'] = {
            'korean_threshold': self.korean_threshold_spin.value() / 100.0,
            'description': 'Korean character ratio threshold for language detection (0.0-1.0)'
        }
        
        save_prompt_config(prompt_config)
    
    def get_tab_title(self) -> str:
        return '🌐 언어감지'
