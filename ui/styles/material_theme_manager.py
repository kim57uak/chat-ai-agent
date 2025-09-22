"""Material Theme Manager - Material Design 테마 시스템"""

import json
import os
from typing import Dict, Any, Optional
from enum import Enum


class MaterialThemeType(Enum):
    # Light Themes
    MATERIAL_LIGHT = "material_light"
    MATERIAL_LIGHTER = "material_lighter"
    MATERIAL_PALENIGHT = "material_palenight"
    MATERIAL_SKYBLUE = "material_skyblue"
    MATERIAL_SANDYBEACH = "material_sandybeach"
    MATERIAL_GITHUB = "material_github"
    MATERIAL_SOLARIZED_LIGHT = "material_solarized_light"
    
    # Dark Themes
    MATERIAL_DARK = "material_dark"
    MATERIAL_OCEAN = "material_ocean"
    MATERIAL_DARKER = "material_darker"
    MATERIAL_FOREST = "material_forest"
    MATERIAL_VOLCANO = "material_volcano"
    MATERIAL_DRACULA = "material_dracula"
    MATERIAL_GITHUB_DARK = "material_github_dark"
    MATERIAL_ARC_DARK = "material_arc_dark"
    MATERIAL_ONE_DARK = "material_one_dark"
    MATERIAL_MOONLIGHT = "material_moonlight"
    MATERIAL_NIGHT_OWL = "material_night_owl"
    MATERIAL_SOLARIZED_DARK = "material_solarized_dark"
    ZOMBIE_DARK = "zombie_dark"
    IPHONE_DARK = "iphone_dark"
    DEEP_DARK = "deep_dark"
    ICE_AGE = "ice_age"
    CRYPTO_BITCOIN = "crypto_bitcoin"
    CRYPTO_ETHEREUM = "crypto_ethereum"


