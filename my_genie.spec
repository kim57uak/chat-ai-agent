# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect packages completely
cryptography_datas, cryptography_binaries, cryptography_hiddenimports = collect_all('cryptography')
pycryptodome_datas, pycryptodome_binaries, pycryptodome_hiddenimports = collect_all('Crypto')
loguru_datas, loguru_binaries, loguru_hiddenimports = collect_all('loguru')
keyring_datas, keyring_binaries, keyring_hiddenimports = collect_all('keyring')
pygments_datas, pygments_binaries, pygments_hiddenimports = collect_all('pygments')
astropy_datas, astropy_binaries, astropy_hiddenimports = collect_all('astropy')

# Data science packages - explicit collect_all to ensure all submodules included
pandas_datas, pandas_binaries, pandas_hiddenimports = collect_all('pandas')
numpy_datas, numpy_binaries, numpy_hiddenimports = collect_all('numpy')
matplotlib_datas, matplotlib_binaries, matplotlib_hiddenimports = collect_all('matplotlib')
seaborn_datas, seaborn_binaries, seaborn_hiddenimports = collect_all('seaborn')
scipy_datas, scipy_binaries, scipy_hiddenimports = collect_all('scipy')

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
    
    # Web templates and static files
    ('ui/components/web/templates', 'ui/components/web/templates'),
    ('ui/components/web/static', 'ui/components/web/static'),
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
    binaries=(
        cryptography_binaries + pycryptodome_binaries + loguru_binaries + keyring_binaries + pygments_binaries +
        pandas_binaries + numpy_binaries + matplotlib_binaries + seaborn_binaries + scipy_binaries +
        astropy_binaries
    ),
    datas=(
        datas + 
        cryptography_datas + pycryptodome_datas + loguru_datas + keyring_datas + pygments_datas +
        pandas_datas + numpy_datas + matplotlib_datas + seaborn_datas + scipy_datas +
        astropy_datas
    ),
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
        
        # Security & Encryption
        'keyring',
        'keyring.backends',
        'Crypto',
        'Crypto.Cipher',
        'Crypto.Cipher.AES',
        'Crypto.Protocol',
        'Crypto.Protocol.KDF',
        'Crypto.Hash',
        'Crypto.Hash.SHA1',
        'Crypto.Util',
        'Crypto.Util.Padding',
        
        # Logging
        'loguru',
        
        # Third-party
        'requests',
        'dateutil',
        'markdown',
        'anthropic',
        'openai',
        'google.generativeai',
        
        # Pygments - code highlighting
        'pygments.lexers',
        'pygments.styles',
        'pygments.formatters',
        'pygments.formatters.html',
        
        # Data science - explicit imports from hook files to ensure modules are found
        # pandas (from hook-pandas.py)
        'pandas.plotting',
        'pandas.plotting._core',
        'pandas.plotting._matplotlib',
        'pandas.plotting._misc',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.skiplist',
        # numpy (from hook-numpy.py)
        'numpy.core',
        'numpy.core._multiarray_umath',
        'numpy.core._multiarray_tests',
        'numpy.core._rational_tests',
        'numpy.core._struct_ufunc_tests',
        'numpy.random',
        'numpy.linalg',
        'numpy.fft',
        # matplotlib (from hook-matplotlib.py)
        'matplotlib.pyplot',
        'matplotlib.backends',
        'matplotlib.backends.backend_agg',
        'matplotlib.backends.backend_pdf',
        'matplotlib.figure',
        # scipy (from hook-scipy.py)
        'scipy.stats',
        'scipy.special',
        'scipy.linalg',
        'scipy.integrate',
        'scipy.optimize',
        'scipy.interpolate',
        'scipy.sparse'
        
        # Project modules
        'core',
        'core.security',
        'core.session',
        'core.logging',
        'ui',
        'mcp',
        'tools',
        'utils',
    ] + (
        cryptography_hiddenimports + pycryptodome_hiddenimports + loguru_hiddenimports + keyring_hiddenimports + pygments_hiddenimports +
        pandas_hiddenimports + numpy_hiddenimports + matplotlib_hiddenimports + 
        seaborn_hiddenimports + scipy_hiddenimports + astropy_hiddenimports
    ),
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[
        'hooks/rthook_pygments.py',
        'hooks/rthook_pandas.py',
        'hooks/rthook_numpy.py',
        'hooks/rthook_matplotlib.py',
        'hooks/rthook_scipy.py',
        'hooks/rthook_seaborn.py',
        'hooks/rthook_astropy.py',
    ],
    excludes=[
        # Large ML libraries not needed
        'torch',
        'torchvision', 
        'torchaudio',
        'transformers',
        'tensorflow',
        'keras',
        'plotly',
        'bokeh',
        'pyarrow',
        'fastparquet',
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
        name='MyGenie_beta',
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
        name='MyGenie',
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
        name='MyGenie'
    )
    
    app = BUNDLE(
        coll,
        name='MyGenie.app',
        icon='image/Agentic_AI_transparent.png' if Path('image/Agentic_AI_transparent.png').exists() else None,
        bundle_identifier='com.mygenie.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'LSMinimumSystemVersion': '11.0',
            'LSEnvironment': {
                'PYTHONIOENCODING': 'utf-8',
                'LANG': 'en_US.UTF-8',
            },
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'MyGenie Document',
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
        name='MyGenie',
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
