"""
Session List Item Widget
세션 목록 아이템 위젯
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict
from datetime import datetime

from ui.styles.theme_manager import theme_manager
from core.logging import get_logger

logger = get_logger("session_list_item")


class SessionListItem(QWidget):
    """현대적인 세션 목록 아이템"""

    clicked = pyqtSignal(int)  # session_id
    delete_requested = pyqtSignal(int)  # session_id

    def __init__(self, session_data: Dict, parent=None):
        super().__init__(parent)
        self.session_data = session_data
        self.session_id = session_data["id"]
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

        self.title_label = QLabel(self.session_data["title"])
        self.title_label.setWordWrap(False)
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
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

        last_used = self.session_data.get("last_used_at", "")
        if last_used:
            try:
                dt = datetime.fromisoformat(last_used.replace("Z", "+00:00"))
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
            title_color = colors.get(
                "text_primary", "#ffffff" if is_dark else "#000000"
            )
            self.title_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {title_color};
                    font-size: 14px;
                    font-weight: 600;
                    margin-bottom: 4px;
                }}
            """
            )

            # 메시지 수 배지
            primary_color = colors.get("primary", "#1976d2")
            primary_variant = colors.get("primary_variant", "#1565c0")
            on_primary = colors.get("on_primary", "#ffffff")
            self.message_count_label.setStyleSheet(
                f"""
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
            """
            )

            # 시간 배지
            if hasattr(self, "time_label"):
                secondary_color = colors.get("text_secondary", "#666666")
                surface_color = colors.get("surface", "#f5f5f5")
                self.time_label.setStyleSheet(
                    f"""
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
                """
                )

            # 선택 표시 아이콘 스타일
            self.selected_icon.setStyleSheet(
                f"""
                QLabel {{
                    color: {primary_color};
                    font-size: 12px;
                    font-weight: bold;
                }}
            """
            )

            self.update_item_style(colors)

    def update_item_style(self, colors):
        """깔끔한 아이템 스타일"""
        is_dark = theme_manager.is_material_dark_theme()

        if self.is_selected:
            # 선택된 상태
            primary_color = colors.get("primary", "#1976d2")
            self.setStyleSheet(
                f"""
                SessionListItem {{
                    background-color: {primary_color}20;
                    border: 2px solid {primary_color};
                    border-radius: 8px;
                    margin: 2px;
                }}
            """
            )
        else:
            # 기본 상태
            bg_color = colors.get("surface", "#f5f5f5" if not is_dark else "#2d2d2d")
            border_color = colors.get(
                "divider", "#e0e0e0" if not is_dark else "#404040"
            )

            self.setStyleSheet(
                f"""
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
            """
            )

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
                logger.debug(f"SessionListItem이 이미 삭제됨: {e}")
                return
            raise

    def show_context_menu(self, position):
        """우클릭 컨텍스트 메뉴 표시"""
        menu = QMenu(self)
        delete_action = menu.addAction("🗑️ 세션 삭제")
        delete_action.triggered.connect(
            lambda: self.delete_requested.emit(self.session_id)
        )
        menu.exec(position)
