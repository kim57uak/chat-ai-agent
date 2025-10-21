"""
Markdown Renderer - 최적화 완료
"""
from core.logging import get_logger
import re

logger = get_logger("markdown_renderer")


class MarkdownRenderer:
    """마크다운 렌더링"""
    
    PLACEHOLDERS = ('__MERMAID_PLACEHOLDER_', '__MATH_PLACEHOLDER_', '__CODE_BLOCK_')
    
    STYLES = {
        'h1': 'color: #fff; margin: 16px 0 8px 0;',
        'h2': 'color: #eee; margin: 14px 0 6px 0;',
        'h3': 'color: #ddd; margin: 12px 0 4px 0;',
        'p': 'color: #ccc; margin: 4px 0; line-height: 1.6;',
        'list': 'color: #ccc; margin: 2px 0;',
        'strong': 'color: #fff;'
    }
    
    def process(self, text: str) -> str:
        """마크다운 처리"""
        try:
            lines = text.split('\n')
            return '\n'.join(self._process_line(line) for line in lines)
        except Exception as e:
            logger.error(f"[MARKDOWN] 처리 오류: {e}")
            return text
    
    def _process_line(self, line: str) -> str:
        """한 줄 처리"""
        # Placeholder 보호
        if any(p in line for p in self.PLACEHOLDERS):
            return line
        
        # 이미 HTML 태그가 있는 줄은 그대로 유지
        stripped = line.strip()
        if stripped.startswith(('<div', '</div>', '<p>', '</p>', '<ul>', '</ul>', '<li>', '</li>', '<pre>', '</pre>')):
            return line
        
        # 헤더
        if line.startswith('### '):
            return f'<h3 style="{self.STYLES["h3"]}">{line[4:]}</h3>'
        if line.startswith('## '):
            return f'<h2 style="{self.STYLES["h2"]}">{line[3:]}</h2>'
        if line.startswith('# '):
            return f'<h1 style="{self.STYLES["h1"]}">{line[2:]}</h1>'
        
        # 리스트
        if line.startswith('- '):
            return f'<div style="{self.STYLES["list"]}">• {line[2:]}</div>'
        
        # 빈 줄
        if not line.strip():
            return '<br>'
        
        # 굵은 글씨
        if '**' in line:
            line = re.sub(r'\*\*(.*?)\*\*', rf'<strong style="{self.STYLES["strong"]}">\1</strong>', line)
        
        return f'<p style="{self.STYLES["p"]}">{line}</p>'
