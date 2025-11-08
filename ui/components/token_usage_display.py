"""
Token usage display component for showing detailed token consumption
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QGroupBox, QScrollArea,
                            QFrame, QProgressBar, QTableWidget, QTableWidgetItem,
                            QHeaderView, QTabWidget, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject
from PyQt6.QtGui import QFont, QPalette
from core.token_tracker import token_tracker, StepType
from core.token_accumulator import token_accumulator
from core.token_tracking import get_unified_tracker
from core.token_tracking.data_adapter import DataAdapter
from typing import Dict, Optional
import json
from datetime import datetime
from core.logging import get_logger

logger = get_logger("token_usage_display")


class AsyncDataProcessor(QObject):
    """비동기 데이터 처리 워커"""
    
    data_ready = pyqtSignal(dict)  # 처리된 데이터 시그널
    
    def __init__(self):
        super().__init__()

        # 성능 최적화 - 디바운서
        from ui.event_debouncer import get_event_debouncer
        self._debouncer = get_event_debouncer()
        super().__init__()
        self._should_stop = False
    
    def process_data(self):
        """백그라운드에서 데이터 처리"""
        if self._should_stop:
            return
        
        try:
            # 무거운 통계 계산을 백그라운드에서 수행
            stats = token_tracker.get_conversation_stats()
            
            # 전체 히스토리 통계 계산
            history = token_tracker.conversation_history
            current_conv = token_tracker.current_conversation
            
            all_conversations = list(history)
            if current_conv and current_conv not in history:
                all_conversations.append(current_conv)
            
            # 모델별 통계 계산
            model_stats = {}
            for conv in all_conversations:
                model = conv.model_name
                if model not in model_stats:
                    model_stats[model] = {'count': 0, 'tokens': 0}
                model_stats[model]['count'] += 1
                model_stats[model]['tokens'] += conv.total_tokens
            
            processed_data = {
                'current_stats': stats,
                'total_conversations': len(all_conversations),
                'total_tokens': sum(conv.total_tokens for conv in all_conversations),
                'model_stats': model_stats
            }
            
            if not self._should_stop:
                self.data_ready.emit(processed_data)
                
        except Exception as e:
            logger.error(f"비동기 데이터 처리 오류: {e}")
    
    def stop(self):
        """처리 중단"""
        self._should_stop = True


class TokenUsageDisplay(QWidget):
    """토큰 사용량 표시 위젯"""
    
    export_requested = pyqtSignal(str)  # 내보내기 요청 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.unified_tracker = None
        try:
            from core.security.secure_path_manager import secure_path_manager
            db_path = secure_path_manager.get_database_path()
            self.unified_tracker = get_unified_tracker(db_path)
            logger.info(f"Unified tracker connected: {db_path}")
        except Exception as e:
            logger.warning(f"Unified tracker not available: {e}")
        
        self.setup_ui()
        self.setup_timer()
        self.setup_async_processing()
        self.connect_token_accumulator()
        self.apply_theme()
    
    def connect_token_accumulator(self):
        """토큰 누적기와 연결"""
        token_accumulator.token_updated.connect(self.on_token_updated)
    
    def setup_ui(self):
        """UI 설정 - 패딩/마진 최소화, 가독성 최우선"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 8, 4)  # 우측 여백 8px로 조정
        layout.setSpacing(4)  # 최소 간격
        
        # 제목 - 더 큰 폰트와 명확한 아이콘
        title = QLabel("📊 Token Tracker")
        title.setFont(QFont("SF Pro Display", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                padding: 8px;
                margin: 2px;
                font-weight: 700;
            }
        """)
        layout.addWidget(title)
        
        # 기간 필터
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(4)
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Current", "7 Days", "30 Days", "All Time"])
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        self.period_combo.setMinimumHeight(32)
        filter_layout.addWidget(self.period_combo)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # 탭 위젯 - 패딩 최소화
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget {
                margin: 0px;
                padding: 0px;
            }
            QTabWidget::pane {
                margin: 2px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.tab_widget)
        
        # 현재 대화 탭
        self.current_tab = self.create_current_conversation_tab()
        self.tab_widget.addTab(self.current_tab, "Current")
        
        # 단계별 상세 탭
        self.steps_tab = self.create_steps_detail_tab()
        self.tab_widget.addTab(self.steps_tab, "Steps")
        
        # 통계 탭
        self.stats_tab = self.create_statistics_tab()
        self.tab_widget.addTab(self.stats_tab, "Stats")
        
        # 컨트롤 버튼
        self.create_control_buttons(layout)
    
    def create_current_conversation_tab(self):
        """현재 대화 탭 생성 - 패딩 최소화, 가독성 최우선"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 현재 대화 정보 - 더 큰 박스
        self.current_info_group = QGroupBox("💬 Current")
        current_layout = QVBoxLayout(self.current_info_group)
        current_layout.setContentsMargins(8, 12, 8, 8)
        current_layout.setSpacing(6)
        
        # 기본 정보 - 더 큰 폰트
        self.conversation_id_label = QLabel("ID: -")
        self.model_name_label = QLabel("Model: -")
        self.steps_count_label = QLabel("Steps: 0")
        self.duration_label = QLabel("Time: 0ms")
        
        for label in [self.conversation_id_label, self.model_name_label, 
                     self.steps_count_label, self.duration_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 600;
                    padding: 4px 8px;
                    margin: 2px;
                }
            """)
        
        current_layout.addWidget(self.conversation_id_label)
        current_layout.addWidget(self.model_name_label)
        current_layout.addWidget(self.steps_count_label)
        current_layout.addWidget(self.duration_label)
        
        # 토큰 사용량 요약 - 더 큰 박스
        self.token_summary_group = QGroupBox("🔢 Tokens")
        token_layout = QVBoxLayout(self.token_summary_group)
        token_layout.setContentsMargins(8, 12, 8, 8)
        token_layout.setSpacing(6)
        
        self.actual_tokens_label = QLabel("Session: 0 tokens")
        self.estimated_tokens_label = QLabel("Current: 0 tokens")
        self.accuracy_label = QLabel("Accuracy: N/A")
        
        for label in [self.actual_tokens_label, self.estimated_tokens_label, self.accuracy_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 600;
                    padding: 4px 8px;
                    margin: 2px;
                }
            """)
        
        token_layout.addWidget(self.actual_tokens_label)
        token_layout.addWidget(self.estimated_tokens_label)
        token_layout.addWidget(self.accuracy_label)
        
        # 진행률 표시 - 더 큰 박스
        self.progress_group = QGroupBox("⚡ Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        progress_layout.setContentsMargins(8, 12, 8, 8)
        progress_layout.setSpacing(6)
        
        self.current_step_label = QLabel("Step: -")
        self.current_step_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                padding: 4px 8px;
                margin: 2px;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(24)
        
        progress_layout.addWidget(self.current_step_label)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.current_info_group)
        layout.addWidget(self.token_summary_group)
        layout.addWidget(self.progress_group)
        layout.addStretch()
        
        return widget
    
    def create_steps_detail_tab(self):
        """단계별 상세 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 단계별 테이블
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(8)
        self.steps_table.setHorizontalHeaderLabels([
            "Step", "Type", "Duration (ms)", "Input Tokens", 
            "Output Tokens", "Total Tokens", "Tool", "Accuracy"
        ])
        
        # 테이블 설정
        header = self.steps_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.steps_table.setAlternatingRowColors(True)
        self.steps_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.steps_table)
        
        return widget
    
    def create_statistics_tab(self):
        """통계 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 전체 통계
        self.overall_stats_group = QGroupBox("📊 Overall")
        stats_layout = QVBoxLayout(self.overall_stats_group)
        
        self.total_conversations_label = QLabel("Total Conversations: 0")
        self.total_tokens_label = QLabel("Total Tokens: 0")
        self.total_cost_label = QLabel("Total Cost: $0.00")
        self.avg_tokens_label = QLabel("Avg Tokens/Conv: 0")
        
        for label in [self.total_conversations_label, self.total_tokens_label,
                     self.total_cost_label, self.avg_tokens_label]:
            label.setStyleSheet("font-size: 14px; font-weight: 600; padding: 4px 8px;")
        
        stats_layout.addWidget(self.total_conversations_label)
        stats_layout.addWidget(self.total_tokens_label)
        stats_layout.addWidget(self.total_cost_label)
        stats_layout.addWidget(self.avg_tokens_label)
        
        # Mode breakdown (NEW)
        self.mode_stats_group = QGroupBox("💬 Mode Breakdown")
        mode_layout = QVBoxLayout(self.mode_stats_group)
        self.mode_stats_text = QTextEdit()
        self.mode_stats_text.setMaximumHeight(100)
        self.mode_stats_text.setReadOnly(True)
        mode_layout.addWidget(self.mode_stats_text)
        
        # 모델별 통계
        self.model_stats_group = QGroupBox("🤖 Model Statistics")
        model_layout = QVBoxLayout(self.model_stats_group)
        self.model_stats_text = QTextEdit()
        self.model_stats_text.setMaximumHeight(120)
        self.model_stats_text.setReadOnly(True)
        model_layout.addWidget(self.model_stats_text)
        
        # Agent breakdown (NEW)
        self.agent_stats_group = QGroupBox("🔧 Agent Breakdown")
        agent_layout = QVBoxLayout(self.agent_stats_group)
        self.agent_stats_text = QTextEdit()
        self.agent_stats_text.setMaximumHeight(100)
        self.agent_stats_text.setReadOnly(True)
        agent_layout.addWidget(self.agent_stats_text)
        
        # Cost Analysis (NEW)
        self.cost_analysis_group = QGroupBox("💰 Cost Analysis")
        cost_layout = QVBoxLayout(self.cost_analysis_group)
        self.most_expensive_label = QLabel("Most Expensive: -")
        self.most_used_label = QLabel("Most Used: -")
        self.avg_cost_label = QLabel("Avg Cost/1K tokens: $0.000000")
        
        for label in [self.most_expensive_label, self.most_used_label, self.avg_cost_label]:
            label.setStyleSheet("font-size: 14px; font-weight: 600; padding: 4px 8px;")
        
        cost_layout.addWidget(self.most_expensive_label)
        cost_layout.addWidget(self.most_used_label)
        cost_layout.addWidget(self.avg_cost_label)
        
        scroll_layout.addWidget(self.overall_stats_group)
        scroll_layout.addWidget(self.mode_stats_group)
        scroll_layout.addWidget(self.model_stats_group)
        scroll_layout.addWidget(self.agent_stats_group)
        scroll_layout.addWidget(self.cost_analysis_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def create_control_buttons(self, layout):
        """컨트롤 버튼 생성 - 더 큰 버튼, 명확한 아이콘"""
        button_layout = QHBoxLayout()  # 가로 배치
        button_layout.setContentsMargins(4, 4, 4, 4)
        button_layout.setSpacing(4)
        
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.refresh_display)
        self.refresh_button.setMinimumHeight(36)
        
        self.export_button = QPushButton("📤 Export")
        self.export_button.clicked.connect(self.export_data)
        self.export_button.setMinimumHeight(36)
        
        self.clear_button = QPushButton("🗑️ Clear")
        self.clear_button.clicked.connect(self.clear_history)
        self.clear_button.setMinimumHeight(36)
        
        for button in [self.refresh_button, self.export_button, self.clear_button]:
            button.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    font-weight: 700;
                    padding: 8px 12px;
                    margin: 2px;
                }
            """)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
    
    def apply_theme(self):
        """세션 패널과 동일한 현대적인 Material Design 테마 적용"""
        try:
            from ui.styles.theme_manager import theme_manager
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                is_dark = theme_manager.is_material_dark_theme()
                
                # 세션 패널과 동일한 색상 설정
                bg_color = colors.get('background', '#121212')
                text_color = colors.get('text_primary', '#ffffff' if is_dark else '#000000')
                surface_color = colors.get('surface', '#1e1e1e')
                primary_color = colors.get('primary', '#bb86fc')
                secondary_color = colors.get('secondary', '#03dac6')
                on_primary_color = colors.get('on_primary', '#000000' if is_dark else '#ffffff')
                divider_color = colors.get('divider', '#333333' if is_dark else '#e0e0e0')
                primary_variant_color = colors.get('primary_variant', '#3700b3')
                
                # 세션 패널과 동일한 스타일 적용
                self.setStyleSheet(f"""
                    TokenUsageDisplay {{
                        background-color: {bg_color};
                        color: {text_color};
                        border: none;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    }}
                    
                    QLabel {{
                        color: {text_color};
                        font-size: 14px;
                        font-weight: 600;
                        padding: 4px 8px;
                        background: transparent;
                        border: none;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    }}
                    
                    QGroupBox {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {surface_color}, 
                            stop:1 {bg_color});
                        border: 2px solid {divider_color};
                        border-radius: 16px;
                        padding: 12px;
                        margin: 6px;
                        font-weight: 700;
                        font-size: 14px;
                        color: {text_color};
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    }}
                    
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        left: 12px;
                        padding: 8px 16px;
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {primary_color}, 
                            stop:1 {primary_variant_color});
                        color: {on_primary_color};
                        border-radius: 12px;
                        font-weight: 800;
                        font-size: 13px;
                        border: 2px solid {primary_variant_color};
                    }}
                    
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {primary_color}, 
                            stop:1 {primary_variant_color});
                        color: {on_primary_color};
                        border: none;
                        border-radius: 20px;
                        font-weight: 800;
                        font-size: 16px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        padding: 16px 20px;
                        margin: 6px;
                        transition: all 0.3s ease;
                    }}
                    
                    QPushButton:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {primary_variant_color}, 
                            stop:1 {primary_color});
                        transform: translateY(-2px);
                    }}
                    
                    QPushButton:pressed {{
                        background: {primary_variant_color};
                        transform: translateY(0px);
                    }}
                    
                    QTabWidget {{
                        background: transparent;
                        border: none;
                    }}
                    
                    QTabWidget::pane {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {surface_color}, 
                            stop:1 {bg_color});
                        border: 2px solid {divider_color};
                        border-radius: 16px;
                        margin: 4px;
                        padding: 8px;
                    }}
                    
                    QTabBar::tab {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {bg_color}, 
                            stop:1 {surface_color});
                        color: {text_color};
                        border: 2px solid {divider_color};
                        padding: 10px 20px;
                        margin: 3px;
                        border-radius: 12px;
                        font-weight: 700;
                        font-size: 13px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    }}
                    
                    QTabBar::tab:selected {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {primary_color}, 
                            stop:1 {primary_variant_color});
                        color: {on_primary_color};
                        border: 3px solid {primary_variant_color};
                        font-weight: 800;
                        transform: translateY(-1px);
                    }}
                    
                    QTabBar::tab:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {primary_variant_color}, 
                            stop:1 {primary_color});
                        color: {on_primary_color};
                        border: 2px solid {primary_color};
                    }}
                    
                    TokenUsageDisplay QTableWidget {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {surface_color}, 
                            stop:1 {bg_color}) !important;
                        color: {text_color} !important;
                        border: 2px solid {divider_color} !important;
                        border-radius: 16px !important;
                        gridline-color: {divider_color} !important;
                        font-size: 13px !important;
                        font-weight: 600 !important;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif !important;
                        padding: 8px !important;
                        margin: 6px !important;
                    }}
                    
                    TokenUsageDisplay QTableWidget::item {{
                        padding: 8px 12px !important;
                        border: none !important;
                        background: transparent !important;
                        border-radius: 8px !important;
                        margin: 2px !important;
                    }}
                    
                    TokenUsageDisplay QTableWidget::item:selected {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {primary_color}, 
                            stop:1 {primary_variant_color}) !important;
                        color: {on_primary_color} !important;
                        border-radius: 8px !important;
                    }}
                    
                    TokenUsageDisplay QTableWidget::item:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {primary_color}20, 
                            stop:1 {primary_variant_color}20) !important;
                        border-radius: 8px !important;
                    }}
                    
                    TokenUsageDisplay QHeaderView::section {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {primary_color}, 
                            stop:1 {primary_variant_color}) !important;
                        color: {on_primary_color} !important;
                        border: 2px solid {primary_variant_color} !important;
                        padding: 12px 16px !important;
                        font-weight: 800 !important;
                        font-size: 12px !important;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif !important;
                        border-radius: 12px !important;
                        margin: 2px !important;
                    }}
                    
                    TokenUsageDisplay QHeaderView::section:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {primary_variant_color}, 
                            stop:1 {primary_color}) !important;
                        transform: translateY(-1px) !important;
                    }}
                    
                    QTextEdit {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {bg_color}, 
                            stop:1 {surface_color});
                        color: {text_color};
                        border: 2px solid {divider_color};
                        border-radius: 16px;
                        padding: 12px;
                        font-size: 13px;
                        font-weight: 600;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        selection-background-color: {primary_color};
                    }}
                    
                    QScrollBar:vertical {{
                        background: {colors.get('scrollbar_track', surface_color)};
                        width: 8px;
                        border-radius: 4px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 {colors.get('scrollbar', colors.get('text_secondary', '#b3b3b3'))}, 
                            stop:1 {primary_color});
                        border-radius: 4px;
                        min-height: 20px;
                    }}
                    QScrollBar::handle:vertical:hover {{
                        background: {primary_color};
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        border: none;
                        background: none;
                    }}
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                        background: none;
                    }}
                    
                    QTextEdit QScrollBar:vertical {{
                        background: {colors.get('scrollbar_track', surface_color)};
                        width: 8px;
                        border-radius: 4px;
                    }}
                    QTextEdit QScrollBar::handle:vertical {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 {colors.get('scrollbar', colors.get('text_secondary', '#b3b3b3'))}, 
                            stop:1 {primary_color});
                        border-radius: 4px;
                        min-height: 20px;
                    }}
                    QTextEdit QScrollBar::handle:vertical:hover {{
                        background: {primary_color};
                    }}
                    QTextEdit QScrollBar::add-line:vertical, QTextEdit QScrollBar::sub-line:vertical {{
                        border: none;
                        background: none;
                    }}
                    QTextEdit QScrollBar::add-page:vertical, QTextEdit QScrollBar::sub-page:vertical {{
                        background: none;
                    }}
                    
                    QProgressBar {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {surface_color}, 
                            stop:1 {bg_color});
                        border: 2px solid {divider_color};
                        border-radius: 12px;
                        text-align: center;
                        font-weight: 700;
                        font-size: 12px;
                        color: {text_color};
                        padding: 2px;
                    }}
                    
                    QProgressBar::chunk {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {primary_color}, 
                            stop:1 {primary_variant_color});
                        border-radius: 10px;
                        margin: 1px;
                    }}
                """)
        except Exception as e:
            logger.error(f"토큰 패널 테마 적용 오류: {e}")
    
    def update_theme(self):
        """테마 업데이트"""
        self.apply_theme()
    
    def setup_timer(self):
        """자동 새로고침 타이머 설정 - 성능 최적화"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_display)
        self.refresh_timer.start(500)  # 0.5초마다 새로고침
        
        # 데이터 변경 감지용 캐시
        self._last_stats_hash = None
        self._last_steps_count = 0
    
    def setup_async_processing(self):
        """비동기 처리 설정"""
        self.worker_thread = QThread()
        self.data_processor = AsyncDataProcessor()
        self.data_processor.moveToThread(self.worker_thread)
        
        # 시그널 연결
        self.data_processor.data_ready.connect(self.on_async_data_ready)
        
        # 스레드 시작
        self.worker_thread.start()
        
        # 비동기 처리 타이머 (무거운 작업용)
        self.async_timer = QTimer()
        self.async_timer.timeout.connect(self.data_processor.process_data)
        self.async_timer.start(1000)  # 1초마다 비동기 처리
    
    def refresh_display(self):
        """화면 새로고침 - 변경된 데이터만 업데이트"""
        try:
            # 현재 통계 해시 계산
            stats = token_tracker.get_conversation_stats()
            current_hash = hash(str(stats)) if stats else 0
            current_steps = len(stats.get('steps', [])) if stats else 0
            
            # 데이터가 변경된 경우만 업데이트
            if (current_hash != self._last_stats_hash or 
                current_steps != self._last_steps_count):
                
                self.update_current_conversation()
                
                # 단계 테이블은 새로운 단계가 추가된 경우만 업데이트
                if current_steps != self._last_steps_count:
                    self.update_steps_table()
                
                # 통계 업데이트
                self.update_statistics()
                
                self._last_stats_hash = current_hash
                self._last_steps_count = current_steps
                
        except Exception as e:
            logger.error(f"토큰 사용량 화면 새로고침 오류: {e}")
    
    def update_current_conversation(self):
        """현재 대화 정보 업데이트"""
        stats = token_tracker.get_conversation_stats()
        
        # 전체 히스토리 토큰 계산 (누락된 대화 포함)
        total_history_tokens = 0
        if hasattr(token_tracker, 'conversation_history') and token_tracker.conversation_history:
            total_history_tokens = sum(conv.total_tokens for conv in token_tracker.conversation_history)
        
        if not stats:
            self.conversation_id_label.setText("Conversation ID: -")
            self.model_name_label.setText("Model: -")
            self.steps_count_label.setText("Steps: 0")
            self.duration_label.setText("Duration: 0ms")
            # 전체 세션 토큰 계산
            session_input_total, session_output_total, session_total = token_tracker.get_session_total_tokens()
            
            if session_total > 0:
                self.actual_tokens_label.setText(f"Session Total: {session_total:,} tokens (IN:{session_input_total:,} OUT:{session_output_total:,})")
            else:
                self.actual_tokens_label.setText("Session Total: 0 tokens")
            self.estimated_tokens_label.setText("Current: No active conversation")
            self.accuracy_label.setText("Accuracy: -")
            self.current_step_label.setText("Current Step: -")
            self.progress_bar.setVisible(False)
            return
        
        # 기본 정보
        self.conversation_id_label.setText(f"Conversation ID: {stats['conversation_id']}")
        self.model_name_label.setText(f"Model: {stats['model_name']}")
        self.steps_count_label.setText(f"Steps: {stats['steps_count']}")
        self.duration_label.setText(f"Duration: {stats['duration_ms']:.1f}ms")
        
        # 토큰 정보 - 실제 토큰과 추정 토큰 분리 표시
        current_actual_total = stats.get('total_actual_tokens', 0)
        estimated_total = stats.get('total_estimated_tokens', 0)
        
        # 세션 전체 토큰 (추정 토큰 사용)
        session_input_total, session_output_total, session_total = token_tracker.get_session_total_tokens()
        
        # 토큰 누적기에서 세션 총합 가져오기
        session_total = token_accumulator.get_session_total()
        accumulator_input = session_total.prompt_tokens
        accumulator_output = session_total.completion_tokens
        accumulator_total = session_total.total_tokens
        
        # 현재 대화의 실제 토큰 정보 추출
        current_actual_input = 0
        current_actual_output = 0
        
        for step in stats.get('steps', []):
            if 'additional_info' in step and step['additional_info']:
                info = step['additional_info']
                current_actual_input += info.get('input_tokens', 0)
                current_actual_output += info.get('output_tokens', 0)
        
        # 세션 전체 토큰 표시 (추정 토큰 기반)
        self.actual_tokens_label.setText(f"📊 Session Total: {session_total:,} tokens (IN:{session_input_total:,} OUT:{session_output_total:,})")
        
        # 현재 대화 토큰 표시 - 누적기 정보 우선 사용
        if accumulator_total > 0:
            self.estimated_tokens_label.setText(f"🔥 Session Actual: {accumulator_total:,} tokens (IN:{accumulator_input:,} OUT:{accumulator_output:,})")
        elif current_actual_input > 0 or current_actual_output > 0:
            self.estimated_tokens_label.setText(f"Current Actual: {current_actual_input + current_actual_output:,} tokens (IN:{current_actual_input:,} OUT:{current_actual_output:,})")
        else:
            self.estimated_tokens_label.setText(f"Current Estimated: {estimated_total:,} tokens")
        
        # 정확도 계산 (실제 토큰이 있을 때만)
        if current_actual_input > 0 or current_actual_output > 0:
            actual_total = current_actual_input + current_actual_output
            if actual_total > 0 and estimated_total > 0:
                accuracy = min(100.0, (1 - abs(actual_total - estimated_total) / actual_total) * 100)
                self.accuracy_label.setText(f"Current Accuracy: {accuracy:.1f}%")
            else:
                self.accuracy_label.setText("Current Accuracy: N/A")
        else:
            self.accuracy_label.setText("Current Accuracy: N/A (No actual tokens)")
        
        # 현재 단계 (마지막 단계)
        if stats.get('steps'):
            last_step = stats['steps'][-1]
            self.current_step_label.setText(f"Last Step: {last_step['step_name']}")
        else:
            self.current_step_label.setText("Current Step: -")
    
    def update_steps_table(self):
        """단계별 테이블 업데이트 - 가상화 적용"""
        stats = token_tracker.get_conversation_stats()
        
        if not stats or not stats.get('steps'):
            self.steps_table.setRowCount(0)
            return
        
        steps = stats['steps']
        
        # 최대 50개 단계만 표시 (성능 최적화)
        max_display_steps = 50
        display_steps = steps[-max_display_steps:] if len(steps) > max_display_steps else steps
        
        self.steps_table.setRowCount(len(display_steps))
        
        # 테이블 업데이트 일시 중단 (성능 향상)
        self.steps_table.setUpdatesEnabled(False)
        
        for i, step in enumerate(display_steps):
            # 단계 번호
            self.steps_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            
            # 단계 타입
            self.steps_table.setItem(i, 1, QTableWidgetItem(step.get('step_type', '-')))
            
            # 소요 시간
            duration = step.get('duration_ms', 0)
            self.steps_table.setItem(i, 2, QTableWidgetItem(f"{duration:.1f}"))
            
            # 토큰 정보 - 실제 토큰과 추정 토큰 분리
            actual_tokens = step.get('actual_tokens', 0)
            estimated_tokens = step.get('estimated_tokens', 0)
            
            # additional_info에서 실제 토큰 정보 추출
            actual_input_tokens = 0
            actual_output_tokens = 0
            estimated_input_tokens = 0
            estimated_output_tokens = 0
            
            if 'additional_info' in step and step['additional_info']:
                info = step['additional_info']
                actual_input_tokens = info.get('input_tokens', 0)
                actual_output_tokens = info.get('output_tokens', 0)
                estimated_input_tokens = info.get('estimated_input_tokens', 0)
                estimated_output_tokens = info.get('estimated_output_tokens', 0)
            
            # 표시할 토큰 수 결정 (실제 토큰이 있으면 실제, 없으면 추정)
            display_input = actual_input_tokens if actual_input_tokens > 0 else estimated_input_tokens
            display_output = actual_output_tokens if actual_output_tokens > 0 else estimated_output_tokens
            display_total = display_input + display_output
            
            # 테이블 업데이트
            self.steps_table.setItem(i, 3, QTableWidgetItem(f"{display_input:,}"))  # 입력 토큰
            self.steps_table.setItem(i, 4, QTableWidgetItem(f"{display_output:,}" if display_output > 0 else "-"))  # 출력 토큰
            self.steps_table.setItem(i, 5, QTableWidgetItem(f"{display_total:,}"))  # 전체 토큰
            
            # 도구명
            tool_name = step.get('tool_name', '-')
            if not tool_name or tool_name == 'None':
                tool_name = '-'
            self.steps_table.setItem(i, 6, QTableWidgetItem(tool_name))
            
            # 정확도 계산 (실제 토큰과 추정 토큰 비교)
            if actual_input_tokens > 0 or actual_output_tokens > 0:
                actual_total = actual_input_tokens + actual_output_tokens
                estimated_total = estimated_input_tokens + estimated_output_tokens
                if actual_total > 0 and estimated_total > 0:
                    accuracy = min(100.0, (1 - abs(actual_total - estimated_total) / actual_total) * 100)
                else:
                    accuracy = 100.0 if actual_total == estimated_total else 0.0
            else:
                accuracy = 0.0  # 실제 토큰 정보가 없으면 정확도 계산 불가
            
            self.steps_table.setItem(i, 7, QTableWidgetItem(f"{accuracy:.1f}%" if accuracy > 0 else "N/A"))
        
        # 테이블 업데이트 재개
        self.steps_table.setUpdatesEnabled(True)
    
    def update_statistics(self):
        """통계 정보 업데이트"""
        # Try unified tracker first
        if self.unified_tracker:
            self._update_statistics_unified()
            return
        
        # Fallback to legacy tracker
        history = token_tracker.conversation_history
        current_conv = token_tracker.current_conversation
        
        all_conversations = list(history)
        if current_conv and current_conv not in history:
            all_conversations.append(current_conv)
        
        if not all_conversations:
            self.total_conversations_label.setText("Total Conversations: 0")
            self.avg_tokens_label.setText("Avg Tokens/Conv: 0")
            self.total_tokens_label.setText("Total Tokens: 0")
            if hasattr(self, 'total_cost_label'):
                self.total_cost_label.setText("Total Cost: $0.00")
            if hasattr(self, 'mode_stats_text'):
                self.mode_stats_text.clear()
            self.model_stats_text.clear()
            if hasattr(self, 'agent_stats_text'):
                self.agent_stats_text.clear()
            return
        
        # 전체 통계
        total_conversations = len(all_conversations)
        total_tokens = sum(conv.total_tokens for conv in all_conversations)
        avg_tokens = total_tokens / total_conversations if total_conversations > 0 else 0
        
        # 정확도 계산
        accuracies = []
        for conv in all_conversations:
            if conv.total_tokens > 0 and conv.total_estimated_tokens > 0:
                accuracy = min(100.0, (1 - abs(conv.total_tokens - conv.total_estimated_tokens) / conv.total_tokens) * 100)
                accuracies.append(accuracy)
        
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        
        self.total_conversations_label.setText(f"Total Conversations: {total_conversations}")
        self.avg_tokens_label.setText(f"Avg Tokens/Conv: {avg_tokens:.1f}")
        self.total_tokens_label.setText(f"Total Tokens: {total_tokens:,}")
        if hasattr(self, 'total_cost_label'):
            self.total_cost_label.setText("Total Cost: $0.000000")
        if hasattr(self, 'avg_accuracy_label'):
            self.avg_accuracy_label.setText(f"Avg Accuracy: {avg_accuracy:.1f}%")
        
        # 모델별 통계
        model_stats = {}
        for conv in all_conversations:
            model = conv.model_name
            if model not in model_stats:
                model_stats[model] = {'count': 0, 'tokens': 0, 'accuracies': []}
            
            model_stats[model]['count'] += 1
            model_stats[model]['tokens'] += conv.total_tokens
            
            if conv.total_tokens > 0 and conv.total_estimated_tokens > 0:
                accuracy = min(100.0, (1 - abs(conv.total_tokens - conv.total_estimated_tokens) / conv.total_tokens) * 100)
                model_stats[model]['accuracies'].append(accuracy)
        
        # 모델별 통계 텍스트 생성
        stats_text = ""
        for model, stats in model_stats.items():
            avg_model_accuracy = sum(stats['accuracies']) / len(stats['accuracies']) if stats['accuracies'] else 0
            stats_text += f"{model}:\n"
            stats_text += f"  Conversations: {stats['count']}\n"
            stats_text += f"  Total Tokens: {stats['tokens']:,}\n"
            stats_text += f"  Avg Tokens: {stats['tokens'] / stats['count']:.1f}\n"
            stats_text += f"  Accuracy: {avg_model_accuracy:.1f}%\n\n"
        
        self.model_stats_text.setPlainText(stats_text)
    
    def export_data(self):
        """데이터 내보내기"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"token_usage_{timestamp}.json"
        
        try:
            token_tracker.export_conversation_data(filename)
            message = f"토큰 사용량 데이터가 {filename}으로 내보내졌습니다."
            self.export_requested.emit(message)
        except Exception as e:
            error_msg = f"데이터 내보내기 실패: {str(e)}"
            logger.error(f"데이터 내보내기 오류: {e}")
            self.export_requested.emit(error_msg)
    

    
    def on_async_data_ready(self, data):
        """비동기 처리된 데이터 수신"""
        try:
            # UI 스레드에서 안전하게 통계 업데이트
            self.update_statistics_from_data(data)
        except Exception as e:
            logger.error(f"비동기 데이터 처리 오류: {e}")
    
    def update_statistics_from_data(self, data):
        """비동기 처리된 데이터로 통계 업데이트"""
        total_conversations = data['total_conversations']
        total_tokens = data['total_tokens']
        model_stats = data['model_stats']
        
        avg_tokens = total_tokens / total_conversations if total_conversations > 0 else 0
        
        self.total_conversations_label.setText(f"Total Conversations: {total_conversations}")
        self.avg_tokens_label.setText(f"Avg Tokens/Conv: {avg_tokens:.1f}")
        self.total_tokens_label.setText(f"Total Tokens: {total_tokens:,}")
        
        # 모델별 통계 텍스트 생성
        stats_text = ""
        for model, stats in model_stats.items():
            stats_text += f"{model}:\n"
            stats_text += f"  Conversations: {stats['count']}\n"
            stats_text += f"  Total Tokens: {stats['tokens']:,}\n"
            stats_text += f"  Avg Tokens: {stats['tokens'] / stats['count']:.1f}\n\n"
        
        self.model_stats_text.setPlainText(stats_text)
    
    def _update_statistics_unified(self):
        """통합 트래커로 통계 업데이트"""
        try:
            # 현재 세션 통계
            stats = self.unified_tracker.get_session_stats()
            
            # Mode breakdown (전체)
            mode_breakdown = self.unified_tracker.get_mode_breakdown()
            
            # Model breakdown (전체)
            model_breakdown = self.unified_tracker.get_model_breakdown()
            
            # Agent breakdown (전체)
            agent_breakdown = self.unified_tracker.get_agent_breakdown()
            
            # Overall 통계
            total_tokens = sum(data['total_tokens'] for data in model_breakdown.values()) if model_breakdown else 0
            total_cost = sum(data['total_cost'] for data in model_breakdown.values()) if model_breakdown else 0.0
            total_convs = len(set(mode_breakdown.keys())) if mode_breakdown else 0
            
            self.total_conversations_label.setText(f"Total Conversations: {total_convs}")
            self.total_tokens_label.setText(f"Total Tokens: {total_tokens:,}")
            self.total_cost_label.setText(f"Total Cost: ${total_cost:.6f}")
            avg_tokens = total_tokens // total_convs if total_convs > 0 else 0
            self.avg_tokens_label.setText(f"Avg Tokens/Conv: {avg_tokens:,}")
            
            # Mode Breakdown
            if mode_breakdown:
                mode_text = ""
                for mode, data in mode_breakdown.items():
                    mode_text += f"{mode.upper()}:\n"
                    mode_text += f"  Tokens: {data['total_tokens']:,}\n"
                    mode_text += f"  Cost: ${data['total_cost']:.6f}\n\n"
                self.mode_stats_text.setPlainText(mode_text)
            else:
                self.mode_stats_text.setPlainText("No data yet")
            
            # Model Breakdown
            if model_breakdown:
                model_text = ""
                for model, data in model_breakdown.items():
                    model_text += f"{model}:\n"
                    model_text += f"  Tokens: {data['total_tokens']:,}\n"
                    model_text += f"  Cost: ${data['total_cost']:.6f}\n"
                    model_text += f"  Count: {data['count']}\n\n"
                self.model_stats_text.setPlainText(model_text)
            else:
                self.model_stats_text.setPlainText("No data yet")
            
            # Agent Breakdown
            if agent_breakdown:
                agent_text = ""
                for agent, data in agent_breakdown.items():
                    agent_text += f"{agent}:\n"
                    agent_text += f"  Tokens: {data['total_tokens']:,}\n"
                    agent_text += f"  Cost: ${data['total_cost']:.6f}\n"
                    agent_text += f"  Count: {data['count']}\n\n"
                self.agent_stats_text.setPlainText(agent_text)
            else:
                self.agent_stats_text.setPlainText("No data yet")
            
            # Cost Analysis
            if model_breakdown:
                # Most expensive model
                most_expensive = max(model_breakdown.items(), key=lambda x: x[1]['total_cost'])
                self.most_expensive_label.setText(f"Most Expensive: {most_expensive[0]} (${most_expensive[1]['total_cost']:.6f})")
                
                # Most used model
                most_used = max(model_breakdown.items(), key=lambda x: x[1]['total_tokens'])
                self.most_used_label.setText(f"Most Used: {most_used[0]} ({most_used[1]['total_tokens']:,} tokens)")
                
                # Average cost per 1K tokens
                if total_tokens > 0:
                    avg_cost_per_1k = (total_cost / total_tokens) * 1000
                    self.avg_cost_label.setText(f"Avg Cost/1K tokens: ${avg_cost_per_1k:.6f}")
            else:
                self.most_expensive_label.setText("Most Expensive: -")
                self.most_used_label.setText("Most Used: -")
                self.avg_cost_label.setText("Avg Cost/1K tokens: $0.000000")
            
        except Exception as e:
            logger.error(f"통합 트래커 통계 업데이트 오류: {e}", exc_info=True)
    
    def clear_history(self):
        """히스토리 지우기"""
        token_tracker.conversation_history.clear()
        if hasattr(token_tracker, 'current_conversation'):
            token_tracker.current_conversation = None
        
        if self.unified_tracker and hasattr(self.unified_tracker, '_session_cache'):
            self.unified_tracker._session_cache.clear()
        
        self.refresh_display()
    
    def on_token_updated(self, token_info):
        """토큰 누적기에서 토큰 업데이트 수신"""
        try:
            model = token_info.get('model', '')
            usage = token_info.get('usage')
            session_total = token_info.get('session_total')
            
            if usage and session_total:
                logger.info(f"토큰 업데이트 수신: {model} +{usage.total_tokens} = {session_total.total_tokens}")
                # UI 즉시 업데이트
                self.refresh_display()
        except Exception as e:
            logger.error(f"토큰 업데이트 처리 오류: {e}")
    
    def on_period_changed(self, period: str):
        """기간 필터 변경"""
        if not self.unified_tracker:
            return
        
        try:
            if period == "Current":
                # 현재 세션만
                self.tab_widget.setTabEnabled(1, True)  # Steps 탭 활성화
                self.update_statistics()
                self.update_steps_table()
            else:
                # 기간 필터: Steps 탭 비활성화 (DB에 step 데이터 없음)
                self.tab_widget.setTabEnabled(1, False)
                if period == "7 Days":
                    self._update_statistics_period(7)
                elif period == "30 Days":
                    self._update_statistics_period(30)
                elif period == "All Time":
                    self._update_statistics_period(None)
        except Exception as e:
            logger.error(f"기간 필터 변경 오류: {e}")
    
    def _update_statistics_period(self, days: int = None):
        """기간별 통계 업데이트"""
        try:
            if days:
                stats = self.unified_tracker.get_historical_stats(days)
            else:
                # All time
                mode_breakdown = self.unified_tracker.get_mode_breakdown()
                model_breakdown = self.unified_tracker.get_model_breakdown()
                agent_breakdown = self.unified_tracker.get_agent_breakdown()
                
                stats = {
                    'mode_breakdown': mode_breakdown,
                    'model_breakdown': model_breakdown,
                    'agent_breakdown': agent_breakdown
                }
            
            # 통계 표시
            self._display_period_stats(stats)
            
        except Exception as e:
            logger.error(f"기간별 통계 업데이트 오류: {e}")
    
    def _display_period_stats(self, stats: Dict):
        """기간별 통계 표시"""
        mode_breakdown = stats.get('mode_breakdown', {})
        model_breakdown = stats.get('model_breakdown', {})
        agent_breakdown = stats.get('agent_breakdown', {})
        
        # Overall
        total_tokens = sum(d.get('total_tokens', 0) for d in model_breakdown.values())
        total_cost = sum(d.get('total_cost', 0) for d in model_breakdown.values())
        total_convs = sum(d.get('count', 0) for d in mode_breakdown.values())
        
        self.total_conversations_label.setText(f"Total Conversations: {total_convs}")
        self.total_tokens_label.setText(f"Total Tokens: {total_tokens:,}")
        self.total_cost_label.setText(f"Total Cost: ${total_cost:.6f}")
        avg_tokens = total_tokens // total_convs if total_convs > 0 else 0
        self.avg_tokens_label.setText(f"Avg Tokens/Conv: {avg_tokens:,}")
        
        # Mode
        if mode_breakdown:
            mode_text = ""
            for mode, data in mode_breakdown.items():
                mode_text += f"{mode.upper()}:\n"
                mode_text += f"  Tokens: {data.get('total_tokens', 0):,}\n"
                mode_text += f"  Cost: ${data.get('total_cost', 0):.6f}\n\n"
            self.mode_stats_text.setPlainText(mode_text)
        else:
            self.mode_stats_text.setPlainText("No data")
        
        # Model
        if model_breakdown:
            model_text = ""
            for model, data in model_breakdown.items():
                model_text += f"{model}:\n"
                model_text += f"  Tokens: {data.get('total_tokens', 0):,}\n"
                model_text += f"  Cost: ${data.get('total_cost', 0):.6f}\n"
                model_text += f"  Count: {data.get('count', 0)}\n\n"
            self.model_stats_text.setPlainText(model_text)
        else:
            self.model_stats_text.setPlainText("No data")
        
        # Agent
        if agent_breakdown:
            agent_text = ""
            for agent, data in agent_breakdown.items():
                agent_text += f"{agent}:\n"
                agent_text += f"  Tokens: {data.get('total_tokens', 0):,}\n"
                agent_text += f"  Cost: ${data.get('total_cost', 0):.6f}\n"
                agent_text += f"  Count: {data.get('count', 0)}\n\n"
            self.agent_stats_text.setPlainText(agent_text)
        else:
            self.agent_stats_text.setPlainText("No data")
        
        # Cost Analysis
        if model_breakdown:
            most_expensive = max(model_breakdown.items(), key=lambda x: x[1].get('total_cost', 0))
            self.most_expensive_label.setText(f"Most Expensive: {most_expensive[0]} (${most_expensive[1].get('total_cost', 0):.6f})")
            
            most_used = max(model_breakdown.items(), key=lambda x: x[1].get('total_tokens', 0))
            self.most_used_label.setText(f"Most Used: {most_used[0]} ({most_used[1].get('total_tokens', 0):,} tokens)")
            
            if total_tokens > 0:
                avg_cost_per_1k = (total_cost / total_tokens) * 1000
                self.avg_cost_label.setText(f"Avg Cost/1K tokens: ${avg_cost_per_1k:.6f}")
        else:
            self.most_expensive_label.setText("Most Expensive: -")
            self.most_used_label.setText("Most Used: -")
            self.avg_cost_label.setText("Avg Cost/1K tokens: $0.000000")
    
    def closeEvent(self, event):
        """위젯 종료 시 스레드 정리"""
        if hasattr(self, 'data_processor'):
            self.data_processor.stop()
        if hasattr(self, 'worker_thread'):
            self.worker_thread.quit()
            self.worker_thread.wait()
        super().closeEvent(event)
    
    def show_processing_progress(self, step_name: str):
        """처리 진행률 표시"""
        self.current_step_label.setText(f"Current Step: {step_name}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 무한 진행률
    
    def hide_processing_progress(self):
        """처리 진행률 숨기기"""
        self.progress_bar.setVisible(False)