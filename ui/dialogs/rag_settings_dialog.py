"""
RAG Settings Dialog (Redesigned)
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QListWidget, QPushButton,
                             QRadioButton, QButtonGroup, QSpinBox, QDoubleSpinBox,
                             QGroupBox, QFormLayout, QMessageBox, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from core.logging import get_logger

logger = get_logger("rag_settings_dialog")


class RAGSettingsDialog(QDialog):
    """RAG 설정 다이얼로그 (탭 기반)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ RAG 설정")
        self.setMinimumSize(700, 600)
        self.setStyleSheet(self._get_themed_dialog_style())
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 탭 위젯
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.addTab(self._create_embedding_tab(), "📊 임베딩 모델")
        self.tabs.addTab(self._create_chunking_tab(), "✂️ 청킹 전략")
        self.tabs.addTab(self._create_search_tab(), "🔍 검색 설정")
        
        # 탭바 좌측 정렬 (반드시 탭 추가 후 설정)
        tab_bar = self.tabs.tabBar()
        tab_bar.setExpanding(False)
        tab_bar.setDrawBase(False)
        # 탭 위젯을 왼쪽 정렬하기 위한 레이아웃
        tab_container = QHBoxLayout()
        tab_container.addWidget(self.tabs)
        tab_container.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(tab_container)
        
        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        reset_btn = QPushButton("⚙️ 기본값 복원")
        reset_btn.setToolTip("청킹, 검색, 배치 설정만 복원 (사용자 모델 보존)")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)
        
        cancel_btn = QPushButton("❌ 취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 저장")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _get_themed_dialog_style(self):
        """웹 스타일 적용 (테마 기반)"""
        from ui.styles.material_theme_manager import material_theme_manager
        
        colors = material_theme_manager.get_theme_colors()
        
        # 테마 색상 추출
        bg = colors.get('background', '#1e293b')
        surface = colors.get('surface', '#334155')
        primary = colors.get('primary', '#6366f1')
        primary_variant = colors.get('primary_variant', '#4f46e5')
        text_color = colors.get('text_primary', '#f1f5f9')
        text_sec_color = colors.get('text_secondary', '#cbd5e0')
        border = colors.get('border', '#475569')
        surface_variant = colors.get('surface_variant', '#475569')
        
        # primary 색상에서 RGB 추출 (그라디언트용)
        try:
            r = int(primary[1:3], 16)
            g = int(primary[3:5], 16)
            b = int(primary[5:7], 16)
            r2 = int(primary_variant[1:3], 16)
            g2 = int(primary_variant[3:5], 16)
            b2 = int(primary_variant[5:7], 16)
        except:
            r, g, b = 99, 102, 241
            r2, g2, b2 = 79, 70, 229
        
        return f"""
            QDialog {{
                background-color: {bg};
                color: {text_color};
                border: none;
            }}
            QLabel {{
                color: {text_color};
                font-size: 14px;
                font-weight: 500;
                padding: 4px 0;
                background: transparent;
            }}
            QTabWidget::pane {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {surface},
                    stop:1 rgba({r}, {g}, {b}, 0.02));
                border: 1px solid rgba({r}, {g}, {b}, 0.3);
                border-radius: 12px;
                padding: 20px;
                margin-top: -1px;
            }}
            QTabBar::tab {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {surface},
                    stop:1 {surface_variant});
                color: {text_sec_color};
                border: 1px solid {border};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 12px 24px;
                margin-right: 4px;
                font-size: 14px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 1),
                    stop:1 rgba({r2}, {g2}, {b2}, 1));
                color: white;
                border-color: rgba({r}, {g}, {b}, 0.8);
            }}
            QTabBar::tab:hover:!selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 0.2),
                    stop:1 rgba({r2}, {g2}, {b2}, 0.2));
                border-color: rgba({r}, {g}, {b}, 0.5);
            }}
            QGroupBox {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {surface},
                    stop:1 rgba({r}, {g}, {b}, 0.03));
                color: {text_color};
                border: 1px solid rgba({r}, {g}, {b}, 0.2);
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 20px;
                font-size: 16px;
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 6px 16px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 1),
                    stop:1 rgba({r2}, {g2}, {b2}, 1));
                color: white;
                border-radius: 6px;
                font-weight: 700;
                font-size: 14px;
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 1),
                    stop:1 rgba({r2}, {g2}, {b2}, 1));
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                margin: 4px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r2}, {g2}, {b2}, 1),
                    stop:1 rgba({r}, {g}, {b}, 1));
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r2}, {g2}, {b2}, 0.8),
                    stop:1 rgba({r}, {g}, {b}, 0.8));
            }}
            QRadioButton {{
                color: {text_color};
                font-size: 14px;
                font-weight: 500;
                spacing: 10px;
                padding: 10px;
                background: transparent;
            }}
            QRadioButton::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid rgba({r}, {g}, {b}, 0.4);
                background-color: {surface};
            }}
            QRadioButton::indicator:checked {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.5,
                    stop:0 rgba({r}, {g}, {b}, 1),
                    stop:0.7 rgba({r2}, {g2}, {b2}, 1));
                border-color: rgba({r}, {g}, {b}, 1);
            }}
            QRadioButton::indicator:hover {{
                border-color: rgba({r}, {g}, {b}, 0.8);
            }}
            QSpinBox, QDoubleSpinBox {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {surface},
                    stop:1 {surface_variant});
                color: {text_color};
                border: 2px solid rgba({r}, {g}, {b}, 0.2);
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                min-height: 24px;
            }}
            QSpinBox:hover, QDoubleSpinBox:hover {{
                border-color: rgba({r}, {g}, {b}, 0.5);
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: rgba({r}, {g}, {b}, 1);
                background-color: {surface};
            }}
            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 0.8),
                    stop:1 rgba({r2}, {g2}, {b2}, 0.8));
                border: none;
                width: 20px;
                border-radius: 4px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover,
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 1),
                    stop:1 rgba({r2}, {g2}, {b2}, 1));
            }}
            QListWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {surface},
                    stop:1 rgba({r}, {g}, {b}, 0.02));
                color: {text_color};
                border: 1px solid rgba({r}, {g}, {b}, 0.2);
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 14px 16px;
                border-radius: 8px;
                margin-bottom: 6px;
                color: {text_color};
            }}
            QListWidget::item:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 0.15),
                    stop:1 rgba({r2}, {g2}, {b2}, 0.15));
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 0.8),
                    stop:1 rgba({r2}, {g2}, {b2}, 0.8));
                color: white;
            }}
            QScrollBar:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {surface},
                    stop:1 rgba({r}, {g}, {b}, 0.05));
                width: 10px;
                margin: 0;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 0.6),
                    stop:1 rgba({r2}, {g2}, {b2}, 0.6));
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({r}, {g}, {b}, 1),
                    stop:1 rgba({r2}, {g2}, {b2}, 1));
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
        """
    
    def _create_embedding_tab(self):
        """임베딩 모델 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("📊 등록된 임베딩 모델")
        label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(label)
        
        # 모델 선택 그룹 (라디오 버튼 방식)
        self.model_group = QGroupBox("모델 선택")
        model_group_layout = QVBoxLayout()
        model_group_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # 상단 정렬
        
        self.model_button_group = QButtonGroup()
        self.model_radios = {}
        
        self.model_group.setLayout(model_group_layout)
        layout.addWidget(self.model_group)
        
        current_label = QLabel("현재 사용 중: -")
        current_label.setStyleSheet("color: #1976d2; font-weight: bold;")
        self.current_model_label = current_label
        layout.addWidget(current_label)
        
        # 버튼 레이아웃
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ 새 모델 추가")
        add_btn.clicked.connect(self._add_model)
        edit_btn = QPushButton("✏️ 편집")
        edit_btn.clicked.connect(self._edit_model)
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.clicked.connect(self._delete_model)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        
        # 선택 버튼 (더 눈에 띄게)
        select_btn = QPushButton("✅ 선택한 모델로 설정")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        select_btn.clicked.connect(self._apply_selected_model)
        btn_layout.addWidget(select_btn)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def _safe_edit_model(self, item):
        """안전한 모델 편집"""
        try:
            if item and hasattr(item, 'data'):
                self._edit_model()
        except Exception as e:
            logger.error(f"Safe edit model failed: {e}")
    
    def _create_chunking_tab(self):
        """청킹 전략 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Scroll area for small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # 기본 전략
        strategy_group = QGroupBox("기본 청킹 전략")
        strategy_group.setMinimumHeight(150)
        strategy_group.setToolTip(
            "청킹(Chunking): 긴 문서를 작은 조각으로 나누는 과정\n"
            "• 임베딩 모델의 토큰 제한을 맞추기 위해 필요\n"
            "• 검색 정확도 향상을 위해 의미 단위로 분할\n"
            "• 각 전략은 문서 유형에 따라 최적화됨"
        )
        strategy_layout = QVBoxLayout()
        
        self.strategy_group = QButtonGroup()
        strategies = [
            ("Sliding Window", "고정 크기 윈도우로 분할 (일반 문서)"),
            ("Semantic", "의미 단위로 분할 (논문, 보고서)"),
            ("Code", "코드 구조 기반 분할 (소스코드)"),
            ("Markdown", "마크다운 구조 기반 분할 (MD 문서)")
        ]
        for i, (strategy, tooltip) in enumerate(strategies):
            radio = QRadioButton(strategy)
            radio.setMinimumHeight(30)
            radio.setToolTip(tooltip)
            self.strategy_group.addButton(radio, i)
            strategy_layout.addWidget(radio)
        
        self.strategy_group.button(0).setChecked(True)
        strategy_group.setLayout(strategy_layout)
        scroll_layout.addWidget(strategy_group)
        
        # 설명
        info_label = QLabel("💡 RAG 관리에서 Auto 선택 시 기본 전략 사용")
        info_label.setStyleSheet("color: #666; padding: 10px; font-size: 11pt;")
        info_label.setWordWrap(True)
        scroll_layout.addWidget(info_label)
        
        # Sliding Window 설정
        sw_group = QGroupBox("📐 Sliding Window")
        sw_group.setMinimumHeight(120)
        sw_layout = QFormLayout()
        sw_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        sw_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.window_size = QSpinBox()
        self.window_size.setRange(100, 2000)
        self.window_size.setValue(500)
        self.window_size.setMinimumHeight(30)
        self.window_size.setToolTip("청크 하나의 크기 (토큰 수)\n권장: 500-1000")
        sw_layout.addRow("Window Size:", self.window_size)
        
        self.overlap_ratio = QDoubleSpinBox()
        self.overlap_ratio.setRange(0.0, 0.5)
        self.overlap_ratio.setSingleStep(0.05)
        self.overlap_ratio.setValue(0.2)
        self.overlap_ratio.setSuffix(" (20%)")
        self.overlap_ratio.setMinimumHeight(30)
        self.overlap_ratio.setToolTip("인접 청크 간 겹치는 비율\n권장: 0.1-0.3 (10-30%)")
        sw_layout.addRow("Overlap:", self.overlap_ratio)
        
        sw_group.setLayout(sw_layout)
        scroll_layout.addWidget(sw_group)
        
        # Semantic 설정
        sem_group = QGroupBox("🧠 Semantic")
        sem_group.setMinimumHeight(100)
        sem_layout = QFormLayout()
        sem_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        sem_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(50, 99)
        self.threshold_spin.setValue(95)
        self.threshold_spin.setSuffix(" %")
        self.threshold_spin.setMinimumHeight(30)
        self.threshold_spin.setToolTip(
            "의미 유사도 임계값 (백분위수)\n"
            "높을수록 더 큰 청크 생성\n"
            "권장: 90-95%"
        )
        sem_layout.addRow("Threshold:", self.threshold_spin)
        
        sem_group.setLayout(sem_layout)
        scroll_layout.addWidget(sem_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_search_tab(self):
        """검색 설정 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # Top-K
        topk_group = QGroupBox("🔍 검색 결과 개수")
        topk_group.setMinimumHeight(100)
        topk_layout = QFormLayout()
        topk_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        topk_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.top_k = QSpinBox()
        self.top_k.setRange(1, 50)
        self.top_k.setValue(10)
        self.top_k.setSuffix(" 개")
        self.top_k.setMinimumHeight(30)
        topk_layout.addRow("Top-K:", self.top_k)
        
        info = QLabel("💡 벡터 검색 시 반환할 문서 개수")
        info.setStyleSheet("color: #666; font-size: 10pt;")
        info.setWordWrap(True)
        topk_layout.addRow("", info)
        
        topk_group.setLayout(topk_layout)
        scroll_layout.addWidget(topk_group)
        
        # 배치 업로드
        batch_group = QGroupBox("📤 배치 업로드")
        batch_group.setMinimumHeight(120)
        batch_layout = QFormLayout()
        batch_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        batch_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.max_workers = QSpinBox()
        self.max_workers.setRange(1, 16)
        self.max_workers.setValue(1)
        self.max_workers.setSuffix(" 개")
        self.max_workers.setMinimumHeight(30)
        self.max_workers.setEnabled(False)
        batch_layout.addRow("동시 작업:", self.max_workers)
        
        self.max_file_size = QSpinBox()
        self.max_file_size.setRange(1, 500)
        self.max_file_size.setValue(50)
        self.max_file_size.setSuffix(" MB")
        self.max_file_size.setMinimumHeight(30)
        batch_layout.addRow("최대 크기:", self.max_file_size)
        
        batch_group.setLayout(batch_layout)
        scroll_layout.addWidget(batch_group)
        
        # 제외 패턴
        exclude_group = QGroupBox("🚫 제외 패턴")
        exclude_group.setMinimumHeight(200)
        exclude_layout = QVBoxLayout()
        
        self.exclude_list = QListWidget()
        self.exclude_list.setMinimumHeight(100)
        exclude_layout.addWidget(self.exclude_list)
        
        exclude_btn_layout = QHBoxLayout()
        add_pattern_btn = QPushButton("➕ 추가")
        add_pattern_btn.setMinimumHeight(30)
        add_pattern_btn.clicked.connect(self._add_exclude_pattern)
        remove_pattern_btn = QPushButton("➖ 제거")
        remove_pattern_btn.setMinimumHeight(30)
        remove_pattern_btn.clicked.connect(self._remove_exclude_pattern)
        exclude_btn_layout.addWidget(add_pattern_btn)
        exclude_btn_layout.addWidget(remove_pattern_btn)
        exclude_btn_layout.addStretch()
        exclude_layout.addLayout(exclude_btn_layout)
        
        info2 = QLabel("💡 업로드 시 제외할 파일/폴더 패턴")
        info2.setStyleSheet("color: #666; font-size: 10pt;")
        info2.setWordWrap(True)
        exclude_layout.addWidget(info2)
        
        exclude_group.setLayout(exclude_layout)
        scroll_layout.addWidget(exclude_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _load_settings(self):
        """설정 로드"""
        try:
            from core.rag.config.rag_config_manager import RAGConfigManager
            
            config_manager = RAGConfigManager()
            
            # 임베딩 모델 로드
            self._load_embedding_models(config_manager)
            
            # 청킹 설정 로드
            chunking_config = config_manager.get_chunking_config()
            default_strategy = chunking_config.get("default_strategy", "sliding_window")
            strategy_map = {"sliding_window": 0, "semantic": 1, "code": 2, "markdown": 3}
            self.strategy_group.button(strategy_map.get(default_strategy, 0)).setChecked(True)
            
            sw_config = chunking_config.get("strategies", {}).get("sliding_window", {})
            self.window_size.setValue(sw_config.get("window_size", 500))
            self.overlap_ratio.setValue(sw_config.get("overlap_ratio", 0.2))
            
            sem_config = chunking_config.get("strategies", {}).get("semantic", {})
            self.threshold_spin.setValue(sem_config.get("threshold_amount", 95))
            
            # 검색 설정 로드
            retrieval_config = config_manager.get_retrieval_config()
            self.top_k.setValue(retrieval_config.get("top_k", 10))
            
            # 배치 설정 로드
            batch_config = config_manager.get_batch_config()
            self.max_workers.setValue(batch_config.get("max_workers", 4))
            self.max_file_size.setValue(batch_config.get("max_file_size_mb", 50))
            
            # 제외 패턴 로드
            exclude_patterns = batch_config.get("exclude_patterns", [])
            for pattern in exclude_patterns:
                self.exclude_list.addItem(pattern)
            
            logger.info("Settings loaded")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    def _load_embedding_models(self, config_manager):
        """임베딩 모델 목록 로드"""
        try:
            # 기존 라디오 버튼 제거
            for radio in self.model_radios.values():
                self.model_button_group.removeButton(radio)
                radio.deleteLater()
            self.model_radios.clear()
            
            # 기존 레이아웃 정리
            layout = self.model_group.layout()
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()
            
            models = config_manager.get_embedding_models()
            current = config_manager.get_current_embedding_model()
            
            # 새 라디오 버튼 생성
            for i, (name, config) in enumerate(models.items()):
                try:
                    radio_text = f"{name} ({config.get('dimension', 768)}차원)"
                    radio = QRadioButton(radio_text)
                    
                    # 현재 모델이면 선택
                    if name == current:
                        radio.setChecked(True)
                    
                    self.model_radios[name] = radio
                    self.model_button_group.addButton(radio, i)
                    layout.addWidget(radio)
                    
                except Exception as e:
                    logger.warning(f"Failed to add model radio {name}: {e}")
                    continue
            
            layout.addStretch()
            self.current_model_label.setText(f"현재 사용 중: {current}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding models: {e}")
            self.current_model_label.setText("현재 사용 중: 알 수 없음")
        

    

    
    def _set_current_model(self, item):
        """선택한 모델을 현재 모델로 설정"""
        if not item:
            return
            
        try:
            from core.rag.config.rag_config_manager import RAGConfigManager
            
            # 안전한 데이터 추출
            name = None
            try:
                name = item.data(Qt.ItemDataRole.UserRole)
            except (RuntimeError, AttributeError):
                # 아이템이 삭제되었거나 손상된 경우
                logger.warning("Item data access failed, refreshing list")
                config_manager = RAGConfigManager()
                self._load_embedding_models(config_manager)
                return
            
            if not name:
                QMessageBox.warning(self, "경고", "올바르지 않은 모델 선택입니다.")
                return
            
            config_manager = RAGConfigManager()
            config_manager.set_current_embedding_model(name)
            
            # UI 업데이트
            self._load_embedding_models(config_manager)
            QMessageBox.information(self, "성공", f"현재 모델이 '{name}'으로 변경되었습니다.")
            
        except Exception as e:
            logger.error(f"Failed to set current model: {e}")
            QMessageBox.critical(self, "오류", f"모델 변경 실패:\n{e}")
    
    def _add_model(self):
        """모델 추가"""
        from .embedding_model_dialog import EmbeddingModelDialog
        from core.rag.config.rag_config_manager import RAGConfigManager
        
        dialog = EmbeddingModelDialog(self)
        if dialog.exec():
            name, config = dialog.get_model_config()
            config_manager = RAGConfigManager()
            config_manager.add_embedding_model(name, config)
            self._load_embedding_models(config_manager)
            QMessageBox.information(self, "성공", f"모델 '{name}'이(가) 추가되었습니다.")
    
    def _edit_model(self):
        """모델 편집"""
        try:
            # 선택된 라디오 버튼에서 모델명 추출
            selected_name = None
            for name, radio in self.model_radios.items():
                if radio.isChecked():
                    selected_name = name
                    break
            
            if not selected_name:
                QMessageBox.warning(self, "경고", "편집할 모델을 선택하세요.")
                return
            
            from .embedding_model_dialog import EmbeddingModelDialog
            from core.rag.config.rag_config_manager import RAGConfigManager
            
            config_manager = RAGConfigManager()
            models = config_manager.get_embedding_models()
            
            if selected_name not in models:
                QMessageBox.warning(self, "경고", "모델 정보를 찾을 수 없습니다.")
                return
            
            model_data = {"name": selected_name, **models[selected_name]}
            dialog = EmbeddingModelDialog(self, edit_model=model_data)
            if dialog.exec():
                _, config = dialog.get_model_config()
                config_manager.update_embedding_model(selected_name, config)
                self._load_embedding_models(config_manager)
                QMessageBox.information(self, "성공", f"모델 '{selected_name}'이(가) 수정되었습니다.")
                
        except Exception as e:
            logger.error(f"Failed to edit model: {e}")
            QMessageBox.critical(self, "오류", f"모델 편집 실패:\n{e}")
    
    def _delete_model(self):
        """모델 삭제"""
        try:
            # 선택된 라디오 버튼에서 모델명 추출
            selected_name = None
            for name, radio in self.model_radios.items():
                if radio.isChecked():
                    selected_name = name
                    break
            
            if not selected_name:
                QMessageBox.warning(self, "경고", "삭제할 모델을 선택하세요.")
                return
            
            from core.rag.config.rag_config_manager import RAGConfigManager
            config_manager = RAGConfigManager()
            current = config_manager.get_current_embedding_model()
            
            if selected_name == current:
                QMessageBox.warning(self, "경고", "현재 사용 중인 모델은 삭제할 수 없습니다.")
                return
            
            reply = QMessageBox.question(self, "확인", f"모델 '{selected_name}'을(를) 삭제하시겠습니까?")
            if reply == QMessageBox.StandardButton.Yes:
                config_manager.delete_embedding_model(selected_name)
                self._load_embedding_models(config_manager)
                QMessageBox.information(self, "성공", f"모델 '{selected_name}'이(가) 삭제되었습니다.")
                
        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
            QMessageBox.critical(self, "오류", f"모델 삭제 실패:\n{e}")
    
    def _apply_selected_model(self):
        """선택한 모델을 현재 모델로 설정"""
        try:
            logger.info("Starting model selection process")
            
            # 선택된 라디오 버튼 찾기
            selected_radio = None
            selected_name = None
            
            logger.info(f"Available model radios: {list(self.model_radios.keys())}")
            
            for name, radio in self.model_radios.items():
                logger.debug(f"Checking radio {name}: checked={radio.isChecked()}")
                if radio.isChecked():
                    selected_radio = radio
                    selected_name = name
                    break
            
            logger.info(f"Selected model: {selected_name}")
            
            if not selected_name:
                logger.warning("No model selected")
                QMessageBox.warning(self, "경고", "설정할 모델을 선택하세요.")
                return
            
            from core.rag.config.rag_config_manager import RAGConfigManager
            config_manager = RAGConfigManager()
            
            # 현재 모델과 동일한지 확인
            current_model = config_manager.get_current_embedding_model()
            logger.info(f"Current model: {current_model}, Selected: {selected_name}")
            
            if current_model == selected_name:
                logger.info("Same model selected, showing info message")
                QMessageBox.information(self, "알림", f"이미 '{selected_name}' 모델이 사용 중입니다.")
                return
            
            # 모델 변경
            logger.info(f"Changing model from {current_model} to {selected_name}")
            config_manager.set_current_embedding_model(selected_name)
            
            # UI 업데이트
            logger.info("Updating UI")
            self._load_embedding_models(config_manager)
            
            # 성공 메시지
            logger.info("Showing success message")
            QMessageBox.information(self, "성공", f"현재 모델이 '{selected_name}'으로 변경되었습니다.")
            
        except Exception as e:
            logger.error(f"Failed to apply selected model: {e}", exc_info=True)
            QMessageBox.critical(self, "오류", f"모델 설정 실패:\n{str(e)}")
    
    def _add_exclude_pattern(self):
        """제외 패턴 추가"""
        from PyQt6.QtWidgets import QInputDialog
        pattern, ok = QInputDialog.getText(self, "패턴 추가", "제외할 패턴:")
        if ok and pattern:
            self.exclude_list.addItem(pattern)
    
    def _remove_exclude_pattern(self):
        """제외 패턴 제거"""
        current_item = self.exclude_list.currentItem()
        if current_item:
            self.exclude_list.takeItem(self.exclude_list.row(current_item))
    
    def _reset_defaults(self):
        """기본값 복원 (사용자 모델 보존)"""
        reply = QMessageBox.question(
            self, "확인",
            "청킹, 검색, 배치 설정을 기본값으로 복원하시겠습니까?\n\n" +
            "※ 사용자 임베딩 모델은 보존되고 내장 모델로 전환됩니다."
        )
        if reply == QMessageBox.StandardButton.Yes:
            from core.rag.config.rag_config_manager import RAGConfigManager
            config_manager = RAGConfigManager()
            
            # 사용자 모델 백업
            user_models = config_manager.get_embedding_models().copy()
            
            # 기본 설정으로 복원
            config_manager.config = config_manager.DEFAULT_CONFIG.copy()
            
            # 사용자 모델 복원 (내장 모델 제외)
            if user_models:
                # 내장 모델 유지
                config_manager.config["embedding"]["models"].update(user_models)
            
            # 내장 모델로 전환
            config_manager.config["embedding"]["current"] = "dragonkue-KoEn-E5-Tiny"
            
            config_manager._save_config(config_manager.config)
            self._load_settings()
            
            preserved_count = len(user_models)
            QMessageBox.information(
                self, "완료", 
                f"기본값으로 복원되었습니다.\n" +
                f"내장 모델로 전환되었습니다.\n" +
                f"사용자 모델 {preserved_count}개 보존되었습니다."
            )
    
    def get_settings(self):
        """현재 설정 반환"""
        try:
            strategy_map = {0: "sliding_window", 1: "semantic", 2: "code", 3: "markdown"}
            default_strategy = strategy_map[self.strategy_group.checkedId()]
            
            exclude_patterns = []
            for i in range(self.exclude_list.count()):
                exclude_patterns.append(self.exclude_list.item(i).text())
            
            return {
                "chunking": {
                    "default_strategy": default_strategy,
                    "strategies": {
                        "sliding_window": {
                            "window_size": self.window_size.value(),
                            "overlap_ratio": self.overlap_ratio.value()
                        },
                        "semantic": {
                            "threshold_type": "percentile",
                            "threshold_amount": self.threshold_spin.value()
                        }
                    }
                },
                "retrieval": {
                    "top_k": self.top_k.value()
                },
                "batch_upload": {
                    "max_workers": self.max_workers.value(),
                    "max_file_size_mb": self.max_file_size.value(),
                    "exclude_patterns": exclude_patterns
                }
            }
        except Exception as e:
            logger.error(f"Failed to get settings: {e}")
            return {}
    
    def _save_settings(self):
        """설정 저장"""
        try:
            from core.rag.config.rag_config_manager import RAGConfigManager
            
            config_manager = RAGConfigManager()
            settings = self.get_settings()
            
            # 설정 업데이트
            config_manager.config.update(settings)
            config_manager._save_config(config_manager.config)
            
            logger.info("Settings saved")
            QMessageBox.information(self, "성공", "설정이 저장되었습니다.")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "오류", f"설정 저장 실패:\n{e}")
