@echo off
chcp 65001 >nul
echo 🚀 안전한 ChatAI Agent Windows 빌드 시작
echo ================================================

REM 가상환경 확인
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ 가상환경을 찾을 수 없습니다. 전역 Python을 사용합니다.
)

REM 필요한 패키지 확인
echo 필요한 패키지 확인 중...
python -c "import PyQt6, requests, anthropic" 2>nul
if errorlevel 1 (
    echo ❌ 필요한 패키지가 설치되지 않았습니다.
    echo pip install -r requirements.txt 를 실행하세요.
    pause
    exit /b 1
)

REM Python 스크립트 실행
echo Python 빌드 스크립트 실행 중...
python build_safe.py

if errorlevel 1 (
    echo ❌ 빌드 실패!
    pause
    exit /b 1
)

echo.
echo ================================================
echo ✅ 빌드 완료! dist 폴더를 확인하세요.
echo.
if exist "dist\ChatAIAgent.exe" (
    echo 생성된 파일: dist\ChatAIAgent.exe
)
if exist "dist\ChatAIAgent-Windows.zip" (
    echo 생성된 패키지: dist\ChatAIAgent-Windows.zip
)
echo.
pause