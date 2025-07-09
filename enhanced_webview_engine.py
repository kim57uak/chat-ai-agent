#!/usr/bin/env python3
"""
향상된 웹뷰 엔진 - 추가 기능 구현
"""
import re

class EnhancedWebViewEngine:
    """향상된 웹뷰 텍스트 포맷팅 엔진"""
    
    def __init__(self):
        self.code_blocks = []
        self.inline_codes = []
    
    def format_text(self, text):
        """텍스트 포맷팅 - 확장된 마크다운 지원"""
        
        # 1. 인라인 코드 처리 먼저
        self.inline_codes = []
        text = self._extract_inline_codes(text)
        
        # 2. 코드 블록 처리
        self.code_blocks = []
        text = self._extract_code_blocks(text)
        
        # 3. HTML 이스케이프 처리
        text = self._escape_html(text)
        
        # 4. 마크다운 포맷팅
        text = self._format_markdown(text)
        
        # 5. 테이블 처리
        text = self._format_tables(text)
        
        # 6. 링크 처리
        text = self._format_links(text)
        
        # 7. 인라인 코드 복원
        text = self._restore_inline_codes(text)
        
        # 8. 코드 블록 복원
        text = self._restore_code_blocks(text)
        
        # 9. 줄바꿈 처리
        text = self._format_lines(text)
        
        return text
    
    def _extract_inline_codes(self, text):
        """인라인 코드 추출"""
        def extract_inline(match):
            code_content = match.group(1)
            placeholder = f"__INLINE_CODE_{len(self.inline_codes)}__"
            self.inline_codes.append(code_content)
            return placeholder
        
        return re.sub(r'`([^`\n]+)`', extract_inline, text)
    
    def _extract_code_blocks(self, text):
        """코드 블록 추출"""
        def extract_block(match):
            language = match.group(1) or ''
            code_content = match.group(2)
            placeholder = f"__CODE_BLOCK_{len(self.code_blocks)}__"
            self.code_blocks.append((language, code_content))
            return placeholder
        
        return re.sub(r'```(\w*)\n([\s\S]*?)```', extract_block, text)
    
    def _escape_html(self, text):
        """HTML 이스케이프"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def _format_markdown(self, text):
        """마크다운 포맷팅"""
        # 헤더 처리
        text = re.sub(r'^### (.*?)$', r'<h3 style="color: #81C784; margin: 16px 0 8px 0; font-size: 16px;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2 style="color: #4FC3F7; margin: 20px 0 10px 0; font-size: 18px;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*?)$', r'<h1 style="color: #FFD54F; margin: 24px 0 12px 0; font-size: 20px;">\1</h1>', text, flags=re.MULTILINE)
        
        # 굵은 글씨
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #FFD54F; font-weight: 600;">\1</strong>', text)
        
        # 기울임
        text = re.sub(r'\*(.*?)\*', r'<em style="color: #FFA726; font-style: italic;">\1</em>', text)
        
        # 불릿 포인트 (여러 레벨 지원)
        text = re.sub(r'^  • (.*?)$', r'<div style="margin: 4px 0; margin-left: 40px; color: #e8e8e8;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">◦</span>\1</div>', text, flags=re.MULTILINE)
        text = re.sub(r'^• (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span>\1</div>', text, flags=re.MULTILINE)
        
        # 번호 목록
        text = re.sub(r'^(\d+)\. (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #4FC3F7; font-weight: bold; margin-right: 8px;">\1.</span>\2</div>', text, flags=re.MULTILINE)
        
        return text
    
    def _format_tables(self, text):
        """테이블 포맷팅"""
        lines = text.split('\n')
        result_lines = []
        in_table = False
        
        for line in lines:
            if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    result_lines.append('<table style="border-collapse: collapse; margin: 12px 0; width: 100%; max-width: 600px;">')
                    in_table = True
                
                # 헤더 구분선 건너뛰기
                if re.match(r'^\|[\s\-\|:]+\|$', line.strip()):
                    continue
                
                cells = [cell.strip() for cell in line.strip().split('|')[1:-1]]
                cell_style = 'padding: 8px 12px; border: 1px solid #444444; background-color: #2a2a2a;'
                row_html = '<tr>' + ''.join(f'<td style="{cell_style}">{cell}</td>' for cell in cells) + '</tr>'
                result_lines.append(row_html)
            else:
                if in_table:
                    result_lines.append('</table>')
                    in_table = False
                result_lines.append(line)
        
        if in_table:
            result_lines.append('</table>')
        
        return '\n'.join(result_lines)
    
    def _format_links(self, text):
        """링크 포맷팅"""
        # [텍스트](URL) 형식
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color: #4FC3F7; text-decoration: underline;" target="_blank">\1</a>', text)
        
        # 자동 URL 감지
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        text = re.sub(url_pattern, r'<a href="\g<0>" style="color: #4FC3F7; text-decoration: underline;" target="_blank">\g<0></a>', text)
        
        return text
    
    def _restore_inline_codes(self, text):
        """인라인 코드 복원"""
        for i, code_content in enumerate(self.inline_codes):
            placeholder = f"__INLINE_CODE_{i}__"
            escaped_code = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            code_html = f'<code style="background-color: #2d2d2d; color: #e8e8e8; padding: 2px 6px; border-radius: 3px; font-family: Consolas, Monaco, monospace; font-size: 11px;">{escaped_code}</code>'
            text = text.replace(placeholder, code_html)
        
        return text
    
    def _restore_code_blocks(self, text):
        """코드 블록 복원"""
        for i, (language, code_content) in enumerate(self.code_blocks):
            placeholder = f"__CODE_BLOCK_{i}__"
            
            # 언어별 색상 테마
            lang_colors = {
                'python': '#3776ab',
                'javascript': '#f7df1e',
                'html': '#e34f26',
                'css': '#1572b6',
                'sql': '#336791',
                'bash': '#4eaa25'
            }
            
            lang_color = lang_colors.get(language.lower(), '#81C784')
            
            # 코드 줄별 처리
            code_lines = code_content.strip().split('\n')
            formatted_lines = []
            
            for line_num, line in enumerate(code_lines, 1):
                escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                escaped_line = escaped_line.replace(' ', '&nbsp;')
                
                line_html = f'''
                <div style="display: flex; margin: 0; padding: 0; line-height: 1.4;">
                    <span style="color: #666; font-size: 10px; margin-right: 12px; min-width: 20px; text-align: right; user-select: none;">{line_num}</span>
                    <span>{escaped_line}</span>
                </div>'''
                formatted_lines.append(line_html)
            
            # 언어 라벨
            lang_label = f'<div style="background-color: {lang_color}; color: white; padding: 4px 8px; font-size: 10px; font-weight: bold; border-radius: 3px 3px 0 0; display: inline-block;">{language.upper() if language else "CODE"}</div>' if language else ''
            
            code_html = f'''
            <div style="margin: 12px 0;">
                {lang_label}
                <div style="background-color: #2d2d2d; border: 1px solid #444444; border-radius: {'0 6px 6px 6px' if language else '6px'}; padding: 12px; font-family: Consolas, Monaco, monospace; font-size: 12px; color: #e8e8e8; overflow-x: auto;">
                    {"".join(formatted_lines)}
                </div>
            </div>'''
            
            text = text.replace(placeholder, code_html)
        
        return text
    
    def _format_lines(self, text):
        """줄바꿈 처리"""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('<br>')
            elif any(line.startswith(tag) for tag in ['<div', '<h1', '<h2', '<h3', '<table', '<tr', '<td']):
                formatted_lines.append(line)
            else:
                formatted_lines.append(f'<div style="margin: 3px 0; line-height: 1.5; color: #e8e8e8;">{line}</div>')
        
        return '\n'.join(formatted_lines)

# 테스트 함수
def test_enhanced_engine():
    """향상된 엔진 테스트"""
    
    engine = EnhancedWebViewEngine()
    
    test_text = """# 향상된 웹뷰 엔진 테스트

