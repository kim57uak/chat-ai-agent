"""Enhanced markdown formatter with proper mermaid and math support"""

import re
import uuid
from typing import Dict, List, Tuple


class EnhancedMarkdownFormatter:
    """Mermaid와 수식을 제대로 지원하는 향상된 마크다운 포매터"""
    
    def __init__(self):
        self.protected_blocks = {}
        self.block_counter = 0
    
    def format_basic_markdown(self, text: str) -> str:
        """기본 마크다운 포맷팅"""
        if not text:
            return ""
        
        try:
            # 1단계: 특수 블록들을 보호 (순서 중요!)
            text = self._protect_special_blocks(text)
            
            # 2단계: 이미지 처리
            text = self._preprocess_images(text)
            
            # 3단계: 마크다운을 HTML로 변환
            html = self._markdown_to_html(text)
            
            # 4단계: 보호된 블록들 복원
            html = self._restore_protected_blocks(html)
            
            # 5단계: 다크 테마 스타일 적용
            html = self._apply_dark_theme_styles(html)
            
            # 6단계: 코드 복사 버튼 추가
            html = self._add_copy_buttons(html)
            
            return html
            
        except Exception as e:
            print(f"마크다운 포맷팅 오류: {e}")
            return self._fallback_format(text)
    
    def _protect_special_blocks(self, text: str) -> str:
        """특수 블록들을 보호"""
        self.protected_blocks = {}
        self.block_counter = 0
        
        # 1. 수식 블록 보호 ($$...$$)
        text = self._protect_math_blocks(text)
        
        # 2. 인라인 수식 보호 ($...$)
        text = self._protect_inline_math(text)
        
        # 3. Mermaid 다이어그램 보호
        text = self._protect_mermaid_blocks(text)
        
        # 4. 일반 코드 블록 보호
        text = self._protect_code_blocks(text)
        
        return text
    
    def _protect_math_blocks(self, text: str) -> str:
        """수식 블록 보호 ($$...$$)"""
        def protect_block(match):
            math_content = match.group(1).strip()
            placeholder = f"__PROTECTED_MATH_BLOCK_{self.block_counter}__"
            self.protected_blocks[placeholder] = f'<div class="math-block">$$\\n{math_content}\\n$$</div>'
            self.block_counter += 1
            return placeholder
        
        # 여러 줄에 걸친 수식 블록 처리
        pattern = r'\\$\\$\\s*\\n([\\s\\S]*?)\\n\\s*\\$\\$'
        text = re.sub(pattern, protect_block, text)
        
        # 한 줄 수식 블록 처리
        pattern = r'\\$\\$([^$\\n]+?)\\$\\$'
        text = re.sub(pattern, protect_block, text)
        
        return text
    
    def _protect_inline_math(self, text: str) -> str:
        """인라인 수식 보호 ($...$)"""
        def protect_inline(match):
            math_content = match.group(1).strip()
            placeholder = f"__PROTECTED_INLINE_MATH_{self.block_counter}__"
            self.protected_blocks[placeholder] = f'<span class="math-inline">${math_content}$</span>'
            self.block_counter += 1
            return placeholder
        
        # 인라인 수식 패턴 (줄바꿈이 없는 $...$)
        pattern = r'\\$([^$\\n]+?)\\$'
        text = re.sub(pattern, protect_inline, text)
        
        return text
    
    def _protect_mermaid_blocks(self, text: str) -> str:
        """Mermaid 다이어그램 보호"""
        def protect_mermaid(match):
            mermaid_content = match.group(1).strip()
            # 문법 수정: 세미콜론 제거, 한글 텍스트 따옴표 처리
            mermaid_content = self._fix_mermaid_syntax(mermaid_content)
            placeholder = f"__PROTECTED_MERMAID_{self.block_counter}__"
            self.protected_blocks[placeholder] = f'<div class="mermaid">\\n{mermaid_content}\\n</div>'
            self.block_counter += 1
            return placeholder
        
        def protect_graph_td(match):
            graph_content = match.group(0).strip()
            # graph TD 문법 수정
            graph_content = self._fix_mermaid_syntax(graph_content)
            placeholder = f"__PROTECTED_MERMAID_{self.block_counter}__"
            self.protected_blocks[placeholder] = f'<div class="mermaid">\\n{graph_content}\\n</div>'
            self.block_counter += 1
            return placeholder
        
        # ```mermaid ... ``` 패턴
        pattern = r'```mermaid\\s*\\n([\\s\\S]*?)\\n```'
        text = re.sub(pattern, protect_mermaid, text)
        
        # graph TD 패턴 (코드 블록 없이)
        pattern = r'graph\s+TD[\\s\\S]*?(?=\\n\\n|$)'
        text = re.sub(pattern, protect_graph_td, text)
        
        return text
    
    def _protect_code_blocks(self, text: str) -> str:
        """일반 코드 블록 보호"""
        def protect_code(match):
            language = match.group(1) if match.group(1) else ""
            code_content = match.group(2).strip()
            placeholder = f"__PROTECTED_CODE_{self.block_counter}__"
            
            # 코드 블록 HTML 생성
            code_id = f'code_{uuid.uuid4().hex[:8]}'
            code_html = f'''<div class="code-block-container">
<button onclick="copyCode('{code_id}')" class="copy-btn">복사</button>
<pre><code id="{code_id}" class="language-{language}">{self._escape_html(code_content)}</code></pre>
</div>'''
            
            self.protected_blocks[placeholder] = code_html
            self.block_counter += 1
            return placeholder
        
        # ```language ... ``` 패턴 (mermaid 제외)
        pattern = r'```(?!mermaid)([a-zA-Z0-9_+-]*)?\\s*\\n([\\s\\S]*?)\\n```'
        text = re.sub(pattern, protect_code, text)
        
        return text
    
    def _restore_protected_blocks(self, html: str) -> str:
        """보호된 블록들 복원"""
        for placeholder, content in self.protected_blocks.items():
            html = html.replace(placeholder, content)
        return html
    
    def _markdown_to_html(self, text: str) -> str:
        """마크다운을 HTML로 변환"""
        lines = text.split('\\n')
        html_lines = []
        in_list = False
        in_ordered_list = False
        in_table = False
        
        for line in lines:
            stripped = line.strip()
            
            # 보호된 블록은 그대로 통과
            if stripped.startswith('__PROTECTED_'):
                html_lines.append(line)
                continue
            
            # 헤더 처리
            if stripped.startswith('#'):
                level = len(stripped) - len(stripped.lstrip('#'))
                if level <= 6:
                    title = stripped[level:].strip()
                    html_lines.append(f'<h{level}>{self._apply_inline_formatting(title)}</h{level}>')
                    continue
            
            # 테이블 처리
            if '|' in stripped and len(stripped.split('|')) >= 3:
                if not in_table:
                    html_lines.append('<table>')
                    in_table = True
                
                cells = [cell.strip() for cell in stripped.split('|')[1:-1]]
                if all(cell.replace('-', '').replace(':', '').strip() == '' for cell in cells):
                    continue  # 구분선 무시
                
                row_html = '<tr>' + ''.join(f'<td>{self._apply_inline_formatting(cell)}</td>' for cell in cells) + '</tr>'
                html_lines.append(row_html)
                continue
            else:
                if in_table:
                    html_lines.append('</table>')
                    in_table = False
            
            # 순서 있는 리스트
            if re.match(r'^\\d+\\.\\s', stripped):
                if not in_ordered_list:
                    if in_list:
                        html_lines.append('</ul>')
                        in_list = False
                    html_lines.append('<ol>')
                    in_ordered_list = True
                
                content = re.sub(r'^\\d+\\.\\s', '', stripped)
                html_lines.append(f'<li>{self._apply_inline_formatting(content)}</li>')
                continue
            else:
                if in_ordered_list:
                    html_lines.append('</ol>')
                    in_ordered_list = False
            
            # 순서 없는 리스트
            if stripped.startswith(('- ', '* ', '+ ')):
                if not in_list:
                    if in_ordered_list:
                        html_lines.append('</ol>')
                        in_ordered_list = False
                    html_lines.append('<ul>')
                    in_list = True
                
                content = stripped[2:]
                html_lines.append(f'<li>{self._apply_inline_formatting(content)}</li>')
                continue
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
            
            # 인용문
            if stripped.startswith('> '):
                content = stripped[2:]
                html_lines.append(f'<blockquote>{self._apply_inline_formatting(content)}</blockquote>')
                continue
            
            # 수평선
            if stripped in ['---', '***', '___']:
                html_lines.append('<hr>')
                continue
            
            # 빈 줄
            if not stripped:
                html_lines.append('<br>')
                continue
            
            # 일반 텍스트
            if stripped:
                html_lines.append(f'<p>{self._apply_inline_formatting(stripped)}</p>')
        
        # 열린 태그들 닫기
        if in_table:
            html_lines.append('</table>')
        if in_list:
            html_lines.append('</ul>')
        if in_ordered_list:
            html_lines.append('</ol>')
        
        return '\\n'.join(html_lines)
    
    def _apply_inline_formatting(self, text: str) -> str:
        """인라인 포맷팅 적용"""
        # 보호된 블록은 건드리지 않음
        if text.startswith('__PROTECTED_'):
            return text
        
        # 굵은 글씨 **text** 또는 __text__
        text = re.sub(r'\\*\\*(.*?)\\*\\*', r'<strong>\\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong>\\1</strong>', text)
        
        # 기울임 *text* 또는 _text_ (굵은 글씨와 겹치지 않도록)
        text = re.sub(r'(?<!\\*)\\*([^*]+?)\\*(?!\\*)', r'<em>\\1</em>', text)
        text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<em>\\1</em>', text)
        
        # 취소선 ~~text~~
        text = re.sub(r'~~(.*?)~~', r'<del>\\1</del>', text)
        
        # 인라인 코드 `code`
        text = re.sub(r'`([^`]+)`', r'<code>\\1</code>', text)
        
        # 링크 [text](url)
        text = re.sub(r'\\[([^\\]]+)\\]\\(([^)]+)\\)', r'<a href="\\2">\\1</a>', text)
        
        return text
    
    def _preprocess_images(self, text: str) -> str:
        """이미지 전처리"""
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
            
            return f'''<div class="image-container">
<img id="{image_id}" src="data:{mime_type};base64,{base64_data}" alt="AI 생성 이미지" onclick="this.style.transform = this.style.transform ? '' : 'scale(1.5)'; this.style.transition = 'transform 0.3s ease';">
<div class="image-caption">🖼️ AI 생성 이미지 (클릭하여 확대)</div>
</div>'''
        
        text = re.sub(r'\\[IMAGE_BASE64\\]([^\\[]+)\\[/IMAGE_BASE64\\]', format_base64_image, text, flags=re.DOTALL)
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
        html = re.sub(r'<a href="([^"]*)"([^>]*)', 
            r'<a href="\\1" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;" target="_blank"\\2', html)
        
        # 강조 스타일
        html = html.replace('<strong>', '<strong style="color: #ffffff; font-weight: 600;">')
        html = html.replace('<em>', '<em style="color: #ffffff; font-style: italic;">')
        
        # 인라인 코드 스타일
        html = html.replace('<code>', 
            '<code style="background-color: #444; padding: 2px 4px; border-radius: 3px; color: #fff; font-family: \'Consolas\', \'Monaco\', monospace;">')
        
        # 수평선 스타일
        html = html.replace('<hr>', 
            '<hr style="border: none; border-top: 2px solid #555; margin: 20px 0; background: linear-gradient(to right, transparent, #555, transparent);">')
        
        return html
    
    def _add_copy_buttons(self, html: str) -> str:
        """코드 블록에 복사 버튼 추가 (이미 처리됨)"""
        # 코드 블록은 이미 _protect_code_blocks에서 복사 버튼이 추가됨
        return html
    
    def _fix_mermaid_syntax(self, code: str) -> str:
        """Mermaid 문법 수정"""
        # 세미콜론 제거
        code = re.sub(r';$', '', code, flags=re.MULTILINE)
        
        # 한글 텍스트를 따옴표로 감싸기
        def quote_korean(match):
            text = match.group(1)
            if re.search(r'[가-힣]', text) and not (text.startswith('"') and text.endswith('"')):
                return f'["{text}"]'
            return match.group(0)
        
        code = re.sub(r'\[([^\]]+)\]', quote_korean, code)
        code = re.sub(r'\{([^\}]+)\}', lambda m: f'{{"{ m.group(1)}"}}' if re.search(r'[가-힣]', m.group(1)) else m.group(0), code)
        
        return code
    
    def _escape_html(self, text: str) -> str:
        """HTML 이스케이프"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def _fallback_format(self, text: str) -> str:
        """폴백 포맷팅"""
        text = self._escape_html(text)
        lines = text.split('\\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                formatted_lines.append(f'<div style="margin: 4px 0; line-height: 1.6; color: #cccccc;">{line}</div>')
            else:
                formatted_lines.append('<br>')
        
        return '\\n'.join(formatted_lines)