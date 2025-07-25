"""Markdown formatter for basic markdown elements"""

import re
import uuid
from .syntax_highlighter import SyntaxHighlighter


class MarkdownFormatter:
    """Handles basic markdown formatting"""
    
    def __init__(self):
        self.syntax_highlighter = SyntaxHighlighter()
    
    def format_basic_markdown(self, text: str) -> str:
        """Apply basic markdown formatting"""
        # 코드블록 처리
        code_blocks = []
        text = self._extract_code_blocks(text, code_blocks)
        
        # 기본 마크다운 처리
        text = self._format_headers(text)
        text = self._format_text_styles(text)
        text = self._format_links(text)
        text = self._format_lists(text)
        text = self._format_horizontal_rules(text)
        text = self._format_regular_text(text)
        
        # 코드블록 복원
        text = self._restore_code_blocks(text, code_blocks)
        
        return text
    
    def _extract_code_blocks(self, text: str, code_blocks: list) -> str:
        """코드블록을 추출하고 플레이스홀더로 치환"""
        def store_codeblock(match):
            lang = match.group(1) if match.group(1) else ''
            code_content = match.group(2).strip()
            
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
        
        return re.sub(
            r'```(\w*)\n([\s\S]*?)```',
            store_codeblock,
            text,
            flags=re.MULTILINE | re.DOTALL
        )
    
    def _restore_code_blocks(self, text: str, code_blocks: list) -> str:
        """코드블록 플레이스홀더를 실제 HTML로 복원"""
        for i, code_block in enumerate(code_blocks):
            text = text.replace(f'__CODEBLOCK_{i}__', code_block)
        return text
    
    def _format_headers(self, text: str) -> str:
        """헤더 포맷팅"""
        text = re.sub(r'^(#{1,6})\s*\1+\s*', r'\1 ', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*?)$', r'<h1 style="color: #ffffff; margin: 20px 0 10px 0; font-size: 20px; font-weight: 600;">\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2 style="color: #eeeeee; margin: 16px 0 8px 0; font-size: 18px; font-weight: 600;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.*?)$', r'<h3 style="color: #dddddd; margin: 14px 0 7px 0; font-size: 16px; font-weight: 600;">\1</h3>', text, flags=re.MULTILINE)
        return text
    
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
    
    def _format_lists(self, text: str) -> str:
        """리스트 포맷팅"""
        text = re.sub(r'^(\d+)\. (.*?)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #aaaaaa; margin-right: 6px;">\1.</span>\2</div>', text, flags=re.MULTILINE)
        text = re.sub(r'^[•\-\*] (.*?)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #aaaaaa; margin-right: 6px;">•</span>\1</div>', text, flags=re.MULTILINE)
        return text
    
    def _format_horizontal_rules(self, text: str) -> str:
        """수평선 포맷팅"""
        text = re.sub(r'^-{10,}$', '---', text, flags=re.MULTILINE)
        text = re.sub(r'^={10,}$', '---', text, flags=re.MULTILINE)
        text = re.sub(r'^\*{10,}$', '---', text, flags=re.MULTILINE)
        text = re.sub(r'^---+$', r'<hr style="border: none; border-top: 1px solid #555; margin: 16px 0;">', text, flags=re.MULTILINE)
        return text
    
    def _format_regular_text(self, text: str) -> str:
        """일반 텍스트 포맷팅"""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('<br>')
            elif line.startswith('<') or '__CODEBLOCK_' in line:
                formatted_lines.append(line)
            else:
                formatted_lines.append(f'<div style="margin: 2px 0; line-height: 1.4; color: #cccccc;">{line}</div>')
        
        return '\n'.join(formatted_lines)