# RAG Topic Management - Phase 4 완료

## ✅ 완료된 작업

### 1. File Scanner
**파일**: `core/rag/batch/file_scanner.py`

#### 지원 확장자 (50개 이상)
- **텍스트**: txt, text, log
- **문서**: md, markdown, rst, pdf, doc, docx
- **코드**: py, js, ts, jsx, tsx, java, cpp, c, h, hpp, go, rs, rb, php, swift, kt, scala, cs, lua, sh, bash, zsh, sql, r, m
- **웹**: html, htm, css, scss, sass, xml, json, yaml, yml
- **데이터**: csv, tsv, jsonl
- **설정**: ini, cfg, conf, config, toml, env

#### 기능
- 재귀적 폴더 스캔
- 제외 패턴 (node_modules, .git, venv 등)
- 파일 크기 제한 (기본 50MB)
- 파일 정보 추출

#### 사용 예시
```python
from core.rag.batch.file_scanner import FileScanner

scanner = FileScanner(
    exclude_patterns={'node_modules', '.git'},
    max_file_size_mb=50
)

files = scanner.scan_folder("/path/to/folder")
print(f"Found {len(files)} files")

for file in files:
    info = scanner.get_file_info(file)
    print(f"{info['name']}: {info['size']} bytes")
```

### 2. Batch Processor
**파일**: `core/rag/batch/batch_processor.py`

#### 기능
- 병렬 처리 (ThreadPoolExecutor)
- 자동 청킹 전략 선택
- 임베딩 생성
- SQLite + LanceDB 동시 저장
- 실시간 콜백 (진행, 완료, 오류)

#### 사용 예시
```python
from core.rag.batch.batch_processor import BatchProcessor

processor = BatchProcessor(
    storage_manager=storage,
    embeddings=embeddings,
    max_workers=4
)

def on_progress(file_path, current, total):
    print(f"Processing: {current}/{total}")

def on_complete(file_path, doc_id, chunk_count):
    print(f"Completed: {file_path.name} - {chunk_count} chunks")

def on_error(file_path, error):
    print(f"Error: {file_path.name} - {error}")

processor.process_files(
    files,
    topic_id="topic_123",
    on_progress=on_progress,
    on_complete=on_complete,
    on_error=on_error
)
```

### 3. Progress Tracker
**파일**: `core/rag/batch/progress_tracker.py`

#### 추적 정보
- 전체 파일 수
- 처리된 파일 수
- 실패한 파일 수
- 총 청크 수
- 경과 시간
- 처리 속도 (files/s)
- 오류 목록

#### 사용 예시
```python
from core.rag.batch.progress_tracker import ProgressTracker

tracker = ProgressTracker()
tracker.start(total_files=100)

# 처리 중
tracker.update(chunk_count=5)

# 오류 발생
tracker.add_error("file.txt", "Read error")

# 통계 조회
stats = tracker.get_stats()
print(f"Progress: {tracker.get_progress_percentage():.1f}%")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

### 4. Batch Uploader (통합)
**파일**: `core/rag/batch/batch_uploader.py`

#### 통합 기능
- FileScanner + BatchProcessor + ProgressTracker
- 원스톱 배치 업로드
- 설정 기반 동작

#### 사용 예시
```python
from core.rag.batch.batch_uploader import BatchUploader
from core.rag.storage.rag_storage_manager import RAGStorageManager
from core.rag.embeddings.embedding_factory import EmbeddingFactory
from core.rag.config.rag_config_manager import RAGConfigManager

# 설정
config_manager = RAGConfigManager()
embedding_config = config_manager.get_embedding_config()
batch_config = config_manager.get_batch_config()

# 임베딩
embedding_type = embedding_config.pop('type')
embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)

# 스토리지
storage = RAGStorageManager()
topic_id = storage.create_topic(name="My Project")

# 업로더
uploader = BatchUploader(storage, embeddings, batch_config)

# 업로드
stats = uploader.upload_folder(
    "/path/to/folder",
    topic_id,
    on_progress=lambda c, t, p, s: print(f"{c}/{t} ({p:.1f}%)"),
    on_complete=lambda s: print(f"Done: {s['total_chunks']} chunks")
)
```

## 📊 설정 파일

### rag_config.json
```json
{
  "batch_upload": {
    "max_workers": 4,
    "max_file_size_mb": 50,
    "exclude_patterns": [
      "node_modules",
      ".git",
      "venv",
      "__pycache__",
      "dist",
      "build"
    ]
  }
}
```

## 🔄 전체 워크플로우

### 1. 폴더 스캔
```
FileScanner
    ↓