class MaterialThemeManager:
    """Material Design 테마 관리자"""
    
    def __init__(self, theme_file: str = "theme.json"):
        self.theme_file = theme_file
        self.themes = {}
        self.current_theme_key = "material_dark"
        self._load_themes()
    
    def _load_themes(self):
        """테마 파일에서 테마 정보 로드"""
        try:
            if os.path.exists(self.theme_file):
                with open(self.theme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.themes = data.get("themes", {})
                    # 현재 테마가 이미 설정되어 있지 않은 경우에만 업데이트
                    if not hasattr(self, '_theme_loaded'):
                        self.current_theme_key = data.get("current_theme", "material_dark")
                        self._theme_loaded = True
            else:
                self._create_default_themes()
        except Exception as e:
            print(f"테마 로드 오류: {e}")
            self._create_default_themes()
    
    @property
    def current_theme(self):
        """현재 테마 객체 반환 (호환성을 위해)"""
        return type('ThemeType', (), {'value': self.current_theme_key})()
    
    @current_theme.setter
    def current_theme(self, value):
        """현재 테마 설정 (호환성을 위해)"""
        if hasattr(value, 'value'):
            self.current_theme_key = value.value
        else:
            self.current_theme_key = str(value)
    
    def _create_default_themes(self):
        """기본 테마 생성"""
        default_data = {
            "current_theme": "material_dark",
            "themes": {
                "material_dark": {
                    "name": "Material Dark",
                    "type": "dark",
                    "colors": {
                        "background": "#121212",
                        "surface": "#1e1e1e",
                        "primary": "#bb86fc",
                        "text_primary": "#ffffff"
                    }
                }
            }
        }
        self.themes = default_data["themes"]
        self._save_themes()
    
    def _save_themes(self):
        """현재 테마 설정을 파일에 저장"""
        try:
            data = {
                "current_theme": self.current_theme_key,
                "themes": self.themes
            }
            with open(self.theme_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"테마 저장 오류: {e}")
    
    def get_current_theme(self) -> Dict[str, Any]:
        """현재 테마 정보 반환"""
        return self.themes.get(self.current_theme_key, {})
    
    def set_theme(self, theme_key: str):
        """테마 변경"""
        if theme_key in self.themes:
            self.current_theme_key = theme_key
            self._save_themes()
        else:
            print(f"존재하지 않는 테마: {theme_key}")
    
    def get_theme_colors(self) -> Dict[str, str]:
        """현재 테마의 색상 정보 반환"""
        theme = self.get_current_theme()
        return theme.get("colors", {})
    
    def get_loading_bar_config(self) -> Dict[str, str]:
        """현재 테마의 로딩바 설정 반환"""
        theme = self.get_current_theme()
        return theme.get("loading_bar", {})
    
    def is_dark_theme(self) -> bool:
        """현재 테마가 다크 테마인지 확인"""
        theme = self.get_current_theme()
        return theme.get("type", "dark") == "dark"
    
    def generate_qt_stylesheet(self) -> str:
        """Qt 스타일시트 생성"""
        colors = self.get_theme_colors()
        loading_config = self.get_loading_bar_config()
        
        return f"""
        QMainWindow {{
            background-color: {colors.get('background', '#121212')};
            color: {colors.get('text_primary', '#ffffff')};
        }}
        
        QWidget {{
            background-color: {colors.get('background', '#121212')};
            color: {colors.get('text_primary', '#ffffff')};
        }}
        
        QMenuBar {{
            background-color: {colors.get('surface', '#1e1e1e')};
            color: {colors.get('text_primary', '#ffffff')};
            border: none;
            border-bottom: 1px solid {colors.get('divider', '#333333')};
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
            background-color: {colors.get('primary', '#bb86fc')};
            color: {colors.get('on_primary', '#000000')};
        }}
        
        QMenu {{
            background-color: {colors.get('surface', '#1e1e1e')};
            color: {colors.get('text_primary', '#ffffff')};
            border: 1px solid {colors.get('divider', '#333333')};
            border-radius: 8px;
            padding: 8px;
        }}
        
        QMenu::item {{
            padding: 12px 20px;
            border-radius: 6px;
            margin: 2px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors.get('primary', '#bb86fc')};
            color: {colors.get('on_primary', '#000000')};
        }}
        
        QPushButton {{
            background-color: {colors.get('primary', '#bb86fc')};
            color: {colors.get('on_primary', '#000000')};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            font-size: 14px;
        }}
        
        QPushButton:hover {{
            background-color: {colors.get('primary_variant', '#3700b3')};
        }}
        
        QPushButton:pressed {{
            background-color: {colors.get('primary_variant', '#3700b3')};
        }}
        
        QTextEdit {{
            background-color: {colors.get('surface', '#1e1e1e')};
            color: {colors.get('text_primary', '#ffffff')};
            border: 1px solid {colors.get('divider', '#333333')};
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            selection-background-color: {colors.get('primary', '#bb86fc')};
        }}
        
        QTextEdit:focus {{
            border-color: {colors.get('primary', '#bb86fc')};
        }}
        
        QLabel {{
            color: {colors.get('text_primary', '#ffffff')};
            font-size: 14px;
        }}
        
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
        
        QScrollBar:vertical {{
            background: {colors.get('surface', '#1e1e1e')};
            width: 12px;
            border-radius: 6px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background: {colors.get('primary', '#bb86fc')};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {colors.get('primary_variant', '#3700b3')};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        """
    
    def _get_code_text_color(self) -> str:
        """코드 블록용 텍스트 색상 반환"""
        colors = self.get_theme_colors()
        # True Gray 테마 특별 처리
        if colors.get('primary') == '#6B7280':
            return "#1F2937"  # True Gray: 진한 회색
        elif self.is_dark_theme():
            return "#e8e8e8"  # 다크 테마: 밝은 회색
        else:
            return "#2d3748"  # 라이트 테마: 어두운 회색
    
    def _get_mermaid_text_color(self) -> str:
        """Mermaid 다이어그램용 텍스트 색상 반환"""
        colors = self.get_theme_colors()
        # True Gray 테마 특별 처리
        if colors.get('primary') == '#6B7280':
            return "#1F2937"  # True Gray: 진한 회색
        elif self.is_dark_theme():
            return "#ffffff"  # 다크 테마: 흰색
        else:
            return "#1a202c"  # 라이트 테마: 진한 회색
    
    def _get_mermaid_node_fill(self) -> str:
        """Mermaid 노드 배경색 반환"""
        colors = self.get_theme_colors()
        # True Gray 테마 특별 처리
        if colors.get('primary') == '#6B7280':
            return "#F3F4F6"  # True Gray: 밝은 회색
        elif self.is_dark_theme():
            return "#4a5568"  # 다크 테마: 어두운 회색
        else:
            return "#f7fafc"  # 라이트 테마: 밝은 회색
    
    def _get_button_colors(self) -> Dict[str, str]:
        """버튼 색상 반환"""
        if self.is_dark_theme():
            return {
                "copy_bg": "rgba(95,95,100,0.45)",
                "copy_text": "rgba(208,208,208,0.7)",
                "copy_border": "rgba(160,160,165,0.3)",
                "copy_hover_bg": "rgba(105,105,110,0.475)",
                "copy_hover_text": "rgba(240,240,240,0.85)",
                "delete_bg": "rgba(220,53,69,0.4)",
                "delete_text": "rgba(255,255,255,0.7)",
                "delete_border": "rgba(220,53,69,0.3)",
                "delete_hover_bg": "rgba(220,53,69,0.475)"
            }
        else:
            return {
                "copy_bg": "rgba(107,114,128,0.15)",
                "copy_text": "rgba(55,65,81,0.8)",
                "copy_border": "rgba(156,163,175,0.4)",
                "copy_hover_bg": "rgba(107,114,128,0.25)",
                "copy_hover_text": "rgba(31,41,55,0.9)",
                "delete_bg": "rgba(239,68,68,0.15)",
                "delete_text": "rgba(127,29,29,0.8)",
                "delete_border": "rgba(239,68,68,0.4)",
                "delete_hover_bg": "rgba(239,68,68,0.25)"
            }
    
    def generate_web_css(self) -> str:
        """웹뷰용 Material Design CSS 생성"""
        colors = self.get_theme_colors()
        code_text_color = self._get_code_text_color()
        mermaid_text_color = self._get_mermaid_text_color()
        mermaid_node_fill = self._get_mermaid_node_fill()
        
        return f"""
        * {{
            box-sizing: border-box;
        }}
        
        html, body {{
            background-color: {colors.get('background', '#121212')} !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
            font-family: 'Roboto', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
            font-size: 16px !important;
            font-weight: 400 !important;
            line-height: 1.5 !important;
            letter-spacing: 0.15px !important;
            margin: 0 !important;
            padding: 16px !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }}
        
        .message {{
            margin: 24px 0 !important;
            padding: 16px 20px !important;
            border-radius: 12px !important;
            position: relative !important;
            transition: all 0.2s cubic-bezier(0.4, 0.0, 0.2, 1) !important;
            box-shadow: 0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12) !important;
        }}
        
        .message:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0px 3px 3px -2px rgba(0,0,0,0.2), 0px 3px 4px 0px rgba(0,0,0,0.14), 0px 1px 8px 0px rgba(0,0,0,0.12) !important;
        }}
        
        .message.user {{
            background: {colors.get('user_bg', 'rgba(187, 134, 252, 0.12)')} !important;
            border-left: 3px solid {colors.get('user_border', '#bb86fc')} !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        
        .message.ai {{
            background: {colors.get('ai_bg', 'rgba(3, 218, 198, 0.12)')} !important;
            border-left: 3px solid {colors.get('ai_border', '#03dac6')} !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        
        .message.system {{
            background: {colors.get('system_bg', 'rgba(179, 179, 179, 0.12)')} !important;
            border-left: 3px solid {colors.get('system_border', '#b3b3b3')} !important;
            color: {colors.get('text_secondary', '#b3b3b3')} !important;
            font-size: 13px !important;
        }}
        
        .message-header {{
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            margin-bottom: 8px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            opacity: 0.9 !important;
            color: {colors.get('text_secondary', '#b3b3b3')} !important;
        }}
        
        .message-content {{
            line-height: 1.6 !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        
        /* True Gray 테마 특별 처리 */
        .message.system .message-content {{
            color: {colors.get('text_secondary', '#6B7280')} !important;
        }}
        
        .copy-message-btn {{
            position: absolute !important;
            top: 12px !important;
            right: 16px !important;
            background-color: {colors.get('surface', '#1e1e1e')} !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
            border: 1px solid {colors.get('divider', '#333333')} !important;
            padding: 6px 12px !important;
            border-radius: 6px !important;
            cursor: pointer !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            opacity: 0 !important;
            transition: all 0.2s ease !important;
        }}
        
        .message:hover .copy-message-btn {{
            opacity: 1 !important;
        }}
        
        .copy-message-btn:hover {{
            background-color: {colors.get('primary', '#bb86fc')} !important;
            color: {colors.get('on_primary', '#000000')} !important;
            border-color: {colors.get('primary', '#bb86fc')} !important;
        }}
        
        pre {{
            background-color: {colors.get('code_bg', '#2d2d2d')} !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 16px !important;
            margin: 16px 0 !important;
            overflow-x: auto !important;
            font-family: 'Roboto Mono', 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace !important;
            font-size: 14px !important;
            font-weight: 400 !important;
            line-height: 1.43 !important;
            letter-spacing: 0.25px !important;
            color: {code_text_color} !important;
            box-shadow: 0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12) !important;
        }}
        
        code {{
            background-color: {colors.get('code_bg', '#2d2d2d')} !important;
            border: 1px solid {colors.get('code_border', '#404040')} !important;
            border-radius: 4px !important;
            padding: 2px 6px !important;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace !important;
            font-size: 12px !important;
            color: {code_text_color} !important;
        }}
        
        pre code {{
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            color: inherit !important;
        }}
        
        h1 {{
            color: {colors.get('text_primary', '#ffffff')} !important;
            font-size: 24px !important;
            font-weight: 400 !important;
            line-height: 1.334 !important;
            letter-spacing: 0px !important;
            margin: 24px 0 16px 0 !important;
        }}
        
        h2 {{
            color: {colors.get('text_primary', '#ffffff')} !important;
            font-size: 20px !important;
            font-weight: 500 !important;
            line-height: 1.6 !important;
            letter-spacing: 0.15px !important;
            margin: 20px 0 12px 0 !important;
        }}
        
        h3, h4, h5, h6 {{
            color: {colors.get('text_primary', '#ffffff')} !important;
            font-size: 16px !important;
            font-weight: 500 !important;
            line-height: 1.57 !important;
            letter-spacing: 0.1px !important;
            margin: 16px 0 8px 0 !important;
        }}
        
        p {{
            margin: 8px 0 !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        
        /* True Gray 테마에서 더 진한 텍스트 색상 사용 */
        .message p {{
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        
        .message.system p {{
            color: {colors.get('text_secondary', '#6B7280')} !important;
        }}
        
        ul, ol {{
            margin: 8px 0 !important;
            padding-left: 20px !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        
        li {{
            margin: 4px 0 !important;
            line-height: 1.5 !important;
        }}
        
        blockquote {{
            border-left: 3px solid {colors.get('primary', '#bb86fc')} !important;
            padding-left: 16px !important;
            margin: 12px 0 !important;
            color: {colors.get('text_secondary', '#b3b3b3')} !important;
            font-style: italic !important;
            background: {colors.get('surface', '#1e1e1e')} !important;
            padding: 12px 16px !important;
            border-radius: 0 8px 8px 0 !important;
        }}
        
        a {{
            color: {colors.get('primary', '#bb86fc')} !important;
            text-decoration: none !important;
        }}
        
        a:hover {{
            color: {colors.get('primary_variant', '#3700b3')} !important;
            text-decoration: underline !important;
        }}
        
        strong {{
            color: {colors.get('text_primary', '#ffffff')} !important;
            font-weight: 600 !important;
        }}
        
        em {{
            color: {colors.get('text_secondary', '#b3b3b3')} !important;
            font-style: italic !important;
        }}
        
        ::-webkit-scrollbar {{
            width: 8px !important;
            height: 8px !important;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {colors.get('scrollbar_track', '#1e1e1e')} !important;
            border-radius: 4px !important;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {colors.get('scrollbar', '#555555')} !important;
            border-radius: 4px !important;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {colors.get('primary', '#bb86fc')} !important;
        }}
        
        /* Mermaid 다이어그램 테마별 스타일 */
        .mermaid {{
            background-color: {colors.get('code_bg', '#2d2d2d')} !important;
            border: 1px solid {colors.get('code_border', '#404040')} !important;
            border-radius: 8px !important;
            padding: 20px !important;
            margin: 16px 0 !important;
            text-align: center !important;
            overflow-x: auto !important;
            min-height: 100px !important;
        }}
        
        .mermaid .node rect,
        .mermaid .node circle,
        .mermaid .node ellipse,
        .mermaid .node polygon {{
            fill: {mermaid_node_fill} !important;
            stroke: {colors.get('primary', '#bb86fc')} !important;
            stroke-width: 2px !important;
        }}
        
        .mermaid .edgePath path {{
            stroke: {colors.get('primary', '#bb86fc')} !important;
            stroke-width: 2px !important;
        }}
        
        .mermaid .edgeLabel {{
            background-color: {colors.get('code_bg', '#2d2d2d')} !important;
            color: {mermaid_text_color} !important;
        }}
        
        .mermaid text {{
            fill: {mermaid_text_color} !important;
            font-family: inherit !important;
        }}
        
        /* 테이블 스타일 */
        table {{
            border-collapse: collapse !important;
            width: 100% !important;
            margin: 12px 0 !important;
            background-color: {colors.get('surface', '#1e1e1e')} !important;
            border: 1px solid {colors.get('code_border', '#404040')} !important;
            border-radius: 8px !important;
            overflow: hidden !important;
        }}
        
        th {{
            background-color: {colors.get('primary', '#bb86fc')} !important;
            color: {colors.get('on_primary', '#000000')} !important;
            padding: 12px !important;
            text-align: left !important;
            font-weight: 600 !important;
            border-bottom: 2px solid {colors.get('primary_variant', '#3700b3')} !important;
        }}
        
        td {{
            padding: 10px 12px !important;
            border-bottom: 1px solid {colors.get('divider', '#333333')} !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
            vertical-align: top !important;
        }}
        
        tr:nth-child(even) {{
            background-color: {colors.get('code_bg', '#2d2d2d')} !important;
        }}
        
        tr:hover {{
            background-color: {colors.get('user_bg', 'rgba(187, 134, 252, 0.12)')} !important;
        }}
        
        /* 테이블 내부 요소들 */
        table p {{
            margin: 4px 0 !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        
        table strong {{
            color: {colors.get('text_primary', '#ffffff')} !important;
            font-weight: 600 !important;
        }}
        
        table em {{
            color: {colors.get('text_secondary', '#b3b3b3')} !important;
            font-style: italic !important;
        }}
        
        table code {{
            background-color: {colors.get('background', '#121212')} !important;
            color: {code_text_color} !important;
            border: 1px solid {colors.get('divider', '#333333')} !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
            font-size: 11px !important;
        }}
        
        table a {{
            color: {colors.get('primary', '#bb86fc')} !important;
            text-decoration: none !important;
        }}
        
        table a:hover {{
            color: {colors.get('primary_variant', '#3700b3')} !important;
            text-decoration: underline !important;
        }}
        
        table ul, table ol {{
            margin: 4px 0 !important;
            padding-left: 16px !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        
        table li {{
            margin: 2px 0 !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        """
    
    def get_available_themes(self) -> Dict[str, str]:
        """사용 가능한 테마 목록 반환"""
        return {theme_key: theme_data.get("name", theme_key) 
                for theme_key, theme_data in self.themes.items()}


# 전역 Material Theme Manager 인스턴스
material_theme_manager = MaterialThemeManager()