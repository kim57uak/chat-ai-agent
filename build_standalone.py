#!/usr/bin/env python3
"""
ChatAI Agent Standalone Build Script
Windows와 macOS용 standalone 실행 파일 생성
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def clean_build():
    """빌드 디렉토리 정리"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ {dir_name} 디렉토리 정리 완료")

def check_requirements():
    """필요한 파일들 확인"""
    required_files = [
        'main.py',
        'image/Agentic_AI_transparent.png',
        'ai_model.json',
        'templates.json',
        'theme.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 필수 파일이 없습니다:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✓ 필수 파일 확인 완료")
    return True

def build_executable():
    """실행 파일 빌드"""
    system = platform.system()
    print(f"🔨 {system}용 빌드 시작...")
    
    try:
        # PyInstaller 실행
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            'chat_ai_agent.spec'
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ PyInstaller 빌드 완료")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def create_distribution():
    """배포용 패키지 생성"""
    system = platform.system()
    dist_dir = Path('dist')
    
    if system == 'Darwin':  # macOS
        app_path = dist_dir / 'ChatAIAgent.app'
        if app_path.exists():
            print(f"✓ macOS 앱 번들 생성: {app_path}")
            
            # DMG 생성 (선택사항)
            try:
                subprocess.run([
                    'hdiutil', 'create', '-volname', 'ChatAIAgent',
                    '-srcfolder', str(app_path),
                    '-ov', '-format', 'UDZO',
                    str(dist_dir / 'ChatAIAgent-macOS.dmg')
                ], check=True)
                print("✓ DMG 파일 생성 완료")
            except:
                print("⚠️ DMG 생성 실패 (선택사항)")
                
    elif system == 'Windows':  # Windows
        exe_path = dist_dir / 'ChatAIAgent.exe'
        if exe_path.exists():
            print(f"✓ Windows 실행 파일 생성: {exe_path}")
    
    else:  # Linux
        exe_path = dist_dir / 'ChatAIAgent'
        if exe_path.exists():
            print(f"✓ Linux 실행 파일 생성: {exe_path}")

def main():
    """메인 빌드 프로세스"""
    print("🚀 ChatAI Agent Standalone 빌드 시작")
    print("=" * 50)
    
    # 1. 빌드 디렉토리 정리
    clean_build()
    
    # 2. 필수 파일 확인
    if not check_requirements():
        sys.exit(1)
    
    # 3. 실행 파일 빌드
    if not build_executable():
        sys.exit(1)
    
    # 4. 배포 패키지 생성
    create_distribution()
    
    print("=" * 50)
    print("✅ 빌드 완료!")
    print(f"📦 결과물: dist/ 디렉토리 확인")
    
    # 빌드 결과 표시
    dist_dir = Path('dist')
    if dist_dir.exists():
        print("\n📁 생성된 파일들:")
        for item in dist_dir.iterdir():
            size = ""
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                size = f" ({size_mb:.1f}MB)"
            print(f"   - {item.name}{size}")

if __name__ == '__main__':
    main()