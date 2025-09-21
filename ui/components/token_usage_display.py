"""
Token usage display component for showing detailed token consumption
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QGroupBox, QScrollArea,
                            QFrame, QProgressBar, QTableWidget, QTableWidgetItem,
                            QHeaderView, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QObject
from PyQt6.QtGui import QFont, QPalette
from core.token_tracker import token_tracker, StepType
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AsyncDataProcessor(QObject):
    """비동기 데이터 처리 워커"""
    
    data_ready = pyqtSignal(dict)  # 처리된 데이터 시그널
    
    def __init__(self):
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
        self.setup_ui()
        self.setup_timer()
        self.setup_async_processing()
        self.apply_theme()
    
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
        
        # 전체 통계
        self.overall_stats_group = QGroupBox("Overall Statistics")
        stats_layout = QVBoxLayout(self.overall_stats_group)
        
        self.total_conversations_label = QLabel("Total Conversations: 0")
        self.avg_tokens_label = QLabel("Average Tokens per Conversation: 0")
        self.total_tokens_label = QLabel("Total Tokens Used: 0")
        self.avg_accuracy_label = QLabel("Average Accuracy: 0%")
        
        stats_layout.addWidget(self.total_conversations_label)
        stats_layout.addWidget(self.avg_tokens_label)
        stats_layout.addWidget(self.total_tokens_label)
        stats_layout.addWidget(self.avg_accuracy_label)
        
        # 모델별 통계
        self.model_stats_group = QGroupBox("Model Statistics")
        model_layout = QVBoxLayout(self.model_stats_group)
        
        self.model_stats_text = QTextEdit()
        self.model_stats_text.setMaximumHeight(150)
        self.model_stats_text.setReadOnly(True)
        model_layout.addWidget(self.model_stats_text)
        
        layout.addWidget(self.overall_stats_group)
        layout.addWidget(self.model_stats_group)
        layout.addStretch()
        
        return widget
    
    def create_control_buttons(self, layout):
        """컨트롤 버튼 생성 - 더 큰 버튼, 명확한 아이콘"""
        button_layout = QVBoxLayout()  # 세로 배치로 변경
        button_layout.setContentsMargins(4, 4, 4, 4)
        button_layout.setSpacing(4)
        
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.refresh_display)
        self.refresh_button.setMinimumHeight(36)
        
        self.export_button = QPushButton("📤 Export JSON")
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
        """채팅창과 동일한 Material Design 테마 적용 - 대비색 개선"""
        try:
            from ui.styles.theme_manager import theme_manager
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                is_dark = theme_manager.is_material_dark_theme()
                
                # 테마별 대비색 설정
                bg_color = colors.get('background', '#121212')
                text_color = colors.get('text_primary', '#ffffff' if is_dark else '#000000')
                surface_color = colors.get('surface', '#1e1e1e')
                primary_color = colors.get('primary', '#bb86fc')
                secondary_color = colors.get('secondary', '#03dac6')
                
                # 테마별 추가 색상 설정
                on_primary_color = colors.get('on_primary', '#000000' if is_dark else '#ffffff')
                divider_color = colors.get('divider', '#333333' if is_dark else '#e0e0e0')
                primary_variant_color = colors.get('primary_variant', '#3700b3')
                
                # 전체 패널 스타일 - 채팅창과 동일한 배경
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
                        background-color: {surface_color};
                        border: 1px solid {divider_color};
                        border-radius: 12px;
                        padding: 8px;
                        margin: 4px;
                        font-weight: 700;
                        font-size: 14px;
                        color: {text_color};
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    }}
                    
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        left: 8px;
                        padding: 4px 8px;
                        background: {primary_color};
                        color: {on_primary_color};
                        border-radius: 6px;
                        font-weight: 700;
                        font-size: 13px;
                    }}
                    
                    QPushButton {{
                        background-color: {primary_color};
                        color: {on_primary_color};
                        border: 2px solid {primary_variant_color};
                        padding: 12px 16px;
                        border-radius: 14px;
                        font-weight: 700;
                        font-size: 14px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        margin: 2px;
                    }}
                    
                    QPushButton:hover {{
                        background-color: {primary_variant_color};
                    }}
                    
                    QPushButton:pressed {{
                        background-color: {primary_variant_color};
                    }}
                    
                    QTabWidget {{
                        background: transparent;
                        border: none;
                    }}
                    
                    QTabWidget::pane {{
                        background-color: {surface_color};
                        border: 1px solid {divider_color};
                        border-radius: 12px;
                        margin: 2px;
                    }}
                    
                    QTabBar::tab {{
                        background-color: {bg_color};
                        color: {text_color};
                        border: 1px solid {divider_color};
                        padding: 8px 16px;
                        margin: 2px;
                        border-radius: 6px;
                        font-weight: 600;
                        font-size: 13px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    }}
                    
                    QTabBar::tab:selected {{
                        background-color: {primary_color};
                        color: {on_primary_color};
                        border-color: {primary_variant_color};
                        font-weight: 700;
                    }}
                    
                    QTabBar::tab:hover {{
                        background-color: {primary_variant_color};
                        color: {on_primary_color};
                    }}
                    
                    QTableWidget {{
                        background-color: {surface_color};
                        color: {text_color};
                        border: 1px solid {divider_color};
                        border-radius: 12px;
                        gridline-color: {divider_color};
                        font-size: 13px;
                        font-weight: 500;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    }}
                    
                    QTableWidget::item {{
                        padding: 8px;
                        border: none;
                    }}
                    
                    QTableWidget::item:selected {{
                        background-color: {primary_color};
                        color: {on_primary_color};
                    }}
                    
                    QHeaderView::section {{
                        background-color: {primary_color};
                        color: {on_primary_color};
                        border: 1px solid {primary_variant_color};
                        padding: 8px;
                        font-weight: 700;
                        font-size: 12px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    }}
                    
                    QTextEdit {{
                        background-color: {bg_color};
                        color: {text_color};
                        border: 1px solid {divider_color};
                        border-radius: 12px;
                        padding: 8px;
                        font-size: 13px;
                        font-weight: 500;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        selection-background-color: {primary_color};
                    }}
                    
                    QProgressBar {{
                        background-color: {surface_color};
                        border: 1px solid {divider_color};
                        border-radius: 8px;
                        text-align: center;
                        font-weight: 600;
                        font-size: 12px;
                        color: {text_color};
                    }}
                    
                    QProgressBar::chunk {{
                        background-color: {primary_color};
                        border-radius: 6px;
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
        self.refresh_timer.start(2000)  # 2초마다 새로고침 (성능 최적화)
        
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
        self.async_timer.start(5000)  # 5초마다 비동기 처리
    
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
                
                # 통계는 비동기로 처리됨 (별도 처리 불필요)
                
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
        
        # 토큰 누적기에서 누적 토큰 가져오기
        from core.simple_token_accumulator import token_accumulator
        accumulator_input, accumulator_output, accumulator_total = token_accumulator.get_total()
        
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
            self.estimated_tokens_label.setText(f"Current Conversation: {accumulator_total:,} tokens (IN:{accumulator_input:,} OUT:{accumulator_output:,}) [누적기]")
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
        history = token_tracker.conversation_history
        current_conv = token_tracker.current_conversation
        
        # 현재 대화도 포함하여 계산
        all_conversations = list(history)
        if current_conv and current_conv not in history:
            all_conversations.append(current_conv)
        
        if not all_conversations:
            self.total_conversations_label.setText("Total Conversations: 0")
            self.avg_tokens_label.setText("Average Tokens per Conversation: 0")
            self.total_tokens_label.setText("Total Tokens Used: 0")
            self.avg_accuracy_label.setText("Average Accuracy: 0%")
            self.model_stats_text.clear()
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
        self.avg_tokens_label.setText(f"Average Tokens per Conversation: {avg_tokens:.1f}")
        self.total_tokens_label.setText(f"Total Tokens Used: {total_tokens:,}")
        self.avg_accuracy_label.setText(f"Average Accuracy: {avg_accuracy:.1f}%")
        
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
        self.avg_tokens_label.setText(f"Average Tokens per Conversation: {avg_tokens:.1f}")
        self.total_tokens_label.setText(f"Total Tokens Used: {total_tokens:,}")
        
        # 모델별 통계 텍스트 생성
        stats_text = ""
        for model, stats in model_stats.items():
            stats_text += f"{model}:\n"
            stats_text += f"  Conversations: {stats['count']}\n"
            stats_text += f"  Total Tokens: {stats['tokens']:,}\n"
            stats_text += f"  Avg Tokens: {stats['tokens'] / stats['count']:.1f}\n\n"
        
        self.model_stats_text.setPlainText(stats_text)
    
    def clear_history(self):
        """히스토리 지우기"""
        token_tracker.conversation_history.clear()
        if hasattr(token_tracker, 'current_conversation'):
            token_tracker.current_conversation = None
        self.refresh_display()
    
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