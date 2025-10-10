#!/bin/bash

# Chat AI Agent 모니터링 스크립트
cd "$(dirname "$0")"

# 가상환경 확인 및 활성화
if [ ! -d "venv" ]; then
    echo "❌ 가상환경이 없습니다. venv를 먼저 생성하세요."
    echo "💡 python -m venv venv"
    exit 1
fi

echo "🔧 가상환경 활성화..."
source venv/bin/activate

# psutil 설치 확인
if ! python -c "import psutil" 2>/dev/null; then
    echo "📦 psutil 설치 중..."
    pip install psutil -q
    if [ $? -eq 0 ]; then
        echo "✅ psutil 설치 완료"
    else
        echo "❌ psutil 설치 실패"
        exit 1
    fi
fi

# 모니터링 실행
echo ""
python monitor_chatai.py "$@"
