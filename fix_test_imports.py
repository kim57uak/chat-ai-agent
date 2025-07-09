#!/usr/bin/env python3
"""test 폴더의 모든 Python 파일에 sys.path 설정 추가"""

import os
import re

def fix_imports():
    test_dir = "/Users/dolpaks/Downloads/project/chat-ai-agent/test"
    
    # sys.path 추가 코드
    path_fix = """import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
    
    for filename in os.listdir(test_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(test_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 이미 sys.path 설정이 있는지 확인
            if 'sys.path.append' in content:
                continue
                
            # from core. import가 있는지 확인
            if 'from core.' not in content:
                continue
            
            # shebang과 docstring 다음에 sys.path 추가
            lines = content.split('\n')
            insert_index = 0
            
            # shebang 건너뛰기
            if lines[0].startswith('#!'):
                insert_index = 1
            
            # docstring 건너뛰기
            if insert_index < len(lines) and lines[insert_index].strip().startswith('"""'):
                # 멀티라인 docstring 찾기
                for i in range(insert_index + 1, len(lines)):
                    if lines[i].strip().endswith('"""'):
                        insert_index = i + 1
                        break
            
            # 빈 줄 건너뛰기
            while insert_index < len(lines) and lines[insert_index].strip() == '':
                insert_index += 1
            
            # sys.path 코드 삽입
            lines.insert(insert_index, path_fix.rstrip())
            
            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            print(f"✅ {filename} 수정 완료")

if __name__ == "__main__":
    fix_imports()
    print("🎉 모든 테스트 파일 import 경로 수정 완료!")