from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox, QMessageBox
from PyQt6.QtCore import Qt

class UserPromptDialog(QDialog):
    def __init__(self, ai_client, parent=None):
        super().__init__(parent)
        self.ai_client = ai_client
        self.setWindowTitle('유저 프롬프트 설정')
        self.setModal(True)
        self.resize(600, 400)
        
        self.setup_ui()
        self.load_current_prompt()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 모델 선택
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel('모델 선택:'))
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(['GPT', 'Gemini', '공통'])
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        layout.addLayout(model_layout)
        
        # 프롬프트 입력
        layout.addWidget(QLabel('유저 프롬프트:'))
        
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText('사용자 메시지에 추가될 프롬프트를 입력하세요...')
        layout.addWidget(self.prompt_text)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton('저장')
        self.save_button.clicked.connect(self.save_prompt)
        
        self.cancel_button = QPushButton('취소')
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton('기본값 복원')
        self.reset_button.clicked.connect(self.reset_to_default)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def load_current_prompt(self):
        """현재 프롬프트 로드"""
        current_prompt = self.ai_client.get_current_user_prompt()
        self.prompt_text.setPlainText(current_prompt)
    
    def on_model_changed(self):
        """모델 변경 시 해당 프롬프트 로드"""
        model_type = self.model_combo.currentText().lower()
        if model_type == 'gpt':
            prompt = self.ai_client.user_prompt.get('gpt', '')
        elif model_type == 'gemini':
            prompt = self.ai_client.user_prompt.get('gemini', '')
        else:  # 공통
            # GPT 프롬프트를 기본으로 표시
            prompt = self.ai_client.user_prompt.get('gpt', '')
        
        self.prompt_text.setPlainText(prompt)
    
    def save_prompt(self):
        """프롬프트 저장"""
        prompt_text = self.prompt_text.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, '경고', '유저 프롬프트를 입력해주세요.')
            return
        
        model_type = self.model_combo.currentText().lower()
        if model_type == '공통':
            model_type = 'both'
        
        try:
            self.ai_client.update_user_prompt(prompt_text, model_type)
            # 저장 후 즉시 새로고침
            self.ai_client.user_prompt = self.ai_client._load_user_prompt()
            QMessageBox.information(self, '성공', '유저 프롬프트가 저장되었습니다.')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, '오류', f'저장 중 오류가 발생했습니다: {str(e)}')
            print(f'유저 프롬프트 저장 오류: {str(e)}')
    
    def reset_to_default(self):
        """기본값으로 복원"""
        reply = QMessageBox.question(
            self, '확인', 
            '기본 유저 프롬프트로 복원하시겠습니까?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            default_prompt = '다음 규칙을 따라 답변해주세요: 1. 구조화된 답변 2. 가독성 우선 3. 명확한 분류 4. 핵심 요약 5. 한국어 사용'
            self.prompt_text.setPlainText(default_prompt)