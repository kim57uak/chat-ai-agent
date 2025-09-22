"""
Session Management Panel
채팅창 왼쪽에 표시되는 세션 관리 패널
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QLineEdit, QDialog, QDialogButtonBox,
    QMessageBox, QMenu, QInputDialog, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
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
        """UI 설정"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # 상단: 제목과 삭제 버튼 - 정렬 개선
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 2, 2, 2)
        header_layout.setSpacing(8)
        
        # 제목
        self.title_label = QLabel(self.session_data['title'])
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.title_label, 1)
        
        # 삭제 버튼 - 고급스러운 디자인
        self.delete_btn = QPushButton()
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.session_id))
        self.delete_btn.hide()  # 기본적으로 숨김
        self.delete_btn.setObjectName("delete_button")
        header_layout.addWidget(self.delete_btn, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addLayout(header_layout)
        
        # 카테고리 표시 제거 (불필요한 하늘색 라인)
        
        # 하단: 메시지 수와 시간 - 정렬 개선
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(2, 2, 2, 2)
        footer_layout.setSpacing(12)
        
        # 메시지 수 - 아이콘 정렬
        self.message_count_label = QLabel(f"💬 {self.session_data['message_count']}")
        self.message_count_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.message_count_label.setStyleSheet("font-size: 16px;")
        footer_layout.addWidget(self.message_count_label, 0, Qt.AlignmentFlag.AlignLeft)
        
        footer_layout.addStretch()
        
        # 마지막 사용 시간 - 정렬 개선
        last_used = self.session_data.get('last_used_at', '')
        if last_used:
            try:
                dt = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                time_str = dt.strftime("%m/%d %H:%M")
                self.time_label = QLabel(time_str)
                self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                footer_layout.addWidget(self.time_label, 0, Qt.AlignmentFlag.AlignRight)
            except:
                pass
        
        layout.addLayout(footer_layout)
        self.setLayout(layout)
    
    def apply_theme(self):
        """현대적인 Material Design 테마 적용 - 대비 개선"""
        if theme_manager.use_material_theme:
            colors = theme_manager.material_manager.get_theme_colors()
            is_dark = theme_manager.is_material_dark_theme()
            
            # 테마별 대비 색상 설정
            if is_dark:
                title_color = '#ffffff'
                message_bg = '#4f46e5'
                time_bg = '#374151'
                shadow_color = 'rgba(0,0,0,1.0)'
            else:
                title_color = '#000000'
                message_bg = '#1976d2'
                time_bg = '#6b7280'
                shadow_color = 'rgba(255,255,255,1.0)'
            
            # 제목 스타일 - 테마별 대비색 적용
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: {title_color};
                    font-size: 16px;
                    font-weight: 700;
                    line-height: 1.2;
                    background: transparent;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            
            # 메시지 수 스타일 - 테마별 배경색 적용
            self.message_count_label.setStyleSheet(f"""
                QLabel {{
                    color: #ffffff;
                    font-size: 16px;
                    font-weight: 700;
                    padding: 4px 8px;
                    background: {message_bg};
                    border-radius: 8px;
                    border: 1px solid {colors.get('divider', '#333333')};
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                }}
            """)
            
            # 시간 스타일 - 테마별 배경색 적용
            if hasattr(self, 'time_label'):
                self.time_label.setStyleSheet(f"""
                    QLabel {{
                        color: #ffffff;
                        font-size: 12px;
                        font-weight: 600;
                        padding: 2px 6px;
                        background: {time_bg};
                        border-radius: 6px;
                        border: 1px solid {colors.get('divider', '#333333')};
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                    }}
                """)
            
            # 삭제 버튼 스타일 - 고급스러운 디자인
            self.delete_btn.setStyleSheet(f"""
                QPushButton#delete_button {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 #dc2626, stop:1 #b91c1c);
                    color: #ffffff;
                    border: 2px solid #b91c1c;
                    border-radius: 14px;
                    font-size: 20px;
                    font-weight: 800;
                    qproperty-text: "✖️";
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                }}
                QPushButton#delete_button:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 #b91c1c, stop:1 #dc2626);
                    border: 2px solid #dc2626;
                    transform: scale(1.1);
                }}
                QPushButton#delete_button:pressed {{
                    background: #991b1b;
                    transform: scale(0.9);
                }}
            """)
            
            # 아이템 전체 스타일
            self.update_item_style(colors)
    
    def update_item_style(self, colors):
        """테마별 대비색을 고려한 아이템 스타일"""
        is_dark = theme_manager.is_material_dark_theme()
        
        if self.is_selected:
            # 선택된 상태
            selected_bg = colors.get('primary', '#4f46e5')
            selected_border = colors.get('primary_variant', '#3700b3')
            self.setStyleSheet(f"""
                SessionListItem {{
                    background: {selected_bg};
                    border: 2px solid {selected_border};
                    border-radius: 8px;
                    margin: 2px;
                }}
            """)
        else:
            # 기본 상태 - 테마별 배경색
            if is_dark:
                item_bg = '#374151'
                item_border = '#6b7280'
                hover_bg = '#4b5563'
                hover_border = '#9ca3af'
            else:
                item_bg = '#e5e7eb'
                item_border = '#d1d5db'
                hover_bg = '#d1d5db'
                hover_border = '#9ca3af'
            
            self.setStyleSheet(f"""
                SessionListItem {{
                    background: {item_bg};
                    border: 1px solid {item_border};
                    border-radius: 8px;
                    margin: 2px;
                }}
                SessionListItem:hover {{
                    background: {hover_bg};
                    border: 2px solid {hover_border};
                }}
            """)
    
    def set_selected(self, selected: bool):
        """선택 상태 설정"""
        self.is_selected = selected
        if theme_manager.use_material_theme:
            colors = theme_manager.material_manager.get_theme_colors()
            self.update_item_style(colors)
    
    def enterEvent(self, event):
        """마우스 진입 시 삭제 버튼 표시"""
        self.delete_btn.show()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """마우스 벗어날 시 삭제 버튼 숨김"""
        self.delete_btn.hide()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.session_id)
        super().mousePressEvent(event)


