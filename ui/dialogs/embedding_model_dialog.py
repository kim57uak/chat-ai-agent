"""
Embedding Model Dialog
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QCheckBox,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from core.logging import get_logger

logger = get_logger("embedding_model_dialog")


class EmbeddingModelDialog(QDialog):
    """임베딩 모델 추가/편집 다이얼로그"""
    
    def __init__(self, parent=None, edit_model=None):
        super().__init__(parent)
        self.edit_model = edit_model
        self.setWindowTitle("➕ 임베딩 모델 추가" if not edit_model else "✏️ 임베딩 모델 편집")
        self.setMinimumWidth(500)
        self.setStyleSheet(self._get_themed_dialog_style())
        self._init_ui()
        
        if edit_model:
            self._load_model_data(edit_model)
    
    def _get_themed_dialog_style(self):
        """글래스모피즘 스타일 적용 (테마 기반)"""
        from ui.styles.material_theme_manager import material_theme_manager
        
        colors = material_theme_manager.get_theme_colors()
        glass_config = material_theme_manager.get_glassmorphism_config()
        
        bg = colors.get('background', '#fefefe')
        surface = colors.get('surface', 'rgba(250, 251, 253, 0.95)')
        primary = colors.get('primary', '#8b8fc4')
        text = colors.get('text_primary', '#1a1a1a')
        text_sec = colors.get('text_secondary', '#4a4a4a')
        border_op = glass_config.get('border_opacity', 0.2)
        
        # 테마 타입 판별
        theme_type = material_theme_manager.get_current_theme_type()
        is_dark = theme_type == 'dark'
        
        # 배경색 계산
        if is_dark:
            dialog_bg = f"rgba(30, 30, 30, 0.95)"
            input_bg = f"rgba(50, 50, 50, 0.8)"
            input_border = f"rgba(100, 100, 100, 0.5)"
            text_color = "#ffffff"
            text_sec_color = "#cccccc"
        else:
            dialog_bg = f"rgba(255, 255, 255, 0.95)"
            input_bg = f"rgba(245, 245, 245, 0.9)"
            input_border = f"rgba(200, 200, 200, 0.6)"
            text_color = "#1a1a1a"
            text_sec_color = "#4a4a4a"
        
        return f"""
            QDialog {{
                background: {dialog_bg};
                border: 1px solid {input_border};
                border-radius: 16px;
            }}
            QLabel {{
                color: {text_color};
                font-size: 13px;
                font-weight: 500;
                padding: 4px 0;
                background: transparent;
            }}
            QLineEdit {{
                background: {input_bg};
                border: 1px solid {input_border};
                border-radius: 8px;
                color: {text_color};
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 2px solid {primary};
            }}
            QComboBox {{
                background: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QComboBox:hover {{
                border: 2px solid {primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: {dialog_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-radius: 8px;
                selection-background-color: {primary};
                selection-color: white;
            }}
            QCheckBox {{
                color: {text_color};
                font-size: 13px;
                spacing: 8px;
                padding: 6px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {input_border};
                background: {input_bg};
            }}
            QCheckBox::indicator:checked {{
                background: {primary};
                border: 2px solid {primary};
            }}
            QPushButton {{
                background: {primary};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {primary};
                opacity: 0.9;
            }}
        """
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 모델 이름
        name_label = QLabel("모델 이름:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("예: my-custom-model")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        
        # 모델 타입
        type_label = QLabel("모델 타입:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Local (HuggingFace)", "OpenAI", "Google"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        layout.addWidget(type_label)
        layout.addWidget(self.type_combo)
        
        # 모델 경로 (Local용)
        path_label = QLabel("모델 경로:")
        self.path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("/Users/user/models/my-model")
        self.browse_btn = QPushButton("📁")
        self.browse_btn.setMaximumWidth(50)
        self.browse_btn.clicked.connect(self._browse_path)
        self.path_layout.addWidget(self.path_input)
        self.path_layout.addWidget(self.browse_btn)
        self.path_label = path_label
        layout.addWidget(path_label)
        layout.addLayout(self.path_layout)
        
        # API 키 (OpenAI/Google용)
        api_label = QLabel("API 키:")
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("sk-...")
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_label = api_label
        layout.addWidget(api_label)
        layout.addWidget(self.api_input)
        
        # 모델명 (OpenAI/Google용)
        model_label = QLabel("모델명:")
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("text-embedding-3-small")
        self.model_label = model_label
        layout.addWidget(model_label)
        layout.addWidget(self.model_input)
        
        # 임베딩 차원
        dim_label = QLabel("임베딩 차원:")
        self.dim_input = QLineEdit()
        self.dim_input.setPlaceholderText("768")
        layout.addWidget(dim_label)
        layout.addWidget(self.dim_input)
        
        # 캐시 사용
        self.cache_check = QCheckBox("캐시 사용")
        self.cache_check.setChecked(True)
        layout.addWidget(self.cache_check)
        
        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        self._on_type_changed(self.type_combo.currentText())
    
    def _on_type_changed(self, type_text):
        """타입 변경 시 필드 표시/숨김"""
        is_local = type_text == "Local (HuggingFace)"
        
        self.path_label.setVisible(is_local)
        self.path_input.setVisible(is_local)
        self.browse_btn.setVisible(is_local)
        
        self.api_label.setVisible(not is_local)
        self.api_input.setVisible(not is_local)
        self.model_label.setVisible(not is_local)
        self.model_input.setVisible(not is_local)
    
    def _browse_path(self):
        """경로 선택"""
        path = QFileDialog.getExistingDirectory(self, "모델 폴더 선택")
        if path:
            self.path_input.setText(path)
    
    def _load_model_data(self, model_data):
        """모델 데이터 로드"""
        self.name_input.setText(model_data.get("name", ""))
        self.name_input.setReadOnly(True)  # 이름 변경 불가
        
        model_type = model_data.get("type", "local")
        if model_type == "local":
            self.type_combo.setCurrentText("Local (HuggingFace)")
            self.path_input.setText(model_data.get("model_path", ""))
        elif model_type == "openai":
            self.type_combo.setCurrentText("OpenAI")
            self.api_input.setText(model_data.get("api_key", ""))
            self.model_input.setText(model_data.get("model", ""))
        elif model_type == "google":
            self.type_combo.setCurrentText("Google")
            self.api_input.setText(model_data.get("api_key", ""))
            self.model_input.setText(model_data.get("model", ""))
        
        self.dim_input.setText(str(model_data.get("dimension", 768)))
        self.cache_check.setChecked(model_data.get("enable_cache", True))
    
    def _on_save(self):
        """저장"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "경고", "모델 이름을 입력하세요.")
            return
        
        type_text = self.type_combo.currentText()
        
        if type_text == "Local (HuggingFace)":
            path = self.path_input.text().strip()
            if not path:
                QMessageBox.warning(self, "경고", "모델 경로를 입력하세요.")
                return
        else:
            api_key = self.api_input.text().strip()
            model = self.model_input.text().strip()
            if not api_key or not model:
                QMessageBox.warning(self, "경고", "API 키와 모델명을 입력하세요.")
                return
        
        try:
            dimension = int(self.dim_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "경고", "차원은 숫자여야 합니다.")
            return
        
        self.accept()
    
    def get_model_config(self):
        """모델 설정 반환"""
        name = self.name_input.text().strip()
        type_text = self.type_combo.currentText()
        dimension = int(self.dim_input.text().strip())
        enable_cache = self.cache_check.isChecked()
        
        if type_text == "Local (HuggingFace)":
            return name, {
                "type": "local",
                "model_path": self.path_input.text().strip(),
                "dimension": dimension,
                "enable_cache": enable_cache
            }
        elif type_text == "OpenAI":
            return name, {
                "type": "openai",
                "model": self.model_input.text().strip(),
                "api_key": self.api_input.text().strip(),
                "dimension": dimension
            }
        else:  # Google
            return name, {
                "type": "google",
                "model": self.model_input.text().strip(),
                "api_key": self.api_input.text().strip(),
                "dimension": dimension
            }
