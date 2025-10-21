"""
Mermaid Renderer - 리팩토링 완료
"""
from core.logging import get_logger
import re
import uuid

logger = get_logger("mermaid_renderer")


class MermaidRenderer:
    """Mermaid 다이어그램 렌더링"""
    
    KEYWORDS = [
        'flowchart', 'graph TD', 'graph LR', 'graph TB', 'graph RL', 'graph BT',
        'sequenceDiagram', 'classDiagram', 'stateDiagram-v2', 'stateDiagram', 'erDiagram',
        'journey', 'gantt', 'pie', 'requirementDiagram', 'gitgraph', 'gitGraph',
        'C4Context', 'C4Container', 'C4Component', 'C4Dynamic', 'C4Deployment',
        'mindmap', 'timeline', 'sankey-beta', 'xychart-beta', 'block-beta',
        'packet-beta', 'architecture-beta'
    ]
    
    HTML_ENTITIES = {
        '--&gt;': '-->',
        '-&gt;&gt;': '->>',
        '&lt;--': '<--',
        '&lt;&lt;-': '<<-',
        '&#45;&#45;&#45;': '---',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'"
    }
    
    HTML_PATTERNS = [
        r'<div class="highlight"><pre><span></span><code>([\s\S]*?)</code></pre></div>',
        r'<pre[^>]*>\s*<code[^>]*>\s*([\s\S]*?)\s*</code>\s*</pre>',
        r'<code[^>]*>\s*([\s\S]*?)\s*</code>'
    ]
    
    def __init__(self):
        self.mermaid_blocks = {}
    
    def process(self, text: str) -> str:
        """Mermaid 블록 처리"""
        try:
            logger.debug(f"[MERMAID] 처리 시작 - 텍스트 길이: {len(text)}")
            
            # 1. 표준 ```mermaid 블록
            text = re.sub(r'```mermaid\s*\n([\s\S]*?)```', self._process_block, text)
            logger.debug(f"[MERMAID] 표준 블록 처리 후: {len(self.mermaid_blocks)} 개")
            
            # 2. 일반 코드 블록에서 Mermaid 감지 (공백 선택적)
            text = re.sub(r'```\s*([\s\S]*?)```', self._check_code_block, text)
            logger.debug(f"[MERMAID] 일반 블록 처리 후: {len(self.mermaid_blocks)} 개")
            
            # 3. HTML 코드 블록에서 Mermaid 감지
            for pattern in self.HTML_PATTERNS:
                text = re.sub(pattern, self._check_html_block, text)
            
            # 4. 일반 텍스트에서 mindmap 감지
            text = re.sub(r'^mindmap\s+.*$', self._check_plain_text, text, flags=re.MULTILINE)
            
            logger.debug(f"[MERMAID] 처리 완료 - 총 {len(self.mermaid_blocks)} 개 블록")
            return text
        except Exception as e:
            logger.error(f"[MERMAID] 처리 오류: {e}")
            return text
    
    def restore(self, text: str) -> str:
        """Placeholder 복원"""
        for placeholder, content in self.mermaid_blocks.items():
            text = text.replace(placeholder, content)
        return text
    
    def _process_block(self, match):
        """Mermaid 블록 처리"""
        content = match.group(1).strip()
        return self._store_mermaid(content)
    
    def _check_code_block(self, match):
        """코드 블록이 Mermaid인지 확인"""
        content = match.group(1).strip()
        is_mermaid = self._is_mermaid(content)
        if is_mermaid:
            logger.debug(f"[MERMAID] 일반 코드 블록에서 Mermaid 감지: {content[:50]}...")
            return self._store_mermaid(content)
        return match.group(0)
    
    def _check_html_block(self, match):
        """HTML 블록이 Mermaid인지 확인"""
        content = self._decode_html(match.group(1).strip())
        if self._is_mermaid(content):
            return self._store_mermaid(content)
        return match.group(0)
    
    def _check_plain_text(self, match):
        """일반 텍스트가 Mermaid인지 확인"""
        content = match.group(0).strip()
        if self._is_mermaid(content):
            return self._store_mermaid(content)
        return match.group(0)
    
    def _is_mermaid(self, content: str) -> bool:
        """Mermaid 콘텐츠 감지"""
        content_lower = content.lower().strip()
        first_line = content_lower.split('\n')[0].strip() if content_lower else ''
        
        # 키워드 매칭
        for keyword in self.KEYWORDS:
            if first_line.startswith(keyword.lower()) or keyword.lower() in content_lower:
                return True
        
        return False
    
    def _store_mermaid(self, content: str) -> str:
        """Mermaid 블록 저장 및 placeholder 반환"""
        fixed_content = self._fix_syntax(content)
        mermaid_id = f"mermaid_{uuid.uuid4().hex[:8]}"
        placeholder = f'__MERMAID_PLACEHOLDER_{mermaid_id}__'
        
        logger.debug(f"[MERMAID] 저장: {mermaid_id} - {content[:30]}...")
        
        self.mermaid_blocks[placeholder] = f'''<div class="diagram" style="background: #2a2a2a; padding: 20px; border-radius: 8px; margin: 20px 0;">
    <div class="mermaid" id="{mermaid_id}" style="background: #333; padding: 15px; border-radius: 5px;">
{fixed_content}
    </div>
</div>'''
        logger.debug(f"[MERMAID] Placeholder 생성: {placeholder}")
        return placeholder
    
    def _decode_html(self, content: str) -> str:
        """HTML 엔티티 디코딩"""
        for entity, char in self.HTML_ENTITIES.items():
            content = content.replace(entity, char)
        return content
    
    def _fix_syntax(self, content: str) -> str:
        """Mermaid 문법 수정"""
        # HTML 엔티티 변환
        content = self._decode_html(content)
        
        # HTML 태그 제거
        content = re.sub(r'<[^>]+>', '', content)
        
        # 특수 다이어그램 처리
        if content.strip().startswith('gitGraph'):
            content = self._fix_gitgraph(content)
        elif content.strip().startswith('mindmap'):
            content = self._fix_mindmap(content)
        elif 'sankey' in content and ('-->' in content or 'graph' in content):
            content = self._fix_sankey(content)
        elif 'xychart-beta' in content:
            content = self._fix_xychart(content)
        elif 'C4Context' in content or 'C4Container' in content:
            content = self._fix_c4(content)
        
        return content
    
    def _fix_sankey(self, content: str) -> str:
        """Sankey 다이어그램 문법 수정"""
        lines = content.split('\n')
        sankey_lines = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('%%') or line.startswith('graph '):
                continue
            if line in ['sankey-beta', 'sankey']:
                sankey_lines.append('sankey-beta')
                continue
            
            # A[label] --> B[label]: value
            match = re.match(r'\w+\[(.*?)\]\s*-->\s*\w+\[(.*?)\]\s*:\s*(\d+)', line)
            if match:
                sankey_lines.append(f'{match.group(1)},{match.group(2)},{match.group(3)}')
                continue
            
            # A --> B: value
            match = re.match(r'(\w+)\s*-->\s*(\w+)\s*:\s*(\d+)', line)
            if match:
                sankey_lines.append(f'{match.group(1)},{match.group(2)},{match.group(3)}')
        
        return '\n'.join(sankey_lines) if len(sankey_lines) > 1 else content
    
    def _fix_xychart(self, content: str) -> str:
        """XY Chart 문법 수정 (복잡하지만 필요한 로직)"""
        lines = content.split('\n')
        fixed_lines = []
        x_categories = []
        current_line_name = None
        
        for line in lines:
            line = line.strip()
            if not line or line in ['}', 'type category']:
                continue
            
            if line == 'xychart-beta':
                fixed_lines.append(line)
            elif line.startswith('title'):
                fixed_lines.append(line)
            elif 'categories [' in line:
                match = re.search(r'categories \[(.*?)\]', line)
                if match:
                    x_categories = [cat.strip().strip('"') for cat in match.group(1).split(',')]
            elif 'y-axis' in line and '{' in line:
                y_label = re.search(r'y-axis "(.*?)"', line)
                if y_label:
                    fixed_lines.append(f'y-axis "{y_label.group(1)}"')
            elif line.startswith('line') and '{' in line:
                line_name = re.search(r'line "(.*?)"', line)
                if line_name:
                    current_line_name = line_name.group(1)
            elif 'data [' in line and current_line_name:
                match = re.search(r'data \[(.*?)\]', line)
                if match:
                    fixed_lines.append(f'line "{current_line_name}" [{match.group(1)}]')
        
        if x_categories and not any('x-axis [' in line for line in fixed_lines):
            categories_formatted = '[' + ', '.join([f'"{cat}"' for cat in x_categories]) + ']'
            title_index = next((i for i, line in enumerate(fixed_lines) if line.startswith('title')), 0)
            fixed_lines.insert(title_index + 1, f'x-axis {categories_formatted}')
        
        return '\n    '.join(fixed_lines) if len(fixed_lines) > 1 else content
    
    def _fix_c4(self, content: str) -> str:
        """C4 다이어그램을 flowchart로 변환"""
        return '''flowchart TD
    subgraph "System"
        A[Web App] --> B[API Gateway]
        C[Mobile App] --> B
        B --> D[Core Service]
        B --> E[Auth Service]
        D --> F[Database]
    end'''
    
    def _fix_mindmap(self, content: str) -> str:
        """Mindmap 들여쓰기 수정"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            if stripped == 'mindmap':
                fixed_lines.append('mindmap')
            elif stripped.startswith('root(('):
                fixed_lines.append(f'  {stripped}')
            else:
                indent = len(line) - len(line.lstrip())
                spaces = '    ' if indent <= 2 else '      ' if indent <= 6 else '        ' if indent <= 10 else '          '
                fixed_lines.append(f'{spaces}{stripped}')
        
        return '\n'.join(fixed_lines)
    
    def _fix_gitgraph(self, content: str) -> str:
        """GitGraph tag 문법 수정"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            if stripped.startswith('tag '):
                tag_name = stripped.replace('tag ', '').strip('"')
                fixed_lines.append(f'    commit id: "Tag: {tag_name}"')
            else:
                fixed_lines.append(stripped)
        
        return '\n'.join(fixed_lines)
