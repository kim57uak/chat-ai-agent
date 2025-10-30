@echo off
chcp 65001 >nul

REM bat 파일이 있는 디렉토리로 이동
cd /d "%~dp0"

echo 🚀 ChatAI Agent Windows 패키징 시작
echo ================================================
echo 작업 디렉토리: %CD%
echo.

REM 필수 파일 확인
if not exist "build_mygenie.py" (
    echo ❌ build_mygenie.py 파일을 찾을 수 없습니다.
    echo 프로젝트 폴더에서 실행하세요: chat-ai-agent\
    echo.
    echo 사용법:
    echo   1. 프로젝트 폴더로 이동
    echo   2. 해당 폴더에서 CMD 열기
    echo   3. build_mygenie.bat 실행
    pause
    exit /b 1
)

REM Windows 긴 경로명 지원 활성화
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f >nul 2>&1

REM 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ 가상환경을 찾을 수 없습니다.
    echo.
    echo 가상환경 생성 방법:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
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
python -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo ❌ 필수 패키지가 설치되지 않았습니다.
    echo Windows 호환 버전으로 자동 설치를 시작합니다...
    echo.
    
    pip install --upgrade pip
    
    REM Core packages
    pip install PyQt6==6.7.1 PyQt6-Qt6==6.7.3 PyQt6-WebEngine==6.7.0 PyQt6-WebEngine-Qt6==6.7.3 PyQt6_sip==13.8.0
    pip install pyinstaller==6.15.0 pyinstaller-hooks-contrib==2025.8
    
    REM AI/LLM packages
    pip install openai anthropic google-generativeai==0.8.5
    pip install langchain langchain-core langchain-openai langchain-anthropic langchain-google-genai langchain-perplexity langchain-text-splitters
    pip install langsmith tiktoken==0.9.0
    
    REM HTTP/Network
    pip install requests requests-toolbelt==1.0.0 httpx aiohttp
    
    REM Security
    pip install cryptography==42.0.8 keyring pycryptodome
    
    REM Data processing
    pip install pandas numpy openpyxl xlsxwriter==3.2.5
    pip install matplotlib seaborn scikit-learn astropy
    pip install python-docx==1.2.0 python-pptx==1.0.2 PyPDF2==3.0.1 lxml==6.0.0
    
    REM Markdown and formatting
    pip install Markdown==3.8.2 Pygments==2.19.2 pymdown-extensions==10.16.1 python-markdown-math==0.9
    
    REM Utilities
    pip install python-dotenv==1.1.1 PyYAML==6.0.2 tqdm==4.67.1 tenacity==9.1.2 filetype==1.2.0 regex==2024.11.6
    pip install boto3 replicate==1.0.7 SQLAlchemy==2.0.41
    pip install loguru black
    
    if errorlevel 1 (
        echo ❌ 패키지 설치 실패.
        echo 가상환경을 사용하세요: python -m venv venv
        pause
        exit /b 1
    )
    
    echo ✅ 모든 패키지 설치 완료!
)

REM 패키징 스크립트 실행 (멀티코어 병렬 처리 활성화)
echo 패키징 스크립트 실행 중...
python "%~dp0build_mygenie.py"

if errorlevel 1 (
    echo ❌ 패키징 실패!
    if exist "%~dp0restore_configs.py" (
        echo 🔄 긴급 설정 파일 복구 시도 중...
        python "%~dp0restore_configs.py"
    )
    pause
    exit /b 1
)

echo.
echo ================================================
echo ✅ 패키징 완료! dist_windows 폴더를 확인하세요.
echo.

REM 결과 파일 확인
if exist "dist_windows\MyGenie_beta.exe" (
    echo 📁 생성된 실행 파일: dist_windows\MyGenie_beta.exe
    for %%I in ("dist_windows\MyGenie_beta.exe") do echo    크기: %%~zI bytes
)

if exist "dist_windows\MyGenie_beta-Windows.zip" (
    echo 📦 생성된 배포 패키지: dist_windows\MyGenie_beta-Windows.zip
    for %%I in ("dist_windows\MyGenie_beta-Windows.zip") do echo    크기: %%~zI bytes
)

echo.
echo 💡 사용법:
echo    1. dist_windows\MyGenie_beta.exe 를 원하는 위치에 복사
echo    2. 같은 폴더에 config.json 파일을 생성하고 API 키 설정
echo    3. 실행 파일을 더블클릭하여 실행
echo.
echo ⚠️ 중요: 패키징된 앱에는 샘플 설정만 포함됩니다.
echo    실제 사용을 위해서는 본인의 API 키를 설정해야 합니다.
echo.
echo 🔧 문제 발생 시: python restore_configs.py 실행
echo.
pause