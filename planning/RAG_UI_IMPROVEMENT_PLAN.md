# RAG 시스템 개선 작업 계획서

## 📋 개요

RAG(Retrieval-Augmented Generation) 시스템의 사용성과 성능을 개선하기 위한 4가지 핵심 작업

**작성일**: 2024-01-XX  
**예상 소요 시간**: 약 1시간 30분  
**난이도**: 중급

---

## 🎯 작업 우선순위

| 순위 | 작업명 | 난이도 | 예상 시간 | 상태 |
|------|--------|--------|-----------|------|
| 1 | 벡터DB 자동 정리 | ⭐ 쉬움 | 10분 | 📝 계획 |
| 2 | 비동기 처리 개선 | ⭐ 쉬움 | 5분 | 📝 계획 |
| 3 | 외장 임베딩 모델 | ⭐⭐ 중간 | 30분 | 📝 계획 |
| 4 | RAG 설정 UI 개선 | ⭐⭐⭐ 복잡 | 40분 | 📝 계획 |

---

## ✅ 우선순위 1: 벡터DB 수동 최적화 버튼

### 📌 목표
사용자가 필요할 때 클릭하여 삭제된 벡터 데이터를 물리적으로 정리할 수 있는 버튼 제공

### 🔍 현재 문제점
- 문서/토픽 삭제 시 논리적 삭제만 수행 (마킹만 함)
- 삭제된 데이터가 디스크에 계속 남아있어 공간 낭비
- 수동으로 정리할 방법이 없음

### 💡 해결 방안

#### 1. UI 버튼 위치
```
┌─────────────────────────────────────────────────┐
│  📚 RAG Document Management                     │
├─────────────────────────────────────────────────┤
│  [🧹 OPTIMIZE DB]  [📁 NEW TOPIC]  [📤 UPLOAD]  │  ← 맨 앞에 위치
│  ...                                            │
└─────────────────────────────────────────────────┘
```

#### 2. 버튼 클릭 시 동작
```python
def _on_optimize_db(self):
    """벡터DB 최적화 (비동기)"""
    reply = QMessageBox.question(
        self, "DB 최적화",
        "삭제된 데이터를 물리적으로 정리합니다.\n시간이 걸릴 수 있습니다. 계속하시겠습니까?"
    )
    if reply == QMessageBox.StandardButton.Yes:
        self._start_optimize_worker()
```

#### 3. 백그라운드 Worker 스레드
```python
class OptimizeWorker(QThread):
    finished = pyqtSignal(dict)  # stats
    error = pyqtSignal(str)
    
    def run(self):
        # compact_files() → cleanup_old_versions() → optimize()
        # 진행 상황 로깅
        pass
```

#### 4. 진행 다이얼로그
```
┌─────────────────────────────────────┐
│  🧹 벡터DB 최적화 중...             │
├─────────────────────────────────────┤
│                                     │
│  ⏳ 삭제된 데이터 정리 중...        │
│                                     │
│  [━━━━━━━━━━━━━━━━━━━━━━━━━━━━]   │
│                                     │
│  잠시만 기다려주세요...             │
│                                     │
└─────────────────────────────────────┘
```

### 📁 수정 파일
- `ui/rag/rag_management_window.py`
  - 툴바에 "🧹 OPTIMIZE DB" 버튼 추가 (맨 앞)
  - `_on_optimize_db()` 메서드 추가
  - `OptimizeWorker` 클래스 추가
  - 진행 다이얼로그 표시

- `core/rag/storage/rag_storage_manager.py`
  - `optimize_vector_db()` 메서드 추가 (public)

- `core/rag/vector_store/lancedb_store.py`
  - `optimize()` 메서드 확인 (이미 존재)

### ✅ 완료 조건
- [ ] 툴바 맨 앞에 "🧹 OPTIMIZE DB" 버튼 표시
- [ ] 버튼 클릭 시 확인 다이얼로그 표시
- [ ] 백그라운드 Worker로 비동기 실행
- [ ] 진행 중 다이얼로그 표시
- [ ] 완료 후 결과 메시지 표시
- [ ] UI 블로킹 없음 확인

---

## ✅ 우선순위 2: RAG 관리 메뉴 비동기 처리 개선

### 📌 목표
메뉴 클릭 시 화면 멈춤 현상 완전 제거

