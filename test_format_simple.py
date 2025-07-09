#!/usr/bin/env python3
import re

def format_text(text):
    """현재 앱에서 사용하는 format_text 함수와 동일"""
    
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
        
        code_html = f'''<div style="background-color: #2d2d2d; border: 1px solid #444444; border-radius: 6px; padding: 12px; margin: 8px 0; font-family: Consolas, Monaco, monospace; font-size: 12px; color: #e8e8e8;">{"".join(formatted_lines)}</div>'''
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

# 테스트
test_text = """사칙연산을 수행하는 간단한 파이썬 코드를 작성해 드리겠습니다.

```python
def calculator(num1, num2):
    # 덧셈
    add = num1 + num2
    # 뺄셈
    subtract = num1 - num2
    return add, subtract

num1 = float(input("첫 번째 숫자: "))
num2 = float(input("두 번째 숫자: "))
result = calculator(num1, num2)
print(f"덧셈: {result[0]}")
print(f"뺄셈: {result[1]}")
```

위 코드를 실행하면 결과를 확인할 수 있습니다."""

print("=== 테스트 시작 ===")
formatted = format_text(test_text)
print("=== 포맷팅 결과 ===")
print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

# HTML 파일로 저장
html_content = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>테스트</title>
<style>body {{ background-color: #1a1a1a; color: #e8e8e8; font-family: Arial, sans-serif; padding: 20px; }}</style>
</head><body>{formatted}</body></html>"""

with open('/Users/dolpaks/Downloads/project/chat-ai-agent/format_test_result.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("\nformat_test_result.html 파일 생성 완료!")
print("브라우저에서 열어서 코드 블록이 올바르게 표시되는지 확인하세요.")