#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        # 코드 블록 내부의 줄바꿈을 <br>로 변환
        code_with_br = code_content.strip().replace('\n', '<br>')
        code_html = f'<div style="background-color: #2d2d2d; border: 1px solid #444444; border-radius: 6px; padding: 12px; margin: 8px 0; font-family: Consolas, Monaco, monospace; font-size: 12px; color: #e8e8e8; white-space: pre-wrap;">{code_with_br}</div>'
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

if __name__ == '__main__':
    test_text = """자바로 계산기 코드를 작성해 드리겠습니다.

**주요 기능:**
• **덧셈**: 두 수를 더합니다
• **뺄셈**: 두 수를 뺍니다

```java
import java.util.Scanner;

public class Calculator {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        System.out.println("첫 번째 숫자:");
        double num1 = scanner.nextDouble();
    }
}
```

이 코드를 실행하면 콘솔에서 계산할 수 있습니다."""
    
    result = format_text(test_text)
    print("=== 포맷팅 결과 ===")
    print(result)
    print("\n=== HTML 파일로 저장 ===")
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>테스트</title>
    <style>
        body {{ background-color: #1a1a1a; color: #e8e8e8; font-family: Arial, sans-serif; padding: 20px; }}
    </style>
</head>
<body>
    {result}
</body>
</html>
"""
    
    with open('/Users/dolpaks/Downloads/project/chat-ai-agent/test_output.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("test_output.html 파일이 생성되었습니다. 브라우저에서 확인해보세요.")