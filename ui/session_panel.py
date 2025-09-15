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
        
        # 상단: 제목과 삭제 버튼
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 제목
        self.title_label = QLabel(self.session_data['title'])
        self.title_label.setWordWrap(True)
        header_layout.addWidget(self.title_label, 1)
        
        # 삭제 버튼
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.session_id))
        self.delete_btn.hide()  # 기본적으로 숨김
        header_layout.addWidget(self.delete_btn)
        
        layout.addLayout(header_layout)
        
        # 카테고리 표시 제거 (불필요한 하늘색 라인)
        
        # 하단: 메시지 수와 시간
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(8)
        
        # 메시지 수
        self.message_count_label = QLabel(f"💬 {self.session_data['message_count']}")
        footer_layout.addWidget(self.message_count_label)
        
        footer_layout.addStretch()
        
        # 마지막 사용 시간
        last_used = self.session_data.get('last_used_at', '')
        if last_used:
            try:
                dt = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                time_str = dt.strftime("%m/%d %H:%M")
                self.time_label = QLabel(time_str)
                footer_layout.addWidget(self.time_label)
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
                    text-shadow: 1px 1px 2px {shadow_color};
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            
            # 메시지 수 스타일 - 테마별 배경색 적용
            self.message_count_label.setStyleSheet(f"""
                QLabel {{
                    color: #ffffff;
                    font-size: 13px;
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
            
            # 삭제 버튼 스타일
            self.delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background: #dc2626;
                    color: #ffffff;
                    border: 1px solid {colors.get('divider', '#333333')};
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: #b91c1c;
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
        """UI 설정 - 패딩/마진 최소화, 가독성 최우선"""
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)  # 최소 마진
        layout.setSpacing(6)  # 적절한 간격
        
        # 헤더 - 더 큰 폰트와 명확한 아이콘
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 4, 4, 4)
        header_label = QLabel("💬 Sessions")
        header_font = QFont("SF Pro Display", 16, QFont.Weight.Bold)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        
        # 새로고침 버튼 - 더 큰 버튼
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setToolTip("새로고침")
        refresh_btn.clicked.connect(self.load_sessions)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # 검색 - 더 큰 입력창
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search sessions...")
        self.search_edit.textChanged.connect(self.search_sessions)
        self.search_edit.setMinimumHeight(44)  # 더 큰 입력창
        layout.addWidget(self.search_edit)
        
        # 세션 목록 - 더 큰 리스트
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
        
        # 하단 버튼들 - 더 큰 버튼들
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(2, 2, 2, 2)
        button_layout.setSpacing(6)
        
        # 새 세션 버튼 - 더 큰 버튼
        self.new_session_btn = QPushButton("➕ New Session")
        self.new_session_btn.setMinimumHeight(44)
        self.new_session_btn.clicked.connect(self.create_new_session)
        button_layout.addWidget(self.new_session_btn)
        
        # 세션 관리 버튼들 - 더 큰 버튼들
        manage_layout = QHBoxLayout()
        manage_layout.setSpacing(4)
        
        self.rename_btn = QPushButton("✏️")
        self.rename_btn.setToolTip("세션 이름 변경")
        self.rename_btn.setEnabled(False)
        self.rename_btn.setMinimumHeight(40)
        self.rename_btn.clicked.connect(self.rename_session)
        
        self.export_btn = QPushButton("📤")
        self.export_btn.setToolTip("세션 내보내기")
        self.export_btn.setEnabled(False)
        self.export_btn.setMinimumHeight(40)
        self.export_btn.clicked.connect(self.export_session)
        
        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setToolTip("세션 삭제")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.clicked.connect(self.delete_session)
        
        manage_layout.addWidget(self.rename_btn)
        manage_layout.addWidget(self.export_btn)
        manage_layout.addWidget(self.delete_btn)
        button_layout.addLayout(manage_layout)
        
        layout.addLayout(button_layout)
        
        # 통계 정보 - 더 큰 박스
        self.stats_label = QLabel()
        # 통계 라벨 스타일은 apply_theme에서 설정
        self.stats_label.setMinimumHeight(36)
        self.stats_label.setObjectName("stats_label")  # 스타일 적용을 위한 이름 설정
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
        dialog.resize(300, 200)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"세션 '{session['title']}'를 내보내기:"))
        
        # 라디오 버튼 그룹
        button_group = QButtonGroup()
        
        text_radio = QRadioButton("텍스트 파일 (.txt)")
        html_radio = QRadioButton("HTML 파일 (.html)")
        json_radio = QRadioButton("JSON 파일 (.json)")
        md_radio = QRadioButton("Markdown 파일 (.md)")
        
        text_radio.setChecked(True)  # 기본 선택
        
        button_group.addButton(text_radio, 0)
        button_group.addButton(html_radio, 1)
        button_group.addButton(json_radio, 2)
        button_group.addButton(md_radio, 3)
        
        layout.addWidget(text_radio)
        layout.addWidget(html_radio)
        layout.addWidget(json_radio)
        layout.addWidget(md_radio)
        
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
            # 파일 형식 매핑
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
        
        # 새로고침 버튼 - 채팅창 버튼과 동일
        refresh_style = f"""
        QPushButton {{
            background-color: {secondary_color};
            color: {colors.get('on_secondary', '#000000')};
            border: 2px solid {colors.get('secondary_variant', '#018786')};
            border-radius: 14px;
            font-weight: 700;
            font-size: 16px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 8px;
            margin: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors.get('secondary_variant', '#018786')};
        }}
        """
        
        # 검색 입력창 - 테마별 대비색 적용
        is_dark = theme_manager.is_material_dark_theme()
        input_text_color = text_color if is_dark else colors.get('text_primary', '#000000')
        placeholder_color = colors.get('text_secondary', '#b3b3b3') if is_dark else '#999999'
        
        search_style = f"""
        QLineEdit {{
            background-color: {surface_color};
            color: {input_text_color};
            border: 1px solid {colors.get('divider', '#333333')};
            border-radius: 12px;
            font-size: 15px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 18px;
            margin: 4px;
            selection-background-color: {primary_color};
        }}
        QLineEdit:focus {{
            border-color: {primary_color};
        }}
        QLineEdit::placeholder {{
            color: {placeholder_color};
        }}
        """
        
        # 리스트 위젯 - 채팅창과 동일한 배경
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
            background: {colors.get('surface', '#1e1e1e')};
            width: 12px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background: {primary_color};
            border-radius: 6px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {colors.get('primary_variant', '#3700b3')};
        }}
        """
        
        # 새 세션 버튼 - 채팅창 전송 버튼과 동일
        button_style = f"""
        QPushButton {{
            background-color: {primary_color};
            color: {colors.get('on_primary', '#000000')};
            border: 2px solid {colors.get('primary_variant', '#3700b3')};
            border-radius: 14px;
            font-weight: 800;
            font-size: 18px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 12px 16px;
            margin: 4px;
        }}
        QPushButton:hover {{
            background-color: {colors.get('primary_variant', '#3700b3')};
        }}
        """
        
        # 관리 버튼들 - 채팅창 업로드 버튼과 동일
        manage_button_style = f"""
        QPushButton {{
            background-color: {secondary_color};
            color: {colors.get('on_secondary', '#000000')};
            border: 2px solid {colors.get('secondary_variant', '#018786')};
            border-radius: 14px;
            font-weight: 700;
            font-size: 16px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            padding: 8px 12px;
            margin: 2px;
        }}
        QPushButton:hover {{
            background-color: {colors.get('secondary_variant', '#018786')};
        }}
        QPushButton:disabled {{
            background-color: {surface_color};
            color: {colors.get('text_secondary', '#b3b3b3')};
            border-color: {colors.get('divider', '#333333')};
        }}
        """
        
        # 통계 라벨 스타일 - 테마별 대비색 적용
        is_dark = theme_manager.is_material_dark_theme()
        stats_text_color = colors.get('text_secondary', '#b3b3b3') if is_dark else colors.get('text_primary', '#333333')
        
        stats_style = f"""
        QLabel {{
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
        
        # 헤더 라벨 찾아서 스타일 적용
        for child in self.findChildren(QLabel):
            if "Sessions" in child.text() or "세션" in child.text():
                child.setStyleSheet(header_style)
                break
        
        # 새로고침 버튼 찾아서 스타일 적용
        for child in self.findChildren(QPushButton):
            if child.toolTip() == "새로고침":
                child.setStyleSheet(refresh_style)
                break
        
        self.search_edit.setStyleSheet(search_style)
        self.session_list.setStyleSheet(list_style)
        self.new_session_btn.setStyleSheet(button_style)
        self.rename_btn.setStyleSheet(manage_button_style)
        self.export_btn.setStyleSheet(manage_button_style)
        self.delete_btn.setStyleSheet(manage_button_style)
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
    
    def update_theme(self):
        """테마 업데이트"""
        self.apply_theme()
        # 모든 세션 아이템에도 테마 적용
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            widget = self.session_list.itemWidget(item)
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme()