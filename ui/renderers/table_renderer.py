"""
Table Renderer - 마크다운 테이블 렌더링 전담
"""
from core.logging import get_logger
import re

logger = get_logger("table_renderer")


class TableRenderer:
    """마크다운 테이블 렌더링 (Single Responsibility)"""
    
    def has_table(self, text: str) -> bool:
        """테이블 존재 여부 확인"""
        lines = text.strip().split('\n')
        table_lines = [line for line in lines if '|' in line and line.strip()]
        
        if len(table_lines) < 2:
            return False
        
        # 구분자 확인
        has_separator = any(
            pattern in line 
            for line in table_lines 
            for pattern in ['---', ':--', '--:', '===']
        )
        
        return has_separator and len(table_lines) >= 2
    
    def process(self, text: str) -> str:
        """마크다운 테이블을 HTML로 변환"""
        try:
            if not self.has_table(text):
                return text
            
            lines = text.strip().split('\n')
            table_lines = [line for line in lines if '|' in line and line.strip()]
            
            if len(table_lines) < 2:
                return text
            
            # 테마 색상
            from ui.styles.theme_manager import theme_manager
            colors = theme_manager.material_manager.get_theme_colors() if theme_manager.use_material_theme else {}
            is_dark = theme_manager.material_manager.is_dark_theme()
            
            table_bg = colors.get('surface', '#2a2a2a' if is_dark else '#ffffff')
            header_bg = colors.get('surface_variant', '#3a3a3a' if is_dark else '#f5f5f5')
            border_color = colors.get('divider', '#555' if is_dark else '#e0e0e0')
            text_color = colors.get('text_primary', '#ffffff' if is_dark else '#000000')
            text_secondary = colors.get('text_secondary', '#cccccc' if is_dark else '#666666')
            
            html = f'<table style="border-collapse: collapse; width: 100%; margin: 12px 0; background-color: {table_bg}; border-radius: 6px; overflow: hidden;">'
            
            header_processed = False
            
            for line in table_lines:
                # 구분자 라인 스킵
                if '---' in line or '===' in line or ':--' in line or '--:' in line:
                    continue
                
                cells = [cell.strip() for cell in line.split('|')]
                cells = [c for c in cells if c]  # 빈 셀 제거
                
                if not cells:
                    continue
                
                if not header_processed:
                    # 헤더
                    html += f'<thead><tr style="background-color: {header_bg};">'
                    for cell in cells:
                        formatted = self._format_cell(cell)
                        html += f'<th style="padding: 12px; border: 1px solid {border_color}; color: {text_color}; font-weight: 600; text-align: left;">{formatted}</th>'
                    html += '</tr></thead><tbody>'
                    header_processed = True
                else:
                    # 데이터 행
                    html += f'<tr style="background-color: {table_bg};">'
                    for cell in cells:
                        formatted = self._format_cell(cell)
                        html += f'<td style="padding: 10px; border: 1px solid {border_color}; color: {text_secondary};">{formatted}</td>'
                    html += '</tr>'
            
            html += '</tbody></table>'
            return html
        except Exception as e:
            logger.error(f"[TABLE] 처리 오류: {e}")
            return text
    
    def _format_cell(self, cell_text: str) -> str:
        """셀 내부 마크다운 처리"""
        # 굵게
        cell_text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #fff; font-weight: 600;">\1</strong>', cell_text)
        # 기울임
        cell_text = re.sub(r'(?<!\*)\*(.*?)\*(?!\*)', r'<em style="color: #fff; font-style: italic;">\1</em>', cell_text)
        # 인라인 코드
        cell_text = re.sub(r'`(.*?)`', r'<code style="background: #444; padding: 2px 4px; border-radius: 3px; color: #fff;">\1</code>', cell_text)
        return cell_text
