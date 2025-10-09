#!/usr/bin/env python3
"""
Cross-platform packaging script for ChatAI Agent
Supports macOS and Windows with proper config file handling
"""

import os
import sys
import shutil
import subprocess
import platform
import json
import multiprocessing
import time
from pathlib import Path
from typing import Dict, Any
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

# External config files (contain personal API keys)
EXTERNAL_CONFIG_FILES = [
    "config.json",
    "mcp.json",
    "news_config.json",
    "prompt_config.json",
]

# Internal config files (no personal data)
INTERNAL_CONFIG_FILES = [
    "ai_model.json",
    "templates.json",
    "theme.json",
    "mcp_server_state.json",
    "splitter_state.json",
    "user_config_path.json",
]


class PackageBuilder:
    def __init__(self):
        self.system = platform.system()
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backup_configs"

    def backup_configs(self):
        """Backup existing config files"""
        self.backup_dir.mkdir(exist_ok=True)

        for file in EXTERNAL_CONFIG_FILES:
            if (self.project_root / file).exists():
                shutil.copy(self.project_root / file, self.backup_dir / file)
                print(f"✓ Backed up {file}")

    def restore_configs(self):
        """Restore backed up config files"""
        if not self.backup_dir.exists():
            print("⚠️ 백업 디렉토리가 없습니다.")
            return

        restored_count = 0
        for file in EXTERNAL_CONFIG_FILES:
            backup_file = self.backup_dir / file
            target_file = self.project_root / file

            if backup_file.exists():
                try:
                    shutil.copy(backup_file, target_file)
                    print(f"✓ Restored {file}")
                    restored_count += 1
                except Exception as e:
                    print(f"❌ Failed to restore {file}: {e}")
            else:
                print(f"⚠️ No backup found for {file}")

        # 백업 디렉토리 정리
        try:
            shutil.rmtree(self.backup_dir)
            print(f"✓ Cleanup backup directory ({restored_count} files restored)")
        except Exception as e:
            print(f"⚠️ Failed to cleanup backup directory: {e}")

    def create_sample_configs(self):
        """Create sample config files for packaging"""

        # Sample config.json (no personal keys)
        config_sample = {
            "current_model": "gemini-2.0-flash",
            "models": {
                "gemini-2.0-flash": {
                    "api_key": "YOUR_GOOGLE_API_KEY",
                    "provider": "google",
                },
                "gpt-3.5-turbo": {
                    "api_key": "YOUR_OPENAI_API_KEY",
                    "provider": "openai",
                },
                "sonar-pro": {
                    "api_key": "YOUR_PERPLEXITY_API_KEY",
                    "provider": "perplexity",
                },
                "pollinations-mistral": {
                    "provider": "pollinations",
                    "api_key": "free",
                    "description": "Free coding model",
                    "model_id": "mistral",
                },
            },
            "conversation_settings": {
                "enable_history": True,
                "max_history_pairs": 5,
                "max_tokens_estimate": 20000,
            },
            "response_settings": {
                "max_tokens": 4096,
                "enable_streaming": True,
                "streaming_chunk_size": 100,
            },
            "current_theme": "material_dark",
        }

        # Sample mcp.json (no personal keys/tokens)
        mcp_sample = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                        "/path/to/your/directory",
                    ],
                    "description": "File system access - Change path to your directory",
                },
                "search-server": {
                    "command": "node",
                    "args": ["/path/to/search-server.js"],
                    "env": {"PERPLEXITY_API_KEY": "YOUR_PERPLEXITY_API_KEY"},
                    "description": "Search server - Add your Perplexity API key",
                },
                "mysql": {
                    "command": "npx",
                    "args": ["mysql-mcp-server"],
                    "env": {
                        "MYSQL_HOST": "localhost",
                        "MYSQL_PORT": "3306",
                        "MYSQL_USER": "YOUR_MYSQL_USER",
                        "MYSQL_PASSWORD": "YOUR_MYSQL_PASSWORD",
                        "MYSQL_DATABASE": "YOUR_DATABASE_NAME",
                    },
                    "description": "MySQL database access - Configure your database credentials",
                },
                "gmail": {
                    "command": "npx",
                    "args": ["@gongrzhe/server-gmail-autoauth-mcp"],
                    "description": "Gmail access - Requires OAuth setup",
                },
                "notion": {
                    "command": "npx",
                    "args": ["-y", "@notionhq/notion-mcp-server"],
                    "env": {
                        "OPENAPI_MCP_HEADERS": '{"Authorization": "Bearer YOUR_NOTION_TOKEN", "Notion-Version": "2025-06-29"}'
                    },
                    "description": "Notion API access - Add your Notion integration token",
                },
            }
        }

        # Sample news_config.json
        news_sample = {
            "news_sources": {"domestic": [], "international": [], "earthquake": []},
            "update_interval": 300,
            "max_articles": 10,
        }

        # Sample prompt_config.json
        prompt_sample = {
            "conversation_settings": {
                "enable_history": True,
                "hybrid_mode": True,
                "user_message_limit": 4,
                "ai_response_limit": 4,
                "ai_response_token_limit": 5000,
                "max_history_pairs": 4,
                "max_tokens_estimate": 10000,
            },
            "response_settings": {
                "enable_length_limit": False,
                "max_tokens": 4096,
                "max_response_length": 50000,
                "enable_streaming": True,
                "streaming_chunk_size": 300,
            },
            "language_detection": {
                "korean_threshold": 0.1,
                "description": "Korean character ratio threshold for language detection (0.0-1.0)",
            },
            "theme": {"current_theme": "material_high_contrast"},
            "history_settings": {"initial_load_count": 20, "page_size": 10},
        }

        # Write sample files
        samples = {
            "config.json": config_sample,
            "mcp.json": mcp_sample,
            "news_config.json": news_sample,
            "prompt_config.json": prompt_sample,
        }

        # Reset user config path for packaging
        user_config_reset = {}
        with open(
            self.project_root / "user_config_path.json", "w", encoding="utf-8"
        ) as f:
            json.dump(user_config_reset, f, indent=2, ensure_ascii=False)

        for filename, content in samples.items():
            with open(self.project_root / filename, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            print(f"✓ Created sample {filename} (개인키 제거됨)")

        print("✓ Reset user_config_path.json (외부 경로 초기화)")

    def clean_build(self):
        """완전한 빌드 환경 정리"""
        print("🧹 완전한 빌드 환경 정리 중...")

        # 1. 기존 빌드 디렉토리 삭제
        dirs_to_clean = ["build", "dist"]
        for dir_name in dirs_to_clean:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                try:
                    # 권한 문제 해결을 위해 chmod 후 삭제
                    subprocess.run(["chmod", "-R", "755", str(dir_path)], check=False)
                    shutil.rmtree(dir_path)
                    print(f"✓ Cleaned {dir_name}")
                except Exception as e:
                    print(f"⚠ {dir_name} 삭제 중 오류: {e}")

        # 2. __pycache__ 재귀적 삭제
        try:
            subprocess.run(
                [
                    "find",
                    str(self.project_root),
                    "-name",
                    "__pycache__",
                    "-type",
                    "d",
                    "-exec",
                    "rm",
                    "-rf",
                    "{}",
                    "+",
                ],
                check=False,
                capture_output=True,
            )
            print("✓ Cleaned __pycache__ directories")
        except Exception as e:
            print(f"⚠ __pycache__ 정리 중 오류: {e}")

        # 3. pip 캐시 정리
        try:
            result = subprocess.run(
                ["pip", "cache", "purge"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0 and result.stdout:
                print(f"✓ Pip cache purged: {result.stdout.strip()}")
            else:
                print("✓ Pip cache already clean")
        except Exception as e:
            print(f"⚠ Pip 캐시 정리 중 오류: {e}")

        # 4. PyInstaller 캐시 정리 (있다면)
        pyinstaller_cache = Path.home() / ".pyinstaller_cache"
        if pyinstaller_cache.exists():
            try:
                shutil.rmtree(pyinstaller_cache)
                print("✓ Cleaned PyInstaller cache")
            except Exception as e:
                print(f"⚠ PyInstaller 캐시 정리 중 오류: {e}")

        print("✅ 완전한 빌드 환경 정리 완료")

    def update_spec_file(self):
        """Update PyInstaller spec file for cross-platform compatibility"""
        spec_content = """# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect packages completely
cryptography_datas, cryptography_binaries, cryptography_hiddenimports = collect_all('cryptography')
loguru_datas, loguru_binaries, loguru_hiddenimports = collect_all('loguru')
keyring_datas, keyring_binaries, keyring_hiddenimports = collect_all('keyring')

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
    binaries=cryptography_binaries + loguru_binaries + keyring_binaries,
    datas=datas + cryptography_datas + loguru_datas + keyring_datas,
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
        'core.logging',
        'ui',
        'mcp',
        'tools',
        'utils',
    ] + cryptography_hiddenimports + loguru_hiddenimports + keyring_hiddenimports,
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

# Ensure cryptography is in pure Python modules
for item in cryptography_hiddenimports:
    if item not in [mod[0] for mod in a.pure]:
        a.pure.append((item, '', 'PYMODULE'))

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
        name='ChatAIAgent_beta.app',
        icon='image/Agentic_AI_transparent.png' if Path('image/Agentic_AI_transparent.png').exists() else None,
        bundle_identifier='com.chataiagent.beta.app',
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
"""

        with open(self.project_root / "chat_ai_agent.spec", "w", encoding="utf-8") as f:
            f.write(spec_content)
        print("✓ Updated PyInstaller spec file")

    def verify_and_fix_dependencies(self):
        """빌드 전 필수 의존성 확인 및 자동 수정"""
        print("🔍 필수 의존성 확인 및 자동 수정 중...")
        
        required_packages = [
            ('cryptography', '42.0.8'),
            ('keyring', None),
            ('PyQt6', None),
            ('langchain', None),
            ('openai', None),
        ]
        
        needs_reinstall = []
        for package_info in required_packages:
            package = package_info[0]
            version = package_info[1]
            
            try:
                __import__(package)
                print(f"✓ {package}")
            except ImportError:
                needs_reinstall.append(package_info)
                print(f"❌ {package} 누락")
        
        if needs_reinstall:
            print(f"\n🔧 누락된 패키지 자동 설치 중...")
            for package, version in needs_reinstall:
                try:
                    if version:
                        cmd = ['pip', 'install', '--force-reinstall', '--no-cache-dir', f'{package}=={version}']
                    else:
                        cmd = ['pip', 'install', package]
                    
                    print(f"  설치 중: {package}...")
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    print(f"  ✓ {package} 설치 완료")
                except subprocess.CalledProcessError as e:
                    print(f"  ❌ {package} 설치 실패: {e}")
                    return False
        
        # cryptography는 항상 강제 재설치 (빌드 문제 방지)
        print("\n🔐 cryptography 모듈 강제 재설치 (빌드 안정성 확보)...")
        try:
            cmd = ['pip', 'install', '--force-reinstall', '--no-cache-dir', 'cryptography==42.0.8']
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✓ cryptography 재설치 완료")
        except subprocess.CalledProcessError as e:
            print(f"❌ cryptography 재설치 실패: {e}")
            return False
        
        print("✅ 모든 필수 의존성 확인 및 수정 완료")
        return True

    def build_executable(self, parallel_jobs=None):
        """Build executable using PyInstaller with parallel processing"""
        # 빌드 전 의존성 확인 및 자동 수정
        if not self.verify_and_fix_dependencies():
            print("❌ 의존성 확인 및 수정 실패. 빌드를 중단합니다.")
            return False
        
        if parallel_jobs is None:
            cpu_cores = multiprocessing.cpu_count()
            parallel_jobs = min(cpu_cores, 8)
            print(f"💻 CPU 코어: {cpu_cores}개, 병렬 작업: {parallel_jobs}개")

        # 환경변수로 병렬 처리 설정
        import os

        os.environ["PYINSTALLER_COMPILE_BOOTLOADER_PARALLEL"] = str(parallel_jobs)
        
        try:
            cmd = [
                "pyinstaller",
                "--noconfirm",
                "--clean",
                f"--distpath=dist",
                f"--workpath=build",
                "chat_ai_agent.spec",
            ]
            print(f"🚀 병렬 빌드 시작: {' '.join(cmd)}")

            start_time = time.time()
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            end_time = time.time()

            if result.stdout:
                print("Build output:")
                print(result.stdout)

            print(
                f"✅ PyInstaller build completed in {end_time - start_time:.2f} seconds"
            )
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            if e.stdout:
                print(f"stdout: {e.stdout}")
            if e.stderr:
                print(f"stderr: {e.stderr}")
            return False
        except FileNotFoundError:
            print("❌ PyInstaller not found. Install with: pip install pyinstaller")
            return False

    def create_distribution_package(self):
        """Create distribution packages"""
        dist_dir = self.project_root / "dist"

        if self.system == "Darwin":  # macOS
            app_path = dist_dir / "ChatAIAgent_beta.app"
            if app_path.exists():
                print(f"✓ macOS app created: {app_path}")

                # Create DMG
                try:
                    dmg_path = dist_dir / "ChatAIAgent-macOS_beta.dmg"
                    if dmg_path.exists():
                        dmg_path.unlink()

                    subprocess.run(
                        [
                            "hdiutil",
                            "create",
                            "-volname",
                            "ChatAIAgent",
                            "-srcfolder",
                            str(app_path),
                            "-ov",
                            "-format",
                            "UDZO",
                            str(dmg_path),
                        ],
                        check=True,
                    )
                    print(f"✓ DMG created: {dmg_path}")
                except Exception as e:
                    print(f"⚠ DMG creation failed: {e}")

        elif self.system == "Windows":
            exe_path = dist_dir / "ChatAIAgent.exe"
            if exe_path.exists():
                print(f"✓ Windows executable created: {exe_path}")

                # Create ZIP
                try:
                    import zipfile

                    zip_path = dist_dir / "ChatAIAgent-Windows.zip"
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        zipf.write(exe_path, exe_path.name)
                    print(f"✓ ZIP package created: {zip_path}")
                except Exception as e:
                    print(f"⚠ ZIP creation failed: {e}")

        else:  # Linux
            exe_path = dist_dir / "ChatAIAgent"
            if exe_path.exists():
                print(f"✓ Linux executable created: {exe_path}")

                # Create TAR.GZ
                try:
                    import tarfile

                    tar_path = dist_dir / "ChatAIAgent-Linux.tar.gz"
                    with tarfile.open(tar_path, "w:gz") as tar:
                        tar.add(exe_path, exe_path.name)
                    print(f"✓ TAR.GZ package created: {tar_path}")
                except Exception as e:
                    print(f"⚠ TAR.GZ creation failed: {e}")

    def verify_build(self):
        """Verify build contents"""
        dist_dir = self.project_root / "dist"

        if self.system == "Darwin":
            app_path = dist_dir / "ChatAIAgent_beta.app"
            resources_path = app_path / "Contents" / "Resources"

            if resources_path.exists():
                print("\n📋 Verifying app bundle contents:")
                required_files = [
                    "theme.json",
                    "templates.json",
                    "ai_model.json",
                    "config.json",
                ]

                for required_file in required_files:
                    file_path = resources_path / required_file
                    if file_path.exists():
                        print(f"✓ {required_file}")
                    else:
                        print(f"❌ {required_file} missing")
                        return False

                print("✅ All required files included")
            
            # cryptography 모듈 확인
            print("\n🔐 Verifying cryptography module:")
            internal_path = dist_dir / "ChatAIAgent" / "_internal"
            if internal_path.exists():
                crypto_found = False
                crypto_dirs = []
                
                # cryptography 디렉토리 찾기
                for item in internal_path.iterdir():
                    if item.is_dir() and 'cryptography' in item.name.lower():
                        crypto_dirs.append(item.name)
                        crypto_found = True
                
                # cryptography 관련 파일 찾기
                for item in internal_path.rglob('*cryptography*'):
                    if item.is_file() and item.suffix in ['.so', '.dylib', '.pyd']:
                        print(f"✓ Found: {item.relative_to(internal_path)}")
                        crypto_found = True
                
                if crypto_dirs:
                    print(f"✓ cryptography 디렉토리: {', '.join(crypto_dirs)}")
                
                if not crypto_found:
                    print("❌ cryptography 모듈이 빌드에 포함되지 않았습니다!")
                    print("\n자동 수정을 시도합니다...")
                    print("다음 명령을 실행하세요:")
                    print("  python build_package.py")
                    return False
                else:
                    print("✅ cryptography 모듈 포함 확인")
            
            return True

        return True

    def test_executable(self):
        """빌드된 실행 파일 테스트"""
        dist_dir = self.project_root / "dist"
        
        if self.system == "Darwin":
            exe_path = dist_dir / "ChatAIAgent" / "ChatAIAgent"
        elif self.system == "Windows":
            exe_path = dist_dir / "ChatAIAgent.exe"
        else:
            exe_path = dist_dir / "ChatAIAgent"
        
        if not exe_path.exists():
            print(f"❌ 실행 파일을 찾을 수 없습니다: {exe_path}")
            return False
        
        print(f"실행 파일 테스트: {exe_path}")
        try:
            # 5초 타임아웃으로 실행 테스트
            result = subprocess.run(
                [str(exe_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
        except subprocess.TimeoutExpired:
            # GUI 앱이므로 타임아웃은 정상 (실행은 성공)
            print("✓ 실행 파일이 정상적으로 시작됨 (GUI 앱)")
            return True
        except Exception as e:
            print(f"❌ 실행 테스트 실패: {e}")
            if result.stderr:
                print(f"에러 출력:\n{result.stderr[:500]}")
            return False
        
        # 즉시 종료된 경우 에러 확인
        if result.returncode != 0:
            print(f"❌ 실행 파일 에러 (exit code: {result.returncode})")
            if result.stderr:
                print(f"에러 출력:\n{result.stderr[:500]}")
            return False
        
        return True

    def show_results(self):
        """Show build results"""
        dist_dir = self.project_root / "dist"
        if dist_dir.exists():
            print("\n📁 Generated files:")
            for item in dist_dir.iterdir():
                if item.is_file():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    print(f"   - {item.name} ({size_mb:.1f}MB)")
                else:
                    print(f"   - {item.name}/ (directory)")

    def build_parallel_tasks(self, parallel_jobs=None):
        """병렬로 실행할 수 있는 작업들을 동시에 처리"""
        if parallel_jobs is None:
            parallel_jobs = min(multiprocessing.cpu_count(), 3)

        print(f"🔄 병렬 작업 시작 ({parallel_jobs} workers)...")

        with ThreadPoolExecutor(max_workers=parallel_jobs) as executor:
            # 병렬로 실행할 작업들
            futures = {
                executor.submit(self.clean_build): "clean_build",
                executor.submit(self.create_sample_configs): "create_configs",
                executor.submit(self.update_spec_file): "update_spec",
            }

            # 작업 완료 대기
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    future.result()
                    print(f"✅ {task_name} completed")
                except Exception as e:
                    print(f"❌ {task_name} failed: {e}")
                    raise

    def build(self, parallel_jobs=None):
        """Main build process with parallel optimization"""
        print(f"🚀 Building ChatAI Agent for {self.system}")
        print("=" * 50)

        try:
            # 0. 의존성 자동 확인 및 수정
            print("\n🔧 Step 0: 의존성 자동 확인 및 수정...")
            if not self.verify_and_fix_dependencies():
                raise Exception("의존성 확인 실패")

            # 1. Backup configs (순차 실행 필요)
            print("\n📦 Step 1: Backing up config files...")
            self.backup_configs()

            # 2-3. 병렬 실행 가능한 작업들 (spec 파일 업데이트 제외)
            print("\n🔄 Step 2: 병렬 작업 시작...")
            if parallel_jobs is None:
                parallel_jobs = min(multiprocessing.cpu_count(), 3)
            
            with ThreadPoolExecutor(max_workers=parallel_jobs) as executor:
                futures = {
                    executor.submit(self.clean_build): "clean_build",
                    executor.submit(self.create_sample_configs): "create_configs",
                }
                for future in as_completed(futures):
                    task_name = futures[future]
                    try:
                        future.result()
                        print(f"✅ {task_name} completed")
                    except Exception as e:
                        print(f"❌ {task_name} failed: {e}")
                        raise

            # 4. PyInstaller 캐시 정리
            print("\n🗑️  Step 3: PyInstaller 캐시 정리...")
            cache_dir = Path.home() / ".pyinstaller_cache"
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir, ignore_errors=True)
                print("✓ 캐시 정리 완료")

            # 5. Build executable (병렬 처리 적용)
            print("\n🔨 Step 4: Building executable with parallel processing...")
            if not self.build_executable(parallel_jobs):
                raise Exception("Build failed")

            # 6. Verify build
            print("\n🔍 Step 5: Verifying build...")
            if not self.verify_build():
                raise Exception("Build verification failed")

            # 7. Create distribution packages
            print("\n📦 Step 6: Creating distribution packages...")
            self.create_distribution_package()

            print("\n" + "=" * 50)
            print("✅ Build completed successfully!")
            print("=" * 50)

            # 8. Show results
            self.show_results()
            
            # 9. 실행 테스트
            print("\n🧪 Step 7: 실행 테스트...")
            self.test_executable()

        except Exception as e:
            print(f"\n❌ Build failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Always restore configs - 매우 중요!
            print("\n🔄 원본 설정 파일 복구 중... (테스트 계속을 위해 필수)")
            self.restore_configs()

        return True


def main():
    """Entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ChatAI Agent 빌드 도구")
    parser.add_argument(
        "--parallel",
        "-p",
        type=int,
        default=None,
        help="병렬 작업 수 (기본값: CPU 코어 수 기반 자동 최적화)",
    )

    args = parser.parse_args()

    builder = PackageBuilder()
    builder.build(parallel_jobs=args.parallel)


if __name__ == "__main__":
    main()
