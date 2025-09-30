#!/bin/bash

# 안전한 macOS DMG 생성 스크립트
set -e  # 오류 시 중단

APP_NAME="ChatAIAgent"
DMG_NAME="ChatAIAgent-macOS"
SOURCE_APP="dist/ChatAIAgent.app"
TEMP_DMG_DIR="temp_dmg"
DIST_DIR="dist"

echo "🚀 macOS DMG 생성 시작"
echo "================================================"

# 소스 앱 파일 확인
if [ ! -d "$SOURCE_APP" ]; then
    echo "❌ 오류: $SOURCE_APP 을 찾을 수 없습니다."
    echo "먼저 build_safe.py 를 실행하여 앱을 빌드하세요."
    exit 1
fi

# dist 디렉토리 생성
mkdir -p "$DIST_DIR"

# 기존 파일들 정리
echo "🧹 기존 파일 정리 중..."
rm -rf "$TEMP_DMG_DIR"
rm -f "$DIST_DIR/$DMG_NAME.dmg"

# 임시 디렉토리 생성
echo "📁 임시 디렉토리 생성 중..."
mkdir -p "$TEMP_DMG_DIR"

# 앱 복사 (권한 보존)
echo "📎 앱 복사 중..."
cp -pR "$SOURCE_APP" "$TEMP_DMG_DIR/"

# Applications 폴더로의 심볼릭 링크 생성
echo "🔗 Applications 링크 생성 중..."
ln -s /Applications "$TEMP_DMG_DIR/Applications"

# README 파일 추가 (선택사항)
if [ -f "README.md" ]; then
    cp "README.md" "$TEMP_DMG_DIR/"
    echo "✓ README.md 추가"
fi

# DMG 생성
echo "📦 DMG 파일 생성 중..."
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$TEMP_DMG_DIR" \
    -ov \
    -format UDZO \
    -imagekey zlib-level=9 \
    "$DIST_DIR/$DMG_NAME.dmg"

# 임시 디렉토리 정리
echo "🧹 임시 파일 정리 중..."
rm -rf "$TEMP_DMG_DIR"

# 결과 확인
if [ -f "$DIST_DIR/$DMG_NAME.dmg" ]; then
    DMG_SIZE=$(du -h "$DIST_DIR/$DMG_NAME.dmg" | cut -f1)
    echo "================================================"
    echo "✅ DMG 파일 생성 완료!"
    echo "파일: $DIST_DIR/$DMG_NAME.dmg"
    echo "크기: $DMG_SIZE"
    echo "================================================"
else
    echo "❌ DMG 생성 실패"
    exit 1
fi