### 🔍 현재 상태
- `_load_topics()` 메서드가 이미 Worker 스레드로 비동기 처리됨 ✅
- 초기화(`_lazy_init`)도 Worker 내부에서 실행됨 ✅

### 💡 개선 사항
로딩 중 시각적 피드백만 개선하면 됨

```python
# 로딩 중 표시
loading_item = QTreeWidgetItem(["⏳ 토픽 로딩 중..."])
self.topic_tree.addTopLevelItem(loading_item)
```

### 📁 수정 파일
- `ui/rag/rag_management_window.py`
  - 로딩 메시지 개선 (이미 구현됨)

### ✅ 완료 조건
- [x] 이미 비동기 처리 완료
- [ ] 로딩 중 스피너 또는 애니메이션 추가 (선택사항)

---

## ✅ 우선순위 3: 외장 임베딩 모델 등록 및 사용

### 📌 목표
사용자가 화면에서 직접 임베딩 모델을 등록하고 선택할 수 있도록 구현

### 🔍 현재 문제점
- 기본 모델만 사용 가능 (dragonkue-KoEn-E5-Tiny)
- 사용자 정의 모델 사용 불가
- 설정 파일 직접 수정 필요

### 💡 해결 방안

#### 1. 지원 임베딩 모델 타입
| 타입 | 설명 | 필수 정보 |
|------|------|-----------|
| **Local (HuggingFace)** | 로컬 모델 | 모델 경로, 차원 |
| **OpenAI** | OpenAI API | API 키, 모델명 |
| **Google** | Google API | API 키, 모델명 |
| **Custom** | 사용자 정의 | 구현 필요 |

#### 2. UI 구성

##### 2-1. RAG 설정 다이얼로그 (임베딩 모델 탭)
```
┌─────────────────────────────────────────────┐
│  ⚙️ RAG 설정                                │
├─────────────────────────────────────────────┤
│  [📊 임베딩 모델] [✂️ 청킹 전략] [🔍 검색]  │
├─────────────────────────────────────────────┤
│                                             │
│  📊 등록된 임베딩 모델                      │
│  ┌─────────────────────────────────────┐   │
│  │ ● dragonkue-KoEn-E5-Tiny (384차원) │   │
│  │   openai-small (1536차원)           │   │
│  │   google-embedding-001 (768차원)    │   │
│  │   my-custom-model (768차원)         │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  현재 사용 중: dragonkue-KoEn-E5-Tiny       │
│                                             │
│  [➕ 새 모델 추가]  [✏️ 편집]  [🗑️ 삭제]    │
│                                             │
│                                             │
│                       [취소]  [저장]        │
└─────────────────────────────────────────────┘
```

##### 2-2. 모델 추가 다이얼로그
```
┌─────────────────────────────────────────────┐
│  ➕ 임베딩 모델 추가                        │
├─────────────────────────────────────────────┤
│                                             │
│  모델 이름:                                 │
│  ┌─────────────────────────────────────┐   │
│  │ my-custom-model                     │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  모델 타입:                                 │
│  ┌─────────────────────────────────────┐   │
│  │ ▼ Local (HuggingFace)               │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  모델 경로:                                 │
│  ┌─────────────────────────────────┐ [📁]  │
│  │ /Users/user/models/my-model     │       │
│  └─────────────────────────────────┘       │
│                                             │
│  임베딩 차원:                               │
│  ┌─────────────────────────────────────┐   │
│  │ 768                                 │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ☑ 캐시 사용                                │
│                                             │
│                       [취소]  [저장]        │
└─────────────────────────────────────────────┘
```

#### 3. 데이터 저장 형식 (rag_config.json)
```json
{
  "embedding": {
    "current": "dragonkue-KoEn-E5-Tiny",
    "models": {
      "dragonkue-KoEn-E5-Tiny": {
        "type": "local",
        "model_path": "exp-models/dragonkue-KoEn-E5-Tiny",
        "dimension": 384,
        "enable_cache": true
      },
      "openai-small": {
        "type": "openai",
        "model": "text-embedding-3-small",
        "api_key": "sk-...",
        "dimension": 1536
      },
      "my-custom-model": {
        "type": "local",
        "model_path": "/Users/user/models/my-model",
        "dimension": 768,
        "enable_cache": true
      }
    }
  },
  "chunking": { ... },
  "retrieval": { ... }
}
```

