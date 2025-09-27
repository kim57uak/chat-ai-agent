@echo off
echo 🚀 ChatAI Agent Windows 빌드 시작
echo ==================================================

REM 빌드 디렉토리 정리
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo ✓ 빌드 디렉토리 정리 완료

REM PyInstaller 설치 확인
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller 설치 중...
    pip install pyinstaller
)

REM Windows용 spec 파일 생성
echo # -*- mode: python ; coding: utf-8 -*- > chat_ai_agent_windows.spec
echo. >> chat_ai_agent_windows.spec
echo import os >> chat_ai_agent_windows.spec
echo. >> chat_ai_agent_windows.spec
echo block_cipher = None >> chat_ai_agent_windows.spec
echo. >> chat_ai_agent_windows.spec
echo # 포함할 JSON 파일들 >> chat_ai_agent_windows.spec
echo json_files = [ >> chat_ai_agent_windows.spec
echo     ('ai_model.json', '.'^), >> chat_ai_agent_windows.spec
echo     ('templates.json', '.'^), >> chat_ai_agent_windows.spec
echo     ('theme.json', '.'^), >> chat_ai_agent_windows.spec
echo     ('splitter_state.json', '.'^), >> chat_ai_agent_windows.spec
echo     ('mcp_server_state.json', '.'^), >> chat_ai_agent_windows.spec
echo     ('user_config_path.json', '.'^), >> chat_ai_agent_windows.spec
echo ] >> chat_ai_agent_windows.spec
echo. >> chat_ai_agent_windows.spec
echo # 이미지 파일들 >> chat_ai_agent_windows.spec
echo image_files = [('image', 'image'^)] >> chat_ai_agent_windows.spec
echo. >> chat_ai_agent_windows.spec
echo datas = json_files + image_files >> chat_ai_agent_windows.spec
echo. >> chat_ai_agent_windows.spec
echo a = Analysis( >> chat_ai_agent_windows.spec
echo     ['main.py'], >> chat_ai_agent_windows.spec
echo     pathex=[], >> chat_ai_agent_windows.spec
echo     binaries=[], >> chat_ai_agent_windows.spec
echo     datas=datas, >> chat_ai_agent_windows.spec
echo     hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtWebEngineWidgets', 'sqlite3'], >> chat_ai_agent_windows.spec
echo     hookspath=[], >> chat_ai_agent_windows.spec
echo     hooksconfig={}, >> chat_ai_agent_windows.spec
echo     runtime_hooks=[], >> chat_ai_agent_windows.spec
echo     excludes=[], >> chat_ai_agent_windows.spec
echo     win_no_prefer_redirects=False, >> chat_ai_agent_windows.spec
echo     win_private_assemblies=False, >> chat_ai_agent_windows.spec
echo     cipher=block_cipher, >> chat_ai_agent_windows.spec
echo     noarchive=False, >> chat_ai_agent_windows.spec
echo ^) >> chat_ai_agent_windows.spec
echo. >> chat_ai_agent_windows.spec
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher^) >> chat_ai_agent_windows.spec
echo. >> chat_ai_agent_windows.spec
echo exe = EXE( >> chat_ai_agent_windows.spec
echo     pyz, >> chat_ai_agent_windows.spec
echo     a.scripts, >> chat_ai_agent_windows.spec
echo     a.binaries, >> chat_ai_agent_windows.spec
echo     a.zipfiles, >> chat_ai_agent_windows.spec
echo     a.datas, >> chat_ai_agent_windows.spec
echo     [], >> chat_ai_agent_windows.spec
echo     name='ChatAIAgent', >> chat_ai_agent_windows.spec
echo     debug=False, >> chat_ai_agent_windows.spec
echo     bootloader_ignore_signals=False, >> chat_ai_agent_windows.spec
echo     strip=False, >> chat_ai_agent_windows.spec
echo     upx=True, >> chat_ai_agent_windows.spec
echo     upx_exclude=[], >> chat_ai_agent_windows.spec
echo     runtime_tmpdir=None, >> chat_ai_agent_windows.spec
echo     console=False, >> chat_ai_agent_windows.spec
echo     disable_windowed_traceback=False, >> chat_ai_agent_windows.spec
echo     argv_emulation=False, >> chat_ai_agent_windows.spec
echo     target_arch=None, >> chat_ai_agent_windows.spec
echo     codesign_identity=None, >> chat_ai_agent_windows.spec
echo     entitlements_file=None, >> chat_ai_agent_windows.spec
echo     icon='image\\Agentic_AI_transparent.png' if os.path.exists('image\\Agentic_AI_transparent.png'^) else None, >> chat_ai_agent_windows.spec
echo ^) >> chat_ai_agent_windows.spec

REM PyInstaller 실행
echo 🔨 Windows용 빌드 시작...
pyinstaller --clean --noconfirm chat_ai_agent_windows.spec

if exist dist\ChatAIAgent.exe (
    echo ✓ Windows 실행 파일 생성 완료
    echo 📦 결과물: dist\ChatAIAgent.exe
    dir dist\ChatAIAgent.exe
) else (
    echo ❌ 빌드 실패
    exit /b 1
)

echo ==================================================
echo ✅ Windows 빌드 완료!
pause