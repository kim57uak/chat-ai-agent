#!/bin/bash

# DMG 생성 스크립트
APP_NAME="ChatAIAgent"
DMG_NAME="ChatAIAgent-macOS"
SOURCE_APP="dist/ChatAIAgent.app"
TEMP_DMG_DIR="temp_dmg"

# 기존 파일들 정리
rm -rf "$TEMP_DMG_DIR"
rm -f "dist/$DMG_NAME.dmg"

# 임시 디렉토리 생성
mkdir -p "$TEMP_DMG_DIR"

# 앱 복사 (권한 보존)
cp -pR "$SOURCE_APP" "$TEMP_DMG_DIR/"

# Applications 폴더로의 심볼릭 링크 생성
ln -s /Applications "$TEMP_DMG_DIR/Applications"

# DMG 생성
hdiutil create -volname "$APP_NAME" -srcfolder "$TEMP_DMG_DIR" -ov -format UDZO "dist/$DMG_NAME.dmg"

# 임시 디렉토리 정리
rm -rf "$TEMP_DMG_DIR"

echo "DMG 파일이 생성되었습니다: dist/$DMG_NAME.dmg"