# RAG Topic Management - Phase 5 완료

## ✅ 완료된 작업

### 1. Topic Dialog
**파일**: `ui/rag/topic_dialog.py`

#### 기능
- 토픽 생성/편집
- 부모 토픽 선택
- 이름, 설명 입력

#### 사용 예시
```python
from ui.rag.topic_dialog import TopicDialog

dialog = TopicDialog(storage_manager, parent_topics=topics)
dialog.topic_saved.connect(lambda t: print(f"Saved: {t['name']}"))
dialog.exec()
```

### 2. Topic Tree Widget
**파일**: `ui/rag/topic_tree_widget.py`

#### 기능
- 계층적 토픽 트리 표시
- 문서 수 표시
- 컨텍스트 메뉴 (편집/삭제)
- 토픽 선택 시그널

#### 사용 예시
```python
from ui.rag.topic_tree_widget import TopicTreeWidget

tree = TopicTreeWidget()
tree.load_topics(topics)
tree.topic_selected.connect(lambda id: print(f"Selected: {id}"))
```

### 3. RAG Management Window
**파일**: `ui/rag/rag_management_window.py`

#### 레이아웃
```
┌─────────────────────────────────────────────────────┐
│ [📁 New Topic] [📤 Upload Files] [📁 Upload Folder] │
├──────────┬────────────────────┬─────────────────────┤
│ Topics   │ Documents          │ Preview             │
│ (30%)    │ (40%)              │ (30%)               │
│          │                    │                     │
│ ├─ AI    │ file1.txt (5)      │ Document: file1.txt │
│ │  ├─ML  │ file2.py (10)      │                     │
│ │  └─NLP │ file3.md (3)       │ Chunks: 5           │
│ └─ Web   │                    │ Strategy: sliding   │
│          │                    │                     │
└──────────┴────────────────────┴─────────────────────┘
```

#### 주요 기능
- ✅ 토픽 생성/편집/삭제
- ✅ 토픽 선택 시 문서 목록 표시
- ✅ 파일 업로드 (개별)
- ✅ 폴더 업로드 (배치)
- ✅ 문서 미리보기

### 4. 통합 워크플로우

#### 토픽 생성
```
사용자 → [New Topic] 버튼
    ↓
TopicDialog 표시
    ↓
이름, 부모, 설명 입력
    ↓
[Save] 클릭
    ↓
storage.create_topic()
    ↓
트리 새로고침
```

#### 폴더 업로드
```
사용자 → 토픽 선택 → [Upload Folder] 버튼
    ↓
폴더 선택 다이얼로그
    ↓
BatchUploader.upload_folder()
    ↓
진행 상황 표시
    ↓
완료 메시지
    ↓
문서 목록 새로고침
```

#### 토픽 삭제 (배치 처리 + 벡터 최적화)
```
사용자 → 토픽 우클릭 → [Delete]
    ↓
확인 다이얼로그
    ↓
storage.delete_topic(progress_callback)
    ↓
100개 문서씩 배치 삭제:
  - SQLite 문서 삭제 → commit
  - LanceDB 벡터 삭제 (compact 없이)
  - 진행 상황 콜백 호출
    ↓
마지막에 한 번만:
  - cleanup_old_versions(older_than=1μs, delete_unverified=True)
  - compact_files()
    ↓
트리 새로고침
```

## 🎨 UI 구성 요소

### TopicDialog
- QLineEdit: 토픽 이름
- QComboBox: 부모 토픽 선택
- QTextEdit: 설명
- QPushButton: Save/Cancel

### TopicTreeWidget
- QTreeWidget: 계층적 트리
- 컬럼: [Topics, Documents]
- 컨텍스트 메뉴: Edit, Delete

### RAGManagementWindow
- QSplitter: 3분할 레이아웃
- TopicTreeWidget: 왼쪽
- QListWidget: 중간 (문서 목록)
- QTextEdit: 오른쪽 (미리보기)

## 🚀 실행 방법

### 데모 실행
```bash
source venv/bin/activate
python examples/rag_ui_demo.py
```

### 메인 앱에 통합
```python
from ui.rag.rag_management_window import RAGManagementWindow

# 메뉴에 추가
rag_action = QAction("RAG Management", self)
rag_action.triggered.connect(self._open_rag_management)

def _open_rag_management(self):
    window = RAGManagementWindow(self.storage, self.embeddings)
    window.show()
```

## 📝 사용 시나리오

### 시나리오 1: 새 프로젝트 추가
1. [New Topic] 클릭
2. 이름: "My Project" 입력
3. [Save] 클릭
4. 토픽 선택
5. [Upload Folder] 클릭
6. 프로젝트 폴더 선택
7. 업로드 완료 대기

### 시나리오 2: 계층 구조 생성
1. 루트 토픽 생성: "Programming"
2. 하위 토픽 생성: "Python" (부모: Programming)
3. 하위 토픽 생성: "Django" (부모: Python)
4. 각 토픽에 문서 업로드

### 시나리오 3: 토픽 관리
1. 토픽 우클릭
2. [Edit] 선택 → 이름/설명 수정
3. [Delete] 선택 → 확인 후 삭제

## 🎯 Phase 1-5 통합 예시

