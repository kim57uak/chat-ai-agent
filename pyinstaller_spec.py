#!/usr/bin/env python3
"""
PyInstaller spec generator for Chat AI Agent
Generates platform-specific .spec files for Mac and Windows
"""

import os
import sys
import platform

def generate_spec_content(platform_name):
    """Generate PyInstaller spec content for the given platform"""
    
    # Common configuration
    app_name = "ChatAIAgent"
    main_script = "main.py"
    
    # Platform-specific settings
    if platform_name == "darwin":  # macOS
        icon_file = "icon.icns" if os.path.exists("icon.icns") else None
        bundle_identifier = "com.chataiagent.app"
        app_extension = ".app"
    elif platform_name == "win32":  # Windows
        icon_file = "icon.ico" if os.path.exists("icon.ico") else None
        bundle_identifier = None
        app_extension = ".exe"
    else:  # Linux
        icon_file = "icon.png" if os.path.exists("icon.png") else None
        bundle_identifier = None
        app_extension = ""
    
    # Data files to include
    datas = []
    
    # 필수 설정 파일들 확인 후 추가
    config_files = [
        ('config.json', '.'),
        ('mcp.json', '.'), 
        ('ai_model.json', '.'),
        ('conversation_history.json', '.'),
        ('mcp_server_state.json', '.'),
    ]
    
    for src, dst in config_files:
        if os.path.exists(src):
            datas.append((src, dst))
            print(f"✅ Including: {src}")
        else:
            print(f"⚠️  Missing: {src}")
    
    # 디렉토리들 추가
    directories = [
        ('.amazonq', '.amazonq'),
        ('ui', 'ui'),
        ('core', 'core'),
        ('mcp', 'mcp'),
        ('tools', 'tools'),
    ]
    
    for src, dst in directories:
        if os.path.exists(src):
            datas.append((src, dst))
            print(f"✅ Including directory: {src}")
        else:
            print(f"⚠️  Missing directory: {src}")
    
    # Hidden imports
    hiddenimports = [
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
        'pymdown_extensions',
        'python_markdown_math',
        'PyPDF2',
        'docx',
        'pandas',
        'openpyxl',
        'pptx',
        'PIL',
        'boto3',
    ]
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{main_script}'],
    pathex=[],
    binaries=[],
    datas={datas},
    hiddenimports={hiddenimports},
    hookspath=[],
    hooksconfig={{}},
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
    name='{app_name}',
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
    icon={repr(icon_file) if icon_file else None},
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{app_name}',
)
"""
    
    # Add macOS app bundle configuration
    if platform_name == "darwin":
        spec_content += f"""
app = BUNDLE(
    coll,
    name='{app_name}.app',
    icon={repr(icon_file) if icon_file else None},
    bundle_identifier='{bundle_identifier}',
    info_plist={{
        'CFBundleName': '{app_name}',
        'CFBundleDisplayName': 'Chat AI Agent',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    }},
)
"""
    
    return spec_content

def main():
    """Generate platform-specific spec files"""
    print("🔍 Checking required files...")
    
    # 필수 파일 존재 확인
    required_files = ['config.json', 'mcp.json', 'ai_model.json']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        print("Please ensure these files exist before building.")
        return
    
    current_platform = platform.system().lower()
    
    if current_platform == "darwin":
        platform_name = "darwin"
        spec_filename = "chat-ai-agent-mac.spec"
    elif current_platform == "windows":
        platform_name = "win32"
        spec_filename = "chat-ai-agent-windows.spec"
    else:
        platform_name = "linux"
        spec_filename = "chat-ai-agent-linux.spec"
    
    spec_content = generate_spec_content(platform_name)
    
    with open(spec_filename, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ Generated {spec_filename} for {current_platform}")
    print(f"To build: pyinstaller {spec_filename}")

if __name__ == "__main__":
    main()