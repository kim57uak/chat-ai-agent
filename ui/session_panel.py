"""
Session Management Panel
채팅창 왼쪽에 표시되는 세션 관리 패널
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QLineEdit, QDialog, QDialogButtonBox,
    QMessageBox, QMenu, QInputDialog, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QAction
from typing import Dict, List, Optional
import logging
import os
from datetime import datetime

from core.session import session_manager
from ui.styles.theme_manager import theme_manager
from core.session.session_exporter import SessionExporter

logger = logging.getLogger(__name__)


class NewSessionDialog(QDialog):
    """새 세션 생성 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("새 세션 생성")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        # 제목 입력
        layout.addWidget(QLabel("세션 제목:"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("예: Python 학습, 여행 계획 등")
        layout.addWidget(self.title_edit)
        
        # 카테고리 입력
        layout.addWidget(QLabel("카테고리 (선택사항):"))
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("예: 개발, 여행, 업무 등")
        layout.addWidget(self.category_edit)
        
        # 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # 제목 입력란에 포커스
        self.title_edit.setFocus()
    
    def get_session_data(self) -> Dict[str, str]:
        """세션 데이터 반환"""
        return {
            'title': self.title_edit.text().strip(),
            'category': self.category_edit.text().strip() or None
        }


class SessionListItem(QWidget):
    """현대적인 세션 목록 아이템"""
    
    clicked = pyqtSignal(int)  # session_id
    delete_requested = pyqtSignal(int)  # session_id
    
    def __init__(self, session_data: Dict, parent=None):
        super().__init__(parent)
        self.session_data = session_data
        self.session_id = session_data['id']
        self.is_selected = False
        
        self.setup_ui()
        self.apply_theme()
    
    def setup_ui(self):
        """UI 설정 - 두 줄 효율적 배치"""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # 첫 번째 줄: 선택 표시, 제목
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)
        
        # 선택 표시 아이콘
        self.selected_icon = QLabel("●")
        self.selected_icon.setFixedSize(16, 16)
        self.selected_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selected_icon.hide()
        top_layout.addWidget(self.selected_icon)
        
        self.title_label = QLabel(self.session_data['title'])
        self.title_label.setWordWrap(False)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(self.title_label, 1)
        
        layout.addLayout(top_layout)
        
        # 두 번째 줄: 메시지 수와 날짜
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)
        
        self.message_count_label = QLabel(f"{self.session_data['message_count']}")
        self.message_count_label.setFixedSize(30, 30)
        self.message_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.message_count_label)
        
        bottom_layout.addStretch()
        
        last_used = self.session_data.get('last_used_at', '')
        if last_used:
            try:
                dt = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                time_str = dt.strftime("%m/%d")
                self.time_label = QLabel(time_str)
                self.time_label.setFixedSize(50, 24)
                self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                bottom_layout.addWidget(self.time_label)
            except:
                pass
        
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
    
    def apply_theme(self):
        """깔끔한 테마 적용"""
        if theme_manager.use_material_theme:
            colors = theme_manager.material_manager.get_theme_colors()
            is_dark = theme_manager.is_material_dark_theme()
            
            # 제목 스타일
            title_color = colors.get('text_primary', '#ffffff' if is_dark else '#000000')
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: {title_color};
                    font-size: 14px;
                    font-weight: 600;
                    margin-bottom: 4px;
                }}
            """)
            
            # 메시지 수 배지 - 테마 버튼과 동일한 스타일
            primary_color = colors.get('primary', '#1976d2')
            primary_variant = colors.get('primary_variant', '#1565c0')
            on_primary = colors.get('on_primary', '#ffffff')
            self.message_count_label.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {primary_color}, 
                        stop:1 {primary_variant});
                    color: {on_primary};
                    border: none;
                    border-radius: 15px;
                    font-weight: 700;
                    font-size: 12px;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    padding: 6px 12px;
                    margin: 2px;
                    min-width: 30px;
                    min-height: 30px;
                    text-align: center;
                }}
                QLabel:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {primary_variant}, 
                        stop:1 {primary_color});
                    transform: scale(1.05);
                }}
            """)
            
            # 시간 배지 - 테마 버튼과 동일한 스타일
            if hasattr(self, 'time_label'):
                secondary_color = colors.get('text_secondary', '#666666')
                surface_color = colors.get('surface', '#f5f5f5')
                self.time_label.setStyleSheet(f"""
                    QLabel {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {surface_color}, 
                            stop:1 {secondary_color});
                        color: {colors.get('text_primary', '#000000')};
                        border: none;
                        border-radius: 12px;
                        font-weight: 600;
                        font-size: 11px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        padding: 5px 10px;
                        margin: 2px;
                        min-width: 50px;
                        min-height: 24px;
                        text-align: center;
                    }}
                    QLabel:hover {{
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 {secondary_color}, 
                            stop:1 {surface_color});
                        transform: scale(1.05);
                    }}
                """)
            

            
            # 선택 표시 아이콘 스타일
            self.selected_icon.setStyleSheet(f"""
                QLabel {{
                    color: {primary_color};
                    font-size: 12px;
                    font-weight: bold;
                }}
            """)
            
            self.update_item_style(colors)
    
    def update_item_style(self, colors):
        """깔끔한 아이템 스타일"""
        is_dark = theme_manager.is_material_dark_theme()
        
        if self.is_selected:
            # 선택된 상태
            primary_color = colors.get('primary', '#1976d2')
            self.setStyleSheet(f"""
                SessionListItem {{
                    background-color: {primary_color}20;
                    border: 2px solid {primary_color};
                    border-radius: 8px;
                    margin: 2px;
                }}
            """)
        else:
            # 기본 상태
            bg_color = colors.get('surface', '#f5f5f5' if not is_dark else '#2d2d2d')
            border_color = colors.get('divider', '#e0e0e0' if not is_dark else '#404040')
            
            self.setStyleSheet(f"""
                SessionListItem {{
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                    margin: 2px;
                }}
                SessionListItem:hover {{
                    background-color: {colors.get('primary', '#1976d2')}10;
                    border-color: {colors.get('primary', '#1976d2')};
                }}
            """)
    
    def set_selected(self, selected: bool):
        """선택 상태 설정"""
        self.is_selected = selected
        if selected:
            self.selected_icon.show()
        else:
            self.selected_icon.hide()
        
        if theme_manager.use_material_theme:
            colors = theme_manager.material_manager.get_theme_colors()
            self.update_item_style(colors)
    

    
    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.clicked.emit(self.session_id)
            elif event.button() == Qt.MouseButton.RightButton:
                self.show_context_menu(event.globalPosition().toPoint())
            super().mousePressEvent(event)
        except RuntimeError as e:
            if "wrapped C/C++ object" in str(e):
                print(f"SessionListItem이 이미 삭제됨: {e}")
                return
            raise
    
    def show_context_menu(self, position):
        """우클릭 컨텍스트 메뉴 표시"""
        menu = QMenu(self)
        delete_action = menu.addAction("🗑️ 세션 삭제")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.session_id))
        menu.exec(position)


