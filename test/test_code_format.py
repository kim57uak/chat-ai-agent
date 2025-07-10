#!/usr/bin/env python3
"""코드 포맷팅 테스트"""

import re

def format_text(text):
    """텍스트 포맷팅 - 코드 블록 하이라이팅 포함"""
    
    # 코드 블록 처리 (```언어 코드``` 형식)
    def format_code_block(match):
        lang = match.group(1).strip() if match.group(1) else ''
        code = match.group(2).strip()
        
        # 언어별 색상 설정
        lang_colors = {
            'jql': '#FF6B35',
            'sql': '#336791', 
            'python': '#3776AB',
            'javascript': '#F7DF1E',
            'java': '#ED8B00',
            'json': '#000000'
        }
        
        lang_color = lang_colors.get(lang.lower(), '#888888')
        
        return f'''<p style="margin: 10px 0; padding: 0;"><strong style="color: {lang_color}; font-size: 12px;">[{lang.upper() if lang else 'CODE'}]</strong></p><p style="background-color: #1e1e1e; color: #f8f8f2; padding: 12px; margin: 5px 0; border-left: 4px solid {lang_color}; font-family: monospace; font-size: 13px; white-space: pre-wrap;">{code}</p>'''
    
    # 코드 블록 먼저 처리 (더 유연한 패턴)
    text = re.sub(r'```(\w*)\s*([\s\S]*?)```', format_code_block, text)
    
    return text

if __name__ == '__main__':
    # 테스트
    test_text = '''```jql
    assignee = currentUser() AND updated >= "startOfDay()"
    ```'''

    result = format_text(test_text)
    print("입력:")
    print(test_text)
    print("\n출력:")
    print(result)

