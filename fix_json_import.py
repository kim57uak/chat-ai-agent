#!/usr/bin/env python3
"""
JSON 설정 파일 임포트 문제 해결 스크립트
"""

import os
import sys
import json
import shutil
from pathlib import Path

def check_json_files():
    """JSON 파일들 존재 확인"""
    json_files = [
        'config.json',
        'mcp.json', 
        'ai_model.json',
        'conversation_history.json',
        'mcp_server_state.json'
    ]
    
    for file in json_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"✅ {file} - Valid JSON")
            except json.JSONDecodeError as e:
                print(f"❌ {file} - Invalid JSON: {e}")
        else:
            print(f"⚠️  {file} - Missing")

def fix_spec_file():
    """Spec 파일에서 JSON 파일 경로 수정"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# 현재 디렉토리의 모든 JSON 파일 찾기
json_files = []
for file in os.listdir('.'):
    if file.endswith('.json'):
        json_files.append((file, '.'))
        print(f"Adding JSON file: {file}")

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=json_files + [
        ('.amazonq', '.amazonq'),
        ('ui', 'ui'),
        ('core', 'core'), 
        ('mcp', 'mcp'),
        ('tools', 'tools'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtWebEngineWidgets',
        'google.generativeai',
        'openai',
        'requests',
        'langchain',
        'langchain_openai',
        'langchain_google_genai', 
        'langchain_perplexity',
        'markdown',
        'pygments',
        'PyPDF2',
        'docx',
        'pandas',
        'openpyxl',
        'pptx',
        'PIL',
        'boto3',
        'json',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChatAIAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChatAIAgent',
)

app = BUNDLE(
    coll,
    name='ChatAIAgent.app',
    icon=None,
    bundle_identifier='com.chataiagent.app',
    info_plist={
        'CFBundleName': 'ChatAIAgent',
        'CFBundleDisplayName': 'Chat AI Agent',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
'''
    
    with open('chat-ai-agent-mac.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✅ Updated spec file with JSON file detection")

def create_resource_helper():
    """리소스 파일 접근을 위한 헬퍼 함수 생성"""
    helper_content = '''"""
Resource file helper for PyInstaller bundled apps
"""
import os
import sys
import json
from pathlib import Path

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def load_json_config(filename):
    """Load JSON config file from resources"""
    try:
        config_path = get_resource_path(filename)
        print(f"Loading config from: {config_path}")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Config file not found: {config_path}")
            return {}
    except Exception as e:
        print(f"Error loading config {filename}: {e}")
        return {}

def save_json_config(filename, data):
    """Save JSON config file"""
    try:
        # 개발 환경에서는 현재 디렉토리에 저장
        if hasattr(sys, '_MEIPASS'):
            # 번들된 앱에서는 사용자 디렉토리에 저장
            import os
            config_dir = os.path.expanduser("~/Library/Application Support/ChatAIAgent")
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, filename)
        else:
            config_path = filename
            
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Config saved to: {config_path}")
        return True
    except Exception as e:
        print(f"Error saving config {filename}: {e}")
        return False
'''
    
    with open('core/resource_helper.py', 'w', encoding='utf-8') as f:
        f.write(helper_content)
    print("✅ Created resource helper")

def rebuild_app():
    """앱 재빌드"""
    print("🔨 Rebuilding app...")
    
    # 기존 빌드 정리
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # 빌드 실행
    os.system("source venv/bin/activate && pyinstaller chat-ai-agent-mac.spec --clean --noconfirm")
    
    # 결과물 이동
    if os.path.exists('dist/ChatAIAgent.app'):
        if os.path.exists('build_output/darwin/ChatAIAgent.app'):
            shutil.rmtree('build_output/darwin/ChatAIAgent.app')
        shutil.move('dist/ChatAIAgent.app', 'build_output/darwin/')
        print("✅ App rebuilt and moved to build_output/darwin/")
    else:
        print("❌ Build failed")

def main():
    """메인 함수"""
    print("🔧 Fixing JSON import issues...")
    
    # 1. JSON 파일 확인
    print("\n1. Checking JSON files...")
    check_json_files()
    
    # 2. Spec 파일 수정
    print("\n2. Fixing spec file...")
    fix_spec_file()
    
    # 3. 리소스 헬퍼 생성
    print("\n3. Creating resource helper...")
    create_resource_helper()
    
    # 4. 앱 재빌드
    print("\n4. Rebuilding app...")
    rebuild_app()
    
    print("\n🎉 JSON import fix completed!")
    print("Test the app: open build_output/darwin/ChatAIAgent.app")

if __name__ == "__main__":
    main()