```python
from core.rag.storage.rag_storage_manager import RAGStorageManager
from core.rag.embeddings.embedding_factory import EmbeddingFactory
from core.rag.chunking.chunking_factory import ChunkingFactory
from core.rag.batch.batch_uploader import BatchUploader
from core.rag.config.rag_config_manager import RAGConfigManager
from ui.rag.rag_management_window import RAGManagementWindow

# 1. 설정 로드
config_manager = RAGConfigManager()

# 2. 임베딩 모델 (Phase 2)
embedding_config = config_manager.get_embedding_config()
embedding_type = embedding_config.pop('type')
embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)

# 3. 스토리지 (Phase 1)
storage = RAGStorageManager()

# 4. 토픽 생성 (Phase 5 UI)
topic_id = storage.create_topic(name="AI Research")

# 5. 청킹 전략 (Phase 3)
chunker = ChunkingFactory.get_strategy_for_file("paper.pdf")

# 6. 배치 업로드 (Phase 4)
batch_config = config_manager.get_batch_config()
uploader = BatchUploader(storage, embeddings, batch_config)
stats = uploader.upload_folder("/path/to/papers", topic_id)

# 7. UI 표시 (Phase 5)
window = RAGManagementWindow(storage, embeddings)
window.show()
```

## 🔧 성능 최적화

### 벡터 DB 삭제 최적화 (3단계 프로세스)
**문제**: LanceDB의 `.lance` 파일이 삭제 후에도 남아있음

**원인**: 
- `delete()`: 논리적 삭제만 수행 (삭제 마크만 표시)
- `cleanup_old_versions()`: 시간 제한으로 방금 삭제한 데이터는 정리 안 됨
- `optimize()`: 물리적 삭제를 수행하는 메서드가 호출되지 않음

**해결책 - 3단계 최적화 프로세스**:
```python
from datetime import timedelta

# 1. 배치로 삭제 (optimize 없이)
for doc_id in doc_ids:
    table.delete(f"metadata['document_id'] = '{doc_id}'")

# 2. 마지막에 한 번만 3단계 최적화
# Step 1: 파편화된 파일 병합
table.compact_files()

# Step 2: 삭제된 버전 정리 (시간 제한 없음)
table.cleanup_old_versions(
    older_than=timedelta(seconds=0),  # 시간 제한 없이 모든 삭제 버전 정리
    delete_unverified=True  # 미검증 데이터도 삭제
)

# Step 3: 물리적으로 삭제된 행 완전 제거 및 .lance 파일 재구성
table.optimize()
```

### 3단계 최적화 프로세스 상세

#### Step 1: compact_files()
- 파편화된 여러 `.lance` 파일들을 병합
- 읽기 성능 향상
- 파일 수 감소

#### Step 2: cleanup_old_versions()
- `older_than=timedelta(seconds=0)`: 시간 제한 없이 모든 삭제된 버전 정리
- `delete_unverified=True`: 7일 미만의 미검증 파일도 삭제
- 논리적으로 삭제된 데이터의 메타데이터 제거

#### Step 3: optimize()
- 물리적으로 삭제된 행을 완전히 제거
- `.lance` 파일 재구성 및 압축
- 디스크 공간 즉시 회수
- **가장 중요**: 이 단계가 없으면 파일이 남음

### 배치 삭제 전략
- **100개 단위**: SQLite 문서 + 벡터 삭제
- **커밋 시점**: 각 배치마다 SQLite commit
- **Optimize 시점**: 모든 삭제 완료 후 1회만 (3단계 프로세스)

### 적용 위치
- `core/rag/storage/rag_storage_manager.py`
  - `delete_topic()`: 토픽 삭제 시
  - `delete_document()`: 문서 삭제 시
- `core/rag/vector_store/lancedb_store.py`
  - `delete_by_document_id()`: 문서 ID로 삭제 시
  - `delete_by_topic_id()`: 토픽 ID로 삭제 시

### 성능 개선 효과
- ✅ 삭제 속도 향상 (optimize 오버헤드를 마지막에만 수행)
- ✅ 진행 상황 실시간 표시
- ✅ `.lance` 파일 완전 삭제 (물리적 제거)
- ✅ 디스크 공간 즉시 회수
- ✅ 파일 파편화 방지

## 🎯 다음 단계: Phase 6

### Phase 6: 메인 UI 통합 (1-2일)
- [ ] 메인 윈도우에 RAG 메뉴 추가
- [ ] 글래스모피즘 스타일 적용
- [ ] 문서 미리보기 개선
- [ ] 검색 기능 추가
- [ ] 진행 상황 다이얼로그

## 📚 참고 자료

### 관련 파일
- `ui/rag/topic_dialog.py` - 토픽 다이얼로그
- `ui/rag/topic_tree_widget.py` - 토픽 트리
- `ui/rag/rag_management_window.py` - 메인 윈도우
- `examples/rag_ui_demo.py` - 데모

### PyQt6 컴포넌트
- QTreeWidget: 계층적 트리
- QSplitter: 분할 레이아웃
- QDialog: 다이얼로그
- pyqtSignal: 시그널/슬롯

---

**작성일**: 2024
**Phase**: 5/7 완료
**다음 단계**: Phase 6 (메인 UI 통합)
**상태**: ✅ 완료 (기본 UI)
