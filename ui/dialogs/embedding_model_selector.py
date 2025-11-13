"""
Embedding Model Selector Dialog
임베딩 모델 선택 다이얼로그
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QRadioButton, QButtonGroup, QTextEdit,
                            QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from core.logging import get_logger

logger = get_logger("embedding_model_selector")


class EmbeddingModelSelector(QDialog):
    """임베딩 모델 선택 다이얼로그"""
    
    model_changed = pyqtSignal(str)  # 모델 변경 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("임베딩 모델 선택")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self.manager = None
        self.current_model = None
        self.selected_model = None
        
        self._init_manager()
        self._setup_ui()
        self._load_current_model()
    
    def _init_manager(self):
        """모델 매니저 초기화"""
        try:
            from core.rag.embeddings.embedding_model_manager import EmbeddingModelManager
            self.manager = EmbeddingModelManager()
        except Exception as e:
            logger.error(f"모델 매니저 초기화 실패: {e}")
    
    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("임베딩 모델 선택")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 설명
        desc = QLabel("임베딩 모델을 변경하면 기존 벡터 데이터와 분리됩니다.")
        desc.setStyleSheet("color: #666; margin: 5px 10px;")
        layout.addWidget(desc)
        
        # 모델 선택 그룹
        model_group = QGroupBox("사용 가능한 모델")
        model_layout = QVBoxLayout(model_group)
        
        self.button_group = QButtonGroup()
        self.model_buttons = {}
        
        if self.manager:
            models = self.manager.get_available_models()
            for model_id, model_info in models.items():
                radio = QRadioButton()
                radio.setObjectName(model_id)
                
                # 모델 정보 표시
                info_text = f"{model_info['name']} ({model_info['dimension']}차원)\n{model_info['description']}"
                radio.setText(info_text)
                radio.setStyleSheet("QRadioButton { margin: 5px; }")
                
                self.button_group.addButton(radio)
                self.model_buttons[model_id] = radio
                model_layout.addWidget(radio)
        
        layout.addWidget(model_group)
        
        # 데이터 현황
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(QLabel("모델별 데이터 현황:"))
        layout.addWidget(self.status_text)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self._refresh_status)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("적용")
        apply_btn.clicked.connect(self._apply_changes)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
        self._refresh_status()
    
    def _load_current_model(self):
        """현재 모델 로드"""
        if not self.manager:
            return
        
        self.current_model = self.manager.get_current_model()
        
        # 현재 모델 선택
        if self.current_model in self.model_buttons:
            self.model_buttons[self.current_model].setChecked(True)
            self.selected_model = self.current_model
    
    def _refresh_status(self):
        """데이터 현황 새로고침"""
        if not self.manager:
            self.status_text.setText("모델 매니저를 사용할 수 없습니다.")
            return
        
        try:
            data_status = self.manager.list_model_data()
            status_lines = []
            
            for model_id, info in data_status.items():
                model_name = self.manager.SUPPORTED_MODELS[model_id]["name"]
                doc_count = info.get("document_count", 0)
                is_current = info.get("is_current", False)
                
                status = "현재" if is_current else "대기"
                status_lines.append(f"• {model_name}: {doc_count}개 문서 ({status})")
            
            self.status_text.setText("\\n".join(status_lines))
            
        except Exception as e:
            logger.error(f"상태 새로고침 실패: {e}")
            self.status_text.setText(f"상태 확인 실패: {str(e)}")
    
    def _apply_changes(self):
        """변경사항 적용"""
        # 선택된 모델 확인
        selected_button = self.button_group.checkedButton()
        if not selected_button:
            QMessageBox.warning(self, "경고", "모델을 선택해주세요.")
            return
        
        new_model = selected_button.objectName()
        
        if new_model == self.current_model:
            self.reject()
            return
        
        # 변경 확인
        reply = QMessageBox.question(
            self, 
            "모델 변경 확인",
            f"임베딩 모델을 '{self.manager.SUPPORTED_MODELS[new_model]['name']}'로 변경하시겠습니까?\\n\\n"
            "기존 벡터 데이터는 별도 보관되며, 새 문서를 업로드해야 합니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 모델 변경
        try:
            success, message = self.manager.change_model(new_model)
            
            if success:
                QMessageBox.information(self, "성공", message)
                self.model_changed.emit(new_model)
                self.accept()
            else:
                QMessageBox.critical(self, "오류", message)
                
        except Exception as e:
            logger.error(f"모델 변경 실패: {e}")
            QMessageBox.critical(self, "오류", f"모델 변경 중 오류가 발생했습니다: {str(e)}")