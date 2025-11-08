# RAG Topic Management - Phase 3 완료

## ✅ 완료된 작업

### 1. BaseChunker 인터페이스
**파일**: `core/rag/chunking/base_chunker.py`

```python
class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, text: str, metadata: dict = None) -> List[Document]:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
```

### 2. Sliding Window Chunker
**파일**: `core/rag/chunking/sliding_window_chunker.py`

#### 특징
- RecursiveCharacterTextSplitter 사용
- 청크 크기 및 오버랩 설정 가능
- 현재 기본 전략

#### 사용 예시
```python
from core.rag.chunking.chunking_factory import ChunkingFactory

chunker = ChunkingFactory.create(
    "sliding_window",
    chunk_size=500,
    overlap=100
)

chunks = chunker.chunk(text, metadata={"source": "file.txt"})
```

### 3. Semantic Chunker
**파일**: `core/rag/chunking/semantic_chunker.py`

#### 특징
- LangChain SemanticChunker 사용
- 의미 기반 경계 감지
- 임베딩 모델 필요

#### 사용 예시
```python
from core.rag.embeddings.embedding_factory import EmbeddingFactory

embeddings = EmbeddingFactory.create("local")
chunker = ChunkingFactory.create(
    "semantic",
    embeddings=embeddings,
    threshold_type="percentile",
    threshold=95
)

chunks = chunker.chunk(text, metadata={"source": "file.txt"})
```

### 4. Code Chunker
**파일**: `core/rag/chunking/code_chunker.py`

#### 지원 언어 (18개)
- Python, JavaScript, TypeScript, Java, C++, C, C#
- Go, Rust, Ruby, PHP, Swift, Kotlin, Scala
- Lua, HTML, Markdown, Solidity

#### 사용 예시
```python
chunker = ChunkingFactory.create(
    "code",
    language="python",
    chunk_size=500,
    overlap=50
)

chunks = chunker.chunk(code, metadata={"source": "script.py"})
```

### 5. Markdown Chunker
**파일**: `core/rag/chunking/markdown_chunker.py`

