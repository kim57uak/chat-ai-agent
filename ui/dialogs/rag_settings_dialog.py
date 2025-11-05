"""
RAG Settings Dialog
RAG 설정 대화상자
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, 
    QSpinBox, QPushButton, QGroupBox, QLabel
)
from core.logging import get_logger

logger = get_logger("rag_settings_dialog")


class RAGSettingsDialog(QDialog):
    """RAG 설정 대화상자"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("RAG Settings")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Vector DB 설정
        db_group = QGroupBox("Vector Database")
        db_layout = QFormLayout()
        
        self.db_combo = QComboBox()
        self.db_combo.addItems(["LanceDB", "Chroma", "FAISS"])
        db_layout.addRow("Database:", self.db_combo)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # 임베딩 설정
        embed_group = QGroupBox("Embedding Model")
        embed_layout = QFormLayout()
        
        self.embed_combo = QComboBox()
        self.embed_combo.addItems([
            "dragonkue-KoEn-E5-Tiny",
            "OpenAI text-embedding-3-small",
            "OpenAI text-embedding-3-large"
        ])
        embed_layout.addRow("Model:", self.embed_combo)
        
        embed_group.setLayout(embed_layout)
        layout.addWidget(embed_group)
        
        # 청크 설정
        chunk_group = QGroupBox("Chunking")
        chunk_layout = QFormLayout()
        
        self.chunk_size = QSpinBox()
        self.chunk_size.setRange(100, 2000)
        self.chunk_size.setValue(500)
        self.chunk_size.setToolTip(
            "청크 크기: 문서를 몇 글자 단위로 나눌지 결정합니다.\n"
            "• 값이 클수록: 더 많은 맥락 유지 (검색 정확도 저하 가능)\n"
            "• 값이 작을수록: 정확한 검색 (맥락 손실 가능)\n"
            "• 권장값: 500-1000"
        )
        chunk_layout.addRow("Chunk Size:", self.chunk_size)
        
        self.chunk_overlap = QSpinBox()
        self.chunk_overlap.setRange(0, 500)
        self.chunk_overlap.setValue(50)
        self.chunk_overlap.setToolTip(
            "청크 오버랩: 인접한 청크 간 겹치는 글자 수입니다.\n"
            "• 값이 클수록: 문맥 연속성 향상 (저장 공간 증가)\n"
            "• 값이 작을수록: 저장 공간 절약 (문맥 단절 가능)\n"
            "• 권장값: Chunk Size의 10-20% (예: 50-100)"
        )
        chunk_layout.addRow("Overlap:", self.chunk_overlap)
        
        chunk_group.setLayout(chunk_layout)
        layout.addWidget(chunk_group)
        
        # 검색 설정
        search_group = QGroupBox("Search")
        search_layout = QFormLayout()
        
        self.top_k = QSpinBox()
        self.top_k.setRange(1, 20)
        self.top_k.setValue(5)
        self.top_k.setToolTip(
            "검색 결과 개수: 질문과 가장 유사한 문서 청크를 몇 개 가져올지 결정합니다.\n"
            "• 값이 클수록: 더 많은 정보 제공 (느려질 수 있음)\n"
            "• 값이 작을수록: 핵심 정보만 제공 (빠름)\n"
            "• 권장값: 3-10"
        )
        search_layout.addRow("Top K:", self.top_k)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # 버튼
        btn_layout = QVBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_settings(self):
        """설정 로드"""
        try:
            from utils.config_path import config_path_manager
            import json
            
            config_path = config_path_manager.get_config_path('rag_config.json')
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                self.chunk_size.setValue(settings.get('chunk_size', 500))
                self.chunk_overlap.setValue(settings.get('chunk_overlap', 50))
                self.top_k.setValue(settings.get('top_k', 5))
                
                logger.info(f"Loaded RAG settings from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    def _save_settings(self):
        """설정 저장"""
        try:
            from utils.config_path import config_path_manager
            import json
            
            settings = self.get_settings()
            config_path = config_path_manager.get_config_path('rag_config.json')
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved RAG settings to {config_path}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def get_settings(self) -> dict:
        """현재 설정 반환"""
        return {
            "vector_db": self.db_combo.currentText(),
            "embedding_model": self.embed_combo.currentText(),
            "chunk_size": self.chunk_size.value(),
            "chunk_overlap": self.chunk_overlap.value(),
            "top_k": self.top_k.value()
        }
