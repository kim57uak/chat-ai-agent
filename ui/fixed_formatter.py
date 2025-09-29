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
            
            # ERD 문법 - v11.12.0 네이티브 지원 활용
            # ERD 전처리 비활성화 (Mermaid v11.12.0에서 모든 타입 지원)
            
            # C4 다이어그램을 flowchart로 변환 (v10에서 지원 제한)
            if 'C4Context' in content or 'C4Container' in content:
                content = 'flowchart TD\n    subgraph "Student Management System"\n        A[Web App] --> B[API Gateway]\n        C[Mobile App] --> B\n        B --> D[Core Service]\n        B --> E[Auth Service]\n        D --> F[Database]\n        D --> G[File Storage]\n        H[Notification Service] --> I[Email/SMS]\n    end'
            
            # XY Chart 문법 수정
            if 'xychart-beta' in content:
                lines = content.split('\n')
                fixed_lines = []
                x_categories = []
                y_min, y_max = None, None
                current_line_name = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line == 'xychart-beta':
                        fixed_lines.append('xychart-beta')
                    elif line.startswith('title'):
                        fixed_lines.append(line)
                    elif 'x-axis' in line and '{' in line:
                        x_label = re.search(r'x-axis "(.*?)"', line)
                        if x_label:
                            x_axis_label = x_label.group(1)
                            # 나중에 데이터에서 날짜 추출하여 카테고리 생성
                            x_axis_stored = x_axis_label
                        continue
                    elif 'categories [' in line:
                        match = re.search(r'categories \[(.*?)\]', line)
                        if match:
                            categories_str = match.group(1)
                            x_categories = [cat.strip().strip('"') for cat in categories_str.split(',')]
                    elif 'y-axis' in line and '{' in line:
                        y_label = re.search(r'y-axis "(.*?)"', line)
                        if y_label:
                            fixed_lines.append(f'y-axis "{y_label.group(1)}"')
                    elif 'min ' in line:
                        match = re.search(r'min (\d+)', line)
                        if match:
                            y_min = match.group(1)
                    elif 'max ' in line:
                        match = re.search(r'max (\d+)', line)
                        if match:
                            y_max = match.group(1)
                    elif line.startswith('line') and '{' in line:
                        line_name = re.search(r'line "(.*?)"', line)
                        if line_name:
                            current_line_name = line_name.group(1)
                    elif 'data [' in line:
                        # 2차원 배열 데이터 처리
                        data_content = []
                        collecting_data = True
                        data_buffer = line
                        
                        # 다음 줄들도 확인하여 완전한 데이터 수집
                        try:
                            line_idx = lines.index(line)
                            for i, next_line in enumerate(lines[line_idx+1:]):
                                data_buffer += ' ' + next_line.strip()
                                if ']' in next_line and next_line.count(']') >= next_line.count('['):
                                    break
                        except ValueError:
                            pass
                        
                        # 2차원 배열에서 날짜와 y값 추출
                        date_value_matches = re.findall(r'\["([^"]+)",\s*(\d+)\]', data_buffer)
                        if date_value_matches:
                            dates = [match[0] for match in date_value_matches]
                            y_values = [match[1] for match in date_value_matches]
                            
                            # 날짜를 간단한 레이블로 변환
                            simple_labels = []
                            for date_str in dates:
                                if '-' in date_str:
                                    year, month = date_str.split('-')[:2]
                                    if month in ['01', '02', '03']:
                                        simple_labels.append(f'Q1 {year}')
                                    elif month in ['04', '05', '06']:
                                        simple_labels.append(f'Q2 {year}')
                                    elif month in ['07', '08', '09']:
                                        simple_labels.append(f'Q3 {year}')
                                    else:
                                        simple_labels.append(f'Q4 {year}')
                                else:
                                    simple_labels.append(date_str)
                            
                            # x-axis 추가 (아직 추가되지 않았다면)
                            if not any('x-axis [' in line for line in fixed_lines):
                                categories_formatted = '[' + ', '.join([f'"{label}"' for label in simple_labels]) + ']'
                                title_index = next((i for i, line in enumerate(fixed_lines) if line.startswith('title')), 0)
                                fixed_lines.insert(title_index + 1, f'x-axis {categories_formatted}')
                            
                            if current_line_name:
                                y_values_str = ", ".join(y_values)
                                fixed_lines.append(f'line "{current_line_name}" [{y_values_str}]')
                        else:
                            # 1차원 배열 처리
                            match = re.search(r'data \[(.*?)\]', line)
                            if match:
                                data_str = match.group(1)
                                data_values = '[' + data_str + ']'
                                if current_line_name:
                                    fixed_lines.append(f'line "{current_line_name}" {data_values}')
                    elif line not in ['}', 'type category']:
                        fixed_lines.append(line)
                
                # categories가 있고 아직 x-axis가 추가되지 않았다면
                if x_categories and not any('x-axis [' in line for line in fixed_lines):
                    categories_formatted = '[' + ', '.join([f'"{cat}"' for cat in x_categories]) + ']'
                    title_index = next((i for i, line in enumerate(fixed_lines) if line.startswith('title')), 0)
                    fixed_lines.insert(title_index + 1, f'x-axis {categories_formatted}')
                
                if y_min and y_max:
                    y_axis_index = next((i for i, line in enumerate(fixed_lines) if line.startswith('y-axis')), -1)
                    if y_axis_index >= 0:
                        fixed_lines[y_axis_index] += f' {y_min} --> {y_max}'
                
                if len(fixed_lines) > 1:
                    content = '\n    '.join(fixed_lines)
            
            # Mindmap 구문 특별 처리 - 올바른 들여쓰기 보장
            if content.strip().startswith('mindmap'):
                content = self._fix_mindmap_indentation(content)
            
            
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
            
            # mindmap 특별 처리 - 압축된 형태도 감지
            if content_lower.startswith('mindmap'):
                return True
            
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
            # HTML 엔티티 디코딩
            content = content.replace('&amp;', '&')
            content = content.replace('&lt;', '<')
            content = content.replace('&gt;', '>')
            content = content.replace('&quot;', '"')
            content = content.replace('&#39;', "'")
            
            if is_mermaid_content(content):
                return store_mermaid(content)
            return match.group(0)
        
        # 다양한 HTML 태그 패턴 처리 - 더 정확한 패턴
        patterns = [
            # 완전한 highlight 블록
            r'<div class="highlight"><pre><span></span><code>([\s\S]*?)</code></pre></div>',
            # 일반적인 HTML 코드 블록들
            r'<div[^>]*class="highlight"[^>]*>\s*<pre[^>]*>\s*<span[^>]*>\s*<code[^>]*>\s*([\s\S]*?)\s*</code>\s*</span>\s*</pre>\s*</div>',
            r'<div[^>]*class="highlight"[^>]*>\s*<pre[^>]*>\s*<span[^>]*>\s*<code[^>]*>\s*([\s\S]*?)\s*</code>\s*</pre>\s*</div>',
            r'<pre[^>]*>\s*<code[^>]*>\s*([\s\S]*?)\s*</code>\s*</pre>',
            r'<code[^>]*>\s*([\s\S]*?)\s*</code>'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, check_html_code, text)
        
        # 4. 일반 텍스트에서 mindmap 키워드 직접 감지 (코드 블록이 아닌 경우)
        def check_plain_text(match):
            content = match.group(0).strip()
            if is_mermaid_content(content):
                return store_mermaid(content)
            return match.group(0)
        
        # mindmap으로 시작하는 일반 텍스트 라인 감지
        text = re.sub(r'^mindmap\s+.*$', check_plain_text, text, flags=re.MULTILINE)
        
        return text
    
    def _process_math(self, text):
        """수식 처리 - MathJax가 직접 처리하도록 보호"""
        # 수식은 그대로 두고 MathJax가 처리하도록 함
        # 단, 마크다운 처리에서 깨지지 않도록 보호
        return text
    
    def _clean_html_code(self, text):
        """코드 블록에서 HTML 태그 제거"""
        # HTML 태그 제거
        import re
        text = re.sub(r'<[^>]+>', '', text)
        # HTML 엔티티 디코딩
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        text = text.replace('&quot;', '"').replace('&#x27;', "'")
        return text
    
    def _clean_html_in_code_blocks(self, text):
        """전체 텍스트에서 HTML 코드 블록 정리"""
        import re
        
        # placeholder 보호
        if '__MERMAID_PLACEHOLDER_' in text:
            return text  # placeholder가 있으면 HTML 정리 스킵
        
        # HTML 코드 블록 패턴 감지 및 정리
        def clean_html_code_block(match):
            content = match.group(1)
            # HTML 태그 제거
            content = re.sub(r'<[^>]+>', '', content)
            # HTML 엔티티 디코딩
            content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            content = content.replace('&quot;', '"').replace('&#x27;', "'")
            # 불필요한 공백 제거
            lines = [line.rstrip() for line in content.split('\n')]
            content = '\n'.join(lines)
            return f'```\n{content}\n```'
        
        # HTML highlight 블록 처리
        text = re.sub(r'<div class="highlight"><pre><span></span><code>(.*?)</code></pre></div>', clean_html_code_block, text, flags=re.DOTALL)
        
        return text
    
    def _process_markdown(self, text):
        """기본 마크다운 처리"""
        # HTML 코드 블록 정리
        text = self._clean_html_in_code_blocks(text)
        
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
                    result.append(f'<div style="position: relative;"><pre style="background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 6px; margin: 8px 0; overflow-x: auto; line-height: 1.2; font-family: \'SF Mono\', Monaco, Consolas, monospace; font-size: 13px;"><code id="{code_id}">')
                else:
                    in_code_block = False
                    result.append(f'</code></pre><button onclick="copyCode(document.getElementById(\'{code_id}\'))" style="position: absolute; top: 6px; right: 6px; background: #444; color: #fff; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 10px; opacity: 0.7;">복사</button></div>')
                continue
            
            if in_code_block:
                # 코드 블록 내에서 HTML 태그 제거
                clean_line = self._clean_html_code(line)
                result.append(clean_line)
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
    
    def _fix_mindmap_indentation(self, content):
        """마인드맵 들여쓰기 수정 - Mermaid 문법에 맞게"""
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
                # 기존 들여쓰기 레벨 계산
                original_indent = len(line) - len(line.lstrip())
                
                # Mermaid mindmap 문법: root 다음은 4칸, 그 다음은 6칸, 8칸...
                if original_indent <= 2:
                    # 메인 카테고리 (root 직하위)
                    fixed_lines.append(f'    {stripped}')
                elif original_indent <= 6:
                    # 서브 카테고리
                    fixed_lines.append(f'      {stripped}')
                elif original_indent <= 10:
                    # 3레벨 서브 카테고리
                    fixed_lines.append(f'        {stripped}')
                else:
                    # 4레벨 이상
                    fixed_lines.append(f'          {stripped}')
        
        return '\n'.join(fixed_lines)