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
lancedb_datas, lancedb_binaries, lancedb_hiddenimports = collect_all('lancedb')
sentence_transformers_datas, sentence_transformers_binaries, sentence_transformers_hiddenimports = collect_all('sentence_transformers')
torch_datas, torch_binaries, torch_hiddenimports = collect_all('torch')
torchgen_datas, torchgen_binaries, torchgen_hiddenimports = collect_all('torchgen')
transformers_datas, transformers_binaries, transformers_hiddenimports = collect_all('transformers')
huggingface_hub_datas, huggingface_hub_binaries, huggingface_hub_hiddenimports = collect_all('huggingface_hub')
filelock_datas, filelock_binaries, filelock_hiddenimports = collect_all('filelock')
tokenizers_datas, tokenizers_binaries, tokenizers_hiddenimports = collect_all('tokenizers')
safetensors_datas, safetensors_binaries, safetensors_hiddenimports = collect_all('safetensors')
pyarrow_datas, pyarrow_binaries, pyarrow_hiddenimports = collect_all('pyarrow')

# PDF processing packages
pypdf2_datas, pypdf2_binaries, pypdf2_hiddenimports = collect_all('PyPDF2')
try:
    pdfplumber_datas, pdfplumber_binaries, pdfplumber_hiddenimports = collect_all('pdfplumber')
except:
    pdfplumber_datas, pdfplumber_binaries, pdfplumber_hiddenimports = [], [], []

# torch and transformers dependencies
fsspec_datas, fsspec_binaries, fsspec_hiddenimports = collect_all('fsspec')
jinja2_datas, jinja2_binaries, jinja2_hiddenimports = collect_all('jinja2')
networkx_datas, networkx_binaries, networkx_hiddenimports = collect_all('networkx')
sympy_datas, sympy_binaries, sympy_hiddenimports = collect_all('sympy')
tqdm_datas, tqdm_binaries, tqdm_hiddenimports = collect_all('tqdm')
regex_datas, regex_binaries, regex_hiddenimports = collect_all('regex')
try:
    requests_datas, requests_binaries, requests_hiddenimports = collect_all('requests')
except:
    requests_datas, requests_binaries, requests_hiddenimports = [], [], []
try:
    packaging_datas, packaging_binaries, packaging_hiddenimports = collect_all('packaging')
except:
    packaging_datas, packaging_binaries, packaging_hiddenimports = [], [], []
try:
    pyyaml_datas, pyyaml_binaries, pyyaml_hiddenimports = collect_all('yaml')
except:
    pyyaml_datas, pyyaml_binaries, pyyaml_hiddenimports = [], [], []

