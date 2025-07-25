"""Theme management for UI styling."""


class ThemeManager:
    """Manages application themes and styling."""
    
    @staticmethod
    def get_dark_theme() -> str:
        """Get dark theme stylesheet."""
        return """
            QMainWindow {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #2a2a2a;
                color: #ffffff;
                border-bottom: 1px solid #444444;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #444444;
            }
            QMenu {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #444444;
            }
            QMenu::item:selected {
                background-color: #444444;
            }
        """
    
    @staticmethod
    def get_central_widget_style() -> str:
        """Get central widget styling."""
        return "background-color: #1a1a1a;"