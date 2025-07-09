#!/usr/bin/env python3
import re

def format_text(text):
    """텍스트 포맷팅 디버깅"""
    print(f"1. 입력 텍스트:\n{repr(text)}\n")
    
    # 1. 코드 블록 추출
    code_blocks = []
    def extract_code_block(match):
        code_content = match.group(1)
        placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
        code_blocks.append(code_content)
        print(f"코드 블록 추출: {len(code_content)}자")
        return placeholder
    
    text = re.sub(r'```[^\n]*\n([\s\S]*?)```', extract_code_block, text)
    print(f"2. 코드 블록 추출 후:\n{repr(text)}\n")
    print(f"추출된 코드 블록 수: {len(code_blocks)}")
    for i, block in enumerate(code_blocks):
        print(f"코드 블록 {i}:\n{repr(block)}\n")
    
    # 2. HTML 이스케이프
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    print(f"3. HTML 이스케이프 후:\n{repr(text)}\n")
    
    # 3. **굵은글씨**
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #FFD54F; font-weight: 600;">\1</strong>', text)
    print(f"4. 굵은글씨 처리 후:\n{repr(text)}\n")
    
    # 4. • 불릿 포인트
    text = re.sub(r'^• (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span>\1</div>', text, flags=re.MULTILINE)
    print(f"5. 불릿 포인트 처리 후:\n{repr(text)}\n")
    
    # 5. 코드 블록 복원
    for i, code_content in enumerate(code_blocks):
        placeholder = f"__CODE_BLOCK_{i}__"
        # 코드 블록 내부의 줄바꿈을 <br>로 변환
        code_with_br = code_content.strip().replace('\n', '<br>')
        code_html = f'<div style="background-color: #2d2d2d; border: 1px solid #444444; border-radius: 6px; padding: 12px; margin: 8px 0; font-family: Consolas, Monaco, monospace; font-size: 12px; color: #e8e8e8; white-space: pre-wrap;">{code_with_br}</div>'
        text = text.replace(placeholder, code_html)
        print(f"코드 블록 {i} 복원 완료")
    
    print(f"6. 코드 블록 복원 후:\n{repr(text)}\n")
    
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
    
    result = '\n'.join(formatted_lines)
    print(f"7. 최종 결과:\n{result}\n")
    return result

if __name__ == '__main__':
    test_text = """자바로 계산기 코드를 만들어드리겠습니다.

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
    
    format_text(test_text)