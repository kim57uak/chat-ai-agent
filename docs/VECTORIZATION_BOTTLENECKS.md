# 벡터화 성능 병목 분석 및 개선

## 🐌 현재 병목 포인트

### 1. **순차 처리** (가장 큰 병목)
```python
# 현재: 파일을 하나씩 처리
for file in files:  # ❌ 순차
    process_file(file)
```
- 100개 파일 × 5초 = **500초 (8분)**

### 2. **개별 임베딩 호출**
```python
# 현재: 청크마다 개별 호출
for chunk in chunks:  # ❌ 비효율
    vector = embeddings.embed_documents([chunk])
```
- 네트워크/모델 오버헤드 × 청크 수

### 3. **모델 재초기화**
```python
# 현재: 매번 모델 로드
embeddings = EmbeddingFactory.create_embeddings()  # ❌ 2-3초
```
- 이미 해결됨 (임베딩 풀 사용)

### 4. **DB 쓰기 최적화 부족**
```python
# 현재: 청크마다 개별 삽입
for chunk in chunks:  # ❌ 느림
    db.insert(chunk)
```

## ✅ 개선 방안

### 1. 병렬 처리 (4배 향상)
```python
# 개선: 4개 파일 동시 처리
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_file, f) for f in files]
```
- 100개 파일 ÷ 4 = **125초 (2분)**

### 2. 배치 임베딩 (10배 향상)
```python
# 개선: 32개씩 배치 처리
batch_size = 32
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    vectors = embeddings.embed_documents(batch)  # ✅ 배치
```
- 네트워크 오버헤드 감소
- GPU 활용도 증가

### 3. 벡터 DB 배치 삽입
```python
# 개선: 한 번에 삽입
db.add_documents(all_chunks, embeddings=all_vectors)  # ✅ 배치
```

## 📊 성능 비교

| 방식 | 100개 파일 | 개선율 |
|------|-----------|--------|
| **현재 (순차)** | 500초 (8분) | - |
| **병렬 (4 workers)** | 125초 (2분) | 4배 ⚡ |
| **병렬 + 배치 임베딩** | 50초 (1분) | 10배 ⚡⚡ |
| **병렬 + 배치 + DB 최적화** | 30초 | 16배 ⚡⚡⚡ |

## 🚀 최적화 구현

### 옵션 1: 간단한 병렬화 (즉시 적용 가능)

```python
# core/rag/batch/batch_processor.py 수정
from concurrent.futures import ThreadPoolExecutor

class BatchProcessor:
    def __init__(self, storage_manager, embeddings, max_workers: int = 4):
        self.max_workers = max_workers  # ✅ 병렬 처리
    
    def process_files(self, files, topic_id):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._process_file, f, topic_id): f 
                      for f in files}
            
            for future in as_completed(futures):
                result = future.result()
                # 진행 상황 업데이트
```

### 옵션 2: 배치 임베딩 추가 (중간 난이도)

```python
def _embed_batch(self, texts: List[str], batch_size: int = 32):
    """배치 임베딩"""
    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        vectors = self.embeddings.embed_documents(batch)  # ✅ 배치
        all_vectors.extend(vectors)
    return all_vectors
```

### 옵션 3: 완전 최적화 (고급)

```python
# docs/VECTORIZATION_PERFORMANCE.md 참조
# BatchProcessorOptimized 클래스 사용
```

## 🎯 권장 적용 순서

### Phase 1: 병렬 처리 (즉시)
```python
# config.json 또는 rag_config.json
{
  "batch_upload": {
    "max_workers": 4  # ✅ CPU 코어 수에 맞게
  }
}
```

### Phase 2: 배치 임베딩 (1주일 내)
```python
# embeddings.embed_documents() 호출 시
# 청크를 배치로 묶어서 호출
```

### Phase 3: DB 최적화 (2주일 내)
```python
# LanceDB add_documents() 최적화
# 트랜잭션 배치 처리
```

## 💡 추가 최적화 팁

### 1. 파일 크기 필터링
```python
# 너무 큰 파일 건너뛰기
if file.stat().st_size > 50 * 1024 * 1024:  # 50MB
    logger.warning(f"Skipping large file: {file.name}")
    continue
```

### 2. 캐싱
```python
# 이미 처리된 파일 건너뛰기
if file_hash in processed_hashes:
    logger.info(f"Skipping cached: {file.name}")
    continue
```

### 3. 청킹 전략 최적화
```python
# 작은 청크 = 더 많은 임베딩 호출
# 큰 청크 = 검색 정확도 저하
# 최적: 500-1000 토큰
```

### 4. GPU 활용
```python
# sentence-transformers는 자동으로 GPU 사용
# CUDA 설치 확인
import torch
print(torch.cuda.is_available())  # True면 GPU 사용
```

## 🔧 설정 예시

### 빠른 처리 (정확도 약간 희생)
```json
{
  "batch_upload": {
    "max_workers": 8,
    "batch_size": 64,
    "max_file_size_mb": 10
  },
  "chunking": {
    "window_size": 1000,
    "overlap_ratio": 0.1
  }
}
```

### 균형 (권장)
```json
{
  "batch_upload": {
    "max_workers": 4,
    "batch_size": 32,
    "max_file_size_mb": 50
  },
  "chunking": {
    "window_size": 500,
    "overlap_ratio": 0.2
  }
}
```

### 고품질 (느림)
```json
{
  "batch_upload": {
    "max_workers": 2,
    "batch_size": 16,
    "max_file_size_mb": 100
  },
  "chunking": {
    "window_size": 300,
    "overlap_ratio": 0.3
  }
}
```

## 📈 실제 측정 방법

```python
import time

start = time.time()
processor.process_files(files, topic_id)
elapsed = time.time() - start

print(f"처리 시간: {elapsed:.2f}초")
print(f"파일당 평균: {elapsed/len(files):.2f}초")
print(f"시간당 처리량: {len(files)/(elapsed/3600):.0f}개")
```

## 🎓 결론

**즉시 적용 가능한 개선**:
1. ✅ `max_workers=4` 설정 (병렬 처리)
2. ✅ 임베딩 풀 사용 (이미 적용됨)
3. ✅ 파일 크기 제한

**예상 효과**:
- 100개 파일: 8분 → **2분** (4배 향상)
- 사용자 경험: 대폭 개선
- 추가 비용: 없음
