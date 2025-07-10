#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.chat_widget import ChatWidget
from PyQt6.QtWidgets import QApplication # QApplication 임포트

# QApplication 인스턴스 생성 (테스트를 위해)
app = QApplication(sys.argv)

# ChatWidget 인스턴스 생성
widget = ChatWidget()

# 테스트 텍스트
test_text = """사칙연산을 수행하는 간단한 파이썬 코드를 작성해 드리겠습니다.

```python
def calculator(num1, num2):
    # 덧셈
    add = num1 + num2
    # 뺄셈
    subtract = num1 - num2
    # 곱셈
    multiply = num1 * num2
    # 나눗셈
    divide = num1 / num2
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

위 코드를 실행하면 결과를 확인할 수 있습니다."""

# 포맷팅 테스트
formatted = widget.format_text(test_text)
print("=== 포맷팅 결과 ===")
print(formatted)

# HTML 파일로 저장
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>현재 포맷팅 테스트</title>
    <style>
        body {{ background-color: #1a1a1a; color: #e8e8e8; font-family: Arial, sans-serif; padding: 20px; }}
    </style>
</head>
<body>
    {formatted}
</body>
</html>
"""

with open('/Users/dolpaks/Downloads/project/chat-ai-agent/current_format_test.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("\ncurrent_format_test.html 파일이 생성되었습니다.")

# QApplication 종료 (테스트 환경에서만 필요)
app.quit()