"""최소한의 마크다운 포매터 - mermaid와 수식만 처리"""

import re
import uuid


class MinimalFormatter:
    """mermaid와 수식만 처리하는 최소 포매터"""
    
    def format_basic_markdown(self, text: str) -> str:
        if not text:
            return ""
        
        # 1. Mermaid 처리
        text = self._process_mermaid(text)
        
        # 2. 수식 처리  
        text = self._process_math(text)
        
        # 3. 기본 마크다운 처리
        text = self._process_basic_markdown(text)
        
        return text
    
    def _process_mermaid(self, text):
        """Mermaid 다이어그램 처리"""
        def replace_mermaid(match):
            content = match.group(1).strip()
            return f'<div class="mermaid">\n{content}\n</div>'
        
        return re.sub(r'```mermaid\s*\n([\s\S]*?)\n```', replace_mermaid, text)
    
    def _process_math(self, text):
        """수식 처리"""
        # 블록 수식은 그대로 유지 (MathJax가 처리)
        # 인라인 수식도 그대로 유지
        return text
    
    def _process_basic_markdown(self, text):
        """기본 마크다운 처리"""
        lines = text.split('\n')
        result = []
        in_mermaid = False
        
        for line in lines:
            # Mermaid 블록 감지
            if '<div class="mermaid">' in line:
                in_mermaid = True
                result.append(line)
                continue
            elif '</div>' in line and in_mermaid:
                in_mermaid = False
                result.append(line)
                continue
            elif in_mermaid:
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
            elif line.startswith('* '):
                result.append(f'<div style="color: #ccc; margin: 2px 0;">• {line[2:]}</div>')
            # 빈 줄
            elif line.strip() == '':
                result.append('<br>')
            # 일반 텍스트
            else:
                if line.strip():
                    result.append(f'<p style="color: #ccc; margin: 4px 0; line-height: 1.6;">{line}</p>')
        
        return '\n'.join(result)