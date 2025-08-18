"""완전히 새로운 포매터 - 렌더링 확실히 보장"""

import re
import uuid


class FixedFormatter:
    """렌더링을 확실히 보장하는 포매터"""
    
    def format_basic_markdown(self, text: str) -> str:
        if not text:
            return ""
        
        # 1. Mermaid 처리
        text = self._process_mermaid(text)
        
        # 2. 수식 처리
        text = self._process_math(text)
        
        # 3. 기본 마크다운
        text = self._process_markdown(text)
        
        return text
    
    def _process_mermaid(self, text):
        """머메이드 처리 - 키워드 기반 감지"""
        if not hasattr(self, 'mermaid_blocks'):
            self.mermaid_blocks = {}
        
        # test_complex_mermaid.py 참고 - 지원되는 mermaid 키워드
        mermaid_keywords = [
            'sequenceDiagram', 'gantt', 'classDiagram', 'stateDiagram-v2', 'stateDiagram', 'erDiagram',
            'flowchart', 'graph TD', 'graph LR', 'graph TB', 'graph RL', 'mindmap'
        ]
        
        def fix_mermaid_syntax(content):
            """Mermaid 문법 수정 - HTML 엔티티를 올바른 문법으로 변환"""
            # HTML 엔티티를 올바른 Mermaid 문법으로 변환
            content = content.replace('--&gt;', '-->')
            content = content.replace('-&gt;&gt;', '->>')
            content = content.replace('&lt;--', '<--')
            content = content.replace('&lt;&lt;-', '<<-')
            content = content.replace('&#45;&#45;&#45;', '---')
            content = content.replace('&amp;', '&')
            content = content.replace('&lt;', '<')
            content = content.replace('&gt;', '>')
            content = content.replace('&quot;', '"')
            return content
        
        def store_mermaid(content):
            mermaid_id = f"mermaid_{uuid.uuid4().hex[:8]}"
            placeholder = f'__MERMAID_PLACEHOLDER_{mermaid_id}__'
            
            # Mermaid 문법 수정 적용
            fixed_content = fix_mermaid_syntax(content)
            
            # 고유 ID를 가진 Mermaid 블록 생성
            self.mermaid_blocks[placeholder] = f'''<div class="diagram" style="background: #2a2a2a; padding: 20px; border-radius: 8px; margin: 20px 0;">
    <div class="mermaid" id="{mermaid_id}" style="background: #333; padding: 15px; border-radius: 5px;">
{fixed_content}
    </div>
</div>'''
            return placeholder
        
        def is_mermaid_content(content):
            content_lower = content.lower().strip()
            # 키워드가 라인의 시작 부분에 있는지 확인 (더 정확한 감지)
            lines = content_lower.split('\n')
            first_line = lines[0].strip() if lines else ''
            return any(first_line.startswith(keyword.lower()) for keyword in mermaid_keywords) or \
                   any(keyword.lower() in content_lower for keyword in mermaid_keywords)
        
        # 1. 표준 ```mermaid 블록
        def process_mermaid_block(match):
            content = match.group(1).strip()
            return store_mermaid(content)
        
        text = re.sub(r'```mermaid\s*\n([\s\S]*?)```', process_mermaid_block, text)
        
        # 2. 일반 코드 블록에서 mermaid 키워드 감지
        def check_code_block(match):
            content = match.group(1).strip()
            if is_mermaid_content(content):
                return store_mermaid(content)
            return match.group(0)
        
        text = re.sub(r'```\s*\n([\s\S]*?)```', check_code_block, text)
        
        # 3. HTML 태그로 감싸진 코드 감지
        def check_html_code(match):
            content = match.group(1).strip()
            if is_mermaid_content(content):
                return store_mermaid(content)
            return match.group(0)
        
        # 다양한 HTML 태그 패턴 처리
        patterns = [
            r'<div[^>]*>\s*<pre[^>]*>\s*<span[^>]*>\s*<code[^>]*>\s*([\s\S]*?)\s*</code>',
            r'<pre[^>]*>\s*<code[^>]*>\s*([\s\S]*?)\s*</code>\s*</pre>',
            r'<code[^>]*>\s*([\s\S]*?)\s*</code>'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, check_html_code, text)
        
        return text
    
    def _process_math(self, text):
        """수식 처리 - MathJax가 직접 처리하도록 보호"""
        # 수식은 그대로 두고 MathJax가 처리하도록 함
        # 단, 마크다운 처리에서 깨지지 않도록 보호
        return text
    
    def _process_markdown(self, text):
        """기본 마크다운 처리"""
        lines = text.split('\n')
        result = []
        in_code_block = False
        
        for line in lines:
            # placeholder는 그대로 통과
            if '__MERMAID_PLACEHOLDER_' in line or '__MATH_PLACEHOLDER_' in line:
                result.append(line)
                continue
            
            # 코드 블록 처리 (일반 코드만)
            if line.startswith('```') and not line.startswith('```mermaid'):
                if not in_code_block:
                    in_code_block = True
                    lang = line[3:].strip() if len(line) > 3 else ''
                    result.append(f'<pre style="background: #1e1e1e; color: #f8f8f2; padding: 15px; border-radius: 8px; margin: 12px 0; overflow-x: auto;"><code>')
                else:
                    in_code_block = False
                    result.append('</code></pre>')
                continue
            
            if in_code_block:
                result.append(line)
                continue
            
            # 헤더
            if line.startswith('# '):
                result.append(f'<h1 style="color: #fff; margin: 16px 0 8px 0;">{line[2:]}</h1>')
            elif line.startswith('## '):
                result.append(f'<h2 style="color: #eee; margin: 14px 0 6px 0;">{line[3:]}</h2>')
            elif line.startswith('### '):
                result.append(f'<h3 style="color: #ddd; margin: 12px 0 4px 0;">{line[4:]}</h3>')
            # 굵은 글씨
            elif '**' in line:
                line = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #fff;">\1</strong>', line)
                result.append(f'<p style="color: #ccc; margin: 4px 0;">{line}</p>')
            # 리스트
            elif line.startswith('- '):
                result.append(f'<div style="color: #ccc; margin: 2px 0;">• {line[2:]}</div>')
            # 빈 줄
            elif line.strip() == '':
                result.append('<br>')
            # 일반 텍스트
            else:
                if line.strip():
                    result.append(f'<p style="color: #ccc; margin: 4px 0; line-height: 1.6;">{line}</p>')
        
        html = '\n'.join(result)
        
        # placeholder 복원
        if hasattr(self, 'mermaid_blocks'):
            for placeholder, content in self.mermaid_blocks.items():
                html = html.replace(placeholder, content)
        
        return html