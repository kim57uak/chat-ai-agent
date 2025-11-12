# 벡터 DB 최적화 분석

## 🔍 문제 원인

### 최적화 버튼 클릭 시 발생한 일

```python
# optimize_vector_db() 실행
def optimize_vector_db(self):
    table = self.vector_store.db.open_table(self.vector_store.table_name)
    
    # 1. Compact files (파일 병합)
    table.compact_files()  # ⚠️ 여기서 문제 발생 가능
    
    # 2. Cleanup old versions (오래된 버전 삭제)
    table.cleanup_old_versions(
        older_than=timedelta(seconds=0),  # ⚠️ 즉시 삭제
        delete_unverified=True  # ⚠️ 검증 안 된 것도 삭제
    )
    
    # 3. Optimize (물리적 삭제)
    table.optimize()
```

### 문제점

**`cleanup_old_versions(older_than=timedelta(seconds=0))`**
- ❌ **모든 버전을 즉시 삭제** (0초보다 오래된 것 = 모든 것)
- ❌ **현재 사용 중인 파일도 삭제 가능**
- ❌ **Lance 파일 참조 깨짐**

## 🏗️ 벡터 DB 구조 (모델별 분리)

```
/Users/dolpaks/Downloads/ai_file_folder/config/vectordb/
├── BAAI_bge_m3/                    # 모델 1
│   └── documents.lance/
│       ├── data/
│       │   ├── 0101001...f16e824dd69fc2f820d2804baa.lance  # ❌ 삭제됨
│       │   └── ...
│       └── _versions/
├── intfloat_multilingual-e5-large/ # 모델 2 (없음)
└── dragonkue-KoEn-E5-Tiny/         # 모델 3 (없음)
```

### 모델별 격리

✅ **각 모델은 독립된 폴더**
- 모델 A 최적화 → 모델 B 영향 없음
- 차원 충돌 없음 (모델별 분리)
- 동시 사용 가능

## ⚠️ 최적화의 위험성

### 1. 너무 공격적인 정리
```python
# ❌ 위험: 모든 버전 즉시 삭제
cleanup_old_versions(older_than=timedelta(seconds=0))

# ✅ 안전: 1시간 이상 된 것만 삭제
cleanup_old_versions(older_than=timedelta(hours=1))
```

### 2. 동시 접근 시 충돌
```
프로세스 A: 검색 중 (파일 읽기)
프로세스 B: 최적화 (파일 삭제)  ← 충돌!
```

### 3. 복구 불가능
```
최적화 → 파일 물리적 삭제 → 복구 불가
```

## ✅ 안전한 최적화 방법

### 수정된 코드

```python
def optimize_vector_db(self) -> Dict:
    """안전한 벡터 DB 최적화"""
    try:
        table = self.vector_store.db.open_table(self.vector_store.table_name)
        
        # 1. Compact files (안전)
        table.compact_files()
        logger.info("Compacted files")
        
        # 2. Cleanup old versions (안전하게)
        from datetime import timedelta
        stats = table.cleanup_old_versions(
            older_than=timedelta(hours=1),  # ✅ 1시간 이상 된 것만
            delete_unverified=False  # ✅ 검증된 것만 삭제
        )
        logger.info(f"Cleanup stats: {stats}")
        
        # 3. Optimize (선택적)
        # table.optimize()  # 필요 시에만 실행
        
        return {"success": True, "cleanup_stats": stats}
        
    except Exception as e:
        logger.error(f"Optimize failed: {e}")
        return {"success": False, "error": str(e)}
```

## 🔄 여러 임베딩 모델 처리

### 현재 구조

```python
# 모델별 독립 폴더
/vectordb/
├── BAAI_bge_m3/           # 1024차원
│   └── documents.lance
├── intfloat_e5_large/     # 1024차원
│   └── documents.lance
└── dragonkue_KoEn/        # 384차원
    └── documents.lance
```

### 장점

1. **차원 충돌 없음**
   - 각 모델이 독립된 테이블
   - 다른 차원도 문제없음

2. **동시 사용 가능**
   - 모델 A로 검색
   - 모델 B로 업로드
   - 충돌 없음

3. **최적화 격리**
   - 모델 A 최적화 → 모델 B 영향 없음

### 모델 전환 시나리오

```python
# 1. 사용자가 모델 변경
config_manager.set_current_embedding_model("BAAI_bge_m3")

# 2. 자동으로 해당 모델 폴더 사용
store = LanceDBStore()  # /vectordb/BAAI_bge_m3/

# 3. 이전 모델 데이터는 그대로 유지
# /vectordb/dragonkue_KoEn/ ← 삭제 안 됨
```

## 📊 최적화 타이밍

### 언제 실행?

✅ **권장**:
- 대량 삭제 후 (100개 이상)
- 디스크 공간 부족 시
- 검색 속도 저하 시

❌ **비권장**:
- 매번 삭제 후
- 사용 중일 때
- 자동 스케줄

### 최적화 주기

```python
# 예시: 주간 최적화
from datetime import timedelta

# 7일 이상 된 버전만 정리
table.cleanup_old_versions(
    older_than=timedelta(days=7),
    delete_unverified=False
)
```

## 🛠️ 복구 방법

### 1. 손상된 DB 복구
```bash
python scripts/repair_vector_db.py --all
```

### 2. 백업에서 복원
```bash
# 백업 (최적화 전)
cp -r /vectordb/BAAI_bge_m3 /backup/

# 복원 (문제 발생 시)
rm -rf /vectordb/BAAI_bge_m3
cp -r /backup/BAAI_bge_m3 /vectordb/
```

### 3. 재인덱싱
```python
# 문서 다시 업로드
# 벡터 재생성
```

## 🎯 Best Practices

1. **최적화 전 백업**
   ```bash
   cp -r /vectordb /backup/vectordb_$(date +%Y%m%d)
   ```

2. **안전한 파라미터**
   ```python
   cleanup_old_versions(
       older_than=timedelta(hours=1),  # 충분한 시간
       delete_unverified=False  # 안전 우선
   )
   ```

3. **사용자 확인**
   ```python
   reply = QMessageBox.question(
       "최적화 시 일시적으로 검색이 느려질 수 있습니다. 계속?"
   )
   ```

4. **로깅 강화**
   ```python
   logger.info(f"Before: {table.count_rows()} rows")
   table.optimize()
   logger.info(f"After: {table.count_rows()} rows")
   ```

## 📝 결론

**최적화가 문제였나?**
- ✅ **예**: `older_than=timedelta(seconds=0)` 너무 공격적
- ✅ **예**: 사용 중인 파일 삭제 가능
- ✅ **예**: Lance 파일 참조 깨짐

**여러 모델 처리는?**
- ✅ **안전**: 모델별 독립 폴더
- ✅ **격리**: 최적화 영향 없음
- ✅ **동시 사용**: 가능

**해결책**:
- 안전한 파라미터 사용
- 백업 후 최적화
- 복구 스크립트 준비