class SessionPanel(QWidget):
    """세션 관리 패널"""
    
    session_selected = pyqtSignal(int)  # session_id
    session_created = pyqtSignal(int)   # session_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_session_id = None
        self.setup_ui()
        self.load_sessions()
        
        # 자동 새로고침 타이머 - 비동기 처리
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(lambda: QTimer.singleShot(0, self.refresh_all_data))
        self.refresh_timer.start(30000)  # 30초마다 새로고침
    
    def setup_ui(self):
        """UI 설정 - 로고와 Sessions 문구 삭제, 버튼 재정렬"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(6)
        
        # 상단 버튼들 - 새로운 구성
        top_buttons_layout = QVBoxLayout()
        top_buttons_layout.setContentsMargins(2, 2, 2, 2)
        top_buttons_layout.setSpacing(6)
        
        # +New Session 버튼
        self.new_session_btn = QPushButton("➕ New Session")
        self.new_session_btn.setMinimumHeight(44)
        self.new_session_btn.clicked.connect(self.create_new_session)
        top_buttons_layout.addWidget(self.new_session_btn)
        
        # 현재 모델 버튼 (가운데 창에서 이동)
        self.model_button = QPushButton("🤖 Current Model")
        self.model_button.setMinimumHeight(44)
        self.model_button.clicked.connect(self.show_model_selector)
        top_buttons_layout.addWidget(self.model_button)
        
        # 템플릿 버튼 (가운데 채팅입력 창에서 이동)
        self.template_button = QPushButton("📋 Templates")
        self.template_button.setMinimumHeight(44)
        self.template_button.clicked.connect(self.show_template_manager)
        top_buttons_layout.addWidget(self.template_button)
        
        # 테마 버튼 (클릭시 전체테마보고 선택하기)
        self.theme_button = QPushButton("🎨 Themes")
        self.theme_button.setMinimumHeight(44)
        self.theme_button.clicked.connect(self.show_theme_selector)
        self.theme_button.setToolTip("테마 선택")
        print("테마 버튼 생성 및 연결 완료")
        top_buttons_layout.addWidget(self.theme_button)
        
        layout.addLayout(top_buttons_layout)
        
        # 구분선
        separator = QLabel()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #666666; margin: 8px 0px;")
        layout.addWidget(separator)
        
        # 세션 검색 (세션 리스트 바로 위로 이동)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search sessions...")
        self.search_edit.textChanged.connect(self.search_sessions)
        self.search_edit.setMinimumHeight(44)
        layout.addWidget(self.search_edit)
        
        # 세션 목록
        self.session_list = QListWidget()
        self.session_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fafafa;
            }
            QListWidget::item {
                border: none;
                padding: 2px;
                margin: 2px;
            }
        """)
        layout.addWidget(self.session_list)
        
        # 세션 관리 버튼들 (수정, 익스포트, 삭제 유지)
        manage_layout = QHBoxLayout()
        manage_layout.setContentsMargins(2, 2, 2, 2)
        manage_layout.setSpacing(4)
        
        # 투명한 이모지 버튼 스타일 (35% 증가)
        transparent_emoji_style = """
        QPushButton {
            background: transparent;
            border: none;
            font-size: 28px;
        }
        QPushButton:hover {
            background: transparent;
            font-size: 38px;
        }
        QPushButton:pressed {
            background: transparent;
            font-size: 26px;
        }
        QPushButton:disabled {
            background: transparent;
            opacity: 0.5;
        }
        """
        
        self.rename_btn = QPushButton("✏️")
        self.rename_btn.setToolTip("세션 이름 변경")
        self.rename_btn.setEnabled(False)
        self.rename_btn.setMinimumHeight(50)
        self.rename_btn.setStyleSheet(transparent_emoji_style)
        self.rename_btn.clicked.connect(self.rename_session)
        
        self.export_btn = QPushButton("📤")
        self.export_btn.setToolTip("세션 내보내기")
        self.export_btn.setEnabled(False)
        self.export_btn.setMinimumHeight(50)
        self.export_btn.setStyleSheet(transparent_emoji_style)
        self.export_btn.clicked.connect(self.export_session)
        
        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setToolTip("세션 삭제")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setMinimumHeight(50)
        self.delete_btn.setStyleSheet(transparent_emoji_style)
        self.delete_btn.clicked.connect(self.delete_session)
        
        manage_layout.addWidget(self.rename_btn)
        manage_layout.addWidget(self.export_btn)
        manage_layout.addWidget(self.delete_btn)
        layout.addLayout(manage_layout)
        
        # 세션정보 (유지) - 통계 정보
        self.stats_label = QLabel()
        self.stats_label.setMinimumHeight(36)
        self.stats_label.setObjectName("stats_label")
        self.stats_label.setToolTip("세션 수 | 메시지 수 | DB 용량 | 도구 수 (마지막 숫자 클릭시 상세보기)")
        self.stats_label.mousePressEvent = self.on_stats_label_click
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        self.setMinimumWidth(280)  # 최소 너비 증가
        self.setMaximumWidth(350)  # 최대 너비 설정
        
        # 테마 적용
        self.apply_theme()
        
        # 메인 윈도우 참조 초기화
        self.main_window = None
        
        # 마우스 추적 활성화 (도구 영역 감지용)
        self.setMouseTracking(True)
        self.stats_label.setMouseTracking(True)
        
        # 앱 시작 시 세션 DB에서 로드
        QTimer.singleShot(100, self.load_sessions_from_db)
        
        # 현재 모델 표시 업데이트
        QTimer.singleShot(200, self._update_current_model_display)
    
    def _update_current_model_display(self):
        """현재 모델 표시 업데이트"""
        try:
            from core.file_utils import load_last_model
            current_model = load_last_model()
            if current_model:
                # 모델명이 길면 줄임
                display_name = current_model
                if len(display_name) > 15:
                    display_name = display_name[:12] + "..."
                self.model_button.setText(f"🤖 {display_name}")
                self.model_button.setToolTip(f"현재 모델: {current_model}")
            else:
                self.model_button.setText("🤖 Select Model")
                self.model_button.setToolTip("모델을 선택하세요")
        except Exception as e:
            print(f"현재 모델 표시 업데이트 오류: {e}")
            self.model_button.setText("🤖 Select Model")
            self.model_button.setToolTip("모델을 선택하세요")
    
    def load_sessions_from_db(self):
        """앱 시작 시 세션 DB에서 로드"""
        try:
            sessions = session_manager.get_sessions()
            if sessions:
                logger.info(f"세션 DB에서 {len(sessions)}개 세션 로드됨")
                self.load_sessions()
            else:
                logger.info("세션 DB가 비어있음")
        except Exception as e:
            logger.error(f"세션 DB 로드 오류: {e}")
    
    def refresh_all_data(self):
        """모든 데이터 새로고침 - 비동기 처리"""
        QTimer.singleShot(0, self._async_refresh)
    
    def _async_refresh(self):
        """비동기 데이터 새로고침"""
        try:
            self.load_sessions()
            QTimer.singleShot(100, self.update_stats)
        except Exception as e:
            logger.error(f"비동기 새로고침 오류: {e}")
    
    def load_sessions(self):
        """세션 목록 로드"""
        try:
            sessions = session_manager.get_sessions()
            self.session_list.clear()
            
            for session in sessions:
                item = QListWidgetItem()
                session_widget = SessionListItem(session)
                session_widget.clicked.connect(self.select_session)
                session_widget.delete_requested.connect(self.delete_session_by_id)
                
                item.setSizeHint(session_widget.sizeHint())
                self.session_list.addItem(item)
                self.session_list.setItemWidget(item, session_widget)
            
            # 통계 업데이트
            self.update_stats()
            
        except Exception as e:
            logger.error(f"세션 로드 오류: {e}")
            QMessageBox.warning(self, "오류", f"세션을 불러오는 중 오류가 발생했습니다:\n{e}")
    
    def search_sessions(self, query: str):
        """세션 검색"""
        if not query.strip():
            self.load_sessions()
            return
        
        try:
            sessions = session_manager.search_sessions(query)
            self.session_list.clear()
            
            for session in sessions:
                item = QListWidgetItem()
                session_widget = SessionListItem(session)
                session_widget.clicked.connect(self.select_session)
                session_widget.delete_requested.connect(self.delete_session_by_id)
                
                item.setSizeHint(session_widget.sizeHint())
                self.session_list.addItem(item)
                self.session_list.setItemWidget(item, session_widget)
                
        except Exception as e:
            logger.error(f"세션 검색 오류: {e}")
    
    def select_session(self, session_id: int):
        """세션 선택"""
        self.current_session_id = session_id
        self.rename_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        
        # 메인 윈도우의 현재 세션 ID도 업데이트
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.current_session_id = session_id
            self.main_window._auto_session_created = True
        
        # 선택된 세션 하이라이트
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            widget = self.session_list.itemWidget(item)
            if hasattr(widget, 'session_id') and widget.session_id == session_id:
                widget.set_selected(True)
            else:
                widget.set_selected(False)
        
        self.session_selected.emit(session_id)
        logger.info(f"세션 선택: {session_id}")
    
    def create_new_session(self):
        """새 세션 생성"""
        dialog = NewSessionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_session_data()
            if not data['title']:
                QMessageBox.warning(self, "경고", "세션 제목을 입력해주세요.")
                return
            
            try:
                session_id = session_manager.create_session(
                    title=data['title'],
                    topic_category=data['category']
                )
                
                # 메인 윈도우의 현재 세션 ID 업데이트
                if hasattr(self, 'main_window') and self.main_window:
                    self.main_window.current_session_id = session_id
                    self.main_window._auto_session_created = True
                
                self.refresh_all_data()
                self.select_session(session_id)
                self.session_created.emit(session_id)
                
                QMessageBox.information(self, "성공", f"새 세션 '{data['title']}'이 생성되었습니다.")
                
            except Exception as e:
                logger.error(f"세션 생성 오류: {e}")
                QMessageBox.critical(self, "오류", f"세션 생성 중 오류가 발생했습니다:\n{e}")
    
    def rename_session(self):
        """세션 이름 변경"""
        if not self.current_session_id:
            return
        
        session = session_manager.get_session(self.current_session_id)
        if not session:
            return
        
        new_title, ok = QInputDialog.getText(
            self, "세션 이름 변경", "새 제목:", text=session['title']
        )
        
        if ok and new_title.strip():
            try:
                success = session_manager.update_session(
                    self.current_session_id, 
                    title=new_title.strip()
                )
                
                if success:
                    self.refresh_all_data()
                    QMessageBox.information(self, "성공", "세션 이름이 변경되었습니다.")
                else:
                    QMessageBox.warning(self, "실패", "세션 이름 변경에 실패했습니다.")
                    
            except Exception as e:
                logger.error(f"세션 이름 변경 오류: {e}")
                QMessageBox.critical(self, "오류", f"세션 이름 변경 중 오류가 발생했습니다:\n{e}")
    
    def delete_session(self):
        """세션 삭제"""
        if not self.current_session_id:
            return
        
        session = session_manager.get_session(self.current_session_id)
        if not session:
            return
        
        reply = QMessageBox.question(
            self, "세션 삭제", 
            f"'{session['title']}' 세션을 삭제하시겠습니까?\n\n"
            f"메시지 {session['message_count']}개가 함께 삭제됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 먼저 UI에서 해당 아이템 제거
                self._remove_session_item(self.current_session_id)
                
                success = session_manager.delete_session(self.current_session_id)
                
                if success:
                    # 메인 윈도우의 현재 세션 ID도 초기화
                    if hasattr(self, 'main_window') and self.main_window:
                        if self.main_window.current_session_id == self.current_session_id:
                            self.main_window.current_session_id = None
                            self.main_window._auto_session_created = False
                    
                    self.current_session_id = None
                    self.rename_btn.setEnabled(False)
                    self.export_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)
                    
                    # 지연 새로고침
                    QTimer.singleShot(100, self.refresh_all_data)
                    QMessageBox.information(self, "성공", "세션이 삭제되었습니다.")
                else:
                    QMessageBox.warning(self, "실패", "세션 삭제에 실패했습니다.")
                    # 실패 시 다시 로드
                    self.load_sessions()
                    
            except Exception as e:
                logger.error(f"세션 삭제 오류: {e}")
                QMessageBox.critical(self, "오류", f"세션 삭제 중 오류가 발생했습니다:\n{e}")
                # 오류 시 다시 로드
                self.load_sessions()
    
    def export_session(self):
        """세션 내보내기"""
        if not self.current_session_id:
            return
        
        session = session_manager.get_session(self.current_session_id)
        if not session:
            return
        
        # 내보내기 형식 선택 대화상자
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox, QButtonGroup
        
        dialog = QDialog(self)
        dialog.setWindowTitle("내보내기 형식 선택")
        dialog.setModal(True)
        dialog.resize(300, 250)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"세션 '{session['title']}'를 내보내기:"))
        
        # 라디오 버튼 그룹
        button_group = QButtonGroup()
        
        text_radio = QRadioButton("텍스트 파일 (.txt)")
        html_radio = QRadioButton("HTML 파일 (.html)")
        json_radio = QRadioButton("JSON 파일 (.json)")
        md_radio = QRadioButton("Markdown 파일 (.md)")
        pdf_radio = QRadioButton("PDF 파일 (.pdf)")
        
        text_radio.setChecked(True)  # 기본 선택
        
        button_group.addButton(text_radio, 0)
        button_group.addButton(html_radio, 1)
        button_group.addButton(json_radio, 2)
        button_group.addButton(md_radio, 3)
        button_group.addButton(pdf_radio, 4)
        
        layout.addWidget(text_radio)
        layout.addWidget(html_radio)
        layout.addWidget(json_radio)
        layout.addWidget(md_radio)
        layout.addWidget(pdf_radio)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_format = button_group.checkedId()
            self._export_with_format(session, selected_format)
    
    def _export_with_format(self, session: Dict, format_id: int):
        """선택된 형식으로 내보내기"""
        try:
            if format_id == 4:  # PDF 내보내기
                self._export_to_pdf(session)
                return
            
            # 기존 파일 형식 매핑
            formats = {
                0: ('.txt', 'Text files (*.txt)', SessionExporter.export_to_text),
                1: ('.html', 'HTML files (*.html)', SessionExporter.export_to_html),
                2: ('.json', 'JSON files (*.json)', SessionExporter.export_to_json),
                3: ('.md', 'Markdown files (*.md)', SessionExporter.export_to_markdown)
            }
            
            ext, file_filter, export_func = formats[format_id]
            
            # 기본 파일명 생성
            safe_title = "".join(c for c in session['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
            default_filename = f"{safe_title}_{session['id']}{ext}"
            
            # 파일 저장 대화상자
            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, '세션 내보내기', default_filename, file_filter
            )
            
            if not file_path:
                return
            
            # 메시지 데이터 가져오기 (HTML 포함)
            messages = session_manager.get_session_messages(session['id'], include_html=True)
            
            # 내보내기 실행
            success = export_func(session, messages, file_path)
            
            if success:
                QMessageBox.information(
                    self, '성공', 
                    f'세션이 성공적으로 내보내졌습니다:\n{file_path}'
                )
            else:
                QMessageBox.warning(self, '실패', '내보내기에 실패했습니다.')
                
        except Exception as e:
            logger.error(f"세션 내보내기 오류: {e}")
            QMessageBox.critical(self, '오류', f'내보내기 중 오류가 발생했습니다:\n{e}')
    
    def _export_to_pdf(self, session: Dict):
        """PDF로 내보내기 - HTML 렌더링된 상태로"""
        try:
            # 메시지 데이터 가져오기 (HTML 포함)
            messages = session_manager.get_session_messages(session['id'], include_html=True)
            
            if not messages:
                QMessageBox.information(self, '정보', '내보낼 메시지가 없습니다.')
                return
            
            # PDF 내보내기 실행
            from core.pdf_exporter import PDFExporter
            pdf_exporter = PDFExporter(self)
            
            # 메시지 형식 변환 - HTML 콘텐츠 사용
            formatted_messages = []
            for msg in messages:
                # content는 이미 HTML 렌더링된 상태
                content = msg.get('content', '')
                formatted_messages.append({
                    'role': msg.get('role', 'unknown'),
                    'content': content,
                    'timestamp': msg.get('timestamp', '')
                })
            
            success = pdf_exporter.export_conversation_to_pdf(
                formatted_messages, 
                session.get('title', '대화')
            )
            
            if success:
                QMessageBox.information(self, '성공', 'PDF 내보내기가 완료되었습니다.')
            
        except Exception as e:
            logger.error(f"PDF 내보내기 오류: {e}")
            QMessageBox.critical(self, '오류', f'PDF 내보내기 실패: {str(e)}')
    
    def update_stats(self):
        """통계 정보 업데이트 - 비동기 처리"""
        QTimer.singleShot(0, self._update_stats_async)
    
    def _update_stats_async(self):
        """비동기 통계 업데이트"""
        try:
            stats = session_manager.get_session_stats()
            self.stats_label.setText(
                f"세션 {stats['total_sessions']}개 | "
                f"메시지 {stats['total_messages']}개 | "
                f"{stats['db_size_mb']} MB | "
                f"{stats['available_tools']}개"
            )
        except Exception as e:
            logger.error(f"통계 업데이트 오류: {e}")
            self.stats_label.setText("통계 로드 실패")
    
    def get_current_session_id(self) -> Optional[int]:
        """현재 선택된 세션 ID 반환"""
        return self.current_session_id
    
    def apply_theme(self):
        """테마 적용"""
        try:
            if theme_manager.use_material_theme:
                self._apply_material_theme()
            else:
                self._apply_default_theme()
        except Exception as e:
            logger.error(f"세션 패널 테마 적용 오류: {e}")
    
    def _apply_material_theme(self):
        """채팅창과 동일한 Material Design 테마 적용"""
        colors = theme_manager.material_manager.get_theme_colors()
        
        # 채팅창과 동일한 배경색 사용
        bg_color = colors.get('background', '#121212')
        text_color = colors.get('text_primary', '#ffffff')
        surface_color = colors.get('surface', '#1e1e1e')
        primary_color = colors.get('primary', '#bb86fc')
        secondary_color = colors.get('secondary', '#03dac6')
        
        # 전체 패널 스타일 - 채팅창과 동일한 배경
        panel_style = f"""
        SessionPanel {{
            background-color: {bg_color};
            color: {text_color};
            border: none;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        }}
        """
        
        # 헤더 라벨 스타일 - 테마별 대비색 적용
        is_dark = theme_manager.is_material_dark_theme()
        header_text_color = colors.get('on_primary', '#000000') if is_dark else '#ffffff'
        
        header_style = f"""
        QLabel {{
            color: {header_text_color};
            font-size: 16px;
            font-weight: 700;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 14px 18px;
            background-color: {primary_color};
            border: 2px solid {colors.get('primary_variant', '#3700b3')};
            border-radius: 12px;
            margin: 4px;
        }}
        """
        
        # 새로고침 버튼 - 고급스러운 디자인
        refresh_style = f"""
        QPushButton#refresh_button {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 {secondary_color}, stop:1 {colors.get('secondary_variant', '#018786')});
            color: {colors.get('on_secondary', '#000000')};
            border: 2px solid {colors.get('secondary_variant', '#018786')};
            border-radius: 22px;
            font-weight: 800;
            font-size: 24px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 0px;
            margin: 4px;
            qproperty-text: "♾️";
        }}
        QPushButton#refresh_button:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 {colors.get('secondary_variant', '#018786')}, stop:1 {secondary_color});
            transform: scale(1.05);
            border: 3px solid {primary_color};
        }}
        QPushButton#refresh_button:pressed {{
            background: {colors.get('secondary_variant', '#018786')};
            transform: scale(0.95);
        }}
        """
        
        # 검색 입력창 - Soft Shadow + Rounded Edge + Gradient Depth
        is_dark = theme_manager.is_material_dark_theme()
        shadow_color = "rgba(0,0,0,0.1)" if is_dark else "rgba(0,0,0,0.05)"
        
        # 검색창 배경은 테마 배경색, 테두리만 버튼 테마색
        
        search_style = f"""
        QLineEdit {{
            background: {bg_color};
            color: {text_color};
            border: 1px solid {colors.get('divider', '#333333')};
            border-radius: 18px;
            font-size: 15px;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 20px;
            margin: 6px;
            selection-background-color: {primary_color};
            selection-color: {colors.get('on_primary', '#ffffff')};
            transition: all 0.3s ease;
        }}
        QLineEdit:focus {{
            border: 1px solid {primary_color};
            background: {surface_color};
            transform: translateY(-1px);
        }}
        QLineEdit::placeholder {{
            color: {colors.get('text_secondary', '#b3b3b3')};
            opacity: 0.8;
        }}
        """
        
        # 리스트 위젯 - Soft Shadow + Rounded Edge + Gradient Depth
        shadow_color = "rgba(0,0,0,0.1)" if is_dark else "rgba(0,0,0,0.05)"
        
        list_style = f"""
        QListWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 {bg_color}, 
                stop:1 {surface_color});
            border: 1px solid {colors.get('divider', '#333333')};
            border-radius: 16px;
            padding: 12px;
            margin: 6px;
            outline: none;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        }}
        QListWidget::item {{
            border: none;
            padding: 0px;
            margin: 4px;
            border-radius: 12px;
            background: transparent;
        }}
        QListWidget::item:selected {{
            background: transparent;
            outline: none;
        }}
        QListWidget::item:hover {{
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: {colors.get('scrollbar_track', colors.get('surface', '#1e1e1e'))};
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
        """
        
        # 모든 버튼 공통 스타일 - Soft Shadow + Rounded Edge + Gradient Depth
        is_dark = theme_manager.is_material_dark_theme()
        shadow_color = "rgba(0,0,0,0.2)" if is_dark else "rgba(0,0,0,0.1)"
        shadow_hover = "rgba(0,0,0,0.3)" if is_dark else "rgba(0,0,0,0.15)"
        
        button_style = f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 {primary_color}, 
                stop:1 {colors.get('primary_variant', '#3700b3')});
            color: {colors.get('on_primary', '#000000')};
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
                stop:0 {colors.get('primary_variant', '#3700b3')}, 
                stop:1 {primary_color});
            transform: translateY(-2px);
        }}
        QPushButton:pressed {{
            background: {colors.get('primary_variant', '#3700b3')};
            transform: translateY(0px);
        }}
        """
        
        # 투명한 이모지 버튼 스타일 - 35% 증가
        manage_button_style = """
        QPushButton {
            background: transparent;
            border: none;
            font-size: 28px;
        }
        QPushButton:hover {
            background: transparent;
            font-size: 38px;
        }
        QPushButton:pressed {
            background: transparent;
            font-size: 26px;
        }
        QPushButton:disabled {
            background: transparent;
            opacity: 0.5;
        }
        """
        
        # 통계 라벨 스타일
        is_dark = theme_manager.is_material_dark_theme()
        stats_text_color = colors.get('text_secondary', '#b3b3b3') if is_dark else colors.get('text_primary', '#333333')
        
        stats_style = f"""
        QLabel#stats_label {{
            color: {stats_text_color};
            font-size: 12px;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 12px 20px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 {surface_color}, 
                stop:1 {bg_color});
            border: 1px solid {colors.get('divider', '#333333')};
            border-radius: 16px;
            margin: 6px;
        }}
        """
        
        # 스타일 적용
        self.setStyleSheet(panel_style)
        
        # 헤더 라벨에 스타일 적용
        if hasattr(self, 'header_label'):
            self.header_label.setStyleSheet(header_style)
        
        # 새로고침 버튼은 제거됨
        
        self.search_edit.setStyleSheet(search_style)
        self.session_list.setStyleSheet(list_style)
        # 모든 버튼에 동일한 스타일 적용
        if hasattr(self, 'new_session_btn'):
            self.new_session_btn.setStyleSheet(button_style)
        if hasattr(self, 'model_button'):
            self.model_button.setStyleSheet(button_style)
        if hasattr(self, 'template_button'):
            self.template_button.setStyleSheet(button_style)
        if hasattr(self, 'theme_button'):
            self.theme_button.setStyleSheet(button_style)
        self.rename_btn.setStyleSheet(manage_button_style)
        self.export_btn.setStyleSheet(manage_button_style)
        self.delete_btn.setStyleSheet(manage_button_style)
        # 통계 라벨에 스타일 적용
        if hasattr(self, 'stats_label'):
            self.stats_label.setStyleSheet(stats_style)
    
    def _apply_default_theme(self):
        """기본 테마 적용 - 라이트 테마용 대비색"""
        self.setStyleSheet("""
        SessionPanel {
            background-color: #f5f5f5;
            color: #333333;
            border-right: 1px solid #ddd;
        }
        QLabel {
            color: #333333;
        }
        QLineEdit {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #cccccc;
        }
        QLineEdit::placeholder {
            color: #999999;
        }
        QPushButton {
            background-color: #007acc;
            color: #ffffff;
            border: 1px solid #005a9e;
            border-radius: 8px;
            font-weight: 600;
            padding: 8px 12px;
        }
        QPushButton:hover {
            background-color: #005a9e;
        }
        """)
    
    def delete_session_by_id(self, session_id: int):
        """세션 ID로 삭제 (아이템에서 호출)"""
        session = session_manager.get_session(session_id)
        if not session:
            return
        
        reply = QMessageBox.question(
            self, "세션 삭제", 
            f"'{session['title']}' 세션을 삭제하시겠습니까?\n\n"
            f"메시지 {session['message_count']}개가 함께 삭제됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 먼저 UI에서 해당 아이템 제거
                self._remove_session_item(session_id)
                
                success = session_manager.delete_session(session_id)
                if success:
                    # 메인 윈도우의 현재 세션 ID도 초기화
                    if hasattr(self, 'main_window') and self.main_window:
                        if self.main_window.current_session_id == session_id:
                            self.main_window.current_session_id = None
                            self.main_window._auto_session_created = False
                    
                    if self.current_session_id == session_id:
                        self.current_session_id = None
                        self.rename_btn.setEnabled(False)
                        self.export_btn.setEnabled(False)
                        self.delete_btn.setEnabled(False)
                    
                    # 지연 새로고침
                    QTimer.singleShot(100, self.refresh_all_data)
                    QMessageBox.information(self, "성공", "세션이 삭제되었습니다.")
                else:
                    QMessageBox.warning(self, "실패", "세션 삭제에 실패했습니다.")
                    # 실패 시 다시 로드
                    self.load_sessions()
            except Exception as e:
                logger.error(f"세션 삭제 오류: {e}")
                QMessageBox.critical(self, "오류", f"세션 삭제 중 오류가 발생했습니다:\n{e}")
                # 오류 시 다시 로드
                self.load_sessions()
    
    def _remove_session_item(self, session_id: int):
        """안전하게 세션 아이템 제거"""
        try:
            for i in range(self.session_list.count()):
                item = self.session_list.item(i)
                if item:
                    widget = self.session_list.itemWidget(item)
                    if widget and hasattr(widget, 'session_id') and widget.session_id == session_id:
                        # 위젯 연결 해제
                        widget.clicked.disconnect()
                        widget.delete_requested.disconnect()
                        # 아이템 제거
                        self.session_list.takeItem(i)
                        # 위젯 삭제
                        widget.deleteLater()
                        break
        except Exception as e:
            logger.error(f"세션 아이템 제거 오류: {e}")
    
    def show_model_selector(self):
        """모델 선택기 표시 - 직접 구현"""
        try:
            from PyQt6.QtWidgets import QMenu
            from PyQt6.QtCore import QPoint
            from core.file_utils import load_config, save_last_model, load_last_model
            
            config = load_config()
            models = config.get('models', {})
            
            if not models:
                return
            
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 8px 16px;
                    border-radius: 2px;
                }
                QMenu::item:selected {
                    background-color: rgb(163,135,215);
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #444444;
                    margin: 4px 0px;
                }
            """)
            
            current_model = load_last_model()
            
            # 모델을 카테고리별로 분류
            categorized_models = self._categorize_models(models)
            
            # 카테고리별로 서브메뉴 생성
            for category, category_models in categorized_models.items():
                if not category_models:
                    continue
                    
                category_info = self._get_category_info(category)
                submenu = menu.addMenu(f"{category_info['emoji']} {category_info['name']} ({len(category_models)}개)")
                submenu.setStyleSheet(menu.styleSheet())
                
                # OpenRouter 카테고리는 카테고리별로 세분화
                if category == 'openrouter':
                    self._add_openrouter_category_submenus(submenu, category_models, current_model)
                else:
                    # 일반 카테고리는 그대로 표시
                    for model_name, model_config in sorted(category_models.items()):
                        model_emoji = self._get_model_emoji(model_name, model_config)
                        display_name = self._get_model_display_name(model_name, model_config)
                        
                        action = submenu.addAction(f"{model_emoji} {display_name}")
                        if model_name == current_model:
                            action.setText(f"✅ {display_name} (현재)")
                        def make_handler(model):
                            return lambda: self._select_model(model)
                        action.triggered.connect(make_handler(model_name))
            
            # 버튼 위치에서 메뉴 표시
            button_pos = self.model_button.mapToGlobal(QPoint(0, 0))
            menu.exec(QPoint(button_pos.x(), button_pos.y() + self.model_button.height()))
            
        except Exception as e:
            print(f"모델 선택기 표시 오류: {e}")
    
    def _select_model(self, model_name: str):
        """모델 선택"""
        try:
            from core.file_utils import save_last_model
            save_last_model(model_name)
            # 모델명이 길면 줄임
            display_name = model_name
            if len(display_name) > 15:
                display_name = display_name[:12] + "..."
            self.model_button.setText(f"🤖 {display_name}")
            self.model_button.setToolTip(f"현재 모델: {model_name}")
            
            print(f"모델 선택됨: {model_name}")
        except Exception as e:
            print(f"모델 선택 오류: {e}")
    
    def show_template_manager(self):
        """템플릿 관리자 표시"""
        try:
            from ui.template_dialog import TemplateDialog
            dialog = TemplateDialog(self)
            dialog.template_selected.connect(self._on_template_selected)
            dialog.exec()
        except Exception as e:
            print(f"템플릿 관리자 표시 오류: {e}")
    
    def _on_template_selected(self, content: str):
        """템플릿 선택 시 채팅창 입력창에 내용 입력"""
        try:
            # 메인 윈도우에서 채팅 위젯 찾기
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, 'chat_widget'):
                chat_widget = main_window.chat_widget
                if hasattr(chat_widget, 'input_text'):
                    # 기존 내용에 추가하거나 대체
                    current_text = chat_widget.input_text.toPlainText()
                    if current_text.strip():
                        # 기존 내용이 있으면 줄바꿈 후 추가
                        chat_widget.input_text.setPlainText(current_text + "\n" + content)
                    else:
                        # 비어있으면 바로 입력
                        chat_widget.input_text.setPlainText(content)
                    
                    # 커서를 끝으로 이동
                    cursor = chat_widget.input_text.textCursor()
                    cursor.movePosition(cursor.MoveOperation.End)
                    chat_widget.input_text.setTextCursor(cursor)
                    
                    # 입력창에 포커스
                    chat_widget.input_text.setFocus()
                    
                    print(f"템플릿 내용이 채팅창에 입력되었습니다: {content[:50]}...")
                else:
                    print("채팅 위젯에 input_text가 없습니다")
            else:
                print("메인 윈도우 또는 채팅 위젯을 찾을 수 없습니다")
        except Exception as e:
            print(f"템플릿 선택 처리 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def show_theme_selector(self):
        """테마 선택기 표시 - Light/Dark/Special 구분"""
        try:
            from PyQt6.QtWidgets import QMenu
            from PyQt6.QtCore import QPoint
            
            menu = QMenu(self)
            menu.setTitle("테마 선택")
            
            # 테마 데이터 가져오기
            themes = theme_manager.material_manager.themes
            current_theme = theme_manager.material_manager.current_theme_key
            
            # 타입별로 테마 분류
            light_themes = {}
            dark_themes = {}
            special_themes = {}
            
            for theme_key, theme_data in themes.items():
                theme_type = theme_data.get('type', 'dark')
                theme_name = theme_data.get('name', theme_key)
                
                if theme_type == 'light':
                    light_themes[theme_key] = theme_name
                elif theme_type == 'special':
                    special_themes[theme_key] = theme_name
                else:
                    dark_themes[theme_key] = theme_name
            
            # Light 테마 서브메뉴
            if light_themes:
                light_menu = menu.addMenu("☀️ Light Themes")
                for theme_key, theme_name in light_themes.items():
                    action = light_menu.addAction(f"🎨 {theme_name}")
                    action.setCheckable(True)
                    action.triggered.connect(lambda checked, key=theme_key: self._select_theme(key))
                    if theme_key == current_theme:
                        action.setChecked(True)
            
            # Dark 테마 서브메뉴
            if dark_themes:
                dark_menu = menu.addMenu("🌙 Dark Themes")
                for theme_key, theme_name in dark_themes.items():
                    action = dark_menu.addAction(f"🎨 {theme_name}")
                    action.setCheckable(True)
                    action.triggered.connect(lambda checked, key=theme_key: self._select_theme(key))
                    if theme_key == current_theme:
                        action.setChecked(True)
            
            # Special 테마 서브메뉴
            if special_themes:
                special_menu = menu.addMenu("✨ Special Themes")
                for theme_key, theme_name in special_themes.items():
                    action = special_menu.addAction(f"🎨 {theme_name}")
                    action.setCheckable(True)
                    action.triggered.connect(lambda checked, key=theme_key: self._select_theme(key))
                    if theme_key == current_theme:
                        action.setChecked(True)
            
            # 버튼 위치에서 메뉴 표시
            button_pos = self.theme_button.mapToGlobal(QPoint(0, 0))
            menu.exec(QPoint(button_pos.x(), button_pos.y() + self.theme_button.height()))
            
        except Exception as e:
            print(f"테마 선택기 표시 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def _select_theme(self, theme_key: str):
        """테마 선택"""
        try:
            print(f"테마 선택 시도: {theme_key}")
            
            # 메인 윈도우 찾기
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, '_change_theme'):
                print(f"메인 윈도우에서 테마 변경 호출")
                # QTimer를 사용해 즉시 실행
                QTimer.singleShot(0, lambda: main_window._change_theme(theme_key))
            else:
                print("메인 윈도우를 찾을 수 없거나 _change_theme 메서드가 없음")
                # 직접 테마 설정
                theme_manager.material_manager.set_theme(theme_key)
                self.update_theme()
            
            print(f"테마 선택 완료: {theme_key}")
        except Exception as e:
            print(f"테마 선택 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def _categorize_models(self, models):
        """모델을 카테고리별로 분류"""
        categories = {
            'openrouter': {},
            'google': {},
            'perplexity': {},
            'pollinations': {},
            'other': {}
        }
        
        for model_name, model_config in models.items():
            api_key = model_config.get('api_key', '')
            if not (api_key and api_key != 'none'):
                continue
                
            provider = model_config.get('provider', '')
            
            if provider == 'openrouter':
                categories['openrouter'][model_name] = model_config
            elif provider == 'google':
                categories['google'][model_name] = model_config
            elif provider == 'perplexity':
                categories['perplexity'][model_name] = model_config
            elif provider == 'pollinations':
                categories['pollinations'][model_name] = model_config
            else:
                categories['other'][model_name] = model_config
        
        return categories
    
    def _get_category_info(self, category):
        """카테고리 정보 반환"""
        category_map = {
            'openrouter': {'emoji': '🔀', 'name': 'OpenRouter'},
            'google': {'emoji': '🔍', 'name': 'Google Gemini'},
            'perplexity': {'emoji': '🔬', 'name': 'Perplexity'},
            'pollinations': {'emoji': '🌸', 'name': 'Pollinations'},
            'other': {'emoji': '🤖', 'name': '기타 모델'}
        }
        return category_map.get(category, {'emoji': '🤖', 'name': category})
    
    def _get_model_emoji(self, model_name, model_config):
        """모델별 이모지 반환"""
        if 'image' in model_name.lower():
            return '🎨'
        elif model_config.get('category') == 'reasoning':
            return '🧠'
        elif model_config.get('category') == 'coding':
            return '💻'
        elif model_config.get('category') == 'multimodal':
            return '🖼️'
        elif model_config.get('category') == 'meta_llama':
            return '🦙'
        elif 'gemini' in model_name.lower():
            return '💎'
        elif 'sonar' in model_name.lower():
            return '🔬'
        elif 'pollinations' in model_name.lower():
            return '🌸'
        else:
            return '🤖'
    
    def _get_model_display_name(self, model_name, model_config):
        """모델 표시명 생성"""
        description = model_config.get('description', '')
        if description:
            # 이모지 제거하고 간단한 설명만 추출
            clean_desc = description.split(' - ')[-1] if ' - ' in description else description
            clean_desc = ''.join(char for char in clean_desc if not char.startswith(''))
            return f"{model_name.split('/')[-1]} - {clean_desc[:30]}..."
        return model_name
    
    def _add_openrouter_category_submenus(self, parent_menu, models, current_model):
        """오픈라우터 모델을 카테고리별로 세분화"""
        # 모델을 카테고리별로 그룹화
        category_groups = {
            'reasoning': {},
            'coding': {},
            'multimodal': {},
            'meta_llama': {}
        }
        
        for model_name, model_config in models.items():
            category = model_config.get('category', 'other')
            if category in category_groups:
                category_groups[category][model_name] = model_config
        
        # 카테고리별 서브메뉴 생성
        category_info = {
            'reasoning': {'emoji': '🧠', 'name': '추론 특화'},
            'coding': {'emoji': '💻', 'name': '코딩 특화'},
            'multimodal': {'emoji': '🖼️', 'name': '멀티모달'},
            'meta_llama': {'emoji': '🦙', 'name': 'Meta Llama'}
        }
        
        for category, category_models in category_groups.items():
            if not category_models:
                continue
                
            info = category_info[category]
            category_submenu = parent_menu.addMenu(f"{info['emoji']} {info['name']} ({len(category_models)}개)")
            category_submenu.setStyleSheet(parent_menu.styleSheet())
            
            for model_name, model_config in sorted(category_models.items()):
                display_name = self._get_improved_display_name(model_name, model_config)
                action = category_submenu.addAction(f"🤖 {display_name}")
                if model_name == current_model:
                    action.setText(f"✅ {display_name} (현재)")
                def make_handler(model):
                    return lambda: self._select_model(model)
                action.triggered.connect(make_handler(model_name))
    
    def _get_improved_display_name(self, model_name, model_config):
        """개선된 모델 표시명 생성"""
        description = model_config.get('description', '')
        if description:
            # 이모지 제거하고 간단한 설명만 추출
            clean_desc = description.split(' - ')[-1] if ' - ' in description else description
            import re
            clean_desc = re.sub(r'[🎨💻🧠🖼️🦙🔍🔬🌸🤖⚡🥉💎🎯]', '', clean_desc).strip()
            
            # 모델명 단순화
            simple_name = model_name.split('/')[-1].replace(':free', '').replace('-instruct', '')
            
            # 무료 모델 표시
            free_indicator = ' 🆓' if ':free' in model_name else ''
            
            return f"{simple_name}{free_indicator} - {clean_desc[:25]}..."
        return model_name.split('/')[-1]
    
    def _find_main_window(self):
        """메인 윈도우 찾기"""
        widget = self
        while widget:
            if widget.__class__.__name__ == 'MainWindow':
                return widget
            widget = widget.parent()
        return None
    

    
    def on_stats_label_click(self, event):
        """통계 라벨 클릭 처리 - 마지막 숫자 영역만 반응"""
        text = self.stats_label.text()
        if "개" in text:
            label_width = self.stats_label.width()
            click_x = event.position().x()
            
            # 텍스트의 마지막 1/4 영역에서 클릭한 경우만 반응
            if click_x > label_width * 0.75:
                self.show_tools_detail()
    
    def show_tools_detail(self):
        """MCP 서버 관리 화면 열기"""
        try:
            # 메인 윈도우 찾기
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, 'show_mcp_dialog'):
                main_window.show_mcp_dialog()
            else:
                # 직접 MCP 대화상자 열기
                from ui.mcp_dialog import MCPDialog
                dialog = MCPDialog(self)
                dialog.exec()
            
        except Exception as e:
            logger.error(f"MCP 서버 관리 화면 열기 오류: {e}")
            QMessageBox.warning(self, "오류", f"MCP 서버 관리 화면을 열 수 없습니다:\n{e}")
    

    
    def mouseMoveEvent(self, event):
        """마우스 이동 시 도구 영역에서만 손모양 커서"""
        if hasattr(self, 'stats_label'):
            stats_rect = self.stats_label.geometry()
            if stats_rect.contains(event.position().toPoint()):
                text = self.stats_label.text()
                if "개" in text:
                    # 텍스트의 마지막 1/4 영역에서만 손모양 커서
                    relative_x = event.position().x() - stats_rect.x()
                    if relative_x > stats_rect.width() * 0.75:
                        self.setCursor(Qt.CursorShape.PointingHandCursor)
                    else:
                        self.setCursor(Qt.CursorShape.ArrowCursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)
    
    def update_theme(self):
        """테마 업데이트"""
        self.apply_theme()
        # 모든 세션 아이템에도 테마 적용
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            widget = self.session_list.itemWidget(item)
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme()
    def _remove_session_item(self, session_id: int):
        """안전하게 세션 아이템 제거"""
        try:
            for i in range(self.session_list.count()):
                item = self.session_list.item(i)
                if item:
                    widget = self.session_list.itemWidget(item)
                    if widget and hasattr(widget, 'session_id') and widget.session_id == session_id:
                        # 위젯 연결 해제
                        try:
                            widget.clicked.disconnect()
                            widget.delete_requested.disconnect()
                        except:
                            pass
                        # 아이템 제거
                        self.session_list.takeItem(i)
                        # 위젯 삭제
                        widget.deleteLater()
                        break
        except Exception as e:
            logger.error(f"세션 아이템 제거 오류: {e}")