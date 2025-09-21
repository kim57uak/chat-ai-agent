"""플랫 디자인 테마 - 첨부된 디자인 참고"""

class FlatTheme:
    """플랫 디자인 테마 클래스"""
    
    @staticmethod
    def get_main_window_style():
        """메인 윈도우 스타일 - 고급 블랙 테마"""
        colors = FlatTheme.get_theme_colors()
        return f"""
            QMainWindow {{
                background: {colors.get('background', '#5a5a5f')};
                color: #ffffff;
            }}
            QWidget {{
                background: {colors.get('background', '#5a5a5f')};
                color: #ffffff;
            }}
            QMenuBar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(15, 15, 15, 0.95), 
                    stop:1 rgba(10, 10, 10, 0.95));
                color: #f3f4f6;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                font-size: 14px;
                font-weight: 600;
                padding: 4px 0;
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 10px 16px;
                border-radius: 6px;
                margin: 2px 4px;
            }}
            QMenuBar::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(99, 102, 241, 0.2), 
                    stop:1 rgba(139, 92, 246, 0.2));
                color: #ffffff;
            }}
            QMenu {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(31, 41, 55, 0.95), 
                    stop:1 rgba(17, 24, 39, 0.95));
                color: #f3f4f6;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
                padding: 8px;
            }}
            QMenu::item {{
                padding: 12px 20px;
                border-radius: 6px;
                margin: 2px;
                font-weight: 500;
            }}
            QMenu::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(99, 102, 241, 0.3), 
                    stop:1 rgba(139, 92, 246, 0.3));
                color: #ffffff;
            }}
        """
    
    @staticmethod
    def get_chat_widget_style():
        """채팅 위젯 스타일 - 고급 블랙 테마"""
        colors = FlatTheme.get_theme_colors()
        return f"""
            QWidget {{
                background-color: {colors.get('background', '#5a5a5f')};
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            }}
            QWebEngineView {{
                background-color: {colors.get('background', '#5a5a5f')};
            }}
        """
    
    @staticmethod
    def get_theme_colors():
        """테마 색상 반환"""
        from ui.styles.theme_manager import theme_manager
        if theme_manager.use_material_theme:
            return theme_manager.material_manager.get_theme_colors()
        else:
            # 기본 Flat 테마 색상
            return {
                'background': '#5a5a5f',
                'surface': '#4a4a4f',
                'primary': '#64c8ff',
                'text_primary': '#ffffff'
            }
    
    @staticmethod
    def get_input_area_style():
        """입력 영역 스타일 - 고급 다크 테마"""
        colors = FlatTheme.get_theme_colors()
        background_color = colors.get('background', '#5a5a5f')
        
        return {
            'container': """
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 rgba(45, 45, 55, 0.95), 
                        stop:1 rgba(35, 35, 45, 0.95));
                    border: 2px solid rgba(100, 200, 255, 0.3);
                    border-radius: 16px;

                }
            """,
            'mode_toggle': f"""
                QPushButton {{
                    background-color: {background_color};
                    color: #e8e8e8;
                    border: 1px solid {background_color};
                    border-radius: 12px;
                    padding: 6px 18px;
                    font-size: 40px;
                    font-weight: 700;
                    font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                    min-width: 100px;
                    max-width: 100px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-right: 8px;
                    margin-left: 12px;
                }}
                QPushButton:hover {{
                    background-color: {background_color};
                    color: #ffffff;
                    font-size: 44px;
                }}
                QPushButton:checked {{
                    background-color: {background_color};
                    color: #ffffff;
                }}
            """,
            'input_text': f"""
                QTextEdit {{
                    background: {background_color};
                    color: #e8e8e8;
                    border: none;
                    border-radius: 12px;
                    font-size: 15px;
                    font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                    padding: 8px;
                    selection-background-color: rgba(100, 200, 255, 0.3);
                    line-height: 1.6;
                }}
                QTextEdit::placeholder {{
                    color: #8a8a8a;
                }}
                QTextEdit:focus {{
                    border: none;
                }}
            """,
            'send_button': """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(100, 200, 255, 0.8), 
                        stop:1 rgba(150, 100, 255, 0.8));
                    color: #ffffff;
                    border: 2px solid rgba(100, 200, 255, 0.4);
                    border-radius: 14px;
                    font-weight: 800;
                    font-size: 16px;
                    font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                    padding: 2px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(120, 220, 255, 0.9), 
                        stop:1 rgba(170, 120, 255, 0.9));
                    border-color: rgba(100, 200, 255, 0.6);
                    transform: scale(1.05);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(80, 180, 235, 0.7), 
                        stop:1 rgba(130, 80, 235, 0.7));
                    transform: scale(0.98);
                }
                QPushButton:disabled {
                    background: rgba(55, 65, 81, 0.5);
                    color: #6b7280;
                    border-color: rgba(100, 100, 100, 0.2);
                }
            """,
            'cancel_button': """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(255, 100, 100, 0.8), 
                        stop:1 rgba(255, 150, 100, 0.8));
                    color: #ffffff;
                    border: 2px solid rgba(255, 100, 100, 0.4);
                    border-radius: 14px;
                    font-weight: 800;
                    font-size: 16px;
                    font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                    padding: 2px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(255, 120, 120, 0.9), 
                        stop:1 rgba(255, 170, 120, 0.9));
                    border-color: rgba(255, 100, 100, 0.6);
                    transform: scale(1.05);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(235, 80, 80, 0.7), 
                        stop:1 rgba(235, 130, 80, 0.7));
                    transform: scale(0.98);
                }
            """,
            'upload_button': """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(150, 255, 150, 0.2), 
                        stop:1 rgba(100, 255, 200, 0.2));
                    color: #b0e0b0;
                    border: 2px solid rgba(150, 255, 150, 0.3);
                    border-radius: 14px;
                    font-weight: 700;
                    font-size: 13px;
                    font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                    padding: 2px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(170, 255, 170, 0.3), 
                        stop:1 rgba(120, 255, 220, 0.3));
                    color: #ffffff;
                    border-color: rgba(150, 255, 150, 0.5);
                    transform: scale(1.05);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(130, 235, 130, 0.2), 
                        stop:1 rgba(80, 235, 180, 0.2));
                    transform: scale(0.98);
                }
                QPushButton:disabled {
                    background: rgba(50, 50, 50, 0.5);
                    color: #6b7280;
                    border-color: rgba(100, 100, 100, 0.2);
                }
            """,
            'template_button': """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(255, 200, 100, 0.2), 
                        stop:1 rgba(255, 150, 200, 0.2));
                    color: #e0c0b0;
                    border: 2px solid rgba(255, 200, 100, 0.3);
                    border-radius: 14px;
                    font-weight: 700;
                    font-size: 12px;
                    font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                    padding: 2px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(255, 220, 120, 0.3), 
                        stop:1 rgba(255, 170, 220, 0.3));
                    color: #ffffff;
                    border-color: rgba(255, 200, 100, 0.5);
                    transform: scale(1.05);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(235, 180, 80, 0.2), 
                        stop:1 rgba(235, 130, 180, 0.2));
                    transform: scale(0.98);
                }
                QPushButton:disabled {
                    background: rgba(50, 50, 50, 0.5);
                    color: #6b7280;
                    border-color: rgba(100, 100, 100, 0.2);
                }
            """
        }
    
    @staticmethod
    def get_info_labels_style():
        """정보 라벨 스타일 - 고급 다크 테마"""
        return {
            'model_label': """
                QLabel {
                    color: #ffffff;
                    font-size: 16px;
                    font-weight: 700;
                    font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                    padding: 14px 18px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 rgba(100, 200, 255, 0.3), 
                        stop:1 rgba(150, 100, 255, 0.3));
                    border: 2px solid rgba(100, 200, 255, 0.4);
                    border-radius: 12px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
            """,
            'tools_label': """
                QLabel {
                    color: #b0e0b0;
                    font-size: 16px;
                    font-weight: 700;
                    font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                    padding: 14px 18px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 rgba(150, 255, 150, 0.2), 
                        stop:1 rgba(100, 255, 200, 0.2));
                    border: 2px solid rgba(150, 255, 150, 0.3);
                    border-radius: 12px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
            """,
            'status_label': """
                QLabel {
                    color: #e0e0e0;
                    font-size: 12px;
                    font-weight: 600;
                    font-family: 'Malgun Gothic', '맑은 고딕', system-ui, sans-serif;
                    padding: 8px 16px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 rgba(200, 200, 200, 0.1), 
                        stop:1 rgba(150, 150, 150, 0.1));
                    border: 2px solid rgba(200, 200, 200, 0.2);
                    border-radius: 10px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
            """
        }
    
    @staticmethod
    def get_chat_display_css():
        """채팅 표시 영역 CSS - 첨부 이미지 디자인 매칭"""
        colors = FlatTheme.get_theme_colors()
        bg_color = colors.get('background', '#5a5a5f')
        return f"""
        * {{ 
            box-sizing: border-box !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        
        html, body {{
            background: {bg_color} !important;
            color: #ffffff !important;
            font-family: 'Malgun Gothic', '맑은 고딕', 'Apple SD Gothic Neo', sans-serif !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
            margin: 0 !important;
            padding: 6px !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            min-height: 100vh !important;
        }}
        
        .message {{
            margin: 6px 0 !important;
            padding: 10px 14px !important;
            position: relative !important;
            border-radius: 4px !important;
            border: none !important;
            transition: none !important;
            transform: none !important;
        }}
        
        .message:hover {{
            transform: none !important;
        }}
        
        .message.user {{
            background: transparent !important;
            color: #ffffff !important;
        }}
        
        .message.ai {{
            background: transparent !important;
            color: #ffffff !important;
        }}
        
        .message.system {{
            background: transparent !important;
            color: #e0e0e0 !important;
            font-size: 13px !important;
        }}
        
        .message-header {{
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            margin-bottom: 4px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            opacity: 0.9 !important;
        }}
        
        .message.user .message-header {{
            color: #cccccc !important;
        }}
        
        .message.ai .message-header {{
            color: #cccccc !important;
        }}
        
        .message.system .message-header {{
            color: #999999 !important;
        }}
        
        .message-content {{
            line-height: 1.5 !important;
            font-weight: 400 !important;
            color: #c0c0c0 !important;
            font-size: 14px !important;
        }}
        
        .copy-message-btn {{
            position: absolute !important;
            top: 14px !important;
            right: 18px !important;
            background: rgba(95,95,100,0.9) !important;
            color: #d0d0d0 !important;
            border: 1px solid rgba(160,160,165,0.6) !important;
            padding: 8px 12px !important;
            border-radius: 6px !important;
            cursor: pointer !important;
            font-size: 12px !important;
            font-weight: 700 !important;
            font-family: 'Malgun Gothic', '맑은 고딕', 'Apple SD Gothic Neo', sans-serif !important;
            opacity: 1 !important;
            transition: all 0.25s ease !important;
            z-index: 15 !important;
        }}
        
        .copy-message-btn:hover {{
            background: rgba(105,105,110,0.95) !important;
            border-color: rgba(180,180,185,0.8) !important;
            color: #f0f0f0 !important;
            transform: scale(1.05) !important;
        }}
        
        .copy-message-btn:active {{
            background: rgba(115,115,120,0.85) !important;
            transform: scale(0.98) !important;
        }}
        
        .message.user .copy-message-btn {{
            background: rgba(100,100,105,0.9) !important;
            border-color: rgba(170,170,175,0.7) !important;
            color: #e8e8e8 !important;
        }}
        
        .message.user .copy-message-btn:hover {{
            background: rgba(110,110,115,0.95) !important;
            border-color: rgba(190,190,195,0.8) !important;
            color: #f0f0f0 !important;
        }}
        
        pre {{
            background: {bg_color} !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 16px !important;
            margin: 12px 0 !important;
            overflow-x: auto !important;
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', Consolas, monospace !important;
            font-size: 13px !important;
            color: #d4d4d4 !important;
            line-height: 1.4 !important;
            position: relative !important;
        }}
        
        pre::before,
        pre::after {{
            display: none !important;
        }}
        
        code {{
            background: {bg_color} !important;
            border: none !important;
            border-radius: 3px !important;
            padding: 2px 6px !important;
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', Consolas, monospace !important;
            font-size: 12px !important;
            color: #ce9178 !important;
        }}
        
        pre code {{
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            color: #d4d4d4 !important;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-weight: 600 !important;
            margin: 8px 0 4px 0 !important;
            color: #c0c0c0 !important;
        }}
        
        h1 {{ font-size: 24px !important; }}
        h2 {{ font-size: 20px !important; }}
        h3 {{ font-size: 18px !important; }}
        h4 {{ font-size: 16px !important; }}
        h5 {{ font-size: 15px !important; }}
        h6 {{ font-size: 14px !important; }}
        
        p {{
            margin: 4px 0 !important;
            color: #c0c0c0 !important;
        }}
        
        ul, ol {{
            margin: 4px 0 !important;
            padding-left: 20px !important;
            color: #c0c0c0 !important;
        }}
        
        li {{
            margin: 2px 0 !important;
            line-height: 1.5 !important;
        }}
        
        blockquote {{
            border-left: 3px solid #666666 !important;
            padding-left: 16px !important;
            margin: 12px 0 !important;
            color: #cccccc !important;
            font-style: italic !important;
            background: rgba(255,255,255,0.02) !important;
            padding: 12px 16px !important;
            border-radius: 0 4px 4px 0 !important;
        }}
        
        a {{
            color: #87ceeb !important;
            text-decoration: none !important;
        }}
        
        a:hover {{
            color: #add8e6 !important;
            text-decoration: underline !important;
        }}
        
        strong {{
            color: #c0c0c0 !important;
            font-weight: 600 !important;
        }}
        
        em {{
            color: #e0e0e0 !important;
            font-style: italic !important;
        }}
        
        ::-webkit-scrollbar {{
            width: 6px !important;
            height: 6px !important;
        }}
        
        ::-webkit-scrollbar-track {{
            background: transparent !important;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #555555 !important;
            border-radius: 3px !important;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #666666 !important;
        }}
        
        .file-attachment {{
            background: transparent !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 4px !important;
            padding: 12px 16px !important;
            margin: 8px 0 !important;
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
        }}
        
        .file-icon {{
            font-size: 18px !important;
            width: 32px !important;
            height: 32px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: transparent !important;
            border-radius: 4px !important;
        }}
        
        .file-info {{
            flex: 1 !important;
        }}
        
        .file-name {{
            font-weight: 500 !important;
            color: #ffffff !important;
            font-size: 13px !important;
            margin-bottom: 2px !important;
        }}
        
        .file-size {{
            font-size: 11px !important;
            color: #999999 !important;
        }}
        
        .file-remove {{
            background: rgba(255,0,0,0.2) !important;
            color: #ff6b6b !important;
            border: none !important;
            border-radius: 3px !important;
            padding: 4px 8px !important;
            font-size: 11px !important;
            cursor: pointer !important;
        }}
        """
    
    @staticmethod
    def get_loading_bar_style():
        """현대적이고 화려한 로딩 바 스타일 - 네온 그라데이션 애니메이션"""
        return """
            QProgressBar {
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(15, 15, 25, 0.9), 
                    stop:0.5 rgba(25, 15, 35, 0.9),
                    stop:1 rgba(15, 25, 35, 0.9));
                border-radius: 8px;
                border: 2px solid rgba(100, 200, 255, 0.3);
                height: 8px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(255, 0, 150, 0.9),
                    stop:0.2 rgba(255, 100, 0, 0.9),
                    stop:0.4 rgba(255, 255, 0, 0.9),
                    stop:0.6 rgba(0, 255, 150, 0.9),
                    stop:0.8 rgba(0, 150, 255, 0.9),
                    stop:1 rgba(150, 0, 255, 0.9));
                border-radius: 6px;
                border: none;
            }
        """