## 주요 기능

### 1. 텍스트 포맷팅
- **굵은 글씨**와 *기울임* 지원
- `인라인 코드` 하이라이팅
- 여러 레벨 불릿 포인트:
  • 첫 번째 레벨
    • 두 번째 레벨

### 2. 코드 블록

```python
def hello_world():
    print("Hello, World!")
    return "완료"

# 함수 호출
result = hello_world()
```

```javascript
function greet(name) {
    console.log(`안녕하세요, ${name}님!`);
}
```

### 3. 테이블 지원

| 기능 | 상태 | 설명 |
|------|------|------|
| 마크다운 | ✅ | 완전 지원 |
| 코드 하이라이팅 | ✅ | 언어별 색상 |
| 테이블 | ✅ | 자동 포맷팅 |

### 4. 링크 지원
- 자동 링크: https://github.com
- [명시적 링크](https://www.google.com)

### 5. 번호 목록
1. 첫 번째 항목
2. 두 번째 항목
3. 세 번째 항목"""

    formatted = engine.format_text(test_text)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>향상된 웹뷰 엔진 테스트</title>
    <style>
        body {{ 
            background-color: #1a1a1a; 
            color: #e8e8e8; 
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
            line-height: 1.6;
            margin: 20px;
            max-width: 900px;
        }}
        a {{ color: #4FC3F7; }}
        a:hover {{ color: #29B6F6; }}
    </style>
</head>
<body>
    {formatted}
</body>
</html>"""

    with open('enhanced_webview_test.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("enhanced_webview_test.html 파일이 생성되었습니다!")
    print("브라우저에서 확인해보세요.")

if __name__ == "__main__":
    test_enhanced_engine()