#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextBrowser, QPushButton
from PyQt6.QtCore import Qt

class HTMLTestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML 렌더링 테스트")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # QTextBrowser 생성
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #1a1a1a;
                color: #e8e8e8;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 16px;
                font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        
        layout.addWidget(self.text_browser)
        
        # 테스트 버튼들
        btn1 = QPushButton("코드 블록 테스트")
        btn1.clicked.connect(self.test_code_block)
        layout.addWidget(btn1)
        
        btn2 = QPushButton("마크다운 테스트")
        btn2.clicked.connect(self.test_markdown)
        layout.addWidget(btn2)
        
        btn3 = QPushButton("전체 테스트")
        btn3.clicked.connect(self.test_full)
        layout.addWidget(btn3)
        
        self.setLayout(layout)
    
    def test_code_block(self):
        """코드 블록 테스트"""
        html = """
        <div style="margin: 8px 0; padding: 12px; background: #2d4a2d; border-left: 4px solid #66BB6A; border-radius: 8px;">
            <div style="color: #66BB6A; font-weight: bold; margin-bottom: 8px;">🤖 AI</div>
            <div style="color: #ffffff;">
                자바 계산기 코드입니다:
                <div style="
                    background-color: #2d2d2d;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    padding: 12px;
                    margin: 8px 0;
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 12px;
                    color: #e8e8e8;
                    white-space: pre-wrap;
                ">import java.util.Scanner;

public class Calculator {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        
        System.out.println("첫 번째 숫자:");
        double num1 = scanner.nextDouble();
        
        System.out.println("두 번째 숫자:");
        double num2 = scanner.nextDouble();
        
        System.out.println("연산자 (+, -, *, /):");
        char op = scanner.next().charAt(0);
        
        double result = 0;
        switch (op) {
            case '+': result = num1 + num2; break;
            case '-': result = num1 - num2; break;
            case '*': result = num1 * num2; break;
            case '/': result = num1 / num2; break;
        }
        
        System.out.println("결과: " + result);
    }
}
</div>
            </div>
        </div>
        """
        self.text_browser.setHtml(html)
    
    def test_markdown(self):
        """마크다운 테스트"""
        html = """
        <div style="margin: 8px 0; padding: 12px; background: #2d4a2d; border-left: 4px solid #66BB6A; border-radius: 8px;">
            <div style="color: #66BB6A; font-weight: bold; margin-bottom: 8px;">🤖 AI</div>
            <div style="color: #ffffff;">
                <div style="margin: 3px 0; line-height: 1.5;">계산기의 주요 기능:</div>
                <br>
                <div style="margin: 6px 0; margin-left: 20px;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span><strong style="color: #FFD54F; font-weight: 600;">덧셈</strong>: 두 수를 더합니다</div>
                <div style="margin: 6px 0; margin-left: 20px;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span><strong style="color: #FFD54F; font-weight: 600;">뺄셈</strong>: 두 수를 뺍니다</div>
                <div style="margin: 6px 0; margin-left: 20px;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span><strong style="color: #FFD54F; font-weight: 600;">곱셈</strong>: 두 수를 곱합니다</div>
                <div style="margin: 6px 0; margin-left: 20px;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span><strong style="color: #FFD54F; font-weight: 600;">나눗셈</strong>: 두 수를 나눕니다</div>
            </div>
        </div>
        """
        self.text_browser.setHtml(html)
    
    def test_full(self):
        """전체 테스트"""
        text = """자바로 계산기 코드를 만들어드리겠습니다.

**주요 기능:**
• **덧셈**: 두 수를 더합니다
• **뺄셈**: 두 수를 뺍니다  
• **곱셈**: 두 수를 곱합니다
• **나눗셈**: 두 수를 나눕니다

```java
import java.util.Scanner;

public class Calculator {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        
        System.out.println("첫 번째 숫자:");
        double num1 = scanner.nextDouble();
        
        System.out.println("두 번째 숫자:");
        double num2 = scanner.nextDouble();
        
        System.out.println("연산자 (+, -, *, /):");
        char op = scanner.next().charAt(0);
        
        double result = 0;
        switch (op) {
            case '+': result = num1 + num2; break;
            case '-': result = num1 - num2; break;
            case '*': result = num1 * num2; break;
            case '/': result = num1 / num2; break;
        }
        
        System.out.println("결과: " + result);
    }
}
```

이 코드를 실행하면 콘솔에서 계산할 수 있습니다."""
        
        # 디버깅을 위해 단계별 출력
        print("=== 원본 텍스트 ===")
        print(repr(text))
        
        formatted_text = self.format_text(text)
        
        print("\n=== 포맷팅된 텍스트 ===")
        print(repr(formatted_text))
        
        html = f"""
        <div style="margin: 8px 0; padding: 12px; background: #2d4a2d; border-left: 4px solid #66BB6A; border-radius: 8px;">
            <div style="color: #66BB6A; font-weight: bold; margin-bottom: 8px;">🤖 AI</div>
            <div style="color: #ffffff;">
                {formatted_text}
            </div>
        </div>
        """
        self.text_browser.setHtml(html)
    
    def format_text(self, text):
        """텍스트 포맷팅"""
        import re
        
        print(f"\n1. 입력 텍스트: {repr(text[:100])}...")
        
        # 1. 코드 블록 추출
        code_blocks = []
        def extract_code_block(match):
            code_content = match.group(1)
            placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
            code_blocks.append(code_content)
            print(f"코드 블록 추출: {len(code_content)}자")
            return placeholder
        
        text = re.sub(r'```[^\n]*\n([\s\S]*?)```', extract_code_block, text)
        print(f"2. 코드 블록 추출 후: {repr(text[:100])}...")
        print(f"   추출된 코드 블록 수: {len(code_blocks)}")
        
        # 2. HTML 이스케이프
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        print(f"3. HTML 이스케이프 후: {repr(text[:100])}...")
        
        # 3. **굵은글씨**
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #FFD54F; font-weight: 600;">\1</strong>', text)
        print(f"4. 굵은글씨 처리 후: {repr(text[:100])}...")
        
        # 4. • 불릿 포인트
        text = re.sub(r'^• (.*?)$', r'<div style="margin: 6px 0; margin-left: 20px; color: #e8e8e8;"><span style="color: #81C784; font-weight: bold; margin-right: 8px;">•</span>\1</div>', text, flags=re.MULTILINE)
        print(f"5. 불릿 포인트 처리 후: {repr(text[:100])}...")
        
        # 5. 코드 블록 복원
        for i, code_content in enumerate(code_blocks):
            placeholder = f"__CODE_BLOCK_{i}__"
            # HTML 이스케이프 처리
            escaped_code = code_content.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # 공백을 &nbsp;로 변환하고 줄바꿈을 <br>로 변환
            escaped_code = escaped_code.replace(' ', '&nbsp;').replace('\n', '<br>')
            
            code_html = f'<div style="background-color: #2d2d2d; border: 1px solid #444444; border-radius: 6px; padding: 12px; margin: 8px 0; font-family: Consolas, Monaco, monospace; font-size: 12px; color: #e8e8e8;">{escaped_code}</div>'
            text = text.replace(placeholder, code_html)
            print(f"코드 블록 {i} 복원 완료")
        
        print(f"6. 코드 블록 복원 후: {repr(text[:200])}...")
        
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
        print(f"7. 최종 결과: {repr(result[:200])}...")
        return result

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = HTMLTestWidget()
    widget.show()
    sys.exit(app.exec())