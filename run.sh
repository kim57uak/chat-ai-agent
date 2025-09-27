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

# Python 실행 (안전 모드)
echo "🚀 애플리케이션 실행 중..."

# 메모리 및 스택 제한 설정
ulimit -c 0  # 코어 덤프 비활성화
ulimit -s 8192  # 스택 크기 제한

# Python 실행 (디버그 모드 비활성화)
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1

# 안전한 실행
if python -c "import sys; print('Python 버전:', sys.version)" 2>/dev/null; then
    python main.py
    exit_code=$?
else
    echo "❌ Python 실행 환경에 문제가 있습니다."
    exit 1
fi

if [ $exit_code -eq 0 ]; then
    echo "✅ 애플리케이션 정상 종료"
else
    echo "⚠️ 애플리케이션이 오류와 함께 종료됨 (코드: $exit_code)"
fi

exit $exit_code