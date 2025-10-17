"""
Session Management Panel (Refactored)
세션 관리 패널 - 리팩토링된 버전
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QListWidget, QListWidgetItem, QLabel, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from typing import Optional

from core.session import session_manager
from ui.styles.theme_manager import theme_manager
from core.logging import get_logger

from .session_list_item import SessionListItem
from .session_actions import SessionActions
from .session_exporter import SessionExporter
from .theme_applier import ThemeApplier
from .model_selector import ModelSelector
from .theme_selector import ThemeSelector
from .template_handler import TemplateHandler

logger = get_logger("session_panel")


class SessionPanel(QWidget):
    """세션 관리 패널 - 컴포넌트 조합"""

    session_selected = pyqtSignal(int)  # session_id
    session_created = pyqtSignal(int)  # session_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_session_id = None
        self._auto_selection_done = False
        
        # 컴포넌트 초기화
        self.actions = SessionActions(self)
        self.exporter = SessionExporter(self)
        self.theme_applier = ThemeApplier()
        self.model_selector = ModelSelector(self)
        self.theme_selector = ThemeSelector(self)
        self.template_handler = TemplateHandler(self)
        
        self.setup_ui()
        self.load_sessions()

        # 통계 자동 갱신 타이머
        self.stats_refresh_timer = QTimer(self)
        self.stats_refresh_timer.timeout.connect(self.update_stats)
        self.stats_refresh_timer.start(60000)

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(6)

        # 상단 버튼들
        top_buttons_layout = QVBoxLayout()
        top_buttons_layout.setContentsMargins(2, 2, 2, 2)
        top_buttons_layout.setSpacing(6)

        self.new_session_btn = QPushButton("➕ New Session")
        self.new_session_btn.setMinimumHeight(44)
        self.new_session_btn.clicked.connect(self.actions.create_new_session)
        top_buttons_layout.addWidget(self.new_session_btn)

        self.model_button = QPushButton("🤖 Current Model")
        self.model_button.setMinimumHeight(44)
        self.model_button.clicked.connect(self.show_model_selector)
        top_buttons_layout.addWidget(self.model_button)

        self.template_button = QPushButton("📋 Templates")
        self.template_button.setMinimumHeight(44)
        self.template_button.clicked.connect(self.show_template_manager)
        top_buttons_layout.addWidget(self.template_button)

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

        # 세션 검색
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

        # 세션 관리 버튼들
        manage_layout = QHBoxLayout()
        manage_layout.setContentsMargins(2, 2, 2, 2)
        manage_layout.setSpacing(4)

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
        self.rename_btn.clicked.connect(self.actions.rename_session)

        self.export_btn = QPushButton("📤")
        self.export_btn.setToolTip("세션 내보내기")
        self.export_btn.setEnabled(False)
        self.export_btn.setMinimumHeight(50)
        self.export_btn.setStyleSheet(transparent_emoji_style)
        self.export_btn.clicked.connect(self.exporter.export_session)

        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setToolTip("세션 삭제")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setMinimumHeight(50)
        self.delete_btn.setStyleSheet(transparent_emoji_style)
        self.delete_btn.clicked.connect(self.actions.delete_session)

        manage_layout.addWidget(self.rename_btn)
        manage_layout.addWidget(self.export_btn)
        manage_layout.addWidget(self.delete_btn)
        layout.addLayout(manage_layout)

        # 세션정보 - 통계 정보
        self.stats_label = QLabel()
        self.stats_label.setMinimumHeight(36)
        self.stats_label.setObjectName("stats_label")
        self.stats_label.setToolTip(
            "세션 수 | 메시지 수 | DB 용량 | MCP 서버 수 (마지막 숫자 클릭시 관리화면)"
        )
        self.stats_label.mousePressEvent = self.on_stats_label_click
        layout.addWidget(self.stats_label)

        self.setLayout(layout)
        self.setMinimumWidth(280)
        self.setMaximumWidth(350)

        # 테마 적용
        self.apply_theme()

        # 메인 윈도우 참조 초기화
        self.main_window = None

        # 마우스 추적 활성화
        self.setMouseTracking(True)
        self.stats_label.setMouseTracking(True)

        # 성능 최적화 - 디바운서
        from ui.event_debouncer import get_event_debouncer
        self._debouncer = get_event_debouncer()

        # 앱 시작 시 세션 DB에서 로드
        self._debouncer.debounce("load_sessions", self.load_sessions_from_db, 100)

        # 현재 모델 표시 업데이트
        self._debouncer.debounce("update_model", self._update_current_model_display, 200)

        # 마지막 사용 세션 자동 선택
        self._debouncer.debounce("auto_select", self._auto_select_last_session, 500)
        QTimer.singleShot(1000, self._auto_select_last_session)
        QTimer.singleShot(2000, self._auto_select_last_session)

    def _update_current_model_display(self):
        """현재 모델 표시 업데이트"""
        try:
            from core.file_utils import load_last_model

            current_model = load_last_model()
            if current_model:
                display_name = current_model
                if len(display_name) > 15:
                    display_name = display_name[:12] + "..."
                self.model_button.setText(f"🤖 {display_name}")
                self.model_button.setToolTip(f"현재 모델: {current_model}")
            else:
                self.model_button.setText("🤖 Select Model")
                self.model_button.setToolTip("모델을 선택하세요")
        except Exception as e:
            logger.debug(f"현재 모델 표시 업데이트 오류: {e}")
            self.model_button.setText("🤖 Select Model")

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
                session_widget.delete_requested.connect(self.actions.delete_session_by_id)

                item.setSizeHint(session_widget.sizeHint())
                self.session_list.addItem(item)
                self.session_list.setItemWidget(item, session_widget)

            self.update_stats()

        except Exception as e:
            logger.error(f"세션 로드 오류: {e}")
            QMessageBox.warning(
                self, "오류", f"세션을 불러오는 중 오류가 발생했습니다:\n{e}"
            )

    def search_sessions(self, query: str):
        """세션 검색"""
        if not query.strip():
            self.load_sessions()
            if self.current_session_id:
                session_id = self.current_session_id
                QTimer.singleShot(50, lambda sid=session_id: self._safe_select_session(sid))
            return

        try:
            sessions = session_manager.search_sessions(query)
            self.session_list.clear()

            for session in sessions:
                item = QListWidgetItem()
                session_widget = SessionListItem(session)
                session_widget.clicked.connect(self.select_session)
                session_widget.delete_requested.connect(self.actions.delete_session_by_id)

                item.setSizeHint(session_widget.sizeHint())
                self.session_list.addItem(item)
                self.session_list.setItemWidget(item, session_widget)

            if self.current_session_id:
                session_id = self.current_session_id
                QTimer.singleShot(50, lambda sid=session_id: self._safe_select_session(sid))

        except Exception as e:
            logger.error(f"세션 검색 오류: {e}")

    def _safe_select_session(self, session_id: int):
        """안전한 세션 선택 (객체 존재 확인)"""
        try:
            if self and not self.isHidden():
                self._select_session_without_touch(session_id)
        except RuntimeError:
            pass

    def select_session(self, session_id: int):
        """세션 선택"""
        self.current_session_id = session_id
        self.rename_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

        session_manager.touch_session(session_id)

        if hasattr(self, "main_window") and self.main_window:
            self.main_window.current_session_id = session_id
            self.main_window._auto_session_created = True

        # 선택된 세션 하이라이트
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            widget = self.session_list.itemWidget(item)
            if hasattr(widget, "session_id") and widget.session_id == session_id:
                widget.set_selected(True)
            else:
                widget.set_selected(False)

        self.session_selected.emit(session_id)
        logger.info(f"세션 선택: {session_id}")

    def _select_session_without_touch(self, session_id: int):
        """세션 선택 (last_used_at 업데이트 없이)"""
        self.current_session_id = session_id
        self.rename_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

        if hasattr(self, "main_window") and self.main_window:
            self.main_window.current_session_id = session_id
            self.main_window._auto_session_created = True

        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            widget = self.session_list.itemWidget(item)
            if hasattr(widget, "session_id") and widget.session_id == session_id:
                widget.set_selected(True)
            else:
                widget.set_selected(False)

        self.session_selected.emit(session_id)
        logger.info(f"세션 자동 선택: {session_id}")

    def _auto_select_last_session(self):
        """마지막 사용 세션 자동 선택"""
        if self._auto_selection_done or self.current_session_id:
            return

        try:
            sessions = session_manager.get_sessions(limit=1)
            if sessions:
                last_session = sessions[0]
                if hasattr(self, "main_window") and self.main_window:
                    self.main_window._auto_session_created = True
                    self.main_window.current_session_id = last_session["id"]

                self.select_session(last_session["id"])
                self._auto_selection_done = True
            else:
                self._auto_selection_done = True
        except Exception as e:
            logger.debug(f"자동 선택 오류: {e}")

    def update_stats(self):
        """통계 정보 업데이트"""
        try:
            if not hasattr(self, "stats_label") or self.stats_label is None:
                if hasattr(self, "stats_refresh_timer"):
                    self.stats_refresh_timer.stop()
                return
            QTimer.singleShot(0, self._update_stats_async)
        except RuntimeError as e:
            if "wrapped C/C++ object" in str(e):
                if hasattr(self, "stats_refresh_timer"):
                    self.stats_refresh_timer.stop()
            else:
                raise
        except Exception as e:
            logger.debug(f"통계 업데이트 오류: {e}")

    def _update_stats_async(self):
        """비동기 통계 업데이트"""
        try:
            if not hasattr(self, "stats_label") or self.stats_label is None:
                return

            stats = session_manager.get_session_stats()
            self.stats_label.setText(
                f"세션 {stats['total_sessions']}개 | "
                f"메시지 {stats['total_messages']}개 | "
                f"{stats['db_size_mb']} MB | "
                f"{stats['active_servers']}개"
            )
        except RuntimeError as e:
            if "wrapped C/C++ object" in str(e):
                if hasattr(self, "stats_refresh_timer"):
                    self.stats_refresh_timer.stop()
            else:
                raise
        except Exception as e:
            logger.error(f"통계 업데이트 오류: {e}")
            try:
                if hasattr(self, "stats_label") and self.stats_label is not None:
                    self.stats_label.setText("통계 로드 실패")
            except RuntimeError:
                pass

    def get_current_session_id(self) -> Optional[int]:
        """현재 선택된 세션 ID 반환"""
        return self.current_session_id

    def apply_theme(self):
        """테마 적용"""
        try:
            self.theme_applier.apply_to_panel(self)
        except Exception as e:
            logger.error(f"세션 패널 테마 적용 오류: {e}")



    def _remove_session_item(self, session_id: int):
        """안전하게 세션 아이템 제거"""
        try:
            for i in range(self.session_list.count()):
                item = self.session_list.item(i)
                if item:
                    widget = self.session_list.itemWidget(item)
                    if (
                        widget
                        and hasattr(widget, "session_id")
                        and widget.session_id == session_id
                    ):
                        try:
                            widget.clicked.disconnect()
                            widget.delete_requested.disconnect()
                        except:
                            pass
                        self.session_list.takeItem(i)
                        widget.deleteLater()
                        break
        except Exception as e:
            logger.error(f"세션 아이템 제거 오류: {e}")

    def show_model_selector(self):
        """모델 선택기 표시"""
        self.model_selector.show(self.model_button)

    def show_template_manager(self):
        """템플릿 관리자 표시"""
        self.template_handler.show_manager()

    def show_theme_selector(self):
        """테마 선택기 표시"""
        self.theme_selector.show(self.theme_button)

    def on_stats_label_click(self, event):
        """통계 라벨 클릭 처리"""
        label_width = self.stats_label.width()
        click_x = event.position().x()
        if click_x > label_width * 0.75:
            self.show_tools_detail()

    def show_tools_detail(self):
        """MCP 서버 관리 화면 열기"""
        try:
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, "show_mcp_dialog"):
                main_window.show_mcp_dialog()
            else:
                from ui.mcp_dialog import MCPDialog
                dialog = MCPDialog(self)
                dialog.exec()
        except Exception as e:
            logger.error(f"MCP 서버 관리 화면 열기 오류: {e}")

    def _find_main_window(self):
        """메인 윈도우 찾기"""
        widget = self
        while widget:
            if widget.__class__.__name__ == "MainWindow":
                return widget
            widget = widget.parent()
        return None

    def mouseMoveEvent(self, event):
        """마우스 이동 시 커서 변경"""
        if hasattr(self, "stats_label"):
            stats_rect = self.stats_label.geometry()
            if stats_rect.contains(event.position().toPoint()):
                relative_x = event.position().x() - stats_rect.x()
                if relative_x > stats_rect.width() * 0.75:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)



    def update_theme(self):
        """테마 업데이트"""
        self.apply_theme()
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            widget = self.session_list.itemWidget(item)
            if hasattr(widget, "apply_theme"):
                widget.apply_theme()

    def closeEvent(self, event):
        """패널 종료 시 타이머 정리"""
        try:
            if (
                hasattr(self, "stats_refresh_timer")
                and self.stats_refresh_timer is not None
            ):
                try:
                    self.stats_refresh_timer.stop()
                    self.stats_refresh_timer.timeout.disconnect()
                    self.stats_refresh_timer.deleteLater()
                    self.stats_refresh_timer = None
                except RuntimeError:
                    pass
            logger.debug("SessionPanel 종료 완료")
        except Exception as e:
            logger.debug(f"SessionPanel 종료 중 오류: {e}")
        finally:
            event.accept()
