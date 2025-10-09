"""테마 관리자 - 다중 테마 지원"""
from core.logging import get_logger

logger = get_logger("theme_manager")

from enum import Enum
from typing import Dict, Any
import json
import os
from .material_theme_manager import material_theme_manager
from .material_design_system import material_design_system


class ThemeType(Enum):
    DARK = "dark"
    LIGHT = "light"
    CUSTOM = "custom"


class ThemeManager:
    """테마 관리 클래스"""
    
    def __init__(self):
        self.current_theme = ThemeType.DARK
        self.themes = self._load_default_themes()
        self.custom_themes = self._load_custom_themes()
        self.material_manager = material_theme_manager
        self.use_material_theme = True
        self.material_design = material_design_system
    
    def _load_default_themes(self) -> Dict[str, Dict[str, Any]]:
        """기본 테마 로드"""
        return {
            "dark": {
                "name": "다크 테마",
                "colors": {
                    "background": "linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%)",
                    "text": "#f3f4f6",
                    "user_bg": "linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)",
                    "user_border": "#6366f1",
                    "ai_bg": "linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(5, 150, 105, 0.08) 100%)",
                    "ai_border": "#10b981",
                    "system_bg": "linear-gradient(135deg, rgba(107, 114, 128, 0.08) 0%, rgba(75, 85, 99, 0.08) 100%)",
                    "system_border": "#6b7280",
                    "code_bg": "linear-gradient(135deg, #1f2937 0%, #111827 100%)",
                    "code_border": "#374151",
                    "scrollbar": "linear-gradient(135deg, #4b5563 0%, #374151 100%)",
                    "scrollbar_track": "rgba(0,0,0,0.1)"
                },
                "fonts": {
                    "family": "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
                    "size": "14px",
                    "code_family": "'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, 'Liberation Mono', Menlo, Monaco, monospace"
                },
                "spacing": {
                    "message_margin": "8px 0",
                    "message_padding": "12px",
                    "content_padding": "16px"
                }
            },
            "light": {
                "name": "라이트 테마",
                "colors": {
                    "background": "#ffffff",
                    "text": "#333333",
                    "user_bg": "rgba(163,135,215,0.1)",
                    "user_border": "rgb(163,135,215)",
                    "ai_bg": "rgba(135,163,215,0.1)",
                    "ai_border": "rgb(135,163,215)",
                    "system_bg": "rgba(215,163,135,0.1)",
                    "system_border": "rgb(215,163,135)",
                    "code_bg": "#f8f8f8",
                    "code_border": "#ddd",
                    "scrollbar": "#ccc",
                    "scrollbar_track": "#f0f0f0"
                },
                "fonts": {
                    "family": "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
                    "size": "14px",
                    "code_family": "'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, 'Liberation Mono', Menlo, Monaco, monospace"
                },
                "spacing": {
                    "message_margin": "8px 0",
                    "message_padding": "12px",
                    "content_padding": "16px"
                }
            }
        }
    
    def _load_custom_themes(self) -> Dict[str, Dict[str, Any]]:
        """커스텀 테마 로드 - 비활성화"""
        # custom_themes.json 파일이 없으므로 빈 딕셔너리 반환
        return {}
    
    def get_current_theme(self) -> Dict[str, Any]:
        """현재 테마 반환"""
        if self.use_material_theme:
            return self.material_manager.get_current_theme()
        
        theme_key = self.current_theme.value
        if theme_key in self.themes:
            return self.themes[theme_key]
        return self.themes["dark"]
    
    def set_theme(self, theme_type: ThemeType):
        """테마 설정"""
        self.current_theme = theme_type
    
    def set_material_theme(self, theme_key: str):
        """Material 테마 설정"""
        self.material_manager.set_theme(theme_key)
        self.use_material_theme = True
    
    def get_material_stylesheet(self) -> str:
        """Material 테마 Qt 스타일시트 반환"""
        return self.material_manager.generate_qt_stylesheet()
    
    def get_material_web_css(self) -> str:
        """Material 테마 웹 CSS 반환"""
        return self.material_manager.generate_web_css()
    
    def get_available_material_themes(self) -> Dict[str, str]:
        """사용 가능한 Material 테마 목록 반환"""
        return self.material_manager.get_available_themes()
    
    def is_material_dark_theme(self) -> bool:
        """현재 Material 테마가 다크 테마인지 확인"""
        return self.material_manager.is_dark_theme()
    
    def get_css_variables(self) -> str:
        """CSS 변수 생성"""
        theme = self.get_current_theme()
        colors = theme.get("colors", {})
        fonts = theme.get("fonts", {})
        spacing = theme.get("spacing", {})
        
        css_vars = ":root {\n"
        
        # 색상 변수
        for key, value in colors.items():
            css_vars += f"  --{key.replace('_', '-')}: {value};\n"
        
        # 폰트 변수
        for key, value in fonts.items():
            css_vars += f"  --font-{key.replace('_', '-')}: {value};\n"
        
        # 간격 변수
        for key, value in spacing.items():
            css_vars += f"  --spacing-{key.replace('_', '-')}: {value};\n"
        
        css_vars += "}\n"
        return css_vars
    
    def generate_theme_css(self) -> str:
        """테마 기반 CSS 생성"""
        theme = self.get_current_theme()
        colors = theme.get("colors", {})
        fonts = theme.get("fonts", {})
        spacing = theme.get("spacing", {})
        
        return f"""
        * {{ box-sizing: border-box; }}
        
        body {{
            background-color: {colors.get('background', '#1a1a1a')};
            color: {colors.get('text', '#e8e8e8')};
            font-family: {fonts.get('family', 'Arial, sans-serif')};
            font-size: {fonts.get('size', '14px')};
            line-height: 1.6;
            margin: 8px;
            padding: 0;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        
        .message {{
            margin: {spacing.get('message_margin', '8px 0')};
            padding: {spacing.get('message_padding', '12px')};
            border-radius: 8px;
            position: relative;
            transition: all 0.2s ease;
        }}
        
        .message:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .message.user {{
            background: {colors.get('user_bg', 'rgba(163,135,215,0.15)')};
            border-left: 3px solid {colors.get('user_border', 'rgb(163,135,215)')};
        }}
        
        .message.ai {{
            background: {colors.get('ai_bg', 'rgba(135,163,215,0.15)')};
            border-left: 3px solid {colors.get('ai_border', 'rgb(135,163,215)')};
        }}
        
        .message.system {{
            background: {colors.get('system_bg', 'rgba(215,163,135,0.15)')};
            border-left: 3px solid {colors.get('system_border', 'rgb(215,163,135)')};
        }}
        
        .message-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 12px;
            opacity: 0.8;
        }}
        
        .message-content {{
            line-height: 1.6;
            padding-left: 4px;
        }}
        
        .copy-message-btn {{
            position: absolute;
            top: 8px;
            right: 8px;
            background: rgba(0,0,0,0.6);
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            opacity: 0;
            transition: opacity 0.2s ease;
        }}
        
        .message:hover .copy-message-btn {{
            opacity: 1;
        }}
        
        .copy-message-btn:hover {{
            background: rgba(0,0,0,0.8);
        }}
        
        pre {{
            background: {colors.get('code_bg', '#1e1e1e')};
            border: 1px solid {colors.get('code_border', '#444')};
            border-radius: 6px;
            padding: 16px;
            margin: 12px 0;
            overflow-x: auto;
            font-family: {fonts.get('code_family', 'monospace')};
            font-size: 13px;
            position: relative;
        }}
        
        code {{
            background: {colors.get('code_bg', '#1e1e1e')};
            border: 1px solid {colors.get('code_border', '#444')};
            border-radius: 3px;
            padding: 2px 6px;
            font-family: {fonts.get('code_family', 'monospace')};
            font-size: 12px;
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {colors.get('scrollbar_track', '#2a2a2a')};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {colors.get('scrollbar', '#555')};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {colors.get('scrollbar', '#555')};
            filter: brightness(1.2);
        }}
        """
    
    def save_custom_theme(self, name: str, theme_data: Dict[str, Any]):
        """커스텀 테마 저장 - 비활성화"""
        # custom_themes.json 파일을 사용하지 않으므로 비활성화
        logger.debug(f"커스텀 테마 저장 기능은 비활성화되어 있습니다: {name}")
    
    def get_material_design_stylesheet(self) -> str:
        """Material Design 기반 스타일시트 생성"""
        if not self.use_material_theme:
            return self.generate_theme_css()
        
        colors = self.material_manager.get_theme_colors()
        from .material_stylesheet import create_material_stylesheet
        return create_material_stylesheet(colors, self.material_design)


# 전역 테마 매니저 인스턴스
theme_manager = ThemeManager()