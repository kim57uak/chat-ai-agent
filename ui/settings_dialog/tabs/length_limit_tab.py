"""
Length Limit Tab
AI 파라미터 및 응답 길이 제한 탭
"""

from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QSpinBox, QLineEdit, 
                            QGroupBox, QVBoxLayout, QPushButton, QCheckBox)
from core.file_utils import load_prompt_config, save_prompt_config
from ..base_settings_tab import BaseSettingsTab


class LengthLimitTab(BaseSettingsTab):
    """AI 파라미터 및 응답 길이 제한 탭"""
    
    def create_ui(self):
        """UI 생성"""
        # AI 파라미터 설정 그룹
        param_group = QGroupBox('🎛️ AI 모델 파라미터 설정')
        param_layout = QVBoxLayout(param_group)
        param_layout.setSpacing(12)
        
        # 권장 프리셋 버튼
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel('⚡ 빠른 설정:'))
        
        accurate_btn = QPushButton('📝 정확한 작업')
        accurate_btn.setToolTip('코딩, 분석, 번역에 최적화\nTemp: 0.1, Top P: 0.9, Penalties: 0.0')
        accurate_btn.clicked.connect(lambda: self._apply_preset('accurate'))
        preset_layout.addWidget(accurate_btn)
        
        creative_btn = QPushButton('🎨 창의적 작업')
        creative_btn.setToolTip('글쓰기, 스토리텔링에 최적화\nTemp: 0.9, Top P: 0.95, Freq: 0.3, Pres: 0.6')
        creative_btn.clicked.connect(lambda: self._apply_preset('creative'))
        preset_layout.addWidget(creative_btn)
        
        balanced_btn = QPushButton('💬 일반 대화')
        balanced_btn.setToolTip('균형잡힌 일반 대화\nTemp: 0.7, Top P: 0.9, Penalties: 0.2')
        balanced_btn.clicked.connect(lambda: self._apply_preset('balanced'))
        preset_layout.addWidget(balanced_btn)
        
        preset_layout.addStretch()
        param_layout.addLayout(preset_layout)
        
        # temperature
        temp_layout = QHBoxLayout()
        temp_label = QLabel('Temperature:')
        temp_label.setMinimumWidth(150)
        temp_label.setToolTip('응답의 무작위성/창의성 조절\n• 0.0: 항상 가장 확률 높은 답변\n• 0.1-0.3: 정확한 답변\n• 0.7: 균형잡힌 답변\n• 0.9-1.5: 창의적 답변')
        temp_layout.addWidget(temp_label)
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(0, 200)
        self.temperature_spin.setValue(10)
        self.temperature_spin.setMinimumHeight(40)
        self.temperature_spin.valueChanged.connect(lambda v: self.temperature_spin.setSuffix(f'  →  {v/100:.2f}'))
        self.temperature_spin.setSuffix('  →  0.10')
        temp_layout.addWidget(self.temperature_spin)
        param_layout.addLayout(temp_layout)
        
        # max_tokens
        token_layout = QHBoxLayout()
        token_label = QLabel('Max Tokens:')
        token_label.setMinimumWidth(150)
        token_label.setToolTip('생성할 최대 토큰 수\n• 100-1000: 짧은 답변\n• 1000-4000: 중간 답변\n• 4000-8000: 긴 답변')
        token_layout.addWidget(token_label)
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 1000000)
        self.max_tokens_spin.setValue(4096)
        self.max_tokens_spin.setSuffix(' tokens')
        self.max_tokens_spin.setMinimumHeight(40)
        token_layout.addWidget(self.max_tokens_spin)
        param_layout.addLayout(token_layout)
        
        # top_p
        top_p_layout = QHBoxLayout()
        top_p_label = QLabel('Top P:')
        top_p_label.setMinimumWidth(150)
        top_p_label.setToolTip('Nucleus Sampling\n• 0.1: 상위 10% 확률 토큰만\n• 0.9: 상위 90% 확률 토큰 (권장)')
        top_p_layout.addWidget(top_p_label)
        self.top_p_spin = QSpinBox()
        self.top_p_spin.setRange(0, 100)
        self.top_p_spin.setValue(90)
        self.top_p_spin.setMinimumHeight(40)
        self.top_p_spin.valueChanged.connect(lambda v: self.top_p_spin.setSuffix(f'  →  {v/100:.2f}'))
        self.top_p_spin.setSuffix('  →  0.90')
        top_p_layout.addWidget(self.top_p_spin)
        param_layout.addLayout(top_p_layout)
        
        # top_k
        top_k_layout = QHBoxLayout()
        top_k_label = QLabel('Top K:')
        top_k_label.setMinimumWidth(150)
        top_k_label.setToolTip('Top-K Sampling\n• 40: 상위 40개 단어 중 선택 (권장)\n⚠️ Gemini, OpenRouter만 지원')
        top_k_layout.addWidget(top_k_label)
        self.top_k_spin = QSpinBox()
        self.top_k_spin.setRange(1, 100)
        self.top_k_spin.setValue(40)
        self.top_k_spin.setMinimumHeight(40)
        top_k_layout.addWidget(self.top_k_spin)
        param_layout.addLayout(top_k_layout)
        
        # frequency_penalty
        freq_layout = QHBoxLayout()
        freq_label = QLabel('Frequency Penalty:')
        freq_label.setMinimumWidth(150)
        freq_label.setToolTip('이미 나온 단어의 반복 억제\n⚠️ OpenAI, OpenRouter만 지원')
        freq_layout.addWidget(freq_label)
        self.frequency_penalty_spin = QSpinBox()
        self.frequency_penalty_spin.setRange(-200, 200)
        self.frequency_penalty_spin.setValue(0)
        self.frequency_penalty_spin.setMinimumHeight(40)
        self.frequency_penalty_spin.valueChanged.connect(lambda v: self.frequency_penalty_spin.setSuffix(f'  →  {v/100:.2f}'))
        self.frequency_penalty_spin.setSuffix('  →  0.00')
        freq_layout.addWidget(self.frequency_penalty_spin)
        param_layout.addLayout(freq_layout)
        
        # presence_penalty
        pres_layout = QHBoxLayout()
        pres_label = QLabel('Presence Penalty:')
        pres_label.setMinimumWidth(150)
        pres_label.setToolTip('새로운 주제/단어 도입 장려\n⚠️ OpenAI, OpenRouter만 지원')
        pres_layout.addWidget(pres_label)
        self.presence_penalty_spin = QSpinBox()
        self.presence_penalty_spin.setRange(-200, 200)
        self.presence_penalty_spin.setValue(0)
        self.presence_penalty_spin.setMinimumHeight(40)
        self.presence_penalty_spin.valueChanged.connect(lambda v: self.presence_penalty_spin.setSuffix(f'  →  {v/100:.2f}'))
        self.presence_penalty_spin.setSuffix('  →  0.00')
        pres_layout.addWidget(self.presence_penalty_spin)
        param_layout.addLayout(pres_layout)
        
        # stop_sequences
        stop_layout = QVBoxLayout()
        stop_label = QLabel('Stop Sequences (쉼표로 구분):')
        stop_label.setToolTip('특정 문자열을 만나면 생성 중단\n⚠️ OpenAI, Gemini만 지원')
        stop_layout.addWidget(stop_label)
        self.stop_sequences_edit = QLineEdit()
        self.stop_sequences_edit.setPlaceholderText('예: END, ###, STOP')
        self.stop_sequences_edit.setMinimumHeight(40)
        stop_layout.addWidget(self.stop_sequences_edit)
        param_layout.addLayout(stop_layout)
        
        self.content_layout.addWidget(param_group)
        
        # 응답 길이 제한 그룹
        response_group = QGroupBox('📏 응답 길이 제한 설정')
        response_layout = QVBoxLayout(response_group)
        response_layout.setSpacing(12)
        
        self.enable_length_limit = QCheckBox('응답 길이 제한 사용')
        response_layout.addWidget(self.enable_length_limit)
        
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel('최대 응답 길이:'))
        self.max_response_length_spin = QSpinBox()
        self.max_response_length_spin.setRange(1000, 100000)
        self.max_response_length_spin.setValue(50000)
        self.max_response_length_spin.setSuffix(' 문자')
        self.max_response_length_spin.setMinimumHeight(40)
        length_layout.addWidget(self.max_response_length_spin)
        response_layout.addLayout(length_layout)
        
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
        self.content_layout.addWidget(response_group)
    
    def _apply_preset(self, preset_type: str):
        """프리셋 적용"""
        if preset_type == 'accurate':
            self.temperature_spin.setValue(10)
            self.top_p_spin.setValue(90)
            self.frequency_penalty_spin.setValue(0)
            self.presence_penalty_spin.setValue(0)
        elif preset_type == 'creative':
            self.temperature_spin.setValue(90)
            self.top_p_spin.setValue(95)
            self.frequency_penalty_spin.setValue(30)
            self.presence_penalty_spin.setValue(60)
        elif preset_type == 'balanced':
            self.temperature_spin.setValue(70)
            self.top_p_spin.setValue(90)
            self.frequency_penalty_spin.setValue(20)
            self.presence_penalty_spin.setValue(20)
    
    def load_settings(self):
        """설정 로드"""
        prompt_config = load_prompt_config()
        
        ai_params = prompt_config.get('ai_parameters', {})
        self.temperature_spin.setValue(int(ai_params.get('temperature', 0.1) * 100))
        self.max_tokens_spin.setValue(ai_params.get('max_tokens', 4096))
        self.top_p_spin.setValue(int(ai_params.get('top_p', 0.9) * 100))
        self.top_k_spin.setValue(ai_params.get('top_k', 40))
        self.frequency_penalty_spin.setValue(int(ai_params.get('frequency_penalty', 0.0) * 100))
        self.presence_penalty_spin.setValue(int(ai_params.get('presence_penalty', 0.0) * 100))
        stop_sequences = ai_params.get('stop_sequences', [])
        self.stop_sequences_edit.setText(', '.join(stop_sequences) if stop_sequences else '')
        
        response_settings = prompt_config.get('response_settings', {})
        self.enable_length_limit.setChecked(response_settings.get('enable_length_limit', False))
        self.max_response_length_spin.setValue(response_settings.get('max_response_length', 50000))
        self.enable_streaming.setChecked(response_settings.get('enable_streaming', True))
        self.streaming_chunk_size_spin.setValue(response_settings.get('streaming_chunk_size', 300))
    
    def save_settings(self):
        """설정 저장"""
        prompt_config = load_prompt_config()
        
        stop_text = self.stop_sequences_edit.text().strip()
        stop_sequences = [s.strip() for s in stop_text.split(',') if s.strip()] if stop_text else []
        
        prompt_config['ai_parameters'] = {
            'temperature': self.temperature_spin.value() / 100.0,
            'max_tokens': self.max_tokens_spin.value(),
            'top_p': self.top_p_spin.value() / 100.0,
            'top_k': self.top_k_spin.value(),
            'frequency_penalty': self.frequency_penalty_spin.value() / 100.0,
            'presence_penalty': self.presence_penalty_spin.value() / 100.0,
            'stop_sequences': stop_sequences
        }
        
        prompt_config['response_settings'] = {
            'enable_length_limit': self.enable_length_limit.isChecked(),
            'max_response_length': self.max_response_length_spin.value(),
            'enable_streaming': self.enable_streaming.isChecked(),
            'streaming_chunk_size': self.streaming_chunk_size_spin.value()
        }
        
        save_prompt_config(prompt_config)
    
    def get_tab_title(self) -> str:
        return '🎛️ AI 파라미터'
