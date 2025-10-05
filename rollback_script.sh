#!/bin/bash
# 데이터 마이그레이션 롤백 스크립트
# 생성일: 2025-10-04 04:38:31

echo "데이터베이스 롤백 시작..."

# 현재 DB 백업
cp "/Users/dolpaks/Downloads/ai_file_folder/config/db/chat_sessions_encrypted.db" "/Users/dolpaks/Downloads/ai_file_folder/config/db/chat_sessions_encrypted.db.rollback_backup"

# 원본 DB 복원
cp "backups/chat_sessions_backup_20251004_043831.db" "/Users/dolpaks/Downloads/ai_file_folder/config/db/chat_sessions_encrypted.db"

echo "롤백 완료"
echo "원본 백업: backups/chat_sessions_backup_20251004_043831.db"
echo "롤백 전 백업: /Users/dolpaks/Downloads/ai_file_folder/config/db/chat_sessions_encrypted.db.rollback_backup"
