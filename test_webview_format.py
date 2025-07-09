#!/usr/bin/env python3
"""
웹뷰 엔진의 개선된 텍스트 포맷팅 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.chat_widget import ChatWidget
import re

def test_format_text():
    """포맷팅 함수 테스트"""
    
    # ChatWidget 인스턴스 생성 (GUI 없이 포맷팅 함수만 테스트)
    widget = ChatWidget()
    
    # 테스트 텍스트
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
    formatted = widget.format_text(test_text)
    
    print("=== 원본 텍스트 ===")
    print(test_text)
    print("\n=== 포맷팅된 HTML ===")
    print(formatted)
    
    # HTML 파일로 저장
    html_content = f"""
<!DOCTYPE html>
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
</html>
"""

    output_path = '/Users/dolpaks/Downloads/project/chat-ai-agent/webview_format_test.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n테스트 결과가 {output_path} 파일로 저장되었습니다.")
    print("브라우저에서 확인해보세요!")

if __name__ == "__main__":
    test_format_text()