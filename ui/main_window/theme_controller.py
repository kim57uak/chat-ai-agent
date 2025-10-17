"""
Theme Controller
테마 적용 및 관리 전담 클래스
"""

from PyQt6.QtCore import QTimer
from ui.styles.theme_manager import theme_manager
from core.logging import get_logger
from core.safe_timer import safe_timer_manager

logger = get_logger("theme_controller")


class ThemeController:
    """테마 적용 및 관리 전담 클래스"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self._theme_update_timer = None
    
    def apply_current_theme(self):
        """현재 테마 적용"""
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            stylesheet = theme_manager.get_material_design_stylesheet()
            app.setStyleSheet(stylesheet)
            self.main_window.setStyleSheet(stylesheet)
        
        self.apply_splitter_theme()
    
    def apply_splitter_theme(self):
        """스플리터 테마 적용"""
        try:
            colors = theme_manager.material_manager.get_theme_colors()
            primary_color = colors.get('primary', '#bb86fc')
            primary_variant = colors.get('primary_variant', '#3700b3')
            divider_color = colors.get('divider', '#333333')
            surface_color = colors.get('surface', '#1e1e1e')
            
            splitter_style = f"""
            QSplitter::handle {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {divider_color}, 
                    stop:1 {colors.get('text_secondary', '#888888')});
                border: 1px solid {divider_color};
                border-radius: 6px;
                margin: 2px;
                transition: all 0.3s ease;
            }}
            QSplitter::handle:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {colors.get('text_secondary', '#888888')}, 
                    stop:1 {primary_color});
                border-color: {primary_color};
                transform: translateY(-1px);
            }}
            QSplitter::handle:pressed {{
                background: {primary_variant};
                border-color: {primary_variant};
            }}
            
            QScrollBar:vertical {{
                background: {colors.get('scrollbar_track', surface_color)};
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
            
            QScrollBar:horizontal {{
                background: {colors.get('scrollbar_track', surface_color)};
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 {colors.get('scrollbar', colors.get('text_secondary', '#b3b3b3'))}, 
                    stop:1 {primary_color});
                border-radius: 4px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {primary_color};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            """
            
            self.main_window.splitter.setStyleSheet(splitter_style)
            
        except Exception as e:
            logger.debug(f"스플리터 테마 적용 오류: {e}")
    
    def change_theme(self, theme_key: str):
        """테마 변경"""
        try:
            theme_manager.material_manager.set_theme(theme_key)
            
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                new_stylesheet = theme_manager.get_material_design_stylesheet()
                app.setStyleSheet(new_stylesheet)
                self.main_window.setStyleSheet(new_stylesheet)
            
            self.apply_current_theme()
            self.main_window._update_window_title()
            
            if hasattr(self.main_window, 'chat_widget'):
                logger.debug("채팅 위젯 테마 업데이트 시작")
                self.main_window.chat_widget.update_theme()
                logger.debug("채팅 위젯 테마 업데이트 완료")
            
            if hasattr(self.main_window, 'session_panel'):
                self.main_window.session_panel.update_theme()
            
            if hasattr(self.main_window, 'token_display'):
                self.main_window.token_display.update_theme()
            
            if hasattr(self.main_window, 'news_banner'):
                self.main_window.news_banner.update_theme()
            
            self.apply_splitter_theme()
            
            self.main_window.repaint()
            self.main_window.update()
            
            if self._theme_update_timer is None:
                def delayed_update():
                    try:
                        if hasattr(self.main_window, 'chat_widget'):
                            self.main_window.chat_widget.update_theme()
                            if hasattr(self.main_window.chat_widget, 'input_text'):
                                self.main_window.chat_widget.input_text.update()
                            if hasattr(self.main_window.chat_widget, 'input_container'):
                                self.main_window.chat_widget.input_container.update()
                    except Exception as e:
                        logger.debug(f"지연 테마 업데이트 오류: {e}")
                
                self._theme_update_timer = safe_timer_manager.create_timer(
                    100, delayed_update, single_shot=True, parent=self.main_window
                )
            if self._theme_update_timer:
                self._theme_update_timer.start()
            
        except Exception as e:
            logger.debug(f"테마 변경 오류: {e}")
    
    def apply_saved_theme(self):
        """저장된 테마 적용"""
        try:
            self.main_window._update_window_title()
            
            if hasattr(self.main_window, 'chat_widget'):
                self.main_window.chat_widget.update_theme()
            
            if hasattr(self.main_window, 'session_panel'):
                self.main_window.session_panel.update_theme()
        except Exception as e:
            logger.debug(f"저장된 테마 적용 오류: {e}")
    
    def apply_dialog_theme(self, msg_box):
        """다이얼로그에 테마 적용"""
        colors = theme_manager.material_manager.get_theme_colors()
        
        primary = colors.get('primary', '#6366f1')
        primary_variant = colors.get('primary_variant', '#4f46e5')
        background = colors.get('background', '#ffffff')
        text_primary = colors.get('text_primary', '#000000')
        
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {background};
                color: {text_primary};
            }}
            QMessageBox QLabel {{
                color: {text_primary};
                font-size: 14px;
            }}
            QMessageBox QPushButton {{
                background-color: {primary};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {primary_variant};
            }}
        """)
