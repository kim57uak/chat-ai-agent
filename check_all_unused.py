#!/usr/bin/env python3
import os
import subprocess
import sys
import re

def extract_class_names(file_path):
    """파일에서 클래스명들을 추출"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # class 정의 찾기
        class_matches = re.findall(r'^class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', content, re.MULTILINE)
        return class_matches
    except:
        return []

def find_unused_files_in_folder(folder):
    """특정 폴더에서 사용하지 않는 파일들을 찾아서 리스트업"""
    
    # 폴더의 모든 Python 파일 찾기
    result = subprocess.run(['find', folder, '-name', '*.py', '-type', 'f'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        return []
    
    files = [f.strip() for f in result.stdout.split('\n') if f.strip() and '__pycache__' not in f]
    
    unused_files = []
    
    for file_path in files:
        # __init__.py 파일은 제외
        if file_path.endswith('__init__.py'):
            continue
            
        # 파일명에서 확장자 제거
        filename = os.path.basename(file_path).replace('.py', '')
        
        # 클래스명 추출
        class_names = extract_class_names(file_path)
        
        # 검색 패턴들
        search_patterns = [
            # 모듈 import 패턴
            f"from.*{filename}",
            f"import.*{filename}",
            f"from {file_path.replace('.py', '').replace('/', '.')}",
            f"import {file_path.replace('.py', '').replace('/', '.')}",
        ]
        
        # 클래스명 패턴 추가
        for class_name in class_names:
            search_patterns.append(class_name)
        
        is_used = False
        
        for pattern in search_patterns:
            # grep으로 사용 여부 검사
            grep_result = subprocess.run(['grep', '-r', pattern, '--include=*.py', '--exclude-dir=venv', '--exclude-dir=build', '--exclude-dir=dist', '--exclude-dir=.git', '.'], 
                                       capture_output=True, text=True)
            
            if grep_result.returncode == 0 and grep_result.stdout.strip():
                # 자기 자신을 참조하는 경우는 제외
                lines = grep_result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        found_file = line.split(':')[0]
                        if found_file != file_path:
                            is_used = True
                            break
                if is_used:
                    break
        
        if not is_used:
            unused_files.append(file_path)
    
    return unused_files

if __name__ == "__main__":
    folders = ['core', 'mcp', 'tools', 'ui', 'utils']
    
    all_unused = []
    
    for folder in folders:
        if os.path.exists(folder):
            print(f"=== {folder} 폴더 검사 중... ===")
            unused = find_unused_files_in_folder(folder)
            
            if unused:
                print(f"{folder} 폴더에서 사용하지 않는 파일들:")
                for file in sorted(unused):
                    print(f"  UNUSED: {file}")
                    all_unused.append(file)
                print(f"{folder}: {len(unused)}개 파일")
            else:
                print(f"{folder}: 모든 파일이 사용되고 있습니다.")
            print()
    
    if all_unused:
        print(f"=== 전체 요약 ===")
        print(f"총 {len(all_unused)}개의 사용하지 않는 파일 발견:")
        for file in sorted(all_unused):
            print(f"  {file}")
    else:
        print("모든 폴더의 파일들이 사용되고 있습니다.")