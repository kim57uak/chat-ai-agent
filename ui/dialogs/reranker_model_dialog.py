"""
Reranker Model Dialog
Reranker 모델 추가/편집 다이얼로그
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QHBoxLayout, QMessageBox, QComboBox,
                             QLabel, QGroupBox)
from PyQt6.QtCore import Qt
from core.logging import get_logger

logger = get_logger("reranker_model_dialog")


class RerankerModelDialog(QDialog):
    """Reranker 모델 추가/편집 다이얼로그"""
    
    def __init__(self, parent=None, edit_model=None):
        super().__init__(parent)
        self.edit_model = edit_model
        self.setWindowTitle("🎯 Reranker 모델 추가" if not edit_model else "🎯 Reranker 모델 편집")
        self.setMinimumWidth(500)
        self._init_ui()
        
        if edit_model:
            self._load_model_data(edit_model)
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 프리셋 선택
        preset_group = QGroupBox("📋 프리셋 선택 (선택사항)")
        preset_layout = QVBoxLayout()
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("-- 직접 입력 --", None)
        
        from core.rag.reranker_constants import RerankerConstants
        models = RerankerConstants.get_available_models()
        for model in models:
            self.preset_combo.addItem(
                f"{model['name']} - {model['size']}",
                model
            )
        
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        
        info_label = QLabel("💡 프리셋을 선택하면 자동으로 입력됩니다")
        info_label.setStyleSheet("color: #666; font-size: 10pt;")
        preset_layout.addWidget(info_label)
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        # 모델 정보 입력
        form_group = QGroupBox("📝 모델 정보")
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("예: ms-marco-MiniLM-L-12-v2")
        form_layout.addRow("모델명:", self.name_edit)
        
        self.model_id_edit = QLineEdit()
        self.model_id_edit.setPlaceholderText("예: cross-encoder/ms-marco-MiniLM-L-12-v2")
        form_layout.addRow("HuggingFace ID:", self.model_id_edit)
        
        self.size_edit = QLineEdit()
        self.size_edit.setPlaceholderText("예: 128MB")
        form_layout.addRow("크기:", self.size_edit)
        
        self.language_edit = QLineEdit()
        self.language_edit.setPlaceholderText("예: 한영 혼합")
        form_layout.addRow("언어:", self.language_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("❌ 취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 저장")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_preset_changed(self, index):
        """프리셋 선택 시 자동 입력"""
        preset = self.preset_combo.currentData()
        if preset:
            self.name_edit.setText(preset['local_name'])
            self.model_id_edit.setText(preset['model_id'])
            self.size_edit.setText(preset['size'])
            self.language_edit.setText(preset['language'])
    
    def _load_model_data(self, model_data):
        """모델 데이터 로드 (편집 모드)"""
        self.name_edit.setText(model_data.get('name', ''))
        self.name_edit.setEnabled(False)  # 편집 시 이름 변경 불가
        self.model_id_edit.setText(model_data.get('model_id', ''))
        self.size_edit.setText(model_data.get('size', ''))
        self.language_edit.setText(model_data.get('language', ''))
    
    def _save(self):
        """저장"""
        name = self.name_edit.text().strip()
        model_id = self.model_id_edit.text().strip()
        size = self.size_edit.text().strip()
        language = self.language_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "경고", "모델명을 입력하세요.")
            return
        
        if not model_id:
            QMessageBox.warning(self, "경고", "HuggingFace ID를 입력하세요.")
            return
        
        self.accept()
    
    def get_model_config(self):
        """모델 설정 반환"""
        name = self.name_edit.text().strip()
        config = {
            "model_id": self.model_id_edit.text().strip(),
            "size": self.size_edit.text().strip() or "N/A",
            "language": self.language_edit.text().strip() or "다국어"
        }
        return name, config
