from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox, QMessageBox
from PyQt6.QtCore import Qt
from ui.prompts import prompt_manager, ModelType
from ui.styles.flat_theme import FlatTheme

class UserPromptDialog(QDialog):
    def __init__(self, ai_client, parent=None):
        super().__init__(parent)
        self.ai_client = ai_client
        self.setWindowTitle('유저 프롬프트 설정')
        self.setModal(True)
        self.resize(700, 500)
        self.setStyleSheet(self._get_dialog_style())
        
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
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(120, 120, 120, 0.8), 
                    stop:1 rgba(100, 100, 100, 0.8));
                color: #ffffff;
                border: 2px solid rgba(120, 120, 120, 0.4);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(140, 140, 140, 0.9), 
                    stop:1 rgba(120, 120, 120, 0.9));
                border-color: rgba(120, 120, 120, 0.6);
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton('기본값 복원')
        self.reset_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(255, 200, 100, 0.8), 
                    stop:1 rgba(255, 150, 200, 0.8));
                color: #ffffff;
                border: 2px solid rgba(255, 200, 100, 0.4);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(255, 220, 120, 0.9), 
                    stop:1 rgba(255, 170, 220, 0.9));
                border-color: rgba(255, 200, 100, 0.6);
            }
        """)
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
            # 중앙관리 시스템에서 기본 프롬프트 가져오기
            model_type = self.model_combo.currentText().lower()
            if model_type == 'gpt':
                default_prompt = prompt_manager.get_system_prompt(ModelType.OPENAI.value)
            elif model_type == 'gemini':
                default_prompt = prompt_manager.get_system_prompt(ModelType.GOOGLE.value)
            else:
                default_prompt = prompt_manager.get_system_prompt(ModelType.COMMON.value)
            self.prompt_text.setPlainText(default_prompt)
    
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
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(45, 45, 55, 0.95), 
                    stop:1 rgba(35, 35, 45, 0.95));
                border: 2px solid rgba(100, 200, 255, 0.3);
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: #ffffff;
                font-weight: 400;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border-color: rgba(100, 200, 255, 0.6);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(100, 200, 255, 0.8), 
                    stop:1 rgba(150, 100, 255, 0.8));
                color: #ffffff;
                border: 2px solid rgba(100, 200, 255, 0.4);
                border-radius: 10px;
                font-weight: 700;
                font-size: 14px;
                padding: 10px 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(120, 220, 255, 0.9), 
                    stop:1 rgba(170, 120, 255, 0.9));
                border-color: rgba(100, 200, 255, 0.6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(80, 180, 235, 0.7), 
                    stop:1 rgba(130, 80, 235, 0.7));
            }
        """