"""
Theme Selector
테마 선택 전담 클래스 - SRP (Single Responsibility Principle)
"""

from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import QPoint, QTimer
from ui.styles.theme_manager import theme_manager
from core.logging import get_logger

logger = get_logger("theme_selector")


class ThemeSelector:
    """테마 선택 전담 클래스"""

    def __init__(self, parent):
        self.parent = parent

    def show(self, button):
        """테마 선택 메뉴 표시"""
        try:
            menu = QMenu(self.parent)
            themes = theme_manager.material_manager.themes
            current_theme = theme_manager.material_manager.current_theme_key

            categorized = self._categorize_themes(themes)
            self._populate_menu(menu, categorized, current_theme)
            self._show_menu(menu, button)

        except Exception as e:
            logger.debug(f"테마 선택기 표시 오류: {e}")

    def _categorize_themes(self, themes):
        """테마 카테고리 분류"""
        light_themes = {}
        dark_themes = {}
        special_themes = {}

        for theme_key, theme_data in themes.items():
            theme_type = theme_data.get("type", "dark")
            theme_name = theme_data.get("name", theme_key)

            if theme_type == "light":
                light_themes[theme_key] = theme_name
            elif theme_type == "special":
                special_themes[theme_key] = theme_name
            else:
                dark_themes[theme_key] = theme_name

        return {
            "light": light_themes,
            "dark": dark_themes,
            "special": special_themes
        }

    def _populate_menu(self, menu, categorized, current_theme):
        """메뉴 채우기"""
        category_info = {
            "light": {"emoji": "☀️", "name": "Light Themes"},
            "dark": {"emoji": "🌙", "name": "Dark Themes"},
            "special": {"emoji": "✨", "name": "Special Themes"}
        }

        for category, themes in categorized.items():
            if not themes:
                continue

            info = category_info[category]
            submenu = menu.addMenu(f"{info['emoji']} {info['name']}")

            for theme_key, theme_name in themes.items():
                action = submenu.addAction(f"🎨 {theme_name}")
                action.setCheckable(True)
                
                if theme_key == current_theme:
                    action.setChecked(True)

                action.triggered.connect(
                    lambda checked, key=theme_key: self._select_theme(key)
                )

    def _select_theme(self, theme_key):
        """테마 선택"""
        try:
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, "_change_theme"):
                QTimer.singleShot(0, lambda: main_window._change_theme(theme_key))
            else:
                theme_manager.material_manager.set_theme(theme_key)
                if hasattr(self.parent, 'update_theme'):
                    self.parent.update_theme()
        except Exception as e:
            logger.debug(f"테마 선택 오류: {e}")

    def _find_main_window(self):
        """메인 윈도우 찾기"""
        widget = self.parent
        while widget:
            if widget.__class__.__name__ == "MainWindow":
                return widget
            widget = widget.parent()
        return None

    def _show_menu(self, menu, button):
        """메뉴 표시"""
        button_pos = button.mapToGlobal(QPoint(0, 0))
        menu.exec(QPoint(button_pos.x(), button_pos.y() + button.height()))
