"""
Chat Widget Styles Mixin
채팅 위젯 스타일 관련 메서드 분리
"""

from core.logging import get_logger
from ui.styles.flat_theme import FlatTheme
from ui.styles.theme_manager import theme_manager

logger = get_logger("chat_widget_styles")


class ChatWidgetStylesMixin:
    """채팅 위젯 스타일 관련 메서드"""
    
    def _update_mode_combo_style(self):
        """모드 콤보박스 스타일 업데이트"""
        try:
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                primary = colors.get('primary', '#bb86fc')
                surface = colors.get('surface', '#1e1e1e')
                text = colors.get('text_primary', '#ffffff')
                
                style = f"""
                QComboBox {{
                    background-color: {surface};
                    color: {text};
                    border: 2px solid {primary};
                    border-radius: 16px;
                    padding: 0px;
                    font-size: 22px;
                    font-weight: 700;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                }}
                QComboBox:hover {{
                    border-color: {primary};
                    background-color: {primary}20;
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 0px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    width: 0px;
                    height: 0px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {surface};
                    color: {text};
                    border: 2px solid {primary};
                    border-radius: 16px;
                    selection-background-color: {primary};
                    selection-color: {surface};
                    padding: 12px;
                    outline: none;
                    min-width: 220px;
                }}
                QComboBox QAbstractItemView::item {{
                    padding: 28px 36px;
                    border-radius: 12px;
                    min-height: 80px;
                    font-size: 26px;
                    font-weight: 700;
                    margin: 6px;
                }}
                QComboBox QAbstractItemView::item:hover {{
                    background-color: {primary}40;
                }}
                QComboBox QAbstractItemView::item:selected {{
                    background-color: {primary};
                    color: {surface};
                }}
                """
            else:
                style = """
                QComboBox {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 2px solid #666666;
                    border-radius: 16px;
                    padding: 0px;
                    font-size: 22px;
                    font-weight: 700;
                }
                QComboBox:hover {
                    border-color: #888888;
                    background-color: #333333;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 0px;
                }
                QComboBox::down-arrow {
                    image: none;
                    width: 0px;
                    height: 0px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 2px solid #666666;
                    border-radius: 16px;
                    selection-background-color: #666666;
                    padding: 12px;
                    min-width: 220px;
                }
                QComboBox QAbstractItemView::item {
                    padding: 28px 36px;
                    border-radius: 12px;
                    min-height: 80px;
                    font-size: 26px;
                    font-weight: 700;
                    margin: 6px;
                }
                """
            
            self.mode_combo.setStyleSheet(style)
        except Exception as e:
            logger.debug(f"콤보박스 스타일 업데이트 오류: {e}")
    
    def _update_button_styles(self):
        """버튼 스타일 업데이트"""
        try:
            themed_button_style = self._get_themed_button_style()
            cancel_button_style = self._get_cancel_button_style()
            
            if hasattr(self, 'send_button'):
                self.send_button.setStyleSheet(themed_button_style)
            if hasattr(self, 'upload_button'):
                self.upload_button.setStyleSheet(themed_button_style)
            if hasattr(self, 'cancel_button'):
                self.cancel_button.setStyleSheet(cancel_button_style)
        except Exception as e:
            logger.debug(f"버튼 스타일 업데이트 오류: {e}")
    
    def _get_cancel_button_style(self):
        """취소 버튼 전용 빨간색 테두리 스타일"""
        try:
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                bg_color = colors.get('surface', '#1e1e1e')
                
                return f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: 1px solid #FF5252;
                    border-radius: 12px;
                    font-size: 20px;
                    font-weight: bold;
                    color: #FF5252;
                    padding: 0px;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                }}
                QPushButton:hover {{
                    background-color: #FF5252;
                    color: {bg_color};
                    border-color: #FF5252;
                    font-size: 22px;
                }}
                QPushButton:pressed {{
                    background-color: #D32F2F;
                    transform: scale(0.95);
                    font-size: 18px;
                }}
                QPushButton:disabled {{
                    background-color: {bg_color};
                    border-color: #666666;
                    color: #666666;
                    opacity: 0.5;
                }}
                """
            else:
                return """
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #FF5252;
                    border-radius: 12px;
                    font-size: 20px;
                    font-weight: bold;
                    color: #FF5252;
                }
                QPushButton:hover {
                    background-color: #FF5252;
                    color: #FFFFFF;
                    font-size: 22px;
                }
                QPushButton:pressed {
                    background-color: #D32F2F;
                    font-size: 18px;
                }
                QPushButton:disabled {
                    opacity: 0.5;
                }
                """
        except Exception as e:
            logger.debug(f"취소 버튼 스타일 생성 오류: {e}")
            return """
            QPushButton {
                background-color: transparent;
                border: 1px solid #FF5252;
                color: #FF5252;
            }
            """
    
    def _get_themed_button_style(self, colors=None):
        """테마 색상을 적용한 버튼 스타일 생성"""
        try:
            if theme_manager.use_material_theme:
                if not colors:
                    colors = theme_manager.material_manager.get_theme_colors()
                
                bg_color = colors.get('surface', '#1e1e1e')
                primary_color = colors.get('primary', '#bb86fc')
                primary_variant = colors.get('primary_variant', '#3700b3')
                
                return f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: 1px solid {primary_color};
                    border-radius: 12px;
                    font-size: 20px;
                    font-weight: bold;
                    color: {primary_color};
                    padding: 0px;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                }}
                QPushButton:hover {{
                    background-color: {primary_color};
                    color: {bg_color};
                    border-color: {primary_color};
                    font-size: 22px;
                }}
                QPushButton:pressed {{
                    background-color: {primary_variant};
                    transform: scale(0.95);
                    font-size: 18px;
                }}
                QPushButton:disabled {{
                    background-color: {bg_color};
                    border-color: #666666;
                    color: #666666;
                    opacity: 0.5;
                }}
                """
            else:
                return """
                QPushButton {
                    background-color: transparent;
                    border: 1px solid #666666;
                    border-radius: 12px;
                    font-size: 20px;
                    color: #666666;
                }
                QPushButton:hover {
                    background-color: #666666;
                    color: #FFFFFF;
                    font-size: 22px;
                }
                QPushButton:pressed {
                    background-color: #444444;
                    font-size: 18px;
                }
                QPushButton:disabled {
                    opacity: 0.5;
                }
                """
        except Exception as e:
            logger.debug(f"버튼 스타일 생성 오류: {e}")
            return """
            QPushButton {
                background: transparent;
                border: none;
                font-size: 20px;
            }
            """
    
    def _update_input_text_style(self, colors=None):
        """입력창 스타일 동적 업데이트"""
        try:
            if theme_manager.use_material_theme and colors:
                if colors.get('primary') == '#6B7280':
                    input_text_style = f"""
                    QTextEdit {{
                        background-color: #FFFFFF;
                        color: #374151;
                        border: 1px solid {colors.get('divider', '#E5E7EB')};
                        border-radius: 12px;
                        font-size: 15px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        padding: 4px;
                        selection-background-color: {colors.get('primary', '#6B7280')};
                        selection-color: #FFFFFF;
                    }}
                    QTextEdit:focus {{
                        border-color: {colors.get('primary', '#6B7280')};
                        border-width: 2px;
                    }}
                    """
                else:
                    input_text_style = f"""
                    QTextEdit {{
                        background-color: {colors.get('surface', '#1e1e1e')};
                        color: {colors.get('text_primary', '#ffffff')};
                        border: 1px solid {colors.get('divider', '#333333')};
                        border-radius: 12px;
                        font-size: 15px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        padding: 4px;
                        selection-background-color: {colors.get('primary', '#bb86fc')};
                    }}
                    QTextEdit:focus {{
                        border-color: {colors.get('primary', '#bb86fc')};
                    }}
                    """
            elif theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                if colors.get('primary') == '#6B7280':
                    input_text_style = f"""
                    QTextEdit {{
                        background-color: #FFFFFF;
                        color: #374151;
                        border: 1px solid {colors.get('divider', '#E5E7EB')};
                        border-radius: 12px;
                        font-size: 15px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        padding: 4px;
                        selection-background-color: {colors.get('primary', '#6B7280')};
                        selection-color: #FFFFFF;
                    }}
                    QTextEdit:focus {{
                        border-color: {colors.get('primary', '#6B7280')};
                        border-width: 2px;
                    }}
                    """
                else:
                    input_text_style = f"""
                    QTextEdit {{
                        background-color: {colors.get('surface', '#1e1e1e')};
                        color: {colors.get('text_primary', '#ffffff')};
                        border: 1px solid {colors.get('divider', '#333333')};
                        border-radius: 12px;
                        font-size: 15px;
                        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                        padding: 4px;
                        selection-background-color: {colors.get('primary', '#bb86fc')};
                    }}
                    QTextEdit:focus {{
                        border-color: {colors.get('primary', '#bb86fc')};
                    }}
                    """
            else:
                input_text_style = FlatTheme.get_input_area_style()['input_text']
            
            self.input_text.setStyleSheet("")
            self.input_text.setStyleSheet(input_text_style)
            
        except Exception as e:
            logger.debug(f"입력창 스타일 업데이트 오류: {e}")
            self.input_text.setStyleSheet(FlatTheme.get_input_area_style()['input_text'])
    
    def _update_input_container_style(self, container):
        """입력 컨테이너 스타일 동적 업데이트"""
        try:
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                style = f"""
                QWidget {{
                    background-color: {colors.get('surface', '#1e1e1e')};
                    border: 2px solid {colors.get('primary', '#bb86fc')};
                    border-radius: 16px;
                }}
                """
            else:
                style = FlatTheme.get_input_area_style()['container']
            
            container.setStyleSheet(style)
            
        except Exception as e:
            logger.debug(f"입력 컨테이너 스타일 업데이트 오류: {e}")
            container.setStyleSheet(FlatTheme.get_input_area_style()['container'])
    
    def _apply_material_theme_styles(self):
        """재료 테마 스타일 적용"""
        colors = theme_manager.material_manager.get_theme_colors()
        loading_config = theme_manager.material_manager.get_loading_bar_config()
        
        widget_style = f"""
        ChatWidget {{
            background-color: {colors.get('background', '#121212')} !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        }}
        QWidget {{
            background-color: {colors.get('background', '#121212')};
            color: {colors.get('text_primary', '#ffffff')};
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
        }}
        QWebEngineView {{
            background-color: {colors.get('background', '#121212')} !important;
        }}
        """
        self.setStyleSheet(widget_style)
        
        self._apply_material_input_styles(colors)
        
        if hasattr(self, 'loading_bar'):
            loading_style = f"""
            QProgressBar {{
                border: none;
                background-color: {loading_config.get('background', 'rgba(187, 134, 252, 0.1)')};
                border-radius: 8px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background: {loading_config.get('chunk', 'linear-gradient(90deg, #bb86fc 0%, #03dac6 100%)')};
                border-radius: 6px;
            }}
            """
            self.loading_bar.setStyleSheet(loading_style)
    
    def _apply_material_input_styles(self, colors):
        """재료 테마 입력 영역 스타일 적용"""
        is_dark = theme_manager.is_material_dark_theme()
        
        container_style = f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 {colors.get('surface', '#1e1e1e')}, 
                stop:1 {colors.get('background', '#121212')});
            border: 2px solid {colors.get('primary', '#bb86fc')};
            border-radius: 20px;
            transition: all 0.3s ease;
        }}
        QWidget:focus-within {{
            border: 3px solid {colors.get('primary', '#bb86fc')};
            transform: translateY(-2px);
        }}
        """
        
        drag_handle_style = f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {colors.get('divider', '#666666')}, 
                stop:1 {colors.get('text_secondary', '#888888')});
            border-radius: 6px;
            margin: 2px 20px;
            transition: all 0.3s ease;
        }}
        QWidget:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {colors.get('text_secondary', '#888888')}, 
                stop:1 {colors.get('primary', '#bb86fc')});
            transform: translateY(-1px);
        }}
        """
        
        if hasattr(self, 'input_container'):
            self.input_container.setStyleSheet(container_style)
        
        if hasattr(self, 'drag_handle'):
            self.drag_handle.setStyleSheet(drag_handle_style)
        
        self._update_input_text_style(colors)
        
        themed_button_style = self._get_themed_button_style(colors)
        cancel_button_style = self._get_cancel_button_style()
        
        if hasattr(self, 'send_button'):
            self.send_button.setStyleSheet(themed_button_style)
        if hasattr(self, 'upload_button'):
            self.upload_button.setStyleSheet(themed_button_style)
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setStyleSheet(cancel_button_style)
    
    def _apply_initial_theme(self):
        """초기 테마 적용"""
        try:
            if theme_manager.use_material_theme:
                self._apply_material_theme_styles()
            else:
                self.setStyleSheet(FlatTheme.get_chat_widget_style())
            logger.debug("초기 테마 적용 완료")
        except Exception as e:
            logger.debug(f"초기 테마 적용 오류: {e}")
    
    def _apply_theme_if_needed(self):
        """필요시 테마 적용"""
        try:
            if theme_manager.use_material_theme:
                self._apply_material_theme_styles()
                if hasattr(self, 'chat_display'):
                    self.chat_display.update_theme()
        except Exception as e:
            logger.debug(f"테마 적용 오류: {e}")
    
    def update_theme(self):
        """테마 업데이트"""
        try:
            self.setStyleSheet("")
            
            if theme_manager.use_material_theme:
                self._apply_material_theme_styles()
            else:
                self.setStyleSheet(FlatTheme.get_chat_widget_style())
                self._update_input_text_style()
                if hasattr(self, 'input_container'):
                    self._update_input_container_style(self.input_container)
            
            if hasattr(self, 'chat_display'):
                self.chat_display.update_theme()
            
            if hasattr(self, 'loading_bar') and hasattr(self.loading_bar, 'update_theme'):
                self.loading_bar.update_theme()
            
            self._update_button_styles()
            
            if hasattr(self, 'mode_combo'):
                self._update_mode_combo_style()
            
            self.repaint()
            if hasattr(self, 'input_text'):
                self.input_text.repaint()
            if hasattr(self, 'input_container'):
                self.input_container.repaint()
            
            logger.debug("테마 업데이트 완료")
            
        except Exception as e:
            logger.debug(f"테마 업데이트 오류: {e}")
