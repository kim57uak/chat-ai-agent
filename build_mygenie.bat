@echo off
chcp 65001 >nul
echo 🚀 ChatAI Agent Windows 패키징 시작
echo ================================================

REM 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ 가상환경을 찾을 수 없습니다. 전역 Python을 사용합니다.
)

REM Python 버전 확인
echo Python 버전 확인 중...
python --version
if errorlevel 1 (
    echo ❌ Python을 찾을 수 없습니다.
    pause
    exit /b 1
)

REM 필요한 패키지 확인
echo 필요한 패키지 확인 중...
python -c "import PyQt6, requests, anthropic, openai" 2>nul
if errorlevel 1 (
    echo ❌ 필요한 패키지가 설치되지 않았습니다.
    echo pip install -r requirements.txt 를 실행하세요.
    pause
    exit /b 1
)

REM PyInstaller 확인
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ❌ PyInstaller가 설치되지 않았습니다.
    echo pip install pyinstaller 를 실행하세요.
    pause
    exit /b 1
)

REM 패키징 스크립트 실행 (멀티코어 병렬 처리 활성화)
echo 패키징 스크립트 실행 중...
python build_mygenie.py

if errorlevel 1 (
    echo ❌ 패키징 실패!
    echo 🔄 긴급 설정 파일 복구 시도 중...
    python restore_configs.py
    pause
    exit /b 1
)

echo.
echo ================================================
echo ✅ 패키징 완료! dist 폴더를 확인하세요.
echo.

REM 결과 파일 확인
if exist "dist\ChatAIAgent.exe" (
    echo 📁 생성된 실행 파일: dist\ChatAIAgent.exe
    for %%I in ("dist\ChatAIAgent.exe") do echo    크기: %%~zI bytes
)

if exist "dist\ChatAIAgent-Windows.zip" (
    echo 📦 생성된 배포 패키지: dist\ChatAIAgent-Windows.zip
    for %%I in ("dist\ChatAIAgent-Windows.zip") do echo    크기: %%~zI bytes
)

echo.
echo 💡 사용법:
echo    1. dist\ChatAIAgent.exe 를 원하는 위치에 복사
echo    2. 같은 폴더에 config.json 파일을 생성하고 API 키 설정
echo    3. 실행 파일을 더블클릭하여 실행
echo.
echo ⚠️ 중요: 패키징된 앱에는 샘플 설정만 포함됩니다.
echo    실제 사용을 위해서는 본인의 API 키를 설정해야 합니다.
echo.
echo 🔧 문제 발생 시: python restore_configs.py 실행
echo.
pause