# LangChain - CRITICAL for RAG functionality
langchain_datas, langchain_binaries, langchain_hiddenimports = collect_all('langchain')
langchain_core_datas, langchain_core_binaries, langchain_core_hiddenimports = collect_all('langchain_core')
langchain_community_datas, langchain_community_binaries, langchain_community_hiddenimports = collect_all('langchain_community')

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
    
    # Embedding models
    ('models/embeddings/dragonkue-KoEn-E5-Tiny', 'models/embeddings/dragonkue-KoEn-E5-Tiny'),
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
        astropy_binaries + lancedb_binaries + sentence_transformers_binaries + torch_binaries + torchgen_binaries + transformers_binaries + huggingface_hub_binaries + filelock_binaries + tokenizers_binaries + safetensors_binaries + pyarrow_binaries +
        fsspec_binaries + jinja2_binaries + networkx_binaries + sympy_binaries + tqdm_binaries + regex_binaries + requests_binaries + packaging_binaries + pyyaml_binaries +
        langchain_binaries + langchain_core_binaries + langchain_community_binaries +
        pypdf2_binaries + pdfplumber_binaries
    ),
    datas=(
        datas + 
        cryptography_datas + pycryptodome_datas + loguru_datas + keyring_datas + pygments_datas +
        pandas_datas + numpy_datas + matplotlib_datas + seaborn_datas + scipy_datas +
        astropy_datas + lancedb_datas + sentence_transformers_datas + torch_datas + torchgen_datas + transformers_datas + huggingface_hub_datas + filelock_datas + tokenizers_datas + safetensors_datas + pyarrow_datas +
        fsspec_datas + jinja2_datas + networkx_datas + sympy_datas + tqdm_datas + regex_datas + requests_datas + packaging_datas + pyyaml_datas +
        langchain_datas + langchain_core_datas + langchain_community_datas +
        pypdf2_datas + pdfplumber_datas
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
        
        # Standard library - CRITICAL
        'sqlite3',
        'json',
        'xml.etree.ElementTree',
        'urllib.parse',
        'urllib.request',
        'base64',
        'hashlib',
        'pdb',
        'bdb',
        'cmd',
        'code',
        'inspect',
        'linecache',
        'traceback',
        'pickle',
        'copy',
        'weakref',
        'collections',
        'functools',
        'itertools',
        're',
        'pathlib',
        'tempfile',
        'shutil',
        'datetime',
        'threading',
        'multiprocessing',
        'subprocess',
        'asyncio',
        'typing',
        'dataclasses',
        'enum',
        'warnings',
        'unittest',
        'unittest.mock',
        
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
        
        # PDF processing
        'PyPDF2',
        'PyPDF2.generic',
        'PyPDF2.pdf',
        'PyPDF2.utils',
        'pdfplumber',
        'pdfplumber.page',
        'pdfplumber.pdf',
        'pdfplumber.utils',
        
        # LangChain - CRITICAL for RAG
        'langchain',
        'langchain.chains',
        'langchain.chains.conversational_retrieval',
        'langchain.chains.conversational_retrieval.base',
        'langchain.chains.retrieval_qa',
        'langchain.chains.retrieval_qa.base',
        'langchain.chains.combine_documents',
        'langchain.chains.combine_documents.stuff',
        'langchain.chains.question_answering',
        'langchain.memory',
        'langchain.memory.buffer',
        'langchain.prompts',
        'langchain.prompts.prompt',
        'langchain.schema',
        'langchain.schema.messages',
        'langchain.schema.document',
        'langchain.schema.retriever',
        'langchain.retrievers',
        'langchain.vectorstores',
        'langchain.vectorstores.base',
        'langchain.embeddings',
        'langchain.embeddings.base',
        'langchain.llms',
        'langchain.llms.base',
        'langchain.chat_models',
        'langchain.chat_models.base',
        'langchain.agents',
        'langchain.agents.agent',
        'langchain.tools',
        'langchain.tools.base',
        'langchain_core',
        'langchain_core.messages',
        'langchain_core.prompts',
        'langchain_core.output_parsers',
        'langchain_core.runnables',
        'langchain_community',
        'langchain_community.vectorstores',
        'langchain_community.embeddings',
        'pydantic',
        'pydantic.fields',
        'pydantic.main',
        'pydantic.types',
        'pydantic.v1',
        'pydantic_core',
        
        # Embeddings & Vector DB - CRITICAL for RAG
        'sentence_transformers',
        'sentence_transformers.models',
        'sentence_transformers.models.Transformer',
        'sentence_transformers.models.Pooling',
        'sentence_transformers.models.Normalize',
        'sentence_transformers.models.Dense',
        'sentence_transformers.models.CNN',
        'sentence_transformers.models.LSTM',
        'sentence_transformers.models.WordEmbeddings',
        'sentence_transformers.models.WordWeights',
        'sentence_transformers.util',
        'sentence_transformers.SentenceTransformer',
        'sentence_transformers.cross_encoder',
        'sentence_transformers.cross_encoder.CrossEncoder',
        'sentence_transformers.evaluation',
        'sentence_transformers.losses',
        'sentence_transformers.datasets',
        'sentence_transformers.readers',
        'sentence_transformers.model_card_templates',
        'sentence_transformers.backend',
        'sentence_transformers.quantization',
        'transformers',
        'transformers.models',
        'transformers.models.auto',
        'transformers.models.auto.modeling_auto',
        'transformers.models.auto.tokenization_auto',
        'transformers.models.auto.configuration_auto',
        'transformers.models.auto.modeling_auto.AutoModel',
        'transformers.models.auto.modeling_auto.AutoModelForSequenceClassification',
        'transformers.models.auto.modeling_auto.AutoModelForMaskedLM',
        'transformers.models.auto.modeling_auto.AutoModelForCausalLM',
        'transformers.models.auto.tokenization_auto.AutoTokenizer',
        'transformers.models.auto.configuration_auto.AutoConfig',
        'transformers.generation',
        'transformers.generation.utils',
        'transformers.generation.configuration_utils',
        'transformers.models.bert',
        'transformers.models.bert.modeling_bert',
        'transformers.models.bert.tokenization_bert',
        'transformers.models.bert.tokenization_bert_fast',
        'transformers.tokenization_utils',
        'transformers.tokenization_utils_base',
        'transformers.tokenization_utils_fast',
        'transformers.configuration_utils',
        'transformers.modeling_utils',
        'transformers.file_utils',
        'transformers.utils',
        'transformers.utils.hub',
        'tokenizers',
        'tokenizers.implementations',
        'tokenizers.models',
        'tokenizers.normalizers',
        'tokenizers.pre_tokenizers',
        'tokenizers.processors',
        'tokenizers.decoders',
        'tokenizers.trainers',
        'huggingface_hub',
        'huggingface_hub.constants',
        'huggingface_hub.file_download',
        'huggingface_hub.hf_api',
        'huggingface_hub.utils',
        'safetensors',
        'safetensors.torch',
        'torch',
        'torch.nn',
        'torch.nn.functional',
        'torch.nn.modules',
        'torch.nn.modules.activation',
        'torch.nn.modules.container',
        'torch.nn.modules.linear',
        'torch.nn.modules.normalization',
        'torch.utils',
        'torch.utils.data',
        'torch._C',
        'torch.jit',
        'torch.jit._script',
        'torch.serialization',
        'lancedb',
        'lancedb.db',
        'lancedb.table',
        'lancedb.embeddings',
        'lancedb.query',
        'pyarrow',
        'pyarrow.parquet',
        
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
        seaborn_hiddenimports + scipy_hiddenimports + astropy_hiddenimports + lancedb_hiddenimports + sentence_transformers_hiddenimports +
        torch_hiddenimports + torchgen_hiddenimports + transformers_hiddenimports + huggingface_hub_hiddenimports + filelock_hiddenimports + tokenizers_hiddenimports + safetensors_hiddenimports + pyarrow_hiddenimports +
        fsspec_hiddenimports + jinja2_hiddenimports + networkx_hiddenimports + sympy_hiddenimports + tqdm_hiddenimports + regex_hiddenimports + requests_hiddenimports + packaging_hiddenimports + pyyaml_hiddenimports +
        langchain_hiddenimports + langchain_core_hiddenimports + langchain_community_hiddenimports +
        pypdf2_hiddenimports + pdfplumber_hiddenimports
    ),
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[
        'hooks/rthook_numpy.py',
        'hooks/rthook_pandas.py',
        'hooks/rthook_matplotlib.py',
        'hooks/rthook_scipy.py',
        'hooks/rthook_seaborn.py',
        'hooks/rthook_astropy.py',
        'hooks/rthook_filelock.py',
        'hooks/rthook_pygments.py',
        'hooks/rthook_sentence_transformers.py',
    ],
    excludes=[
        # Large ML libraries not needed
        'torchvision', 
        'torchaudio',
        'tensorflow',
        'keras',
        'plotly',
        'bokeh',
        'fastparquet',
        'PIL.ImageQt',
        'cv2',
        'skimage',
        # Development tools
        'pytest',
        'doctest',
        'tests',
        'tests.integration',
        'tests.performance',
        # Jupyter/IPython
        'IPython',
        'jupyter',
        'notebook',
        # Other heavy packages
        'statsmodels',
        # Build/monitoring scripts
        'scripts',
        'scripts.migrate_data',
        'scripts.refactor_settings_dialog',
        'scripts.verify_migration',
        'scripts.verify_refactoring',
        'find_unused_files',
        'build_mygenie',
        'cleanup_inactive_sessions',
        'monitor_token_usage',
        # Documentation
        'examples',
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
    
    # Remove duplicate binaries/datas to prevent file conflicts
    seen_binaries = set()
    unique_binaries = []
    for item in a.binaries:
        name = item[0] if isinstance(item, tuple) else str(item)
        if name not in seen_binaries:
            seen_binaries.add(name)
            unique_binaries.append(item)
    
    seen_datas = set()
    unique_datas = []
    for item in a.datas:
        name = item[0] if isinstance(item, tuple) else str(item)
        if name not in seen_datas:
            seen_datas.add(name)
            unique_datas.append(item)
    
    coll = COLLECT(
        exe,
        unique_binaries,
        a.zipfiles,
        unique_datas,
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