class SessionPanel(QWidget):
    """세션 관리 패널"""
    
    session_selected = pyqtSignal(int)  # session_id
    session_created = pyqtSignal(int)   # session_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_session_id = None
        self.setup_ui()
        self.load_sessions()
        
        # 자동 새로고침 타이머
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_sessions)
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
        top_buttons_layout.addWidget(self.theme_button)
        
        layout.addLayout(top_buttons_layout)
        
        # 구분선
        separator = QLabel()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #666666; margin: 8px 0px;")
        layout.addWidget(separator)
        
        # 세션 검색 (세션 리스트 바로 위로 이동)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search sessions...")
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
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        self.setMinimumWidth(280)  # 최소 너비 증가
        self.setMaximumWidth(350)  # 최대 너비 설정
        
        # 테마 적용
        self.apply_theme()
        
        # 메인 윈도우 참조 초기화
        self.main_window = None
        
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
                
                self.load_sessions()
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
                    self.load_sessions()
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
                    self.load_sessions()
                    QMessageBox.information(self, "성공", "세션이 삭제되었습니다.")
                else:
                    QMessageBox.warning(self, "실패", "세션 삭제에 실패했습니다.")
                    
            except Exception as e:
                logger.error(f"세션 삭제 오류: {e}")
                QMessageBox.critical(self, "오류", f"세션 삭제 중 오류가 발생했습니다:\n{e}")
    
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
        """통계 정보 업데이트"""
        try:
            stats = session_manager.get_session_stats()
            self.stats_label.setText(
                f"📊 세션 {stats['total_sessions']}개 | "
                f"메시지 {stats['total_messages']}개"
            )
        except Exception as e:
            logger.error(f"통계 업데이트 오류: {e}")
            self.stats_label.setText("📊 통계 로드 실패")
    
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
        
        # 검색 입력창 - True Gray 테마 특별 처리 (채팅창과 동일)
        is_dark = theme_manager.is_material_dark_theme()
        
        # True Gray 테마 감지 및 특별 처리
        if colors.get('primary') == '#6B7280':  # True Gray 테마
            input_bg_color = '#FFFFFF'
            input_text_color = '#374151'
            input_border_color = colors.get('divider', '#E5E7EB')
            placeholder_color = '#9CA3AF'
            selection_text_color = '#FFFFFF'
        else:
            input_bg_color = surface_color
            input_text_color = text_color if is_dark else colors.get('text_primary', '#000000')
            input_border_color = colors.get('divider', '#333333')
            placeholder_color = colors.get('text_secondary', '#b3b3b3') if is_dark else '#999999'
            selection_text_color = colors.get('on_primary', '#000000')
        
        search_style = f"""
        QLineEdit {{
            background-color: {input_bg_color};
            color: {input_text_color};
            border: 1px solid {input_border_color};
            border-radius: 12px;
            font-size: 15px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 18px;
            margin: 4px;
            selection-background-color: {primary_color};
            selection-color: {selection_text_color};
        }}
        QLineEdit:focus {{
            border-color: {primary_color};
            border-width: 2px;
        }}
        QLineEdit::placeholder {{
            color: {placeholder_color};
        }}
        """
        
        # 리스트 위젯 - 채팅창과 동일한 배경 및 스크롤바
        list_style = f"""
        QListWidget {{
            background-color: {bg_color};
            border: 1px solid {colors.get('divider', '#333333')};
            border-radius: 12px;
            padding: 8px;
            margin: 4px;
            outline: none;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        }}
        QListWidget::item {{
            border: none;
            padding: 0px;
            margin: 2px;
            border-radius: 8px;
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
            background: {colors.get('scrollbar', colors.get('text_secondary', '#b3b3b3'))};
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
        
        # 모든 버튼 공통 스타일 - 동일한 look and feel
        button_style = f"""
        QPushButton {{
            background-color: {primary_color};
            color: {colors.get('on_primary', '#000000')};
            border: 2px solid {colors.get('primary_variant', '#3700b3')};
            border-radius: 14px;
            font-weight: 800;
            font-size: 16px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 12px 16px;
            margin: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors.get('primary_variant', '#3700b3')};
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
        
        # 통계 라벨 스타일 - 테마별 대비색 적용
        is_dark = theme_manager.is_material_dark_theme()
        stats_text_color = colors.get('text_secondary', '#b3b3b3') if is_dark else colors.get('text_primary', '#333333')
        
        stats_style = f"""
        QLabel#stats_label {{
            color: {stats_text_color};
            font-size: 12px;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 8px 16px;
            background-color: {surface_color};
            border: 2px solid {colors.get('divider', '#333333')};
            border-radius: 10px;
            margin: 4px;
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
                    self.load_sessions()
                    QMessageBox.information(self, "성공", "세션이 삭제되었습니다.")
                else:
                    QMessageBox.warning(self, "실패", "세션 삭제에 실패했습니다.")
            except Exception as e:
                logger.error(f"세션 삭제 오류: {e}")
                QMessageBox.critical(self, "오류", f"세션 삭제 중 오류가 발생했습니다:\n{e}")
    
    def show_model_selector(self):
        """모델 선택기 표시 - 계층형"""
        try:
            from PyQt6.QtWidgets import QMenu
            from PyQt6.QtCore import QPoint
            from core.file_utils import load_config
            
            menu = QMenu(self)
            config = load_config()
            models = config.get('models', {})
            
            # 계층형 메뉴 구성
            providers = {}
            for model_name, model_config in models.items():
                provider = model_config.get('provider', 'unknown')
                if provider not in providers:
                    providers[provider] = []
                providers[provider].append(model_name)
            
            # 각 제공자별로 서브메뉴 생성
            for provider, model_list in providers.items():
                provider_menu = menu.addMenu(f"🏢 {provider.title()}")
                for model_name in model_list:
                    action = provider_menu.addAction(f"🤖 {model_name}")
                    action.triggered.connect(lambda checked, m=model_name: self._select_model(m))
            
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
            dialog.exec()
        except Exception as e:
            print(f"템플릿 관리자 표시 오류: {e}")
    
    def show_theme_selector(self):
        """테마 선택기 표시 - 계층구조"""
        try:
            from PyQt6.QtWidgets import QMenu
            from PyQt6.QtCore import QPoint
            
            menu = QMenu(self)
            available_themes = theme_manager.get_available_material_themes()
            current_theme = theme_manager.material_manager.current_theme_key
            
            # theme.json에서 테마 분류 정보 로드
            theme_categories = theme_manager.material_manager.get_theme_categories()
            
            # 각 분류별로 서브메뉴 생성
            for category_key, category_data in theme_categories.items():
                if not category_data.get('themes'):  # 빈 분류는 건너뛰기
                    continue
                    
                category_menu = menu.addMenu(category_data.get('name', category_key.title()))
                
                for theme_key in category_data['themes']:
                    if theme_key in available_themes:
                        theme_name = available_themes[theme_key]
                        action = category_menu.addAction(f"🎨 {theme_name}")
                        action.setCheckable(True)
                        action.triggered.connect(lambda checked, key=theme_key: self._select_theme(key))
                        
                        # 현재 테마 체크 표시
                        if theme_key == current_theme:
                            action.setChecked(True)
            
            # 버튼 위치에서 메뉴 표시
            button_pos = self.theme_button.mapToGlobal(QPoint(0, 0))
            menu.exec(QPoint(button_pos.x(), button_pos.y() + self.theme_button.height()))
            
        except Exception as e:
            print(f"테마 선택기 표시 오류: {e}")
    
    def _select_theme(self, theme_key: str):
        """테마 선택"""
        try:
            # 테마 설정
            theme_manager.material_manager.set_theme(theme_key)
            
            # 메인 윈도우에 테마 변경 알림
            if hasattr(self, 'main_window') and self.main_window:
                self.main_window._change_theme(theme_key)
            
            print(f"테마 선택됨: {theme_key}")
        except Exception as e:
            print(f"테마 선택 오류: {e}")
    
    def update_theme(self):
        """테마 업데이트"""
        self.apply_theme()
        # 모든 세션 아이템에도 테마 적용
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            widget = self.session_list.itemWidget(item)
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme()