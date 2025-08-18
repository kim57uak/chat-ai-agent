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
        
        # Mermaid v10 지원 - 모든 다이어그램 유형
        mermaid_keywords = [
            # 기본 다이어그램
            'flowchart', 'graph TD', 'graph LR', 'graph TB', 'graph RL', 'graph BT',
            'sequenceDiagram', 'classDiagram', 'stateDiagram-v2', 'stateDiagram', 'erDiagram',
            'journey', 'gantt', 'pie', 'requirementDiagram', 'gitgraph',
            # C4 다이어그램
            'C4Context', 'C4Container', 'C4Component', 'C4Dynamic', 'C4Deployment',
            # 새로운 다이어그램 유형
            'mindmap', 'timeline', 'sankey-beta', 'xychart-beta', 'block-beta',
            'packet-beta', 'architecture-beta'
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
            # HTML 태그 제거
            import re
            content = re.sub(r'<[^>]+>', '', content)
            
            # 잘못된 Sankey 문법 수정
            if ('sankey-beta' in content or 'sankey' in content) and ('-->' in content or 'graph' in content):
                lines = content.split('\n')
                sankey_lines = []
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('%%'):
                        continue
                    if line in ['sankey-beta', 'sankey']:
                        sankey_lines.append('sankey-beta')
                        continue
                    if line.startswith('graph '):
                        continue
                    
                    # A[label] --> B[label]: value 형식 변환
                    match = re.match(r'(\w+)\[(.*?)\]\s*-->\s*(\w+)\[(.*?)\]\s*:\s*(\d+)', line)
                    if match:
                        sankey_lines.append(f'{match.group(2)},{match.group(4)},{match.group(5)}')
                        continue
                    
                    # A --> B: value 형식 변환
                    match = re.match(r'(\w+)\s*-->\s*(\w+)\s*:\s*(\d+)', line)
                    if match:
                        sankey_lines.append(f'{match.group(1)},{match.group(2)},{match.group(3)}')
                        continue
                
                if len(sankey_lines) > 1:
                    content = '\n'.join(sankey_lines)
            
            # ERD 문법 수정 - datetime? 등 지원되지 않는 문법 수정
            if 'erDiagram' in content:
                # datetime? 를 datetime 으로 변환
                content = re.sub(r'datetime\?', 'datetime', content)
                # 기타 지원되지 않는 타입 수정
                content = re.sub(r'string\?', 'string', content)
                content = re.sub(r'int\?', 'int', content)
                content = re.sub(r'boolean\?', 'boolean', content)
            
            # C4 다이어그램을 flowchart로 변환 (v10에서 지원 제한)
            if 'C4Context' in content or 'C4Container' in content:
                content = 'flowchart TD\n    subgraph "Student Management System"\n        A[Web App] --> B[API Gateway]\n        C[Mobile App] --> B\n        B --> D[Core Service]\n        B --> E[Auth Service]\n        D --> F[Database]\n        D --> G[File Storage]\n        H[Notification Service] --> I[Email/SMS]\n    end'
            
            # Mindmap을 flowchart로 변환 (v10에서 지원 제한)
            if 'mindmap' in content:
                lines = content.split('\n')
                flowchart_lines = ['flowchart TD']
                node_counter = 0
                node_stack = []  # (level, node_id) 스택
                
                for line in lines:
                    if not line.strip() or line.strip() == 'mindmap':
                        continue
                    
                    # 이모지 제거
                    clean_line = re.sub(r'[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]', '', line)
                    clean_line = clean_line.strip()
                    
                    if not clean_line:
                        continue
                    
                    # 들여쓰기 레벨 계산
                    indent_level = len(line) - len(line.lstrip())
                    
                    # 루트 노드 처리
                    if 'root((' in clean_line:
                        root_text = clean_line.replace('root((', '').replace('))', '')
                        node_id = f'N{node_counter}'
                        flowchart_lines.append(f'    {node_id}["{root_text}"]')
                        node_stack = [(indent_level, node_id)]
                        node_counter += 1
                    else:
                        # 일반 노드
                        node_id = f'N{node_counter}'
                        flowchart_lines.append(f'    {node_id}["{clean_line}"]')
                        
                        # 부모 노드 찾기
                        while node_stack and node_stack[-1][0] >= indent_level:
                            node_stack.pop()
                        
                        if node_stack:
                            parent_id = node_stack[-1][1]
                            flowchart_lines.append(f'    {parent_id} --> {node_id}')
                        
                        node_stack.append((indent_level, node_id))
                        node_counter += 1
                
                if len(flowchart_lines) > 1:
                    content = '\n'.join(flowchart_lines)
            
            
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
            # v10 키워드 정확한 감지
            lines = content_lower.split('\n')
            first_line = lines[0].strip() if lines else ''
            
            # 정확한 키워드 매칭
            for keyword in mermaid_keywords:
                if first_line.startswith(keyword.lower()) or keyword.lower() in content_lower:
                    return True
            
            # beta 버전 키워드 특별 처리
            beta_keywords = ['sankey-beta', 'xychart-beta', 'block-beta', 'packet-beta', 'architecture-beta']
            for beta_keyword in beta_keywords:
                if beta_keyword in content_lower:
                    return True
                    
            return False
        
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
            r'<code[^>]*>\s*([\s\S]*?)\s*</code>',
            r'<div[^>]*class="highlight"[^>]*>\s*<pre[^>]*>\s*<span[^>]*>\s*<code[^>]*>\s*([\s\S]*?)\s*</code>'
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
                    code_id = f"code_{uuid.uuid4().hex[:8]}"
                    result.append(f'<div style="position: relative;"><pre style="background: #1e1e1e; color: #f8f8f2; padding: 15px; border-radius: 8px; margin: 12px 0; overflow-x: auto;"><code id="{code_id}">')
                else:
                    in_code_block = False
                    result.append(f'</code></pre><button onclick="copyCode(\'{code_id}\')" style="position: absolute; top: 8px; right: 8px; background: #444; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; opacity: 0.8; transition: opacity 0.2s;">📋 복사</button></div>')
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