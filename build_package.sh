#!/bin/bash

# ChatAI Agent macOS/Linux 패키징 스크립트
# 안전한 설정 파일 백업/복구 기능 포함

echo "🚀 ChatAI Agent 패키징 시작"
echo "================================================"

# 운영체제 확인
OS=$(uname -s)
echo "운영체제: $OS"

# 가상환경 확인 및 활성화
if [ -d "venv" ]; then
    echo "가상환경 활성화 중..."
    source venv/bin/activate
else
    echo "⚠️ 가상환경을 찾을 수 없습니다. 전역 Python을 사용합니다."
fi

# Python 버전 확인
echo "Python 버전 확인 중..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python3을 찾을 수 없습니다."
    exit 1
fi

# 필요한 패키지 확인
echo "필요한 패키지 확인 중..."
python3 -c "import PyQt6, requests, anthropic, openai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 필요한 패키지가 설치되지 않았습니다."
    echo "pip install -r requirements.txt 를 실행하세요."
    exit 1
fi

# PyInstaller 확인
python3 -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ PyInstaller가 설치되지 않았습니다."
    echo "pip install pyinstaller 를 실행하세요."
    exit 1
fi

# 패키징 스크립트 실행
echo "패키징 스크립트 실행 중..."
python3 build_package.py

if [ $? -ne 0 ]; then
    echo "❌ 패키징 실패!"
    echo "🔄 긴급 설정 파일 복구 시도 중..."
    python3 restore_configs.py
    exit 1
fi

echo ""
echo "================================================"
echo "✅ 패키징 완료! dist 폴더를 확인하세요."
echo ""

# 결과 파일 확인
if [ "$OS" = "Darwin" ]; then
    # macOS
    if [ -d "dist/ChatAIAgent.app" ]; then
        echo "📁 생성된 앱 번들: dist/ChatAIAgent.app"
        echo "   크기: $(du -sh dist/ChatAIAgent.app | cut -f1)"
    fi
    
    if [ -f "dist/ChatAIAgent-macOS.dmg" ]; then
        echo "📦 생성된 배포 패키지: dist/ChatAIAgent-macOS.dmg"
        echo "   크기: $(du -sh dist/ChatAIAgent-macOS.dmg | cut -f1)"
    fi
    
    echo ""
    echo "💡 사용법:"
    echo "   1. ChatAIAgent.app을 Applications 폴더로 이동"
    echo "   2. 홈 디렉토리에 config.json 파일을 생성하고 API 키 설정"
    echo "   3. 앱을 실행"
    
elif [ "$OS" = "Linux" ]; then
    # Linux
    if [ -f "dist/ChatAIAgent" ]; then
        echo "📁 생성된 실행 파일: dist/ChatAIAgent"
        echo "   크기: $(du -sh dist/ChatAIAgent | cut -f1)"
    fi
    
    if [ -f "dist/ChatAIAgent-Linux.tar.gz" ]; then
        echo "📦 생성된 배포 패키지: dist/ChatAIAgent-Linux.tar.gz"
        echo "   크기: $(du -sh dist/ChatAIAgent-Linux.tar.gz | cut -f1)"
    fi
    
    echo ""
    echo "💡 사용법:"
    echo "   1. dist/ChatAIAgent 를 원하는 위치에 복사"
    echo "   2. 같은 폴더에 config.json 파일을 생성하고 API 키 설정"
    echo "   3. chmod +x ChatAIAgent 로 실행 권한 부여"
    echo "   4. ./ChatAIAgent 로 실행"
fi

echo ""
echo "⚠️ 중요: 패키징된 앱에는 샘플 설정 파일만 포함되어 있습니다."
echo "   실제 사용을 위해서는 config.json에 본인의 API 키를 설정해야 합니다."
echo ""
echo "🔧 문제 발생 시: python3 restore_configs.py 실행"