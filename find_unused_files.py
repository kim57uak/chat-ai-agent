#!/usr/bin/env python3
"""미사용 파일 찾기 스크립트"""

import os
import re
from pathlib import Path
from typing import Set

ROOT_DIR = Path('/Users/dolpaks/Downloads/project/chat-ai-agent')

EXCLUDE_DIRS = {'venv', '__pycache__', '.git', '.idea', 'node_modules', '.pytest_cache', 'dist', 'build'}
EXCLUDE_FILES = {'__init__.py', 'setup.py', 'requirements.txt', '.gitignore', 'README.md', 'LICENSE'}

def get_all_python_files() -> Set[Path]:
    """모든 Python 파일 수집 (루트 제외)"""
    files = set()
    for root, dirs, filenames in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        if Path(root) == ROOT_DIR:
            continue
            
        for filename in filenames:
            if filename.endswith('.py') and filename not in EXCLUDE_FILES:
                files.add(Path(root) / filename)
    
    return files

def find_all_references() -> Set[str]:
    """모든 파일에서 import/참조 찾기"""
    refs = set()
    
    for root, dirs, filenames in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for filename in filenames:
            if not filename.endswith('.py'):
                continue
                
            filepath = Path(root) / filename
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # from X import Y
                for match in re.finditer(r'from\s+([\w.]+)\s+import\s+([\w,\s*]+)', content):
                    module = match.group(1)
                    refs.add(module)
                    # 하위 모듈도 추가
                    parts = module.split('.')
                    for i in range(1, len(parts) + 1):
                        refs.add('.'.join(parts[:i]))
                
                # import X
                for match in re.finditer(r'(?:^|\n)import\s+([\w.]+)', content):
                    module = match.group(1)
                    refs.add(module)
                    parts = module.split('.')
                    for i in range(1, len(parts) + 1):
                        refs.add('.'.join(parts[:i]))
                        
            except:
                pass
    
    return refs

def file_to_module(filepath: Path) -> str:
    """파일 경로를 모듈명으로 변환"""
    rel = filepath.relative_to(ROOT_DIR)
    parts = list(rel.parts)
    
    # .py 제거
    if parts[-1].endswith('.py'):
        parts[-1] = parts[-1][:-3]
    
    return '.'.join(parts)

def main():
    print("🔍 미사용 파일 검색 중...\n")
    
    all_files = get_all_python_files()
    refs = find_all_references()
    
    unused = []
    for file in all_files:
        module = file_to_module(file)
        
        # 모듈명이 참조되는지 확인
        is_used = False
        for ref in refs:
            if module == ref or module.startswith(ref + '.') or ref.startswith(module + '.'):
                is_used = True
                break
        
        if not is_used:
            unused.append(file)
    
    print(f"📊 통계:")
    print(f"  - 전체 파일: {len(all_files)}개")
    print(f"  - 참조 발견: {len(refs)}개")
    print(f"  - 미사용 파일: {len(unused)}개\n")
    
    if unused:
        print("🗑️  삭제 대상 파일:\n")
        
        by_dir = {}
        for file in sorted(unused):
            dir_path = file.parent
            if dir_path not in by_dir:
                by_dir[dir_path] = []
            by_dir[dir_path].append(file.name)
        
        for dir_path in sorted(by_dir.keys()):
            rel_dir = dir_path.relative_to(ROOT_DIR)
            print(f"📁 {rel_dir}/")
            for filename in sorted(by_dir[dir_path]):
                print(f"   ❌ {filename}")
            print()
        
        response = input("삭제하시겠습니까? (yes/no): ").strip().lower()
        if response == 'yes':
            for file in unused:
                try:
                    file.unlink()
                    print(f"✅ {file.relative_to(ROOT_DIR)}")
                except Exception as e:
                    print(f"❌ {file.relative_to(ROOT_DIR)}: {e}")
            print(f"\n✨ {len(unused)}개 삭제 완료")
        else:
            print("\n❌ 취소")
    else:
        print("✅ 미사용 파일 없음")

if __name__ == '__main__':
    main()
