# RAG Topic Management - Phase 1 완료

## ✅ 완료된 작업

### 1. SQLite 스키마 (TopicDatabase)
**파일**: `core/rag/storage/topic_database.py`

#### Topics 테이블
```sql
CREATE TABLE topics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT,
    description TEXT,
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES topics(id) ON DELETE CASCADE
)
```

#### Documents 테이블
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT,
    file_type TEXT,
    file_size INTEGER,
    chunk_count INTEGER DEFAULT 0,
    chunking_strategy TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
)
```

#### 주요 기능
- ✅ Topic CRUD (생성, 조회, 수정, 삭제)
- ✅ Document CRUD
- ✅ 계층적 삭제 (토픽 삭제 시 문서 ID 반환)
- ✅ 문서 수 자동 관리 (increment/decrement)
- ✅ 외부 경로 자동 감지 (config_path_manager)

### 2. LanceDB Metadata 확장
**파일**: `core/rag/vector_store/lancedb_store.py`

#### 확장된 메타데이터 필드
```python
{
    "source": "filename.txt",           # 원본 파일명
    "document_id": "doc_abc123",        # SQLite 문서 ID
    "topic_id": "topic_xyz789",         # 토픽 ID
    "chunk_index": 0,                   # 청크 순서
    "chunking_strategy": "sliding_window"  # 청킹 전략
}
```

#### 새로운 메서드
- ✅ `add_documents()`: 확장된 메타데이터로 청크 추가
- ✅ `delete_by_document_id()`: 문서 ID로 모든 청크 삭제
- ✅ `delete_by_topic_id()`: 토픽 ID로 모든 청크 삭제
- ✅ `search()`: 토픽 필터링 검색 지원

### 3. 통합 관리자 (RAGStorageManager)
**파일**: `core/rag/storage/rag_storage_manager.py`

#### 주요 기능
- ✅ SQLite + LanceDB 통합 관리
- ✅ 계층적 삭제 구현
  - 토픽 삭제 → 문서 삭제 → 청크 삭제
  - 문서 삭제 → 청크 삭제
- ✅ 메타데이터 동기화
- ✅ 통계 조회

#### 사용 예시
```python
from core.rag.storage.rag_storage_manager import RAGStorageManager

# 초기화
manager = RAGStorageManager()

# 토픽 생성
topic_id = manager.create_topic(
    name="Python Programming",
    description="Python 관련 문서"
)

# 문서 생성
doc_id = manager.create_document(
    topic_id=topic_id,
    filename="python_basics.txt",
    file_path="/path/to/file.txt",
    file_type="text",
    chunking_strategy="sliding_window"
)

# 청크 추가
chunk_ids = manager.add_chunks(
    doc_id=doc_id,
    chunks=chunks,  # List[Document]
    embeddings=embeddings,  # List[List[float]]
    chunking_strategy="sliding_window"
)

# 토픽 필터링 검색
results = manager.search_chunks(
    query="Python programming",
    k=5,
    topic_id=topic_id,  # 선택적
    query_vector=query_vector
)

# 계층적 삭제
manager.delete_topic(topic_id)  # 문서 + 청크 모두 삭제
```

### 4. 테스트 스크립트
**파일**: `tests/test_rag_storage.py`

#### 테스트 항목
- ✅ 기본 워크플로우 (생성 → 추가 → 검색 → 삭제)
- ✅ 계층적 삭제 (토픽 → 문서 → 청크)
- ✅ 통계 조회

#### 실행 방법
```bash
# 가상환경 활성화
source venv/bin/activate

# 테스트 실행
python tests/test_rag_storage.py
```

## 📊 데이터 흐름

### 업로드 플로우
```
1. 사용자가 파일 업로드
   ↓
2. TopicDatabase에 문서 메타데이터 저장
   - document_id 생성
   - topic_id 연결
   ↓
3. 파일 청킹 (전략 선택)
   ↓