재귀적 탐색
    ↓
확장자 필터링
    ↓
제외 패턴 적용
    ↓
파일 크기 체크
    ↓
파일 목록 반환
```

### 2. 병렬 처리
```
BatchProcessor (ThreadPoolExecutor)
    ↓
파일 1 → 읽기 → 청킹 → 임베딩 → 저장
파일 2 → 읽기 → 청킹 → 임베딩 → 저장
파일 3 → 읽기 → 청킹 → 임베딩 → 저장
파일 4 → 읽기 → 청킹 → 임베딩 → 저장
    ↓
진행 상황 콜백
    ↓
완료/오류 콜백
```

### 3. 저장
```
각 파일마다:
    ↓
SQLite: 문서 메타데이터 저장
    ↓
LanceDB: 청크 + 벡터 저장
    ↓
SQLite: chunk_count 업데이트
```

## 🎯 성능 최적화

### 병렬 처리
- ThreadPoolExecutor 사용
- 기본 4 workers (설정 가능)
- I/O 바운드 작업에 최적화

### 메모리 관리
- 파일별 순차 처리 (전체 로드 X)
- 청크 단위 임베딩
- 스트리밍 저장

### 오류 처리
- 개별 파일 오류가 전체 중단 X
- 오류 로그 수집
- 재시도 없음 (빠른 처리 우선)

## 🧪 테스트 결과

### File Scanner
```
✅ Total files found: 4
   - readme.md (md, 94 bytes)
   - script.py (py, 103 bytes)
   - data.txt (txt, 39 bytes)
   - app.js (js, 62 bytes)
✅ Excluded node_modules
```

### Progress Tracker
```
✅ Processed: 8
✅ Failed: 2
✅ Total chunks: 40
✅ Progress: 100.0%
✅ Complete: True
```

## 📝 사용 시나리오

### 시나리오 1: 프로젝트 전체 업로드
```python
# 프로젝트 폴더 전체 업로드
uploader.upload_folder(
    "/Users/user/my-project",
    topic_id="project_123"
)
```

### 시나리오 2: 문서 폴더 업로드
```python
# 문서 폴더만 업로드
uploader.upload_folder(
    "/Users/user/documents",
    topic_id="docs_456"
)
```

### 시나리오 3: 진행 상황 모니터링
```python
def on_progress(current, total, percentage, stats):
    print(f"[{percentage:.1f}%] {current}/{total}")
    print(f"Chunks: {stats['total_chunks']}")
    print(f"Speed: {stats['files_per_second']:.2f} files/s")
    print(f"Elapsed: {stats['elapsed_seconds']:.1f}s")

