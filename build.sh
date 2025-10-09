#!/bin/bash

# 가상환경 활성화 및 빌드 실행 스크립트
cd "$(dirname "$0")"

echo "🚀 Starting build process..."
echo "📁 Working directory: $(pwd)"

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Please create venv first: python -m venv venv"
    exit 1
fi

# Python 버전 확인
echo "🐍 Python version: $(python --version)"

# 빌드 실행
echo "🔨 Running build_package.py..."
python build_package.py "$@"

# 결과 확인
if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
else
    echo "❌ Build failed!"
    exit 1
fi
