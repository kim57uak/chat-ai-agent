#!/usr/bin/env python3
"""
확장된 웹뷰 엔진 포맷팅 테스트
"""
import re

def format_text(text):
    """확장된 텍스트 포맷팅"""
    
    # 1. 코드 블록 처리 먼저
    code_blocks = []
    def extract_code_block(match):
        code_content = match.group(1)
        placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
        code_blocks.append(code_content)
        return placeholder
    
    text = re.sub(r'```[^\n]*\n([\s\S]*?)```', extract_code_block, text)
    
    # 2. 인라인 코드 처리
    inline_codes = []
    def extract_inline_code(match):
        code_content = match.group(1)
        placeholder = f"__INLINE_CODE_{len(inline_codes)}__"
        inline_codes.append(code_content)
        return placeholder
    
    text = re.sub(r'`([^`]+)`', extract_inline_code, text)
    
    # 3. HTML 이스케이프 처리
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # 4. 헤딩 처리
    text = re.sub(r'^### (.*?)$', r'<h3 style="color: #81C784; margin: 16px 0 8px 0; font-size: 16px;">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2 style="color: #4FC3F7; margin: 20px 0 10px 0; font-size: 18px;">\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*?)$', r'<h1 style="color: #FFD54F; margin: 24px 0 12px 0; font-size: 20px;">\1</h1>', text, flags=re.MULTILINE)
    
    # 5. 링크 처리
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #4FC3F7; text-decoration: underline;" target="_blank">\1</a>', text)
    text = re.sub(r'(https?://[^\s]+)', r'<a href="\1" style="color: #4FC3F7; text-decoration: underline;" target="_blank">\1</a>', text)
    
    # 6. **굵은글씨** 및 *기울임* 처리
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #FFD54F; font-weight: 600;">\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em style="color: #FFA726; font-style: italic;">\1</em>', text)
    
    # 7. 번호 목록 처리
    text = re.sub(r'^(\d+)\. (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #4FC3F7; font-weight: bold; margin-right: 8px;">\1.</span>\2</div>', text, flags=re.MULTILINE)
    
    # 8. 불릿 포인트 처리
    text = re.sub(r'^• (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span>\1</div>', text, flags=re.MULTILINE)
    text = re.sub(r'^- (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span>\1</div>', text, flags=re.MULTILINE)
    
    # 9. 테이블 처리
    lines = text.split('\n')
    table_lines = []
    in_table = False
    for line in lines:
        if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
            if not in_table:
                table_lines.append('<table style="border-collapse: collapse; margin: 12px 0; width: 100%; max-width: 600px;">')
                in_table = True
            cells = [cell.strip() for cell in line.strip().split('|')[1:-1]]
            row_html = '<tr>' + ''.join(f'<td style="padding: 8px 12px; border: 1px solid #444444; background-color: #2a2a2a;">{cell}</td>' for cell in cells) + '</tr>'
            table_lines.append(row_html)
        else:
            if in_table:
                table_lines.append('</table>')
                in_table = False
            table_lines.append(line)
    if in_table:
        table_lines.append('</table>')
    text = '\n'.join(table_lines)
    
    # 10. 인라인 코드 복원
    for i, code_content in enumerate(inline_codes):
        placeholder = f"__INLINE_CODE_{i}__"
        escaped_code = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        code_html = f'<code style="background-color: #2d2d2d; color: #e8e8e8; padding: 2px 6px; border-radius: 3px; font-family: Consolas, Monaco, monospace; font-size: 11px;">{escaped_code}</code>'
        text = text.replace(placeholder, code_html)
    
    # 11. 코드 블록 복원
    for i, code_content in enumerate(code_blocks):
        placeholder = f"__CODE_BLOCK_{i}__"
        code_lines = code_content.strip().split('\n')
        formatted_lines = []
        for line in code_lines:
            escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            escaped_line = escaped_line.replace(' ', '&nbsp;')
            formatted_lines.append(f'<div style="margin: 0; padding: 0; line-height: 1.4;">{escaped_line}</div>')
        
        code_html = f'<div style="background-color: #2d2d2d; border: 1px solid #444444; border-radius: 6px; padding: 12px; margin: 8px 0; font-family: Consolas, Monaco, monospace; font-size: 12px; color: #e8e8e8;">{"".join(formatted_lines)}</div>'
        text = text.replace(placeholder, code_html)
    
    # 12. 줄바꿈 처리
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('<br>')
        elif line.startswith('<') or line.startswith('</'):
            formatted_lines.append(line)
        else:
            formatted_lines.append(f'<div style="margin: 3px 0; line-height: 1.5; color: #e8e8e8;">{line}</div>')
    
    return '\n'.join(formatted_lines)

# 테스트 텍스트
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
    console.log(`Hello, ${name}!`);
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

formatted = format_text(test_text)

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