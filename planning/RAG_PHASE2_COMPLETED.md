# RAG Topic Management - Phase 2 완료

## ✅ 완료된 작업

### 1. BaseEmbeddings 인터페이스
**파일**: `core/rag/embeddings/base_embeddings.py`

이미 구현되어 있음:
- `embed_documents()`: 다중 문서 임베딩
- `embed_query()`: 단일 쿼리 임베딩
- `dimension`: 임베딩 차원 속성

### 2. LocalEmbeddings (KoreanEmbeddings)
**파일**: `core/rag/embeddings/korean_embeddings.py`

기존 구현 활용:
- ✅ dragonkue-KoEn-E5-Tiny 모델 (384 차원)
- ✅ 로컬 모델 우선 로드
- ✅ 임베딩 캐시 지원
- ✅ HuggingFace 폴백

### 3. OpenAI Embeddings
**파일**: `core/rag/embeddings/openai_embeddings.py`

#### 지원 모델
- `text-embedding-3-small`: 1536 차원
- `text-embedding-3-large`: 3072 차원

#### 주요 기능
```python
from core.rag.embeddings.openai_embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    api_key="sk-...",
    model="text-embedding-3-small"
)

# 문서 임베딩
doc_vectors = embeddings.embed_documents(["text1", "text2"])

# 쿼리 임베딩
query_vector = embeddings.embed_query("search query")

# 차원 확인
print(embeddings.dimension)  # 1536
```

### 4. Google Embeddings
**파일**: `core/rag/embeddings/google_embeddings.py`

#### 지원 모델
- `embedding-001`: 768 차원

#### 주요 기능
```python
from core.rag.embeddings.google_embeddings import GoogleEmbeddings

embeddings = GoogleEmbeddings(
    api_key="AIza...",
    model="embedding-001"
)

# task_type 자동 설정
# - retrieval_document: 문서 임베딩
# - retrieval_query: 쿼리 임베딩
```

### 5. Embedding Factory
**파일**: `core/rag/embeddings/embedding_factory.py`

#### Strategy 패턴 구현
```python
from core.rag.embeddings.embedding_factory import EmbeddingFactory

# Local
embeddings = EmbeddingFactory.create(
    "local",
    model="exp-models/dragonkue-KoEn-E5-Tiny",
    enable_cache=True
)

# OpenAI
embeddings = EmbeddingFactory.create(
    "openai",
    api_key="sk-...",
    model="text-embedding-3-small"
)

# Google
embeddings = EmbeddingFactory.create(
    "google",
    api_key="AIza...",
    model="embedding-001"
)
```

### 6. RAG Config Manager
**파일**: `core/rag/config/rag_config_manager.py`

#### 설정 파일 구조
**위치**: `~/.chat-ai-agent/rag_config.json` (또는 사용자 지정 경로)

```json
{
  "embedding": {
    "type": "local",
    "model": "exp-models/dragonkue-KoEn-E5-Tiny",
    "dimension": 384,
    "enable_cache": true
  },
  "chunking": {
    "default_strategy": "sliding_window",
    "strategies": {
      "semantic": {
        "threshold_type": "percentile",
        "threshold_amount": 95
      },
      "sliding_window": {
        "window_size": 500,
        "overlap_ratio": 0.2
      }
    }
  },
  "batch_upload": {
    "max_workers": 4,
    "max_file_size_mb": 50,
    "exclude_patterns": ["node_modules", ".git", "venv", "__pycache__"]
  }
}
```

#### 사용 예시
```python
from core.rag.config.rag_config_manager import RAGConfigManager

# 초기화
config_manager = RAGConfigManager()

# 임베딩 설정 조회
embedding_config = config_manager.get_embedding_config()
# {'type': 'local', 'model': '...', 'dimension': 384, ...}

# 임베딩 설정 업데이트
config_manager.update_embedding_config(
    type="openai",
    api_key="sk-...",
    model="text-embedding-3-small",
    dimension=1536
)

# 청킹 설정 조회
chunking_config = config_manager.get_chunking_config()

# 배치 업로드 설정 조회
batch_config = config_manager.get_batch_config()
```

### 7. 통합 워크플로우

#### 설정 기반 임베딩 생성
```python
from core.rag.config.rag_config_manager import RAGConfigManager
from core.rag.embeddings.embedding_factory import EmbeddingFactory

# 1. 설정 로드
config_manager = RAGConfigManager()
embedding_config = config_manager.get_embedding_config()

# 2. 팩토리로 임베딩 생성
embedding_type = embedding_config.pop('type')
embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)

# 3. 사용
vectors = embeddings.embed_documents(["text1", "text2"])
query_vector = embeddings.embed_query("search query")
```

