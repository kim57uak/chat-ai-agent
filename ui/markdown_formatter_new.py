"""Enhanced markdown formatter using python-markdown library"""

import markdown
import re
import uuid
from typing import Optional
from .syntax_highlighter import SyntaxHighlighter


class MarkdownFormatter:
    """라이브러리 기반 마크다운 포맷터"""
    
    def __init__(self):
        self.syntax_highlighter = SyntaxHighlighter()
        self._init_markdown_parser()
    
    def _init_markdown_parser(self):
        """마크다운 파서 초기화"""
        try:
            extensions = [
                'tables', 'fenced_code', 'codehilite', 'toc',
                'footnotes', 'attr_list', 'def_list', 'abbr',
                'admonition', 'nl2br', 'sane_lists'
            ]
            
            extension_configs = {
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True
                },
                'toc': {
                    'permalink': True
                }
            }
            
            # pymdown-extensions 추가
            try:
                import pymdownx
                extensions.extend([
                    'pymdownx.tasklist',
                    'pymdownx.tilde',
                    'pymdownx.mark',
                    'pymdownx.superfences',
                    'pymdownx.highlight',
                    'pymdownx.emoji',
                    'pymdownx.betterem',
                    'pymdownx.caret',
                    'pymdownx.keys'
                ])
                
                extension_configs.update({
                    'pymdownx.tasklist': {
                        'custom_checkbox': True,
                        'clickable_checkbox': False
                    },
                    'pymdownx.highlight': {
                        'anchor_linenums': True,
                        'line_spans': '__span',
                        'pygments_lang_class': True
                    },
                    'pymdownx.superfences': {
                        'custom_fences': [
                            {
                                'name': 'mermaid',
                                'class': 'mermaid',
                                'format': lambda source: f'<div class="mermaid">{source}</div>'
                            }
                        ]
                    }
                })
            except ImportError:
                pass
            
            # 수학 공식 지원
            try:
                import mdx_math
                extensions.append('mdx_math')
                extension_configs['mdx_math'] = {
                    'enable_dollar_delimiter': True,
                    'add_preview': True
                }
            except ImportError:
                pass
            
            self.md = markdown.Markdown(
                extensions=extensions,
                extension_configs=extension_configs
            )
            
        except Exception:
            # 기본 파서로 폴백
            self.md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    
    def format_basic_markdown(self, text: str) -> str:
        """라이브러리 기반 마크다운 포맷팅"""
        if not text:
            return ""
        
        try:
            # 이미지 처리 (라이브러리 처리 전)
            text = self._preprocess_images(text)
            
            # 마크다운 변환
            html = self.md.convert(text)
            self.md.reset()
            
            # 다크 테마 스타일 적용
            html = self._apply_dark_theme_styles(html)
            
            # 코드 복사 버튼 추가
            html = self._add_copy_buttons(html)
            
            return html
            
        except Exception as e:
            # 폴백: 기본 텍스트 처리
            return self._fallback_format(text)
    
    def _preprocess_images(self, text: str) -> str:
        """이미지 전처리"""
        # Base64 이미지 처리
        def format_base64_image(match):
            base64_data = match.group(1).strip()
            image_id = f'img_{uuid.uuid4().hex[:8]}'
            
            if not base64_data:
                return '<div style="color: #ff6b6b; font-style: italic;">이미지 데이터가 비어있습니다.</div>'
            
            # MIME 타입 감지
            mime_type = 'image/jpeg'
            if base64_data.startswith('/9j/'):
                mime_type = 'image/jpeg'
            elif base64_data.startswith('iVBORw0KGgo'):
                mime_type = 'image/png'
            elif base64_data.startswith('R0lGOD'):
                mime_type = 'image/gif'
            elif base64_data.startswith('UklGR'):
                mime_type = 'image/webp'
            
            return f'''<div style="margin: 16px 0; text-align: center; background: rgba(255,255,255,0.05); padding: 16px; border-radius: 12px;">
<img id="{image_id}" src="data:{mime_type};base64,{base64_data}" alt="AI 생성 이미지" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); cursor: pointer;" onclick="this.style.transform = this.style.transform ? '' : 'scale(1.5)'; this.style.transition = 'transform 0.3s ease';">
<div style="margin-top: 12px; font-size: 12px; color: #87CEEB; font-style: italic;">🖼️ AI 생성 이미지 (클릭하여 확대)</div>
<button onclick="downloadImage('{image_id}')" style="margin-top: 8px; background: #444; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px;" onmouseover="this.style.background='#555'" onmouseout="this.style.background='#444'">이미지 저장</button>
</div>'''
        
        text = re.sub(r'\[IMAGE_BASE64\]([^\[]+)\[/IMAGE_BASE64\]', format_base64_image, text, flags=re.DOTALL)
        
        return text
    
    def _apply_dark_theme_styles(self, html: str) -> str:
        """다크 테마 스타일 적용"""
        # 테이블 스타일
        html = html.replace('<table>', 
            '<table style="border-collapse: collapse; width: 100%; margin: 12px 0; background-color: #2a2a2a; border-radius: 6px; overflow: hidden;">')
        html = html.replace('<th>', 
            '<th style="padding: 12px; border: 1px solid #555; color: #ffffff; font-weight: 600; text-align: left; background-color: #3a3a3a;">')
        html = html.replace('<td>', 
            '<td style="padding: 10px; border: 1px solid #555; color: #cccccc;">')
        
        # 코드 블록 스타일
        html = html.replace('<pre>', 
            '<pre style="background-color: #1e1e1e; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0; position: relative;">')
        html = html.replace('<code>', 
            '<code style="background-color: #444; padding: 2px 4px; border-radius: 3px; color: #fff; font-family: \'Consolas\', \'Monaco\', monospace;">')
        
        # 인용문 스타일
        html = html.replace('<blockquote>', 
            '<blockquote style="margin: 12px 0; padding: 12px 16px; border-left: 4px solid #87CEEB; background-color: rgba(135, 206, 235, 0.1); color: #dddddd; font-style: italic;">')
        
        # 헤더 스타일
        for i in range(1, 7):
            size = 24 - (i * 2)
            html = html.replace(f'<h{i}>', 
                f'<h{i} style="color: #ffffff; margin: {20-i*2}px 0 {10-i}px 0; font-size: {size}px; font-weight: 600;">')
        
        # 리스트 스타일
        html = html.replace('<ul>', 
            '<ul style="color: #cccccc; margin: 8px 0; padding-left: 20px;">')
        html = html.replace('<ol>', 
            '<ol style="color: #cccccc; margin: 8px 0; padding-left: 20px;">')
        html = html.replace('<li>', 
            '<li style="margin: 4px 0; line-height: 1.6;">')
        
        # 링크 스타일
        html = re.sub(r'<a href="([^"]*)"([^>]*)>', 
            r'<a href="\1" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;" target="_blank"\2>', html)
        
        # 강조 스타일
        html = html.replace('<strong>', '<strong style="color: #ffffff; font-weight: 600;">')
        html = html.replace('<em>', '<em style="color: #ffffff; font-style: italic;">')
        
        # 수평선 스타일
        html = html.replace('<hr>', 
            '<hr style="border: none; border-top: 2px solid #555; margin: 20px 0; background: linear-gradient(to right, transparent, #555, transparent);">')
        
        return html
    
    def _add_copy_buttons(self, html: str) -> str:
        """코드 블록에 복사 버튼 추가"""
        def add_copy_button(match):
            code_content = match.group(1)
            code_id = f'code_{uuid.uuid4().hex[:8]}'
            
            return f'''<div style="position: relative; margin: 12px 0;">
<button onclick="copyCode('{code_id}')" class="copy-btn" style="position: absolute; top: 8px; right: 8px; background: #444; color: #fff; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10;" onmouseover="this.style.background='#555'" onmouseout="this.style.background='#444'">복사</button>
<pre style="background-color: #1e1e1e; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 0;"><code id="{code_id}">{code_content}</code></pre>
</div>'''
        
        # 코드 블록에 복사 버튼 추가
        html = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', add_copy_button, html, flags=re.DOTALL)
        
        return html
    
    def _fallback_format(self, text: str) -> str:
        """폴백 포맷팅"""
        # 기본적인 HTML 이스케이프
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # 줄바꿈 처리
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                formatted_lines.append(f'<div style="margin: 4px 0; line-height: 1.6; color: #cccccc;">{line}</div>')
            else:
                formatted_lines.append('<br>')
        
        return '\n'.join(formatted_lines)