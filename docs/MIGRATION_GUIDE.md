# 📋 데이터 마이그레이션 가이드

## 개요

기존 평문 데이터베이스를 암호화된 형태로 안전하게 마이그레이션하는 방법을 설명합니다.

## 🔄 마이그레이션 프로세스

### 1. 사전 준비

#### 1.1 백업 생성
```bash
# 기존 데이터베이스 수동 백업
cp ~/.chat-ai-agent/chat_sessions.db ~/.chat-ai-agent/chat_sessions_backup.db
```

#### 1.2 마이그레이션 검증 (Dry Run)
```bash
# 가상환경 활성화
source venv/bin/activate

# 마이그레이션 시뮬레이션
python scripts/migrate_data.py \
  --old-db ~/.chat-ai-agent/chat_sessions.db \
  --new-db ~/.chat-ai-agent/chat_sessions_encrypted.db \
  --dry-run
```

### 2. 실제 마이그레이션

#### 2.1 마이그레이션 실행
```bash
# 실제 마이그레이션 수행
python scripts/migrate_data.py \
  --old-db ~/.chat-ai-agent/chat_sessions.db \
  --new-db ~/.chat-ai-agent/chat_sessions_encrypted.db
```

#### 2.2 비밀번호 설정
- 프롬프트에서 암호화 비밀번호 입력
- 강력한 비밀번호 사용 권장 (최소 12자, 특수문자 포함)

### 3. 마이그레이션 검증

#### 3.1 기본 검증
```bash
python scripts/verify_migration.py \
  --db ~/.chat-ai-agent/chat_sessions_encrypted.db
```

#### 3.2 상세 검증
```bash
python scripts/verify_migration.py \
  --db ~/.chat-ai-agent/chat_sessions_encrypted.db \
  --detailed
```

## 📊 마이그레이션 결과 예시

### 성공적인 마이그레이션
```
=== 데이터 마이그레이션 시작 ===
백업 생성 완료: backups/chat_sessions_backup_20241204_031500.db
마이그레이션 대상: 세션 25개, 메시지 1,247개
✅ 마이그레이션 성공!
백업 파일: backups/chat_sessions_backup_20241204_031500.db
마이그레이션된 데이터:
  - 세션: 25개
  - 메시지: 1,247개
롤백 스크립트: rollback_script.sh
암호화 버전: 1
```

### 검증 결과
```
=== 기본 검증 ===
데이터베이스 버전: 1
현재 지원 버전: 1
호환성: ✅ 호환
총 세션: 25개
총 메시지: 1,247개
  세션 v1: 25개

=== 데이터 무결성 검증 ===
전체 건강도: 100.0%
세션 유효성: 25/25
메시지 유효성: 1247/1247

✅ 모든 검증 통과
```

## 🔧 고급 옵션

### 강제 덮어쓰기
```bash
python scripts/migrate_data.py \
  --old-db old_database.db \
  --new-db new_database.db \
  --force
```

### 비밀번호 직접 지정 (비권장)
```bash
python scripts/migrate_data.py \
  --old-db old_database.db \
  --new-db new_database.db \
  --password "your_password"
```

## 🚨 롤백 절차

### 자동 롤백 스크립트 사용
```bash
# 마이그레이션 시 생성된 롤백 스크립트 실행
./rollback_script.sh
```

### 수동 롤백
```bash
# 현재 암호화 DB 백업
cp ~/.chat-ai-agent/chat_sessions_encrypted.db \
   ~/.chat-ai-agent/chat_sessions_encrypted_backup.db

# 원본 DB 복원
cp backups/chat_sessions_backup_YYYYMMDD_HHMMSS.db \
   ~/.chat-ai-agent/chat_sessions.db
```

## 📋 체크리스트

### 마이그레이션 전
- [ ] 기존 데이터베이스 백업 완료
- [ ] 가상환경 활성화 확인
- [ ] Dry run 테스트 성공
- [ ] 강력한 비밀번호 준비
- [ ] 충분한 디스크 공간 확인

### 마이그레이션 후
- [ ] 마이그레이션 성공 메시지 확인
- [ ] 백업 파일 존재 확인
- [ ] 롤백 스크립트 생성 확인
- [ ] 검증 스크립트 실행 성공
- [ ] 앱에서 정상 동작 확인

## ⚠️ 주의사항

### 보안
- **비밀번호 분실 시 데이터 복구 불가능**
- 비밀번호를 안전한 곳에 별도 보관
- 명령줄에서 비밀번호 직접 입력 지양

### 데이터
- 마이그레이션 중 앱 실행 금지
- 백업 파일 안전한 위치에 보관
- 원본 데이터베이스는 검증 완료 후 삭제

### 성능
- 대용량 데이터의 경우 시간 소요 가능
- 마이그레이션 중 시스템 리소스 사용량 증가

## 🔍 문제 해결

### 일반적인 오류

#### "기존 데이터베이스가 존재하지 않습니다"
```bash
# 데이터베이스 경로 확인
ls -la ~/.chat-ai-agent/
```

#### "비밀번호가 올바르지 않습니다"
- 비밀번호 재입력
- 키보드 레이아웃 확인

#### "새 데이터베이스가 이미 존재합니다"
```bash
# 기존 암호화 DB 백업 후 삭제
mv ~/.chat-ai-agent/chat_sessions_encrypted.db \
   ~/.chat-ai-agent/chat_sessions_encrypted_old.db
```

### 부분 마이그레이션 실패
```bash
# 검증으로 실패 원인 파악
python scripts/verify_migration.py \
  --db ~/.chat-ai-agent/chat_sessions_encrypted.db \
  --detailed

# 필요시 롤백 후 재시도
./rollback_script.sh
```

## 📞 지원

마이그레이션 관련 문제가 발생하면:
1. 로그 파일 확인
2. 검증 스크립트 실행
3. GitHub Issues에 문의

---

**중요**: 마이그레이션은 되돌릴 수 없는 과정입니다. 반드시 백업을 생성하고 충분히 테스트한 후 진행하세요.