uploader.upload_folder(
    folder_path,
    topic_id,
    on_progress=on_progress
)
```

## 🎯 다음 단계: Phase 5

### Phase 5: Topic 관리 UI (1-2일)
- [ ] Topic 생성 다이얼로그
- [ ] Topic 편집/삭제 기능
- [ ] Topic 계층 구조 UI (드래그 앤 드롭)
- [ ] TopicTreeWidget (검색 기능)

## 🔍 코드 청킹 분석

### 지원 언어 (18개)
**파일**: `core/rag/chunking/code_chunker.py`

1. Python (py)
2. JavaScript (js)
3. TypeScript (ts)
4. Java (java)
5. C++ (cpp)
6. Go (go)
7. Rust (rs)
8. Ruby (rb)
9. PHP (php)
10. Swift (swift)
11. Kotlin (kt)
12. Scala (scala)
13. C (c)
14. C# (cs)
15. Lua (lua)
16. Markdown (md)
17. HTML (html)
18. Solidity (sol)

### 청킹 기준

#### 동작 원리
**LangChain의 RecursiveCharacterTextSplitter 사용**

1. **계층적 우선순위**: 의미 단위 → 구문 단위 → 문자 단위
2. **재귀적 분할**: 큰 블록이 chunk_size 초과 시 다음 구분자로 재분할
3. **언어별 최적화**: 각 언어 문법에 맞춘 구분자 사용
4. **폴백 메커니즘**: 모든 구분자 실패 시 공백/문자 단위 강제 분할

#### 언어별 구분자 (우선순위 순)

**Python**
```python
[
  "\nclass ",      # 1. 클래스 정의
  "\ndef ",        # 2. 함수 정의
  "\n\tdef ",      # 3. 들여쓰기된 메서드
  "\n\n",          # 4. 빈 줄 2개
  "\n",            # 5. 줄바꿈
  " ",             # 6. 공백
  ""               # 7. 문자 단위
]
```

**JavaScript**
```javascript
[
  "\nfunction ",   # 1. 함수 정의
  "\nconst ",      # 2. const 변수
  "\nlet ",        # 3. let 변수
  "\nvar ",        # 4. var 변수
  "\nclass ",      # 5. 클래스 정의
  "\nif ",         # 6. 제어문
  "\nfor ", "\nwhile ", "\nswitch ", "\ncase ", "\ndefault ",
  "\n\n", "\n", " ", ""
]
```

**TypeScript**
```typescript
[
  "\nenum ",       # 1. enum 정의
  "\ninterface ",  # 2. interface 정의
  "\nnamespace ",  # 3. namespace 정의
  "\ntype ",       # 4. type 정의
  "\nclass ",      # 5. 클래스 정의
  "\nfunction ",   # 6. 함수 정의
  "\nconst ", "\nlet ", "\nvar ",
  "\nif ", "\nfor ", "\nwhile ", "\nswitch ", "\ncase ", "\ndefault ",
  "\n\n", "\n", " ", ""
]
```

**Java**
```java
[
  "\nclass ",      # 1. 클래스 정의
  "\npublic ",     # 2. 접근 제어자
  "\nprotected ", "\nprivate ",
  "\nstatic ",     # 3. static 키워드
  "\nif ", "\nfor ", "\nwhile ", "\nswitch ", "\ncase ",
  "\n\n", "\n", " ", ""
]
```

**Go**
```go
[
  "\nfunc ",       # 1. 함수 정의
  "\nvar ",        # 2. 변수 선언
  "\nconst ",      # 3. 상수 선언
  "\ntype ",       # 4. 타입 정의
  "\nif ", "\nfor ", "\nswitch ", "\ncase ",
  "\n\n", "\n", " ", ""
]
```

### 청킹 예시

**원본 Python 코드**
```python
class MyClass:
    def method1(self):
        print("Method 1")
        return True
    
    def method2(self):
        print("Method 2")
        return False

def standalone_function():
    pass
```

**청킹 결과** (chunk_size=100 가정)
```
Chunk 1: "class MyClass:\n    def method1(self):\n        print(\"Method 1\")\n        return True"

Chunk 2: "def method2(self):\n        print(\"Method 2\")\n        return False"

Chunk 3: "def standalone_function():\n    pass"
```

### 핵심 특징

1. **의미 단위 보존**: 클래스, 함수, 메서드 등 완전한 코드 블록 유지
2. **문맥 유지**: 코드 구조와 계층 관계 보존
3. **언어 인식**: 각 언어의 문법적 특성 반영
4. **유연한 크기 조정**: chunk_size와 overlap 설정 가능
5. **자동 폴백**: 지원하지 않는 언어는 기본 텍스트 분할기 사용

### 사용 예시

```python
from core.rag.chunking.code_chunker import CodeChunker

# Python 코드 청킹
chunker = CodeChunker(
    language="python",
    chunk_size=500,
    overlap=50
)

code = """
class Example:
    def method(self):
        pass
"""

chunks = chunker.chunk(code, metadata={"file": "example.py"})
print(f"Created {len(chunks)} chunks")
```

### 설정 가능 파라미터

- **language**: 프로그래밍 언어 (py, js, java 등)
- **chunk_size**: 청크 최대 크기 (기본 500)
- **overlap**: 청크 간 중복 크기 (기본 50)

## 📚 참고 자료

### 관련 파일
- `core/rag/batch/file_scanner.py` - 파일 스캐너
- `core/rag/batch/batch_processor.py` - 배치 프로세서
- `core/rag/batch/progress_tracker.py` - 진행 추적기
- `core/rag/batch/batch_uploader.py` - 통합 업로더
- `core/rag/chunking/code_chunker.py` - 코드 청킹
- `examples/batch_upload_example.py` - 사용 예시

### Python 라이브러리
- `concurrent.futures.ThreadPoolExecutor` - 병렬 처리
- `pathlib.Path` - 파일 경로 처리
- `langchain.text_splitter.RecursiveCharacterTextSplitter` - 코드 청킹

---

**작성일**: 2024
**Phase**: 4/7 완료
**다음 단계**: Phase 5 (Topic 관리 UI)
**상태**: ✅ 완료 (UI 제외)
