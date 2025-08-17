"""Clean markdown formatter using markdown library"""

import markdown
import re
import uuid
from markdown.extensions import codehilite, tables, fenced_code


class CleanMarkdownFormatter:
    """markdown 라이브러리를 사용한 깔끔한 포매터"""
    
    def __init__(self):
        self._init_markdown()
    
    def _init_markdown(self):
        """markdown 파서 초기화"""
        extensions = [
            'tables',
            'fenced_code', 
            'codehilite',
            'nl2br'
        ]
        
        extension_configs = {
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': False
            }
        }
        
        self.md = markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs
        )
    
    def format_basic_markdown(self, text: str) -> str:
        """기본 마크다운 포맷팅"""
        if not text:
            return ""
        
        try:
            # 1. 수식 보호
            text, math_blocks = self._protect_math(text)
            
            # 2. Mermaid 보호  
            text, mermaid_blocks = self._protect_mermaid(text)
            
            # 3. 이미지 처리
            text = self._process_images(text)
            
            # 4. markdown 변환
            html = self.md.convert(text)
            self.md.reset()
            
            # 5. 수식 복원
            html = self._restore_math(html, math_blocks)
            
            # 6. Mermaid 복원
            html = self._restore_mermaid(html, mermaid_blocks)
            
            # 7. 스타일 적용
            html = self._apply_styles(html)
            
            return html
            
        except Exception as e:
            print(f"마크다운 포맷팅 오류: {e}")
            return f'<p style="color: #cccccc;">{text}</p>'
    
    def _protect_math(self, text):
        """수식 보호"""
        math_blocks = {}
        
        # 블록 수식 $$...$$
        def protect_block_math(match):
            key = f"__MATH_BLOCK_{len(math_blocks)}__"
            math_blocks[key] = f'<div class="math-block">$${match.group(1)}$$</div>'
            return key
        
        text = re.sub(r'\$\$([^$]+?)\$\$', protect_block_math, text, flags=re.DOTALL)
        
        # 인라인 수식 $...$
        def protect_inline_math(match):
            key = f"__MATH_INLINE_{len(math_blocks)}__"
            math_blocks[key] = f'<span class="math-inline">${match.group(1)}$</span>'
            return key
        
        text = re.sub(r'\$([^$\n]+?)\$', protect_inline_math, text)
        
        return text, math_blocks
    
    def _protect_mermaid(self, text):
        """Mermaid 보호"""
        mermaid_blocks = {}
        
        def protect_mermaid(match):
            key = f"__MERMAID_{len(mermaid_blocks)}__"
            content = match.group(1).strip()
            mermaid_blocks[key] = f'<div class="mermaid">\n{content}\n</div>'
            return key
        
        text = re.sub(r'```mermaid\s*\n([\s\S]*?)\n```', protect_mermaid, text)
        
        return text, mermaid_blocks
    
    def _restore_math(self, html, math_blocks):
        """수식 복원"""
        for key, value in math_blocks.items():
            html = html.replace(key, value)
        return html
    
    def _restore_mermaid(self, html, mermaid_blocks):
        """Mermaid 복원"""
        for key, value in mermaid_blocks.items():
            html = html.replace(key, value)
        return html
    
    def _process_images(self, text):
        """이미지 처리"""
        def format_image(match):
            base64_data = match.group(1).strip()
            if not base64_data:
                return '<div style="color: #ff6b6b;">이미지 데이터 없음</div>'
            
            image_id = f'img_{uuid.uuid4().hex[:8]}'
            mime_type = 'image/jpeg'
            
            if base64_data.startswith('iVBORw0KGgo'):
                mime_type = 'image/png'
            elif base64_data.startswith('R0lGOD'):
                mime_type = 'image/gif'
            
            return f'''<div style="text-align: center; margin: 16px 0;">
<img id="{image_id}" src="data:{mime_type};base64,{base64_data}" 
     style="max-width: 100%; border-radius: 8px; cursor: pointer;" 
     onclick="this.style.transform = this.style.transform ? '' : 'scale(1.2)';">
<div style="font-size: 12px; color: #87CEEB; margin-top: 8px;">🖼️ 이미지 (클릭 확대)</div>
</div>'''
        
        return re.sub(r'\[IMAGE_BASE64\]([^\[]+)\[/IMAGE_BASE64\]', format_image, text, flags=re.DOTALL)
    
    def _apply_styles(self, html):
        """다크 테마 스타일 적용"""
        # 테이블
        html = html.replace('<table>', 
            '<table style="border-collapse: collapse; width: 100%; margin: 12px 0; background: #2a2a2a; border-radius: 6px;">')
        html = html.replace('<th>', 
            '<th style="padding: 12px; border: 1px solid #555; color: #fff; background: #3a3a3a;">')
        html = html.replace('<td>', 
            '<td style="padding: 10px; border: 1px solid #555; color: #ccc;">')
        
        # 코드
        html = html.replace('<code>', 
            '<code style="background: #444; padding: 2px 4px; border-radius: 3px; color: #fff; font-family: monospace;">')
        html = html.replace('<pre>', 
            '<pre style="background: #1e1e1e; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0;">')
        
        # 링크
        html = re.sub(r'<a href="([^"]*)"', 
            r'<a href="\1" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;"', html)
        
        # 리스트
        html = html.replace('<ul>', '<ul style="color: #ccc; margin: 8px 0; padding-left: 20px;">')
        html = html.replace('<ol>', '<ol style="color: #ccc; margin: 8px 0; padding-left: 20px;">')
        html = html.replace('<li>', '<li style="margin: 4px 0;">')
        
        # 인용문
        html = html.replace('<blockquote>', 
            '<blockquote style="margin: 12px 0; padding: 12px 16px; border-left: 4px solid #87CEEB; background: rgba(135,206,235,0.1); color: #ddd; font-style: italic;">')
        
        # 강조
        html = html.replace('<strong>', '<strong style="color: #fff; font-weight: 600;">')
        html = html.replace('<em>', '<em style="color: #fff; font-style: italic;">')
        
        return html