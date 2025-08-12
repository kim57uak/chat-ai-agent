"""Markdown formatter for basic markdown elements"""

import re
import uuid
from .syntax_highlighter import SyntaxHighlighter
from .table_formatter import TableFormatter


class MarkdownFormatter:
    """Handles basic markdown formatting"""
    
    def __init__(self):
        self.syntax_highlighter = SyntaxHighlighter()
        self.table_formatter = TableFormatter()
    
    def format_basic_markdown(self, text: str) -> str:
        """Apply basic markdown formatting"""
        # 코드블록 처리
        code_blocks = []
        text = self._extract_code_blocks(text, code_blocks)
        
        # 기본 마크다운 처리 (순서 중요: 수평선을 먼저 처리)
        text = self._format_horizontal_rules(text)
        text = self._format_headers(text)
        text = self._format_blockquotes(text)
        text = self._format_lists(text)
        text = self._format_text_styles(text)
        text = self._format_links(text)
        text = self._format_images(text)
        text = self._format_regular_text(text)
        
        # 코드블록 복원
        text = self._restore_code_blocks(text, code_blocks)
        
        return text
    
    def _extract_code_blocks(self, text: str, code_blocks: list) -> str:
        """코드블록을 추출하고 플레이스홀더로 치환"""
        def store_codeblock(match):
            lang = match.group(1) if match.group(1) else ''
            code_content = match.group(2)
            
            highlighted_content = self.syntax_highlighter.highlight(code_content, lang)
            code_id = f'code_{uuid.uuid4().hex[:8]}'
            
            code_html = f'''<div style="position: relative; margin: 12px 0;">
<button onclick="copyCode('{code_id}')" style="
    position: absolute;
    top: 8px;
    right: 8px;
    background: #444;
    color: #fff;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 11px;
    font-weight: 500;
    z-index: 10;
    transition: all 0.2s ease;
" onmouseover="this.style.background='#555'" onmouseout="this.style.background='#444'">복사</button>
<pre style="background: #1e1e1e; color: #f8f8f2; padding: 20px; border-radius: 8px; font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace; font-size: 13px; line-height: 1.5; overflow-x: auto; white-space: pre; tab-size: 4; border: 1px solid #444; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><code id="{code_id}">{highlighted_content}</code></pre>
</div>'''
            
            code_blocks.append(code_html)
            return f'__CODEBLOCK_{len(code_blocks)-1}__'
        
        # 정규식 수정: 다양한 코드블록 형식 지원
        patterns = [
            r'```(\w+)\n([\s\S]*?)```',  # 언어 지정 + 개행
            r'```(\w+)([\s\S]*?)```',   # 언어 지정 만
            r'```\n([\s\S]*?)```',      # 언어 지정 없음 + 개행
            r'```([\s\S]*?)```'        # 기본 형식
        ]
        
        result = text
        for i, pattern in enumerate(patterns):
            if i < 2:  # 언어 지정이 있는 경우
                result = re.sub(pattern, store_codeblock, result, flags=re.MULTILINE | re.DOTALL)
            else:  # 언어 지정이 없는 경우
                def no_lang_match(match):
                    # 가짜 Match 객체 생성
                    class FakeMatch:
                        def __init__(self, content):
                            self.content = content
                        def group(self, n):
                            if n == 1:
                                return ''  # 언어 없음
                            elif n == 2:
                                return self.content
                    return store_codeblock(FakeMatch(match.group(1)))
                
                result = re.sub(pattern, no_lang_match, result, flags=re.MULTILINE | re.DOTALL)
            
            # 코드블록이 처리되었으면 다음 패턴 시도 안 함
            if '__CODEBLOCK_' in result:
                break
        
        # 디버깅 로그 (필요시 주석 해제)
        # if '```' in text:
        #     print(f"[DEBUG] Code block extraction - Original has ```: True")
        #     print(f"[DEBUG] Code blocks found: {len(code_blocks)}")
        #     print(f"[DEBUG] Result has placeholders: {'__CODEBLOCK_' in result}")
        
        return result
    
    def _restore_code_blocks(self, text: str, code_blocks: list) -> str:
        """코드블록 플레이스홀더를 실제 HTML로 복원"""
        for i, code_block in enumerate(code_blocks):
            placeholder = f'__CODEBLOCK_{i}__'
            if placeholder in text:
                text = text.replace(placeholder, code_block)
        
        return text
    
    def _format_headers(self, text: str) -> str:
        """헤더 포맷팅"""
        # 헤더 변환 (긴 패턴부터 우선 처리 - 6단계부터 1단계까지)
        text = re.sub(r'^#{6}(?!#)\s+(.*?)\s*$', r'<h6 style="color: #aaaaaa; margin: 10px 0 5px 0; font-size: 13px; font-weight: 600;">\1</h6>', text, flags=re.MULTILINE)
        text = re.sub(r'^#{5}(?!#)\s+(.*?)\s*$', r'<h5 style="color: #bbbbbb; margin: 12px 0 6px 0; font-size: 14px; font-weight: 600;">\1</h5>', text, flags=re.MULTILINE)
        text = re.sub(r'^#{4}(?!#)\s+(.*?)\s*$', r'<h4 style="color: #cccccc; margin: 12px 0 6px 0; font-size: 15px; font-weight: 600;">\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^#{3}(?!#)\s+(.*?)\s*$', r'<h3 style="color: #dddddd; margin: 14px 0 7px 0; font-size: 16px; font-weight: 600;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^#{2}(?!#)\s+(.*?)\s*$', r'<h2 style="color: #eeeeee; margin: 16px 0 8px 0; font-size: 18px; font-weight: 600;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^#{1}(?!#)\s+(.*?)\s*$', r'<h1 style="color: #ffffff; margin: 20px 0 10px 0; font-size: 20px; font-weight: 600;">\1</h1>', text, flags=re.MULTILINE)
        
        return text
    
    def _format_blockquotes(self, text: str) -> str:
        """블록쿼트 포맷팅"""
        # 단일 라인 블록쿼트
        text = re.sub(r'^>\s+(.+)$', r'<blockquote style="margin: 12px 0; padding: 12px 16px; border-left: 4px solid #87CEEB; background-color: rgba(135, 206, 235, 0.1); color: #dddddd; font-style: italic;">\1</blockquote>', text, flags=re.MULTILINE)
        
        # 다중 라인 블록쿼트 처리
        lines = text.split('\n')
        result_lines = []
        in_blockquote = False
        blockquote_content = []
        
        for line in lines:
            if line.strip().startswith('>'):
                if not in_blockquote:
                    in_blockquote = True
                    blockquote_content = []
                # > 제거하고 내용만 추출
                content = re.sub(r'^>\s*', '', line.strip())
                if content:
                    blockquote_content.append(content)
            else:
                if in_blockquote:
                    # 블록쿼트 종료
                    if blockquote_content:
                        content_joined = '<br>'.join(blockquote_content)
                        quote_html = f'<blockquote style="margin: 12px 0; padding: 12px 16px; border-left: 4px solid #87CEEB; background-color: rgba(135, 206, 235, 0.1); color: #dddddd; font-style: italic;">{content_joined}</blockquote>'
                        result_lines.append(quote_html)
                    in_blockquote = False
                    blockquote_content = []
                result_lines.append(line)
        
        # 마지막에 블록쿼트가 남아있는 경우
        if in_blockquote and blockquote_content:
            content_joined = '<br>'.join(blockquote_content)
            quote_html = f'<blockquote style="margin: 12px 0; padding: 12px 16px; border-left: 4px solid #87CEEB; background-color: rgba(135, 206, 235, 0.1); color: #dddddd; font-style: italic;">{content_joined}</blockquote>'
            result_lines.append(quote_html)
        
        return '\n'.join(result_lines)
    
    def _format_text_styles(self, text: str) -> str:
        """텍스트 스타일 포맷팅"""
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff; font-weight: 600;">\1</strong>', text)
        text = re.sub(r'(?<!\*)\*(.*?)\*(?!\*)', r'<em style="color: #ffffff; font-style: italic;">\1</em>', text)
        text = re.sub(r'~~(.*?)~~', r'<del style="color: #888; text-decoration: line-through;">\1</del>', text)
        text = re.sub(r'`(.*?)`', r'<code style="background-color: #444; padding: 2px 4px; border-radius: 3px; color: #fff;">\1</code>', text)
        return text
    
    def _format_links(self, text: str) -> str:
        """링크 포맷팅"""
        return re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;" target="_blank">\1</a>', text)
    
    def _format_images(self, text: str) -> str:
        """이미지 포맷팅 - 마크다운 이미지와 Base64 이미지 처리"""
        # 1. 마크다운 이미지 형식: ![alt](url)
        text = re.sub(
            r'!\[([^\]]*)\]\(([^\)]+)\)',
            r'<div style="margin: 16px 0; text-align: center;"><img src="\2" alt="\1" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"><div style="margin-top: 8px; font-size: 12px; color: #888; font-style: italic;">\1</div></div>',
            text
        )
        
        # 2. Base64 이미지 태그: [IMAGE_BASE64]data[/IMAGE_BASE64]
        def format_base64_image(match):
            base64_data = match.group(1).strip()
            image_id = f'img_{uuid.uuid4().hex[:8]}'
            
            # Base64 데이터 검증
            if not base64_data:
                return '<div style="color: #ff6b6b; font-style: italic;">이미지 데이터가 비어있습니다.</div>'
            
            # MIME 타입 감지 (기본값: jpeg)
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
        
        # 3. 직접 URL 이미지 (http/https로 시작하고 이미지 확장자로 끝나는 경우)
        text = re.sub(
            r'(https?://[^\s]+\.(jpg|jpeg|png|gif|webp|bmp|svg)(?:\?[^\s]*)?)',
            r'<div style="margin: 16px 0; text-align: center;"><img src="\1" alt="이미지" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"></div>',
            text,
            flags=re.IGNORECASE
        )
        
        return text
    
    def _format_lists(self, text: str) -> str:
        """리스트 포맷팅"""
        # 순서 있는 리스트 (1. 2. 3. 등)
        text = re.sub(r'^(\d+)\. (.+)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #87CEEB; margin-right: 8px; font-weight: 600;">\1.</span>\2</div>', text, flags=re.MULTILINE)
        
        # 비순서 리스트 (-, *, • 등)
        text = re.sub(r'^[\-\*\u2022]\s+(.+)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #87CEEB; margin-right: 8px; font-weight: 600;">•</span>\1</div>', text, flags=re.MULTILINE)
        
        # 들여쓰기된 리스트 (2단계)
        text = re.sub(r'^  [\-\*\u2022]\s+(.+)$', r'<div style="margin: 4px 0; margin-left: 32px; color: #cccccc;"><span style="color: #87CEEB; margin-right: 8px; font-weight: 600;">◦</span>\1</div>', text, flags=re.MULTILINE)
        
        return text
    
    def _format_horizontal_rules(self, text: str) -> str:
        """수평선 포맷팅"""
        # 다양한 수평선 패턴 지원 (개선된 정규식)
        text = re.sub(r'^\s*-{3,}\s*$', r'<hr style="border: none; border-top: 2px solid #555; margin: 20px 0; background: linear-gradient(to right, transparent, #555, transparent);">', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\*{3,}\s*$', r'<hr style="border: none; border-top: 2px solid #555; margin: 20px 0; background: linear-gradient(to right, transparent, #555, transparent);">', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*_{3,}\s*$', r'<hr style="border: none; border-top: 2px solid #555; margin: 20px 0; background: linear-gradient(to right, transparent, #555, transparent);">', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*={3,}\s*$', r'<hr style="border: none; border-top: 2px solid #555; margin: 20px 0; background: linear-gradient(to right, transparent, #555, transparent);">', text, flags=re.MULTILINE)
        
        return text
    
    def _extract_images(self, text: str, image_blocks: list) -> str:
        """이미지를 추출하고 플레이스홀더로 치환"""
        def store_image(match, img_type):
            if img_type == 'markdown':
                alt_text = match.group(1)
                img_url = match.group(2)
                img_html = f'<div style="margin: 16px 0; text-align: center;"><img src="{img_url}" alt="{alt_text}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"><div style="margin-top: 8px; font-size: 12px; color: #888; font-style: italic;">{alt_text}</div></div>'
            elif img_type == 'base64':
                base64_data = match.group(1).strip()
                if not base64_data.startswith('data:image'):
                    base64_data = f'data:image/png;base64,{base64_data}'
                img_html = f'<div style="margin: 16px 0; text-align: center;"><img src="{base64_data}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"><div style="margin-top: 8px; font-size: 12px; color: #888; font-style: italic;">AI 생성 이미지</div></div>'
            elif img_type == 'url':
                img_url = match.group(1)
                img_html = f'<div style="margin: 16px 0; text-align: center;"><img src="{img_url}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"></div>'
            
            image_blocks.append(img_html)
            return f'__IMAGE_{len(image_blocks)-1}__'
        
        # 마크다운 이미지
        text = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', lambda m: store_image(m, 'markdown'), text)
        
        # Base64 이미지
        text = re.sub(r'\[IMAGE_BASE64\]([^\[]+)\[/IMAGE_BASE64\]', lambda m: store_image(m, 'base64'), text, flags=re.DOTALL)
        
        # URL 이미지
        text = re.sub(r'(https?://[^\s]+\.(jpg|jpeg|png|gif|webp|svg)(?:\?[^\s]*)?)', lambda m: store_image(m, 'url'), text, flags=re.IGNORECASE)
        
        return text
    
    def _restore_images(self, text: str, image_blocks: list) -> str:
        """이미지 플레이스홀더를 실제 HTML로 복원"""
        for i, image_block in enumerate(image_blocks):
            placeholder = f'__IMAGE_{i}__'
            if placeholder in text:
                text = text.replace(placeholder, image_block)
        return text
    
    def _format_regular_text(self, text: str) -> str:
        """일반 텍스트 포맷팅 - 줄바꿈과 단락 처리"""
        # 빈 줄을 단락 구분으로 처리
        lines = text.split('\n')
        result_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                # 빈 줄은 단락 구분으로 처리
                result_lines.append('<br>')
            else:
                # 일반 텍스트는 div로 감싸서 줄바꿈 처리
                if not any(tag in line for tag in ['<h1', '<h2', '<h3', '<h4', '<h5', '<h6', '<hr', '<blockquote', '<div', '<pre', '<code', '<img']):
                    result_lines.append(f'<div style="margin: 4px 0; line-height: 1.6; color: #cccccc;">{line}</div>')
                else:
                    result_lines.append(line)
        
        return '\n'.join(result_lines)