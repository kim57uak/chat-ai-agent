#!/bin/bash

# Chat AI Agent 실행 스크립트
# 어디서든 실행 가능한 런처

# 스크립트 위치 기반으로 프로젝트 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "🤖 Chat AI Agent 시작 중..."
echo "📁 프로젝트 경로: $PROJECT_DIR"

# 프로젝트 디렉토리로 이동
cd "$PROJECT_DIR" || {
    echo "❌ 프로젝트 디렉토리를 찾을 수 없습니다: $PROJECT_DIR"
    exit 1
}

# 가상환경 확인 및 활성화
if [ -d "venv" ]; then
    echo "🔧 가상환경 활성화 중..."
    source venv/bin/activate
else
    echo "⚠️  가상환경이 없습니다. 시스템 Python 사용"
fi

# Python 실행
echo "🚀 애플리케이션 실행 중..."
python main.py

echo "✅ 애플리케이션 종료 완료"