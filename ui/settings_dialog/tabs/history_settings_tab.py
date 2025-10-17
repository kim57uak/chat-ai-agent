"""
History Settings Tab
히스토리 설정 탭
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QCheckBox, QSpinBox, QGroupBox, QVBoxLayout
from core.file_utils import load_prompt_config, save_prompt_config
from ..base_settings_tab import BaseSettingsTab


class HistorySettingsTab(BaseSettingsTab):
    """히스토리 설정 탭"""
    
    def create_ui(self):
        """UI 생성"""
        # 대화 히스토리 설정 그룹
        history_group = QGroupBox('💬 대화 히스토리 설정')
        history_layout = QVBoxLayout(history_group)
        history_layout.setSpacing(12)
        
        self.enable_history = QCheckBox('대화 히스토리 사용')
        history_layout.addWidget(self.enable_history)
        
        self.hybrid_mode = QCheckBox('하이브리드 모드 사용')
        history_layout.addWidget(self.hybrid_mode)
        
        user_limit_layout = QHBoxLayout()
        user_limit_layout.addWidget(QLabel('사용자 메시지 제한:'))
        self.user_message_limit_spin = QSpinBox()
        self.user_message_limit_spin.setRange(1, 50)
        self.user_message_limit_spin.setValue(6)
        self.user_message_limit_spin.setSuffix(' 개')
        self.user_message_limit_spin.setMinimumHeight(40)
        user_limit_layout.addWidget(self.user_message_limit_spin)
        history_layout.addLayout(user_limit_layout)
        
        ai_limit_layout = QHBoxLayout()
        ai_limit_layout.addWidget(QLabel('AI 응답 제한:'))
        self.ai_response_limit_spin = QSpinBox()
        self.ai_response_limit_spin.setRange(1, 50)
        self.ai_response_limit_spin.setValue(4)
        self.ai_response_limit_spin.setSuffix(' 개')
        self.ai_response_limit_spin.setMinimumHeight(40)
        ai_limit_layout.addWidget(self.ai_response_limit_spin)
        history_layout.addLayout(ai_limit_layout)
        
        token_limit_layout = QHBoxLayout()
        token_limit_layout.addWidget(QLabel('AI 응답 토큰 제한:'))
        self.ai_response_token_limit_spin = QSpinBox()
        self.ai_response_token_limit_spin.setRange(1000, 50000)
        self.ai_response_token_limit_spin.setValue(4000)
        self.ai_response_token_limit_spin.setSuffix(' tokens')
        self.ai_response_token_limit_spin.setMinimumHeight(40)
        token_limit_layout.addWidget(self.ai_response_token_limit_spin)
        history_layout.addLayout(token_limit_layout)
        
        self.content_layout.addWidget(history_group)
        
        # 페이징 설정 그룹
        paging_group = QGroupBox('📄 페이징 설정')
        paging_layout = QVBoxLayout(paging_group)
        paging_layout.setSpacing(12)
        
        initial_layout = QHBoxLayout()
        initial_layout.addWidget(QLabel('첫 페이지 로딩 갯수:'))
        self.initial_load_count_spin = QSpinBox()
        self.initial_load_count_spin.setRange(10, 200)
        self.initial_load_count_spin.setValue(50)
        self.initial_load_count_spin.setSuffix(' 개')
        self.initial_load_count_spin.setMinimumHeight(40)
        initial_layout.addWidget(self.initial_load_count_spin)
        paging_layout.addLayout(initial_layout)
        
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel('페이징 갯수:'))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(5, 50)
        self.page_size_spin.setValue(10)
        self.page_size_spin.setSuffix(' 개')
        self.page_size_spin.setMinimumHeight(40)
        page_layout.addWidget(self.page_size_spin)
        paging_layout.addLayout(page_layout)
        
        self.content_layout.addWidget(paging_group)
    
    def load_settings(self):
        """설정 로드"""
        prompt_config = load_prompt_config()
        
        conversation_settings = prompt_config.get('conversation_settings', {})
        self.enable_history.setChecked(conversation_settings.get('enable_history', True))
        self.hybrid_mode.setChecked(conversation_settings.get('hybrid_mode', True))
        self.user_message_limit_spin.setValue(conversation_settings.get('user_message_limit', 6))
        self.ai_response_limit_spin.setValue(conversation_settings.get('ai_response_limit', 4))
        self.ai_response_token_limit_spin.setValue(conversation_settings.get('ai_response_token_limit', 4000))
        
        history_settings = prompt_config.get('history_settings', {})
        self.initial_load_count_spin.setValue(history_settings.get('initial_load_count', 50))
        self.page_size_spin.setValue(history_settings.get('page_size', 10))
    
    def save_settings(self):
        """설정 저장"""
        prompt_config = load_prompt_config()
        
        prompt_config['conversation_settings'] = {
            'enable_history': self.enable_history.isChecked(),
            'hybrid_mode': self.hybrid_mode.isChecked(),
            'user_message_limit': self.user_message_limit_spin.value(),
            'ai_response_limit': self.ai_response_limit_spin.value(),
            'ai_response_token_limit': self.ai_response_token_limit_spin.value(),
            'max_history_pairs': self.user_message_limit_spin.value(),
            'max_tokens_estimate': self.ai_response_token_limit_spin.value() * 2
        }
        
        prompt_config['history_settings'] = {
            'initial_load_count': self.initial_load_count_spin.value(),
            'page_size': self.page_size_spin.value()
        }
        
        save_prompt_config(prompt_config)
    
    def get_tab_title(self) -> str:
        return '💬 히스토리'
