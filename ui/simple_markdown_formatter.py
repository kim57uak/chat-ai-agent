"""Simple and reliable markdown formatter"""

import re
import uuid


class SimpleMarkdownFormatter:
    """간단하고 확실한 마크다운 포맷터"""
    
    def __init__(self):
        pass
    
    def format_basic_markdown(self, text: str) -> str:
        """기본 마크다운 포맷팅"""
        if not text:
            return ""
        
        try:
            # 이미지 처리 먼저
            text = self._preprocess_images(text)
            
            # 간단한 마크다운을 HTML로 변환
            html = self._markdown_to_html(text)
            
            # 다크 테마 스타일 적용
            html = self._apply_dark_theme_styles(html)
            
            # 코드 복사 버튼 추가
            html = self._add_copy_buttons(html)
            
            return html
            
        except Exception as e:
            print(f"마크다운 포맷팅 오류: {e}")
            return self._fallback_format(text)
    
    def _markdown_to_html(self, markdown_content):
        """간단한 마크다운을 HTML로 변환"""
        lines = markdown_content.split('\n')
        html_lines = []
        in_code_block = False
        code_language = ""
        
        for line in lines:
            if line.strip().startswith('```'):
                if not in_code_block:
                    # 코드 블록 시작
                    in_code_block = True
                    code_language = line.strip()[3:]
                    if code_language == 'mermaid':
                        html_lines.append('<div class="mermaid">')
                    else:
                        html_lines.append(f'<pre><code class="language-{code_language}">')
                else:
                    # 코드 블록 종료
                    in_code_block = False
                    if code_language == 'mermaid':
                        html_lines.append('</div>')
                    else:
                        html_lines.append('</code></pre>')
                    code_language = ""
            elif in_code_block:
                html_lines.append(line)
            elif line.strip().startswith('# '):
                html_lines.append(f'<h1>{line.strip()[2:]}</h1>')
            elif line.strip().startswith('## '):
                html_lines.append(f'<h2>{line.strip()[3:]}</h2>')
            elif line.strip().startswith('### '):
                html_lines.append(f'<h3>{line.strip()[4:]}</h3>')
            elif line.strip().startswith('#### '):
                html_lines.append(f'<h4>{line.strip()[5:]}</h4>')
            elif line.strip().startswith('##### '):
                html_lines.append(f'<h5>{line.strip()[6:]}</h5>')
            elif line.strip().startswith('###### '):
                html_lines.append(f'<h6>{line.strip()[7:]}</h6>')
            elif line.strip().startswith('| '):
                # 표 처리
                if '|' in line:
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    if all(cell.replace('-', '').strip() == '' for cell in cells):
                        continue  # 구분선 무시
                    row_html = '<tr>' + ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>'
                    if not any('<table>' in prev_line for prev_line in html_lines[-3:]):
                        html_lines.append('<table>')
                    html_lines.append(row_html)
            elif line.strip().startswith('- '):
                # 리스트 처리
                if not any('<ul>' in prev_line for prev_line in html_lines[-2:]):
                    html_lines.append('<ul>')
                html_lines.append(f'<li>{line.strip()[2:]}</li>')
            elif line.strip().startswith('* '):
                # 리스트 처리 (별표)
                if not any('<ul>' in prev_line for prev_line in html_lines[-2:]):
                    html_lines.append('<ul>')
                html_lines.append(f'<li>{line.strip()[2:]}</li>')
            elif re.match(r'^\d+\. ', line.strip()):
                # 순서 리스트
                if not any('<ol>' in prev_line for prev_line in html_lines[-2:]):
                    html_lines.append('<ol>')
                content = re.sub(r'^\d+\. ', '', line.strip())
                html_lines.append(f'<li>{content}</li>')
            elif line.strip().startswith('> '):
                # 인용문
                html_lines.append(f'<blockquote>{line.strip()[2:]}</blockquote>')
            elif line.strip() == '':
                # 빈 줄 처리
                if html_lines and html_lines[-1] == '</ul>':
                    pass
                elif html_lines and html_lines[-1] == '</ol>':
                    pass
                elif html_lines and html_lines[-1].endswith('</table>'):
                    pass
                else:
                    html_lines.append('<br>')
            else:
                if line.strip():
                    # 열린 태그들 닫기
                    if html_lines and not html_lines[-1].endswith('</table>') and any('<table>' in prev_line for prev_line in html_lines[-10:]):
                        html_lines.append('</table>')
                    if html_lines and not html_lines[-1].endswith('</ul>') and any('<ul>' in prev_line for prev_line in html_lines[-10:]):
                        html_lines.append('</ul>')
                    if html_lines and not html_lines[-1].endswith('</ol>') and any('<ol>' in prev_line for prev_line in html_lines[-10:]):
                        html_lines.append('</ol>')
                    
                    # 인라인 포맷팅 적용
                    formatted_line = self._apply_inline_formatting(line)
                    html_lines.append(f'<p>{formatted_line}</p>')
        
        # 마지막에 열린 태그들 닫기
        if any('<table>' in line for line in html_lines) and not any('</table>' in line for line in html_lines):
            html_lines.append('</table>')
        if any('<ul>' in line for line in html_lines) and not any('</ul>' in line for line in html_lines):
            html_lines.append('</ul>')
        if any('<ol>' in line for line in html_lines) and not any('</ol>' in line for line in html_lines):
            html_lines.append('</ol>')
        
        return '\n'.join(html_lines)
    
    def _apply_inline_formatting(self, text):
        """인라인 포맷팅 적용"""
        # 굵은 글씨 **text** 또는 __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
        
        # 기울임 *text* 또는 _text_
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
        
        # 취소선 ~~text~~
        text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', text)
        
        # 인라인 코드 `code`
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # 링크 [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        
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
            
            return f'''<div style="margin: 16px 0; text-align: center; background: rgba(255,255,255,0.05); padding: 16px; border-radius: 12px;">
<img id="{image_id}" src="data:{mime_type};base64,{base64_data}" alt="AI 생성 이미지" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); cursor: pointer;" onclick="this.style.transform = this.style.transform ? '' : 'scale(1.5)'; this.style.transition = 'transform 0.3s ease';">
<div style="margin-top: 12px; font-size: 12px; color: #87CEEB; font-style: italic;">🖼️ AI 생성 이미지 (클릭하여 확대)</div>
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
        
        # 리스트 스타일
        html = html.replace('<ul>', 
            '<ul style="color: #cccccc; margin: 8px 0; padding-left: 20px;">')
        html = html.replace('<ol>', 
            '<ol style="color: #cccccc; margin: 8px 0; padding-left: 20px;">')
        html = html.replace('<li>', 
            '<li style="margin: 4px 0; line-height: 1.6;">')
        
        # 링크 스타일
        html = re.sub(r'<a href="([^"]*)"([^>]*)', 
            r'<a href="\1" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;" target="_blank"\2', html)
        
        # 강조 스타일
        html = html.replace('<strong>', '<strong style="color: #ffffff; font-weight: 600;">')
        html = html.replace('<em>', '<em style="color: #ffffff; font-style: italic;">')
        
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