#### 특징
- 헤더 기반 분할 (#, ##, ###)
- 메타데이터에 헤더 정보 포함
- 구조 보존

#### 사용 예시
```python
chunker = ChunkingFactory.create("markdown")
chunks = chunker.chunk(markdown_text, metadata={"source": "readme.md"})

# 각 청크의 메타데이터에 헤더 정보 포함
# {'Header 1': 'Title', 'Header 2': 'Section', 'source': 'readme.md'}
```

### 6. Chunking Factory
**파일**: `core/rag/chunking/chunking_factory.py`

#### 수동 선택
```python
chunker = ChunkingFactory.create("sliding_window", chunk_size=500)
chunker = ChunkingFactory.create("semantic", embeddings=embeddings)
chunker = ChunkingFactory.create("code", language="python")
chunker = ChunkingFactory.create("markdown")
```

#### 자동 선택 (파일 확장자 기반)
```python
chunker = ChunkingFactory.get_strategy_for_file("script.py")  # → code_py
chunker = ChunkingFactory.get_strategy_for_file("readme.md")  # → markdown
chunker = ChunkingFactory.get_strategy_for_file("data.txt")   # → sliding_window
```

## 📊 청킹 전략 비교

| 전략 | 장점 | 단점 | 사용 케이스 |
|------|------|------|-------------|
| Sliding Window | 빠름, 안정적 | 문맥 무시 | 일반 텍스트 |
| Semantic | 의미 보존 | 느림, 임베딩 필요 | 긴 문서, 에세이 |
| Code | 구문 인식 | 언어별 설정 | 소스 코드 |
| Markdown | 구조 보존 | 마크다운 전용 | 문서, README |

## 🔧 설정 파일 통합

### rag_config.json
```json
{
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
      },
      "code": {
        "chunk_size": 500,
        "overlap": 50
      }
    }
  }
}
```

### 설정 기반 사용
```python
from core.rag.config.rag_config_manager import RAGConfigManager

config_manager = RAGConfigManager()
chunking_config = config_manager.get_chunking_config()

default_strategy = chunking_config["default_strategy"]
strategy_params = chunking_config["strategies"][default_strategy]

chunker = ChunkingFactory.create(default_strategy, **strategy_params)
```

## 🎯 통합 워크플로우

### 파일 업로드 → 청킹 → 임베딩 → 저장
```python
from core.rag.storage.rag_storage_manager import RAGStorageManager
from core.rag.embeddings.embedding_factory import EmbeddingFactory
from core.rag.chunking.chunking_factory import ChunkingFactory
from core.rag.config.rag_config_manager import RAGConfigManager

# 1. 설정 로드
config_manager = RAGConfigManager()

# 2. 임베딩 모델 생성
embedding_config = config_manager.get_embedding_config()
embedding_type = embedding_config.pop('type')
embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)

# 3. 청킹 전략 선택 (자동)
filename = "script.py"
chunker = ChunkingFactory.get_strategy_for_file(filename)

# 4. 파일 읽기 및 청킹
with open(filename, 'r') as f:
    text = f.read()

chunks = chunker.chunk(text, metadata={"source": filename})

# 5. 임베딩 생성
vectors = embeddings.embed_documents([c.page_content for c in chunks])

# 6. 저장
storage = RAGStorageManager()
doc_id = storage.create_document(
    topic_id="topic_123",
    filename=filename,
    file_path="/path/to/script.py",
    file_type="python",
    chunking_strategy=chunker.name
)

chunk_ids = storage.add_chunks(
    doc_id=doc_id,
    chunks=chunks,
    embeddings=vectors,
    chunking_strategy=chunker.name
)

print(f"✅ {len(chunk_ids)} chunks saved with strategy: {chunker.name}")
```

## 🧪 테스트 결과

### 실행
```bash
source venv/bin/activate
python tests/test_chunking_strategies.py
```

### 결과
```
✅ Sliding Window: 10 chunks
✅ Code Chunking: 2 chunks (Python)
✅ Markdown: 4 chunks (헤더 기반)
✅ Auto Selection:
   test.py → code_py
   readme.md → markdown
   data.txt → sliding_window
   script.js → code_js
✅ Semantic: 2 chunks (의미 기반)
```

## 📝 확장 가능성

### 새로운 전략 추가
```python
# core/rag/chunking/table_chunker.py
class TableChunker(BaseChunker):
    def chunk(self, text: str, metadata: dict = None):
        # 테이블 파싱 로직
        pass
    
    @property
    def name(self):
        return "table"

# chunking_factory.py에 등록
elif strategy == "table":
    from .table_chunker import TableChunker
    return TableChunker()
```

## 🎯 다음 단계: Phase 4

### Phase 4: 배치 업로드 (2-3일)
- [ ] FileScanner (50개 이상 확장자)
- [ ] BatchProcessor (SQLite + LanceDB 동시 업데이트)
- [ ] ProgressTracker (실시간 통계)
- [ ] BatchUploadDialog UI (진행률, 통계 카드, 로그)
- [ ] 병렬 처리 (ThreadPoolExecutor)

## 📚 참고 자료

### 관련 파일
- `core/rag/chunking/base_chunker.py` - 인터페이스
- `core/rag/chunking/sliding_window_chunker.py` - 슬라이딩 윈도우
- `core/rag/chunking/semantic_chunker.py` - 의미 기반
- `core/rag/chunking/code_chunker.py` - 코드 전용
- `core/rag/chunking/markdown_chunker.py` - 마크다운
- `core/rag/chunking/chunking_factory.py` - 팩토리
- `tests/test_chunking_strategies.py` - 테스트

### LangChain 문서
- RecursiveCharacterTextSplitter
- SemanticChunker (langchain-experimental)
- Language-specific splitters

---

**작성일**: 2024
**Phase**: 3/7 완료
**다음 단계**: Phase 4 (배치 업로드)
**상태**: ✅ 완료 및 테스트 통과
