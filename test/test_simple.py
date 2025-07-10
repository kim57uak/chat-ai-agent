#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""간단한 테스트"""

import re

def simple_format(text):
    print(f"입력: {repr(text)}")
    
    # 가장 간단한 패턴
    def replace_code(match):
        code = match.group(1).strip()
        return f"[CODE_BLOCK]{code}[/CODE_BLOCK]"
    
    # 여러 패턴 시도
    patterns = [
        r'```[^\n]*\n([\s\S]*?)```',
        r'```([\s\S]*?)```',
        r'```.*?\n(.*?)```',
    ]
    
    for i, pattern in enumerate(patterns):
        result = re.sub(pattern, replace_code, text, flags=re.DOTALL)
        print(f"패턴 {i+1}: {pattern}")
        print(f"결과: {repr(result)}")
        if result != text:
            print("✅ 성공!")
            break
        else:
            print("❌ 실패")

if __name__ == '__main__':
    # 테스트
    test_text = """```sql 
    assignee = currentUser() AND due = today() 
    ```"""

    simple_format(test_text)