#### 4. 구현 세부사항

##### 4-1. CustomEmbeddings 구현 (HuggingFace)
```python
class CustomEmbeddings(BaseEmbeddings):
    def __init__(self, model_path: str, dimension: int = 768, **kwargs):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_path)
        self._dimension = dimension
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()
    
    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text])[0].tolist()
```

##### 4-2. RAGConfigManager 확장
```python
class RAGConfigManager:
    def add_embedding_model(self, name: str, config: Dict):
        """새 임베딩 모델 추가"""
        if "embedding" not in self.config:
            self.config["embedding"] = {"models": {}}
        self.config["embedding"]["models"][name] = config
        self._save_config(self.config)
    
    def set_current_embedding_model(self, name: str):
        """현재 사용 모델 변경"""
        self.config["embedding"]["current"] = name
        self._save_config(self.config)
    
    def get_embedding_models(self) -> Dict:
        """등록된 모든 모델 조회"""
        return self.config.get("embedding", {}).get("models", {})
```

### 📁 수정/신규 파일

#### 신규 파일
- `ui/dialogs/embedding_model_dialog.py` (새 모델 추가/편집 다이얼로그)

#### 수정 파일
- `core/rag/embeddings/custom_embeddings.py`
  - HuggingFace SentenceTransformer 로드 구현
  
- `core/rag/embeddings/embedding_factory.py`
  - 다중 모델 지원 로직 추가
  
- `core/rag/config/rag_config_manager.py`
  - `add_embedding_model()` 메서드 추가
  - `set_current_embedding_model()` 메서드 추가
  - `get_embedding_models()` 메서드 추가
  - `delete_embedding_model()` 메서드 추가
  
- `ui/dialogs/rag_settings_dialog.py`
  - 임베딩 모델 관리 탭 추가

### ✅ 완료 조건
- [ ] 화면에서 새 모델 추가 가능
- [ ] 등록된 모델 목록 표시
- [ ] 현재 사용 중인 모델 선택 가능
- [ ] 모델 편집/삭제 가능
- [ ] rag_config.json에 자동 저장
- [ ] HuggingFace 로컬 모델 로드 성공

---

## ✅ 우선순위 4: RAG 설정 UI 전체 개선

### 📌 목표
사용자가 편하게 RAG 설정을 관리할 수 있는 직관적이고 아름다운 UI 제공

### 🔍 현재 상태
- ✅ 청킹 전략 선택: 업로드 시 콤보박스로 선택 가능
- ✅ Top-K 설정: rag_config.json에 존재
- ❌ 통합 설정 UI: 없음
- ❌ 임베딩 모델 관리: 없음 (우선순위 3에서 추가)

### 💡 개선 방안

#### 1. 탭 기반 설정 화면 구조
```
┌─────────────────────────────────────────────────────┐
│  ⚙️ RAG 설정                                        │
├─────────────────────────────────────────────────────┤
│  [📊 임베딩 모델] [✂️ 청킹 전략] [🔍 검색 설정]    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  (탭별 설정 내용)                                   │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                          [기본값 복원]              │
│                          [취소]  [저장]             │
└─────────────────────────────────────────────────────┘
```

#### 2. 탭 1: 📊 임베딩 모델 (우선순위 3 내용)
- 등록된 모델 목록 (QListWidget)
- 현재 사용 중인 모델 표시 (●)
- 추가/편집/삭제 버튼
- 모델 정보 표시 (타입, 차원, 경로)

#### 3. 탭 2: ✂️ 청킹 전략
```
┌─────────────────────────────────────────────────┐
│  기본 청킹 전략:                                │
│  ┌─────────────────────────────────────────┐   │
│  │ ● Sliding Window                        │   │
│  │ ○ Semantic                              │   │
│  │ ○ Code                                  │   │
│  │ ○ Markdown                              │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  💡 RAG 관리 메뉴에서 "Auto" 선택 시           │
│     이 기본 전략이 사용됩니다                   │
│                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                 │
│  📐 Sliding Window 설정:                        │
│  ┌─────────────────────────────────────────┐   │
│  │ Window Size:    [500_____] tokens       │   │
│  │ Overlap Ratio:  [0.2_____] (20%)        │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                 │
│  🧠 Semantic 설정:                              │
│  ┌─────────────────────────────────────────┐   │
│  │ Threshold Type: [▼ Percentile]         │   │
│  │ Threshold:      [95______] %            │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  💡 청킹 전략 설명:                             │
│  Sliding Window는 고정 크기로 텍스트를 나눕니다 │
│                                                 │
│  📌 사용 흐름:                                  │
│  1. 여기서 기본 전략 설정                       │
│  2. RAG 관리 메뉴에서 업로드 시                 │
│     - "Auto" 선택 → 기본 전략 사용             │
│     - 직접 선택 → 선택한 전략 사용             │
└─────────────────────────────────────────────────┘
```

