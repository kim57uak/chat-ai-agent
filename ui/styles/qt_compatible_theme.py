"""Qt 호환 테마 스타일시트 생성기"""

def generate_qt_compatible_stylesheet(colors, primary):
    """Qt에서 지원하는 CSS 속성만 사용하여 스타일시트 생성"""
    
    def hex_to_rgb(hex_color: str) -> str:
        """HEX 색상을 RGB로 변환"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return f"{int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}"
        return "139, 92, 246"
    
    surface = colors.get('surface', '#1e1e1e')
    background = colors.get('background', '#121212')
    
    return f"""
    /* 기본 설정 */
    * {{
        font-family: "Inter", "SF Pro Display", system-ui, sans-serif;
    }}
    
    QMainWindow {{
        background: {background};
        color: {colors.get('text_primary', '#f8fafc')};
    }}
    
    QWidget {{
        background: transparent;
        color: {colors.get('text_primary', '#f8fafc')};
    }}
    
    /* 메뉴바 */
    QMenuBar {{
        background: {surface};
        border: none;
        border-bottom: 1px solid {colors.get('divider', 'rgba(51, 65, 85, 0.6)')};
        font-size: 13px;
        padding: 8px 0;
    }}
    
    QMenuBar::item {{
        background: transparent;
        padding: 8px 16px;
        border-radius: 8px;
        margin: 0 4px;
    }}
    
    QMenuBar::item:selected {{
        background: rgba({hex_to_rgb(primary)}, 0.1);
        color: {primary};
    }}
    
    /* 메뉴 */
    QMenu {{
        background: {surface};
        border: 1px solid {colors.get('divider', 'rgba(51, 65, 85, 0.6)')};
        border-radius: 12px;
        padding: 8px;
    }}
    
    QMenu::item {{
        padding: 10px 16px;
        border-radius: 6px;
        margin: 1px;
    }}
    
    QMenu::item:selected {{
        background: rgba({hex_to_rgb(primary)}, 0.1);
        color: {primary};
    }}
    
    /* 버튼 */
    QPushButton {{
        background: transparent;
        color: {primary};
        border: 1px solid rgba({hex_to_rgb(primary)}, 0.3);
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 13px;
    }}
    
    QPushButton:hover {{
        background: rgba({hex_to_rgb(primary)}, 0.1);
        border-color: {primary};
    }}
    
    QPushButton:pressed {{
        background: rgba({hex_to_rgb(primary)}, 0.2);
    }}
    
    /* 텍스트 편집기 */
    QTextEdit {{
        background: {surface};
        color: {colors.get('text_primary', '#f8fafc')};
        border: 1px solid {colors.get('divider', 'rgba(51, 65, 85, 0.6)')};
        border-radius: 12px;
        padding: 16px;
        font-size: 14px;
        selection-background-color: rgba({hex_to_rgb(primary)}, 0.3);
    }}
    
    QTextEdit:focus {{
        border-color: {primary};
    }}
    
    /* 라벨 */
    QLabel {{
        color: {colors.get('text_primary', '#f8fafc')};
        font-size: 14px;
    }}
    
    /* 프로그레스바 */
    QProgressBar {{
        border: none;
        background: rgba({hex_to_rgb(primary)}, 0.1);
        border-radius: 4px;
        height: 6px;
    }}
    
    QProgressBar::chunk {{
        background: {primary};
        border-radius: 3px;
    }}
    
    /* 스크롤바 */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        border-radius: 4px;
    }}
    
    QScrollBar::handle:vertical {{
        background: rgba({hex_to_rgb(primary)}, 0.4);
        border-radius: 4px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: rgba({hex_to_rgb(primary)}, 0.6);
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
        height: 0px;
    }}
    
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    /* 스플리터 */
    QSplitter::handle {{
        background: {colors.get('divider', 'rgba(51, 65, 85, 0.6)')};
        border-radius: 2px;
    }}
    
    QSplitter::handle:hover {{
        background: {primary};
    }}
    """