4. 임베딩 생성
   ↓
5. LanceDB에 청크 저장
   - document_id, topic_id 메타데이터 포함
   ↓
6. SQLite에 chunk_count 업데이트
```

### 삭제 플로우
```
토픽 삭제:
1. SQLite에서 문서 ID 목록 조회
2. 각 문서 ID로 LanceDB 청크 삭제
3. topic_id로 LanceDB 청크 삭제 (안전장치)
4. SQLite에서 토픽 삭제 (CASCADE로 문서도 삭제)

문서 삭제:
1. document_id로 LanceDB 청크 삭제
2. SQLite에서 문서 삭제
3. 토픽 문서 수 감소
```

### 검색 플로우
```
1. 사용자 쿼리 입력
   ↓
2. 쿼리 임베딩 생성
   ↓
3. LanceDB 벡터 검색
   - 선택적 topic_id 필터링
   ↓
4. 결과 반환 (메타데이터 포함)
```

## 🎯 다음 단계: Phase 2

### Phase 2: 임베딩 모델 관리 (1-2일)
- [ ] BaseEmbeddingStrategy 인터페이스
- [ ] LocalEmbeddingStrategy (현재 사용 중)
- [ ] CustomLocalEmbeddingStrategy (사용자 모델 폴더)
- [ ] OpenAIEmbeddingStrategy (선택)
- [ ] GoogleEmbeddingStrategy (선택)
- [ ] EmbeddingFactory
- [ ] EmbeddingConfigManager
- [ ] EmbeddingSettingsDialog UI

### 구현 우선순위
1. **BaseEmbeddingStrategy** 인터페이스 정의
2. **LocalEmbeddingStrategy** 리팩토링 (기존 코드 활용)
3. **EmbeddingFactory** 생성
4. **OpenAI/Google** 전략 구현 (선택)
5. **EmbeddingSettingsDialog** UI

## 📝 기술 노트

### 외부 경로 관리
- `config_path_manager.get_user_config_path()` 사용
- 폴백: `~/.chat-ai-agent` (macOS/Linux) 또는 `%LOCALAPPDATA%\ChatAIAgent` (Windows)

### LanceDB 특징
- 벡터 검색 전용 (텍스트 검색 비활성화)
- 메타데이터 필터링 지원
- DELETE 문법: `"id IN ('id1', 'id2')"`
- WHERE 문법: `"metadata.field = 'value'"`

### SQLite CASCADE
- `ON DELETE CASCADE`로 자동 삭제
- 토픽 삭제 시 문서 자동 삭제
- 명시적 청크 삭제는 LanceDB에서 수행

## 🔍 검증 방법

### 1. 데이터베이스 확인
```bash
# SQLite
sqlite3 ~/.chat-ai-agent/rag_topics.db
> SELECT * FROM topics;
> SELECT * FROM documents;

# LanceDB (Python)
import lancedb
db = lancedb.connect("~/.chat-ai-agent/vectordb")
table = db.open_table("documents")
print(table.to_pandas())
```

### 2. 로그 확인
```bash
tail -f ~/.chat-ai-agent/logs/app.log | grep -E "(topic|document|chunk)"
```

### 3. 테스트 실행
```bash
python tests/test_rag_storage.py
```

## 📚 참고 자료

### 관련 파일
- `core/rag/storage/topic_database.py` - SQLite 관리
- `core/rag/vector_store/lancedb_store.py` - LanceDB 관리
- `core/rag/storage/rag_storage_manager.py` - 통합 관리자
- `tests/test_rag_storage.py` - 테스트 스크립트

### 설계 문서
- `planning/RAG_TOPIC_MANAGEMENT_DESIGN.md` - 전체 설계

---

**작성일**: 2024
**Phase**: 1/7 완료
**다음 단계**: Phase 2 (임베딩 모델 관리)
**상태**: ✅ 완료 및 테스트 준비
