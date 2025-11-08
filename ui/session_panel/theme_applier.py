"""
Theme Applier
테마 적용 전담 클래스 - SRP (Single Responsibility Principle)
"""

from ui.styles.theme_manager import theme_manager
from core.logging import get_logger

logger = get_logger("theme_applier")


class ThemeApplier:
    """테마 적용 전담 클래스"""

    @staticmethod
    def apply_to_panel(panel):
        """패널에 테마 적용"""
        try:
            if theme_manager.use_material_theme:
                ThemeApplier._apply_material_theme(panel)
            else:
                ThemeApplier._apply_default_theme(panel)
        except Exception as e:
            logger.error(f"테마 적용 오류: {e}")

    @staticmethod
    def _apply_material_theme(panel):
        """Material Design 테마 적용"""
        colors = theme_manager.material_manager.get_theme_colors()
        bg_color = colors.get("background", "#121212")
        text_color = colors.get("text_primary", "#ffffff")
        surface_color = colors.get("surface", "#1e1e1e")
        primary_color = colors.get("primary", "#bb86fc")
        is_dark = theme_manager.is_material_dark_theme()

        styles = ThemeApplier._build_material_styles(colors, bg_color, text_color, 
                                                      surface_color, primary_color, is_dark)
        
        ThemeApplier._apply_styles(panel, styles)

    @staticmethod
    def _build_material_styles(colors, bg_color, text_color, surface_color, primary_color, is_dark):
        """Material 스타일 생성"""
        return {
            'panel': f"""
                SessionPanel {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: none;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                }}
            """,
            'search': f"""
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
                }}
                QLineEdit:focus {{
                    border: 1px solid {primary_color};
                    background: {surface_color};
                }}
                QLineEdit::placeholder {{
                    color: {colors.get('text_secondary', '#b3b3b3')};
                    opacity: 0.8;
                }}
            """,
            'list': f"""
                QListWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {bg_color}, stop:1 {surface_color});
                    border: 1px solid {colors.get('divider', '#333333')};
                    border-radius: 16px;
                    padding: 12px;
                    margin: 6px;
                    outline: none;
                }}
                QListWidget::item {{
                    border: none;
                    padding: 0px;
                    margin: 4px;
                    border-radius: 12px;
                    background: transparent;
                }}
                QScrollBar:vertical {{
                    background: {colors.get('scrollbar_track', surface_color)};
                    width: 8px;
                    border-radius: 4px;
                }}
                QScrollBar::handle:vertical {{
                    background: {primary_color};
                    border-radius: 4px;
                    min-height: 20px;
                }}
            """,
            'button': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {primary_color}, stop:1 {colors.get('primary_variant', '#3700b3')});
                    color: {colors.get('on_primary', '#000000')};
                    border: none;
                    border-radius: 20px;
                    font-weight: 800;
                    font-size: 16px;
                    padding: 6px 20px;
                    margin: 6px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('primary_variant', '#3700b3')}, stop:1 {primary_color});
                }}
            """,
            'manage_button': """
                QPushButton {
                    background: transparent;
                    border: none;
                    font-size: 28px;
                }
                QPushButton:hover {
                    font-size: 38px;
                }
            """,
            'stats': f"""
                QLabel#stats_label {{
                    color: {colors.get('text_secondary' if is_dark else 'text_primary', '#b3b3b3')};
                    font-size: 12px;
                    font-weight: 600;
                    padding: 12px 20px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {surface_color}, stop:1 {bg_color});
                    border: 1px solid {colors.get('divider', '#333333')};
                    border-radius: 16px;
                    margin: 6px;
                }}
            """
        }

    @staticmethod
    def _apply_styles(panel, styles):
        """스타일 적용"""
        panel.setStyleSheet(styles['panel'])
        panel.search_edit.setStyleSheet(styles['search'])
        panel.session_list.setStyleSheet(styles['list'])
        
        for btn_name in ['new_session_btn', 'model_button', 'template_button', 'theme_button', 'topic_button']:
            if hasattr(panel, btn_name):
                getattr(panel, btn_name).setStyleSheet(styles['button'])
        
        for btn in [panel.rename_btn, panel.export_btn, panel.delete_btn]:
            btn.setStyleSheet(styles['manage_button'])
        
        if hasattr(panel, 'stats_label'):
            panel.stats_label.setStyleSheet(styles['stats'])

    @staticmethod
    def _apply_default_theme(panel):
        """기본 테마 적용"""
        panel.setStyleSheet("""
            SessionPanel {
                background-color: #f5f5f5;
                color: #333333;
                border-right: 1px solid #ddd;
            }
        """)
