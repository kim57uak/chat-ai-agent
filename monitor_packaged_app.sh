#!/bin/bash

# 패키징된 Chat AI Agent 모니터링 스크립트
cd "$(dirname "$0")"

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ 가상환경이 없습니다. venv를 먼저 생성하세요."
    echo "💡 python -m venv venv"
    exit 1
fi

# psutil 설치 확인 (monitor_packaged_app.py가 psutil을 사용하므로)
if ! python -c "import psutil" &>/dev/null; then
    echo "📦 psutil 설치 중..."
    ./venv/bin/pip install psutil -q
    if [ $? -eq 0 ]; then
        echo "✅ psutil 설치 완료"
    else
        echo "❌ psutil 설치 실패"
        exit 1
    fi
fi

echo "📊 패키징된 Chat AI Agent 모니터링 시작..."
python monitor_packaged_app.py "$@"

# 결과 확인 (스크립트 자체의 성공/실패)
if [ $? -eq 0 ]; then
    echo "✅ 모니터링 스크립트 종료"
else
    echo "❌ 모니터링 스크립트 오류 발생"
    exit 1
fi