#### 4. 탭 3: 🔍 검색 설정
```
┌─────────────────────────────────────────────────┐
│  🔍 검색 결과 개수 (Top-K):                     │
│  ┌─────────────────────────────────────────┐   │
│  │ [10___________] 개                      │   │
│  └─────────────────────────────────────────┘   │
│  💡 벡터 검색 시 반환할 문서 개수               │
│                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                 │
│  📤 배치 업로드 설정:                           │
│  ┌─────────────────────────────────────────┐   │
│  │ 최대 동시 작업: [4____] 개              │   │
│  │ 최대 파일 크기: [50___] MB              │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                 │
│  🚫 제외 패턴:                                  │
│  ┌─────────────────────────────────────────┐   │
│  │ node_modules                            │   │
│  │ .git                                    │   │
│  │ venv                                    │   │
│  │ __pycache__                             │   │
│  │ .DS_Store                               │   │
│  └─────────────────────────────────────────┘   │
│  [➕ 추가]  [➖ 제거]                           │
│                                                 │
│  💡 업로드 시 제외할 파일/폴더 패턴             │
└─────────────────────────────────────────────────┘
```

### 🎨 UI 개선 포인트

#### 1. 직관적인 디자인
- ✅ 각 설정 항목에 이모지/아이콘 사용
- ✅ 그룹별로 구분선(━━━) 사용
- ✅ 설명 텍스트 추가 (💡)
- ✅ 라디오 버튼으로 선택 명확화

#### 2. 사용자 경험
- ✅ 실시간 입력 검증 (빨간색 테두리)
- ✅ 도움말 툴팁 (마우스 오버)
- ✅ 기본값 복원 버튼
- ✅ 변경사항 자동 저장

#### 3. 접근성
- ✅ 큰 폰트 사용 (12pt 이상)
- ✅ 충분한 여백 (padding)
- ✅ 명확한 레이블
- ✅ 키보드 네비게이션 지원

### 📁 수정/신규 파일

#### 대폭 수정
- `ui/dialogs/rag_settings_dialog.py`
  - 탭 기반 UI로 전면 재설계
  - 3개 탭 구현 (임베딩/청킹/검색)
  - 실시간 검증 로직 추가
  - 기본값 복원 기능 추가

#### 연결
- `ui/rag/rag_management_window.py`
  - 툴바에 "⚙️ SETTINGS" 버튼 추가
  - 설정 다이얼로그 연결

### ✅ 완료 조건
- [ ] 3개 탭 모두 구현 완료
- [ ] 모든 설정 항목 표시
- [ ] 설정 변경 시 rag_config.json 자동 저장
- [ ] 기본값 복원 기능 동작
- [ ] 입력 검증 및 에러 표시
- [ ] 도움말 툴팁 추가
- [ ] 반응형 레이아웃 (창 크기 조절 대응)

---

## 📊 전체 파일 구조

### 신규 파일
```
ui/dialogs/
  └── embedding_model_dialog.py      # 임베딩 모델 추가/편집 다이얼로그
```

### 수정 파일
```
core/rag/
  ├── storage/
  │   └── rag_storage_manager.py     # 자동 정리 로직 추가
  ├── vector_store/
  │   └── lancedb_store.py           # 백그라운드 optimize 추가
  ├── config/
  │   └── rag_config_manager.py      # 다중 모델 관리 메서드 추가
  └── embeddings/
      ├── embedding_factory.py       # 다중 모델 지원
      └── custom_embeddings.py       # HuggingFace 구현

ui/
  ├── rag/
  │   └── rag_management_window.py   # 설정 메뉴 연결
  └── dialogs/
      └── rag_settings_dialog.py     # 전체 UI 재설계
```

