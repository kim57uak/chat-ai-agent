@echo off
REM Chat AI Agent 실행 스크립트 (Windows)
REM 어디서든 실행 가능한 런처

echo 🤖 Chat AI Agent 시작 중...

REM 스크립트 위치 기반으로 프로젝트 경로 설정
set "PROJECT_DIR=%~dp0"
echo 📁 프로젝트 경로: %PROJECT_DIR%

REM 프로젝트 디렉토리로 이동
cd /d "%PROJECT_DIR%" || (
    echo ❌ 프로젝트 디렉토리를 찾을 수 없습니다: %PROJECT_DIR%
    pause
    exit /b 1
)

REM 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo 🔧 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  가상환경이 없습니다. 시스템 Python 사용
)

REM Python 실행
echo 🚀 애플리케이션 실행 중...
python main.py

echo ✅ 애플리케이션 종료 완료
pause