"""
Tab Style Manager
탭 스타일 관리
"""

from ui.styles.theme_manager import theme_manager


class TabStyleManager:
    """탭 스타일 관리"""
    
    @staticmethod
    def get_tab_widget_style() -> str:
        """탭 위젯 스타일"""
        colors = theme_manager.material_manager.get_theme_colors()
        
        return f"""
            QTabWidget {{
                background: transparent;
                border: none;
            }}
            QTabWidget::pane {{
                background-color: {colors.get('surface', '#334155')};
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 8px;
                margin-top: 2px;
            }}
            QTabBar::tab {{
                background-color: {colors.get('surface_variant', '#475569')};
                color: #ffffff;
                border: 1px solid {colors.get('border', '#64748b')};
                padding: 10px 16px;
                margin: 1px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: {colors.get('primary', '#6366f1')};
                color: {colors.get('on_primary', '#ffffff')};
                border-color: {colors.get('primary', '#6366f1')};
                font-weight: 600;
            }}
            QTabBar::tab:hover {{
                background-color: {colors.get('primary_variant', '#4f46e5')};
                color: {colors.get('on_primary', '#ffffff')};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {colors.get('surface', '#334155')};
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors.get('primary', '#6366f1')};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors.get('primary_variant', '#4f46e5')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """
