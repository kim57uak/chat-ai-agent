#!/usr/bin/env python3
import re

# chat_widget.py 파일 읽기
with open('ui/chat_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()

# JavaScript 실행을 안전하게 처리하는 함수 추가
if '_safe_run_js' not in content:
    # ChatWidget 클래스의 __init__ 메서드 뒤에 함수 추가
    init_pattern = r'(    def __init__\(self, parent=None\):.*?self\.layout\.setContentsMargins\(10, 10, 10, 10\))'
    replacement = r'''\1
    
    def _safe_run_js(self, js_code):
        """JavaScript를 안전하게 실행"""
        def js_callback(result):
            pass
        try:
            self.chat_display.page().runJavaScript(js_code, js_callback)
        except Exception as e:
            print(f"JavaScript 실행 오류: {e}")'''
    
    content = re.sub(init_pattern, replacement, content, flags=re.DOTALL)

# 모든 JavaScript 실행을 안전한 방식으로 변경
content = content.replace('self.chat_display.page().runJavaScript(js_code)', 'self._safe_run_js(js_code)')
content = content.replace('self.chat_display.page().runJavaScript(line_js)', 'self._safe_run_js(line_js)')

# 파일 저장
with open('ui/chat_widget.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("JavaScript 실행 안전화 완료")