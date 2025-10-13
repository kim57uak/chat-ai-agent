#!/bin/bash

# 가상환경 재생성 및 빌드 실행 스크립트
# Usage:
#   ./build.sh              # venv 재생성 + 빌드
#   ./build.sh --skip-venv  # venv 재생성 스킵, 바로 빌드

cd "$(dirname "$0")"

SKIP_VENV=false

# 옵션 파싱
for arg in "$@"; do
    if [ "$arg" = "--skip-venv" ]; then
        SKIP_VENV=true
        break
    fi
done

if [ "$SKIP_VENV" = true ]; then
    echo "⚡ Quick build mode (venv setup skipped)"
    echo "📁 Working directory: $(pwd)"
    
    # 가상환경 존재 확인
    if [ ! -d "venv" ]; then
        echo "❌ venv not found! Run without --skip-venv first."
        exit 1
    fi
    
    # 가상환경 활성화
    echo "🔌 Activating existing virtual environment..."
    source venv/bin/activate
    
    # Python 버전 확인
    echo "🐍 Python version: $(python --version)"
    
    # 빌드 실행
    echo "🔨 Running build_package.py..."
    python build_package.py
else
    echo "🚀 Full build mode (venv recreation + build)"
    echo "📁 Working directory: $(pwd)"
    
    # 1. 기존 가상환경 삭제
    if [ -d "venv" ]; then
        echo "🗑️  Removing existing virtual environment..."
        rm -rf venv
        echo "✓ Virtual environment removed"
    fi
    
    # 2. pip 캐시 정리
    echo "🧹 Purging pip cache..."
    pip cache purge 2>/dev/null || echo "⚠️  pip cache purge not available"
    echo "✓ Pip cache purged"
    
    # 3. 새 가상환경 생성
    echo "📦 Creating new virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment!"
        exit 1
    fi
    echo "✓ Virtual environment created"
    
    # 4. 가상환경 활성화
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
    
    # 5. pip 업그레이드
    echo "⬆️  Upgrading pip..."
    pip install --upgrade pip
    
    # 6. 의존성 설치
    echo "📥 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies!"
        exit 1
    fi
    echo "✓ Dependencies installed"
    
    # 7. Python 버전 확인
    echo "🐍 Python version: $(python --version)"
    
    # 8. 빌드 실행
    echo "🔨 Running build_package.py..."
    python build_package.py
fi

# 결과 확인
if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
else
    echo "❌ Build failed!"
    exit 1
fi
