#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
독립적인 텍스트 포맷팅 테스트 (PyQt6 의존성 없음)
"""
import re

def format_text(text):
    """텍스트 포맷팅 - 마크다운 지원"""
    
    # 1. 코드 블록 처리 먼저 (이스케이프 전에)
    code_blocks = []
    def extract_code_block(match):
        code_content = match.group(1)
        placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
        code_blocks.append(code_content)
        return placeholder
    
    text = re.sub(r'```[^\n]*\n([\s\S]*?)```', extract_code_block, text)
    
    # 2. HTML 이스케이프 처리
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # 3. **굵은글씨** 처리
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #FFD54F; font-weight: 600;">\1</strong>', text)
    
    # 4. • 불릿 포인트 처리
    text = re.sub(r'^• (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span>\1</div>', text, flags=re.MULTILINE)
    
    # 5. 코드 블록 복원
    for i, code_content in enumerate(code_blocks):
        placeholder = f"__CODE_BLOCK_{i}__"
        # 코드 내용을 줄별로 처리
        code_lines = code_content.strip().split('\n')
        formatted_lines = []
        for line in code_lines:
            # HTML 이스케이프 처리
            escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # 공백 문자를 &nbsp;로 변환
            escaped_line = escaped_line.replace(' ', '&nbsp;')
            formatted_lines.append(f'<div style="margin: 0; padding: 0; line-height: 1.4;">{escaped_line}</div>')
        
        code_html = f'<div style="background-color: #2d2d2d; border: 1px solid #444444; border-radius: 6px; padding: 12px; margin: 8px 0; font-family: Consolas, Monaco, monospace; font-size: 12px; color: #e8e8e8;">{" ".join(formatted_lines)}</div>'
        text = text.replace(placeholder, code_html)
    
    # 6. 줄바꿈 처리
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('<br>')
        elif line.startswith('<div') or line.startswith('<strong'):
            formatted_lines.append(line)
        else:
            formatted_lines.append(f'<div style="margin: 3px 0; line-height: 1.5; color: #e8e8e8;">{line}</div>')
    
    return '\n'.join(formatted_lines)

def test_format():
    """포맷팅 테스트"""
    
    test_text = """사칙연산을 수행하는 간단한 파이썬 코드를 작성해 드리겠습니다.

**주요 기능:**
• 덧셈, 뺄셈, 곱셈, 나눗셈
• 사용자 입력 처리
• 결과 출력

```python
def calculator(num1, num2):
    # 덧셈
    add = num1 + num2
    # 뺄셈
    subtract = num1 - num2
    # 곱셈
    multiply = num1 * num2
    # 나눗셈
    divide = num1 / num2 if num2 != 0 else "0으로 나눌 수 없습니다"
    return add, subtract, multiply, divide

# 숫자 입력 받기
num1 = float(input("첫 번째 숫자를 입력하세요: "))
num2 = float(input("두 번째 숫자를 입력하세요: "))

# 계산 결과 출력
result = calculator(num1, num2)
print(f"덧셈 결과: {result[0]}")
print(f"뺄셈 결과: {result[1]}")
print(f"곱셈 결과: {result[2]}")
print(f"나눗셈 결과: {result[3]}")
```

위 코드를 실행하면 **계산 결과**를 확인할 수 있습니다."""

    # 포맷팅 적용
    formatted = format_text(test_text)
    
    print("=== 포맷팅된 HTML ===")
    print(formatted)
    
    # HTML 파일로 저장
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>웹뷰 엔진 포맷팅 테스트</title>
    <style>
        body {{ 
            background-color: #1a1a1a; 
            color: #e8e8e8; 
            font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
            line-height: 1.6;
            margin: 20px;
            max-width: 800px;
        }}
    </style>
</head>
<body>
    <h1 style="color: #4FC3F7;">웹뷰 엔진 포맷팅 테스트</h1>
    {formatted}
</body>
</html>"""

    with open('webview_format_test.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("\nwebview_format_test.html 파일이 생성되었습니다.")

if __name__ == "__main__":
    test_format()