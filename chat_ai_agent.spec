# -*- mode: python ; coding: utf-8 -*-
"""
ChatAI Agent - PyInstaller Spec File
Version: 1.0.0-beta
Target: macOS ARM64 (Apple Silicon)
Minimum macOS: 11.0 (Big Sur)

Build Instructions:
    pyinstaller --clean --noconfirm chat_ai_agent.spec
    
Features:
    - ARM64 전용 빌드 (M1/M2/M3/M4 Mac)
    - cryptography 패키지 완전 포함
    - 런치패드 실행 지원
    - 최소 macOS 11.0 요구
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Version info
VERSION = '1.0.0-beta'
APP_NAME = 'ChatAIAgent'
BUNDLE_ID = 'com.chataiagent.beta.app'

# Collect security packages completely
cryptography_datas, cryptography_binaries, cryptography_hiddenimports = collect_all('cryptography')
keyring_datas, keyring_binaries, keyring_hiddenimports = collect_all('keyring')
loguru_datas, loguru_binaries, loguru_hiddenimports = collect_all('loguru')

# Data files to include
datas = [
    # Internal config files (no personal data)
    ('ai_model.json', '.'),
    ('templates.json', '.'),
    ('theme.json', '.'),
    ('mcp_server_state.json', '.'),
    ('splitter_state.json', '.'),
    ('user_config_path.json', '.'),
    
    # Sample config files (will be replaced by user)
    ('config.json', '.'),
    ('mcp.json', '.'),
    ('news_config.json', '.'),
    ('prompt_config.json', '.'),
    
    # Images
    ('image/Agentic_AI_transparent.png', 'image'),
    ('image/Agentic_AI.png', 'image'),
    ('agentic_ai_128X128.png', '.'),
]

# Filter existing files
filtered_datas = []
for src, dst in datas:
    src_path = Path(src)
    if src_path.exists():
        filtered_datas.append((src, dst))
        print(f"✓ Including: {src}")
    else:
        print(f"⚠ Missing: {src}")

datas = filtered_datas

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=cryptography_binaries + keyring_binaries + loguru_binaries,
    datas=datas + cryptography_datas + keyring_datas + loguru_datas,
    hiddenimports=[
        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebChannel',
        'PyQt6.QtNetwork',
        'PyQt6.QtPrintSupport',
        
        # Standard library
        'sqlite3',
        'json',
        'xml.etree.ElementTree',
        'urllib.parse',
        'urllib.request',
        'base64',
        'hashlib',
        
        # Security & Encryption (hiddenimports에서 중복 제거)
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.kdf',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.ciphers.aead',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.backends.openssl.backend',
        '_cffi_backend',
        
        # Logging
        'loguru',
        
        # Third-party
        'requests',
        'dateutil',
        'markdown',
        'anthropic',
        'openai',
        'google.generativeai',
        
        # Project modules
        'core',
        'core.security',
        'core.session',
        'ui',
        'mcp',
        'tools',
        'utils',
    ] + cryptography_hiddenimports + keyring_hiddenimports + loguru_hiddenimports,
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Large ML libraries not needed
        'torch',
        'torchvision', 
        'torchaudio',
        'transformers',
        'tensorflow',
        'keras',
        'sklearn',
        'scipy',
        'numpy.f2py',
        'matplotlib',
        'seaborn',
        'plotly',
        'bokeh',
        'pandas.plotting',
        'pyarrow',
        'fastparquet',
        'openpyxl.drawing',
        'PIL.ImageQt',
        'cv2',
        'skimage',
        # Development tools
        'pytest',
        'unittest',
        'doctest',
        'pdb',
        'cProfile',
        'profile',
        # Jupyter/IPython
        'IPython',
        'jupyter',
        'notebook',
        # Other heavy packages
        'sympy',
        'networkx',
        'statsmodels',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Platform-specific executable configuration
if sys.platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='ChatAIAgent',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='image/Agentic_AI_transparent.png' if Path('image/Agentic_AI_transparent.png').exists() else None,
    )
elif sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='ChatAIAgent',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch='arm64',
        codesign_identity=None,
        entitlements_file=None,
    )
    
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name='ChatAIAgent'
    )
    
    app = BUNDLE(
        coll,
        name=f'{APP_NAME}_beta.app',
        icon='image/Agentic_AI_transparent.png' if Path('image/Agentic_AI_transparent.png').exists() else None,
        bundle_identifier=BUNDLE_ID,
        info_plist={
            'CFBundleShortVersionString': VERSION,
            'CFBundleVersion': VERSION,
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'LSMinimumSystemVersion': '11.0',
            'LSEnvironment': {
                'PYTHONIOENCODING': 'utf-8',
                'LANG': 'en_US.UTF-8',
            },
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'ChatAIAgent Document',
                    'CFBundleTypeIconFile': 'Agentic_AI_transparent.png',
                    'LSItemContentTypes': ['public.plain-text'],
                    'LSHandlerRank': 'Owner'
                }
            ]
        },
    )
else:
    # Linux
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='ChatAIAgent',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
