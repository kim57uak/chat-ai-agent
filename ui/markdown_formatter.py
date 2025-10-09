"""Enhanced markdown formatter using python-markdown library"""
from core.logging import get_logger

logger = get_logger("markdown_formatter")

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
                    'add_preview': False
                }
                logger.debug("[Math] python-markdown-math 확장 로드됨")
            except ImportError:
                logger.debug("[Math] python-markdown-math 확장 없음 - 기본 처리")
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
            # 수학 공식 보호 (먼저 처리)
            text = self._protect_math_formulas(text)
            
            # Mermaid 다이어그램 보호 (먼저 처리)
            text = self._protect_mermaid_diagrams(text)
            
            # 한글 헤더 전처리
            text = self._preprocess_korean_headers(text)
            
            # 이미지 처리
            text = self._preprocess_images(text)
            
            # 마크다운 변환
            html = self.md.convert(text)
            self.md.reset()
            
            # 보호된 수학 공식 복원
            html = self._restore_math_formulas(html)
            
            # 보호된 Mermaid 다이어그램 복원
            html = self._restore_mermaid_diagrams(html)
            
            # 다크 테마 스타일 적용
            html = self._apply_dark_theme_styles(html)
            
            # 코드 복사 버튼 추가
            html = self._add_copy_buttons(html)
            
            return html
            
        except Exception as e:
            logger.debug(f"마크다운 포맷팅 오류: {e}")
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
    
    def _protect_math_formulas(self, text: str) -> str:
        """수학 공식 보호"""
        self.math_placeholders = {}
        
        # 블록 수식 $$...$$ 보호
        def protect_block_math(match):
            placeholder = f"__MATH_BLOCK_{len(self.math_placeholders)}__"
            self.math_placeholders[placeholder] = match.group(0)
            return placeholder
        
        text = re.sub(r'\$\$([^$]+?)\$\$', protect_block_math, text, flags=re.DOTALL)
        
        # 인라인 수식 $...$ 보호
        def protect_inline_math(match):
            placeholder = f"__MATH_INLINE_{len(self.math_placeholders)}__"
            self.math_placeholders[placeholder] = match.group(0)
            return placeholder
        
        text = re.sub(r'\$([^$\n]+?)\$', protect_inline_math, text)
        
        return text
    
    def _restore_math_formulas(self, html: str) -> str:
        """수학 공식 복원"""
        if hasattr(self, 'math_placeholders'):
            for placeholder, original in self.math_placeholders.items():
                html = html.replace(placeholder, original)
        return html
    
    def _protect_mermaid_diagrams(self, text: str) -> str:
        """머메이드 다이어그램 보호"""
        self.mermaid_placeholders = {}
        
        def protect_mermaid(match):
            mermaid_code = match.group(1).strip()
            placeholder = f"__MERMAID_{len(self.mermaid_placeholders)}__"
            self.mermaid_placeholders[placeholder] = f'<div class="mermaid">{mermaid_code}</div>'
            return placeholder
        
        # ```mermaid ... ``` 패턴 보호
        pattern = r'```mermaid\s*\n([\s\S]*?)\n```'
        text = re.sub(pattern, protect_mermaid, text, flags=re.MULTILINE)
        
        return text
    
    def _restore_mermaid_diagrams(self, html: str) -> str:
        """머메이드 다이어그램 복원"""
        if hasattr(self, 'mermaid_placeholders'):
            for placeholder, mermaid_html in self.mermaid_placeholders.items():
                html = html.replace(placeholder, mermaid_html)
        return html
    
    def _preprocess_korean_headers(self, text: str) -> str:
        """한글 헤더 전처리"""
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # 헤더 패턴 감지
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # 한글이 포함된 헤더인 경우
                if any('\u3131' <= char <= '\u318e' or '\uac00' <= char <= '\ud7a3' for char in title):
                    processed_lines.append('')
                    processed_lines.append(f'{"".join(["#"] * level)} {title}')
                    processed_lines.append('')
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _apply_dark_theme_styles(self, html: str) -> str:
        """다크 테마 스타일 적용 - 웹뷰 CSS와 충돌 방지"""
        # 헤더는 웹뷰 CSS에서 처리하므로 인라인 스타일 제거
        # 다른 요소들만 인라인 스타일 적용
        
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
        
        # 리스트 스타일
        html = html.replace('<ul>', 
            '<ul style="color: #cccccc; margin: 8px 0; padding-left: 20px;">')
        html = html.replace('<ol>', 
            '<ol style="color: #cccccc; margin: 8px 0; padding-left: 20px;">')
        html = html.replace('<li>', 
            '<li style="margin: 4px 0; line-height: 1.6;">')
        
        # 링크 스타일
        import re
        html = re.sub(r'<a href="([^"]*)"([^>]*)', 
            r'<a href="\1" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;" target="_blank"\2', html)
        
        # 강조 스타일
        html = html.replace('<strong>', '<strong style="color: #ffffff; font-weight: 600;">')
        html = html.replace('<em>', '<em style="color: #ffffff; font-style: italic;">')
        
        # 수평선 스타일
        html = html.replace('<hr>', 
            '<hr style="border: none; border-top: 2px solid #555; margin: 20px 0; background: linear-gradient(to right, transparent, #555, transparent);">')
        
        return html
    
    def _add_copy_buttons(self, html: str) -> str:
        """코드 블록에 복사 및 실행 버튼 추가"""
        def add_buttons(match):
            code_content = match.group(1)
            code_id = f'code_{uuid.uuid4().hex[:8]}'
            
            # 언어 감지 (class="language-xxx" 패턴)
            language = ''
            lang_match = re.search(r'class="[^"]*language-([^\s"]+)', match.group(0))
            if lang_match:
                language = lang_match.group(1).lower()
            
            # 실행 가능한 언어 확인
            executable_languages = ['python', 'py', 'javascript', 'js']
            is_executable = language in executable_languages
            
            # 버튼 HTML 생성
            buttons_html = f'''<button onclick="copyCodeBlock('{code_id}')" class="code-action-btn" style="position: absolute; top: 8px; right: {"60px" if is_executable else "8px"}; background: #444; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10; transition: all 0.2s;" onmouseover="this.style.background='#555'; this.style.transform='scale(1.05)';" onmouseout="this.style.background='#444'; this.style.transform='scale(1)';">📋 복사</button>'''
            
            if is_executable:
                exec_lang = 'python' if language in ['python', 'py'] else 'javascript'
                buttons_html += f'''<button onclick="executeCode('{code_id}', '{exec_lang}')" class="code-action-btn" style="position: absolute; top: 8px; right: 8px; background: #4CAF50; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10; transition: all 0.2s;" onmouseover="this.style.background='#45a049'; this.style.transform='scale(1.05)';" onmouseout="this.style.background='#4CAF50'; this.style.transform='scale(1)';">▶️ 실행</button>'''
            
            # 언어 라벨 추가
            lang_label = f'<div style="position: absolute; top: 8px; left: 12px; background: rgba(255,255,255,0.1); color: #aaa; padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; z-index: 10;">{language or "code"}</div>' if language else ''
            
            return f'''<div style="position: relative; margin: 12px 0;">
{lang_label}
{buttons_html}
<pre style="background-color: #1e1e1e; padding: 16px; padding-top: 40px; border-radius: 8px; overflow-x: auto; margin: 0;"><code id="{code_id}" data-language="{language}">{code_content}</code></pre>
</div>'''
        
        # 코드 블록에 버튼 추가
        html = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', add_buttons, html, flags=re.DOTALL)
        
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
    
    def _preprocess_korean_headers(self, text: str) -> str:
        """한글 헤더 전처리"""
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # 한글이 포함된 헤더인 경우 공백 추가
                if any('\u3131' <= char <= '\u318e' or '\uac00' <= char <= '\ud7a3' for char in title):
                    processed_lines.append('')
                    processed_lines.append(f'{"".join(["#"] * level)} {title}')
                    processed_lines.append('')
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)