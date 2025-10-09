"""Material Theme Manager - Material Design 테마 시스템 (수정됨)"""

import json
import os
from typing import Dict, Any, Optional
from utils.config_path import config_path_manager
from core.logging import get_logger

logger = get_logger('ui.theme_manager')

class MaterialThemeManager:
    """Material Design 테마 관리자"""
    
    def __init__(self, theme_file: str = "theme.json"):
        self.theme_file = theme_file
        self.theme_file_path = config_path_manager.get_config_path(theme_file)
        self.themes = {}
        self.theme_categories = {}
        self.current_theme_key = "material_dark"
        self._load_themes()
    
    def _load_themes(self):
        """테마 파일에서 테마 정보 로드"""
        try:
            theme_file_path = config_path_manager.get_config_path(self.theme_file)
            logger.debug(f"Loading theme from: {theme_file_path}")
            if theme_file_path.exists():
                with open(theme_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.themes = data.get("themes", {})
                    self.theme_categories = data.get("theme_categories", {})
                    logger.debug(f"Loaded {len(self.themes)} themes")
                    # 현재 테마가 이미 설정되어 있지 않은 경우에만 업데이트
                    if not hasattr(self, '_theme_loaded'):
                        self.current_theme_key = data.get("current_theme", "material_dark")
                        self._theme_loaded = True
            else:
                logger.debug(f"Theme file not found: {theme_file_path}")
                self._create_default_themes()
        except Exception as e:
            logger.error(f"Theme load error: {e}", exc_info=True)
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
        """기본 테마 생성 - 동적 로드"""
        # theme.json 파일이 없을 때만 기본 테마 생성
        if not self.themes:
            self.themes = {}
            self.current_theme_key = "material_dark"
        self._save_themes()
    
    def _save_themes(self):
        """현재 테마 설정을 파일에 저장"""
        try:
            data = {
                "current_theme": self.current_theme_key,
                "themes": self.themes
            }
            with open(self.theme_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Theme save error: {e}", exc_info=True)
    
    def get_current_theme(self) -> Dict[str, Any]:
        """현재 테마 정보 반환"""
        return self.themes.get(self.current_theme_key, {})
    
    def set_theme(self, theme_key: str):
        """테마 변경"""
        if theme_key in self.themes:
            self.current_theme_key = theme_key
            self._save_themes()
        else:
            logger.warning(f"Theme not found: {theme_key}")
    
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
        """Qt 호환 스타일시트 생성"""
        from .qt_compatible_theme import generate_qt_compatible_stylesheet
        
        colors = self.get_theme_colors()
        primary = colors.get('primary', '#8b5cf6')
        
        return generate_qt_compatible_stylesheet(colors, primary)
    
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
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """HEX 색상을 RGB로 변환"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return f"{int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}"
        return "139, 92, 246"  # 기본값
    
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
    
    def is_glassmorphism_enabled(self) -> bool:
        """글래스모피즘 활성화 상태 확인"""
        try:
            if self.theme_file_path.exists():
                with open(self.theme_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("glassmorphism_enabled", True)
        except Exception:
            pass
        return True  # 기본값은 활성화
    
    def toggle_glassmorphism(self) -> bool:
        """글래스모피즘 활성화/비활성화 토글"""
        try:
            if self.theme_file_path.exists():
                with open(self.theme_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                current_state = data.get("glassmorphism_enabled", True)
                new_state = not current_state
                data["glassmorphism_enabled"] = new_state
                
                with open(self.theme_file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                return new_state
        except Exception as e:
            logger.error(f"Glassmorphism toggle error: {e}", exc_info=True)
        return True
    
    def get_glassmorphism_config(self) -> Dict[str, Any]:
        """글래스모피즘 설정 반환"""
        theme = self.get_current_theme()
        return theme.get("glassmorphism", {
            "blur_intensity": "20px",
            "saturation": "180%",
            "border_opacity": 0.15,
            "shadow_opacity": 0.1,
            "inset_highlight": "rgba(255, 255, 255, 0.1)"
        })
    
    def _generate_glassmorphism_background(self) -> str:
        """글래스모피즘 배경 생성"""
        colors = self.get_theme_colors()
        primary = colors.get('primary', '#bb86fc')
        secondary = colors.get('secondary', '#03dac6')
        background = colors.get('background', '#121212')
        
        if self.is_dark_theme():
            return f"linear-gradient(135deg, {background} 0%, rgba({self._hex_to_rgb(primary)}, 0.05) 25%, rgba({self._hex_to_rgb(secondary)}, 0.03) 50%, {background} 75%, rgba({self._hex_to_rgb(primary)}, 0.02) 100%)"
        else:
            return f"linear-gradient(135deg, {background} 0%, rgba({self._hex_to_rgb(primary)}, 0.03) 25%, rgba({self._hex_to_rgb(secondary)}, 0.02) 50%, {background} 75%, rgba({self._hex_to_rgb(primary)}, 0.01) 100%)"
    
    def _get_glassmorphism_surface(self, base_color: str) -> str:
        """글래스모피즘 표면 색상 생성"""
        colors = self.get_theme_colors()
        primary = colors.get('primary', '#bb86fc')
        glass_config = self.get_glassmorphism_config()
        
        if self.is_dark_theme():
            return f"linear-gradient(135deg, {base_color}, rgba({self._hex_to_rgb(primary)}, 0.08), rgba(255, 255, 255, 0.02))"
        else:
            return f"linear-gradient(135deg, {base_color}, rgba({self._hex_to_rgb(primary)}, 0.05), rgba(255, 255, 255, 0.4))"
    
    def generate_web_css(self) -> str:
        """웹뷰용 Material Design CSS 생성 (글래스모피즘 적용)"""
        colors = self.get_theme_colors()
        code_text_color = self._get_code_text_color()
        mermaid_text_color = self._get_mermaid_text_color()
        mermaid_node_fill = self._get_mermaid_node_fill()
        background_color = colors.get('background', '#121212')
        
        # 글래스모피즘 효과 설정
        glassmorphism_enabled = self.is_glassmorphism_enabled()
        
        if glassmorphism_enabled:
            glassmorphism_bg = self._generate_glassmorphism_background()
            glass_config = self.get_glassmorphism_config()
            blur_intensity = glass_config.get('blur_intensity', '20px')
            saturation = glass_config.get('saturation', '180%')
            border_opacity = 0.25
            shadow_opacity = 0.15
            inset_highlight = 'rgba(255, 255, 255, 0.15)'
            # 배경에만 블러 효과 적용, 텍스트는 선명하게 유지
            backdrop_filter = f"backdrop-filter: blur({blur_intensity}) saturate({saturation});"
            webkit_backdrop_filter = f"-webkit-backdrop-filter: blur({blur_intensity}) saturate({saturation});"
            box_shadow = f"box-shadow: 0 12px 40px rgba(0, 0, 0, {shadow_opacity}), inset 0 1px 0 {inset_highlight};"
        else:
            glassmorphism_bg = background_color
            border_opacity = 0.12
            backdrop_filter = ""
            webkit_backdrop_filter = ""
            box_shadow = "box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);"
        
        css_content = f"""
        html, body {{
            background: {glassmorphism_bg};
            color: {colors.get('text_primary', '#ffffff')};
            font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            font-size: 15px;
            line-height: 1.6;
            margin: 0;
            padding: 16px;
            {backdrop_filter}
            {webkit_backdrop_filter}
        }}
        
        .message {{
            margin: 24px 0 !important;
            padding: 20px 24px !important;
            border-radius: 20px !important;
            position: relative !important;
            border: 1px solid rgba(255, 255, 255, {border_opacity}) !important;
            {backdrop_filter if glassmorphism_enabled else ''}
            {webkit_backdrop_filter if glassmorphism_enabled else ''}
            {box_shadow}
        }}
        
        .message:hover {{
            background: {colors.get('surface_variant', 'rgba(255, 255, 255, 0.03)')} !important;
        }}
        
        .message.user {{
            background: {self._get_glassmorphism_surface(colors.get('user_bg', 'rgba(187, 134, 252, 0.03)')) if glassmorphism_enabled else colors.get('user_bg', 'rgba(187, 134, 252, 0.03)')} !important;
            border-left: 4px solid {colors.get('user_border', '#bb86fc')} !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
            {backdrop_filter if glassmorphism_enabled else ''}
            {webkit_backdrop_filter if glassmorphism_enabled else ''}
        }}
        
        .message.ai {{
            background: {self._get_glassmorphism_surface(colors.get('ai_bg', 'rgba(3, 218, 198, 0.03)')) if glassmorphism_enabled else colors.get('ai_bg', 'rgba(3, 218, 198, 0.03)')} !important;
            border-left: 4px solid {colors.get('ai_border', '#03dac6')} !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
            {backdrop_filter if glassmorphism_enabled else ''}
            {webkit_backdrop_filter if glassmorphism_enabled else ''}
        }}
        
        .message.system {{
            background: {self._get_glassmorphism_surface(colors.get('system_bg', 'rgba(179, 179, 179, 0.03)')) if glassmorphism_enabled else colors.get('system_bg', 'rgba(179, 179, 179, 0.03)')} !important;
            border-left: 4px solid {colors.get('system_border', '#b3b3b3')} !important;
            color: {colors.get('text_secondary', '#b3b3b3')} !important;
            font-size: 13px !important;
            {backdrop_filter if glassmorphism_enabled else ''}
            {webkit_backdrop_filter if glassmorphism_enabled else ''}
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
        
        .message-content, .message-content * {{
            line-height: 1.6 !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        
        .message-content p, .message-content div, .message-content span {{
            color: {colors.get('text_primary', '#ffffff')} !important;
        }}
        
        .copy-message-btn {{
            position: absolute !important;
            top: 16px !important;
            right: 20px !important;
            background: {self._get_glassmorphism_surface('rgba(255, 255, 255, 0.1)')} !important;
            color: {colors.get('text_primary', '#ffffff')} !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            padding: 8px 16px !important;
            border-radius: 12px !important;
            cursor: pointer !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            opacity: 0 !important;
            backdrop-filter: blur(10px) saturate(180%);
            -webkit-backdrop-filter: blur(10px) saturate(180%);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }}
        
        .message:hover .copy-message-btn {{
            opacity: 1 !important;
        }}
        
        .copy-message-btn:hover {{
            background: linear-gradient(135deg, {colors.get('primary', '#bb86fc')}, {colors.get('primary_variant', '#3700b3')}) !important;
            color: {colors.get('on_primary', '#000000')} !important;
            border-color: {colors.get('primary', '#bb86fc')} !important;
        }}
        
        pre {{
            background: {self._get_glassmorphism_surface(colors.get('code_bg', '#2d2d2d'))} !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            margin: 20px 0 !important;
            overflow-x: auto !important;
            font-family: 'Roboto Mono', 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace !important;
            font-size: 14px !important;
            font-weight: 400 !important;
            line-height: 1.43 !important;
            letter-spacing: 0.25px !important;
            color: {code_text_color} !important;
            backdrop-filter: blur(15px) saturate(180%);
            -webkit-backdrop-filter: blur(15px) saturate(180%);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }}
        
        code {{
            background: {self._get_glassmorphism_surface(colors.get('code_bg', '#2d2d2d'))} !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 8px !important;
            padding: 4px 8px !important;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace !important;
            font-size: 12px !important;
            color: {code_text_color} !important;
            backdrop-filter: blur(10px) saturate(150%);
            -webkit-backdrop-filter: blur(10px) saturate(150%);
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
            border-left: 4px solid {colors.get('primary', '#bb86fc')} !important;
            padding-left: 20px !important;
            margin: 16px 0 !important;
            color: {colors.get('text_secondary', '#b3b3b3')} !important;
            font-style: italic !important;
            background: {self._get_glassmorphism_surface(colors.get('surface', '#1e1e1e'))} !important;
            padding: 16px 20px !important;
            border-radius: 0 16px 16px 0 !important;
            backdrop-filter: blur(15px) saturate(180%);
            -webkit-backdrop-filter: blur(15px) saturate(180%);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
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
            background: {self._get_glassmorphism_surface(colors.get('code_bg', '#2d2d2d'))} !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            margin: 16px 0 !important;
            text-align: center !important;
            overflow-x: auto !important;
            min-height: 100px !important;
            backdrop-filter: blur(15px) saturate(180%);
            -webkit-backdrop-filter: blur(15px) saturate(180%);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.1);
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
            margin: 16px 0 !important;
            background: {self._get_glassmorphism_surface(colors.get('surface', '#1e1e1e'))} !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 16px !important;
            overflow: hidden !important;
            backdrop-filter: blur(15px) saturate(180%);
            -webkit-backdrop-filter: blur(15px) saturate(180%);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, {colors.get('primary', '#bb86fc')}, {colors.get('primary_variant', '#3700b3')}) !important;
            color: {colors.get('on_primary', '#000000')} !important;
            padding: 16px !important;
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
            background-color: {background_color} !important;
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
        
        return css_content
    
    def get_available_themes(self) -> Dict[str, str]:
        """사용 가능한 테마 목록 반환 - 동적 로드"""
        return {theme_key: theme_data.get("name", theme_key) 
                for theme_key, theme_data in self.themes.items()}
    
    def get_theme_types(self) -> Dict[str, list]:
        """테마 타입별 분류 반환"""
        light_themes = []
        dark_themes = []
        special_themes = []
        
        for theme_key, theme_data in self.themes.items():
            theme_type = theme_data.get('type', 'dark')
            if theme_type == 'light':
                light_themes.append(theme_key)
            elif theme_type == 'special':
                special_themes.append(theme_key)
            else:
                dark_themes.append(theme_key)
        
        return {
            'light': light_themes,
            'dark': dark_themes,
            'special': special_themes
        }
    
    def get_theme_categories(self) -> Dict[str, Dict]:
        """테마 분류 정보 반환"""
        return self.theme_categories


# 전역 Material Theme Manager 인스턴스
material_theme_manager = MaterialThemeManager()