#### RAG Storage Manager와 통합
```python
from core.rag.storage.rag_storage_manager import RAGStorageManager
from core.rag.config.rag_config_manager import RAGConfigManager
from core.rag.embeddings.embedding_factory import EmbeddingFactory

# 설정 로드
config_manager = RAGConfigManager()
embedding_config = config_manager.get_embedding_config()

# 임베딩 생성
embedding_type = embedding_config.pop('type')
embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)

# 스토리지 초기화
storage = RAGStorageManager()

# 문서 추가
doc_id = storage.create_document(
    topic_id="topic_123",
    filename="test.txt",
    file_path="/path/to/test.txt",
    file_type="text"
)

# 청크 임베딩 및 저장
from langchain.schema import Document
chunks = [Document(page_content="content", metadata={"source": "test.txt"})]
vectors = embeddings.embed_documents([c.page_content for c in chunks])

chunk_ids = storage.add_chunks(
    doc_id=doc_id,
    chunks=chunks,
    embeddings=vectors
)

# 검색
query_vector = embeddings.embed_query("search query")
results = storage.search_chunks(
    query="search query",
    k=5,
    query_vector=query_vector
)
```

## 📊 임베딩 모델 비교

| 모델 | 차원 | 비용 | 속도 | 품질 | 오프라인 |
|------|------|------|------|------|----------|
| Local (E5-Tiny) | 384 | 무료 | 빠름 | 중간 | ✅ |
| OpenAI Small | 1536 | 유료 | 중간 | 높음 | ❌ |
| OpenAI Large | 3072 | 유료 | 느림 | 매우 높음 | ❌ |
| Google | 768 | 무료 티어 | 중간 | 높음 | ❌ |

## 🔧 설정 변경 방법

### 1. 코드로 변경
```python
config_manager = RAGConfigManager()

# OpenAI로 변경
config_manager.update_embedding_config(
    type="openai",
    api_key="sk-...",
    model="text-embedding-3-small",
    dimension=1536
)
```

### 2. 파일 직접 편집
```bash
# 설정 파일 열기
nano ~/.chat-ai-agent/rag_config.json

# embedding 섹션 수정
{
  "embedding": {
    "type": "openai",
    "api_key": "sk-...",
    "model": "text-embedding-3-small",
    "dimension": 1536
  }
}
```

## 🧪 테스트

### 실행 방법
```bash
source venv/bin/activate
python tests/test_embedding_factory.py
```

### 테스트 항목
- ✅ Local 임베딩 생성 및 사용
- ✅ Config Manager 설정 로드/저장
- ✅ Factory + Config 통합

### 테스트 결과
```
✅ Document embeddings: 2 vectors
   Dimension: 384
✅ Query embedding: 384 dimensions
✅ Embedding config loaded
✅ Config updated
✅ Created embeddings from config
   Type: local
   Dimension: 384
```

## 🎯 다음 단계: Phase 3

### Phase 3: 청킹 전략 (3-4시간)
- [ ] SemanticChunkingStrategy (LangChain)
- [ ] CodeChunkingStrategy (LangChain, 20개 언어)
- [ ] MarkdownChunkingStrategy (LangChain)
- [ ] TableChunkingStrategy (직접 구현)
- [ ] SlidingWindowChunkingStrategy (현재 사용 중)
- [ ] ChunkingStrategyFactory

## 📝 기술 노트

### Strategy 패턴 장점
- 런타임에 임베딩 모델 변경 가능
- 새로운 모델 추가 용이 (BaseEmbeddings 구현)
- 설정 파일로 중앙 관리

### 외부 경로 관리
- `config_path_manager.get_user_config_path()` 사용
- 폴백: `~/.chat-ai-agent` (macOS/Linux)
- 폴백: `%LOCALAPPDATA%\ChatAIAgent` (Windows)

### API 키 보안
- 설정 파일에 평문 저장 (주의 필요)
- 향후 개선: 암호화 저장 또는 환경변수 사용

## 📚 참고 자료

### 관련 파일
- `core/rag/embeddings/base_embeddings.py` - 인터페이스
- `core/rag/embeddings/korean_embeddings.py` - Local 전략
- `core/rag/embeddings/openai_embeddings.py` - OpenAI 전략
- `core/rag/embeddings/google_embeddings.py` - Google 전략
- `core/rag/embeddings/embedding_factory.py` - 팩토리
- `core/rag/config/rag_config_manager.py` - 설정 관리자
- `tests/test_embedding_factory.py` - 테스트

### 설계 문서
- `planning/RAG_TOPIC_MANAGEMENT_DESIGN.md` - 전체 설계
- `planning/RAG_PHASE1_COMPLETED.md` - Phase 1 완료

---

**작성일**: 2024
**Phase**: 2/7 완료
**다음 단계**: Phase 3 (청킹 전략)
**상태**: ✅ 완료 및 테스트 통과