---

## 🚀 구현 순서

### Phase 1: 백엔드 개선 (15분)
1. ✅ 우선순위 1: 벡터DB 자동 정리 (10분)
2. ✅ 우선순위 2: 비동기 처리 확인 (5분)

### Phase 2: 임베딩 모델 관리 (30분)
3. ✅ 우선순위 3: 외장 임베딩 모델 (30분)
   - CustomEmbeddings 구현 (10분)
   - RAGConfigManager 확장 (10분)
   - UI 다이얼로그 생성 (10분)

### Phase 3: UI 개선 (40분)
4. ✅ 우선순위 4: RAG 설정 UI 전체 개선 (40분)
   - 탭 1: 임베딩 모델 (10분)
   - 탭 2: 청킹 전략 (15분)
   - 탭 3: 검색 설정 (15분)

**총 예상 시간: 약 1시간 30분**

---

## 📝 테스트 체크리스트

### 우선순위 1: 벡터DB 수동 최적화
- [ ] 툴바에 "🧹 OPTIMIZE DB" 버튼 표시 (맨 앞)
- [ ] 버튼 클릭 시 확인 다이얼로그 표시
- [ ] 백그라운드 실행으로 UI 블로킹 없음 확인
- [ ] 진행 다이얼로그 표시 확인
- [ ] 완료 후 결과 메시지 확인
- [ ] 디스크 공간 실제 감소 확인

### 우선순위 2: 비동기 처리
- [ ] RAG 관리 메뉴 클릭 시 화면 멈춤 없음
- [ ] 로딩 중 메시지 표시 확인

### 우선순위 3: 외장 임베딩 모델
- [ ] 새 모델 추가 성공
- [ ] 모델 선택 변경 성공
- [ ] rag_config.json 저장 확인
- [ ] HuggingFace 모델 로드 성공
- [ ] 임베딩 생성 정상 동작

### 우선순위 4: RAG 설정 UI
- [ ] 3개 탭 모두 표시
- [ ] 모든 설정 항목 정상 표시
- [ ] 설정 변경 후 저장 성공
- [ ] 기본값 복원 동작 확인
- [ ] 입력 검증 동작 확인

---

## 🎯 성공 기준

### 기능적 요구사항
- ✅ 벡터DB 자동 정리로 디스크 공간 최적화
- ✅ 화면 멈춤 없는 부드러운 UX
- ✅ 사용자 정의 임베딩 모델 사용 가능
- ✅ 직관적이고 아름다운 설정 UI

### 비기능적 요구사항
- ✅ 코드 가독성 및 유지보수성
- ✅ SOLID 원칙 준수
- ✅ 에러 처리 및 로깅
- ✅ 사용자 피드백 제공

---

## 📚 참고 자료

### 관련 파일
- `core/rag/storage/rag_storage_manager.py`: RAG 스토리지 관리
- `core/rag/vector_store/lancedb_store.py`: LanceDB 벡터 스토어
- `core/rag/embeddings/embedding_factory.py`: 임베딩 팩토리
- `core/rag/config/rag_config_manager.py`: RAG 설정 관리
- `ui/rag/rag_management_window.py`: RAG 관리 윈도우
- `ui/dialogs/rag_settings_dialog.py`: RAG 설정 다이얼로그

### 기술 스택
- **PyQt6**: UI 프레임워크
- **LanceDB**: 벡터 데이터베이스
- **SentenceTransformers**: 임베딩 모델
- **SQLite**: 메타데이터 저장

---

## 📌 주의사항

### 1. 벡터DB 정리 시
- 백그라운드 실행 필수 (UI 블로킹 방지)
- 정리 중 에러 발생 시 로그만 남기고 계속 진행
- 정리 실패해도 앱 동작에 영향 없도록

### 2. 임베딩 모델 변경 시
- 기존 벡터 데이터와 호환성 없음 경고
- 모델 변경 시 재임베딩 필요 안내
- 차원이 다른 모델 선택 시 경고

### 3. UI 설정 변경 시
- 변경사항 즉시 저장 (자동 저장)
- 잘못된 입력 시 즉시 피드백
- 기본값 복원 시 확인 다이얼로그

---

**작성자**: Amazon Q  
**검토 필요**: 사용자 승인 후 구현 시작
