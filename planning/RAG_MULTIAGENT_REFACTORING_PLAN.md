# 🚀 RAG & Multi-Agent 시스템 리팩토링 계획

## 📋 작업 개요

**목표:** LangChain Multi-Agent 기반 RAG 시스템 구축 (기존 기능 유지 + 확장)

**핵심 원칙:**
- SOLID 원칙 준수
- Strategy, Factory, Observer 패턴 적용
- 벡터DB/임베딩 모델 교체 용이
- 기존 MCP 도구 기능 완전 유지
- **LangChain 100% 적용** (모든 LLM 호출, Agent, Tool 통합)

---

## 🔗 LangChain 100% 적용 전략

### 핵심 방침
**모든 AI 관련 기능은 LangChain을 통해서만 구현합니다.**

### LangChain 통합 원칙
1. **No Direct API Calls**: OpenAI, Google API 직접 호출 금지
2. **LangChain Tools Only**: 모든 도구는 BaseTool 상속
3. **LangChain Chains**: 복잡한 로직은 Chain으로 구성
4. **LangChain Memory**: 대화 히스토리는 Memory 클래스 사용
5. **LangChain Callbacks**: 스트리밍, 로깅은 Callback 사용

### LangChain 아키텍처

```
┌─────────────────────────────────────────────────────┐
│           LangChain Core Layer                      │
├─────────────────────────────────────────────────────┤
│  LLMs: ChatOpenAI, ChatGoogleGenerativeAI, etc.    │
│  Agents: OpenAI Functions, ReAct, Pandas           │
│  Tools: MCP Wrapper, RAG, SQL, Python              │
│  Chains: ConversationalRetrievalChain, etc.        │
│  Memory: ConversationBufferMemory                   │
│  Prompts: ChatPromptTemplate                        │
│  Callbacks: StreamingCallback, LoggingCallback      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│         Application Layer (기존 코드)                │
├─────────────────────────────────────────────────────┤
│  UI: PyQt6 Interface                                │
│  Config: Settings Management                        │
│  Security: Encryption Layer                         │
│  Session: Database Management                       │
└─────────────────────────────────────────────────────┘
```

---

## 🔍 기존 DB 구조 영향도 분석

### 현재 DB 구조 (변경 금지)

```python
# EncryptedDatabase - 세션 테이블
- title: TEXT (평문) - 검색/정렬용
- topic_category: BLOB (암호화)
- model_used: BLOB (암호화)

# 메시지 테이블
- content: BLOB (암호화)
- content_html: BLOB (암호화)
- tool_calls: BLOB (암호화)
```

### 영향도 분석 결과

| 컴포넌트 | 변경 필요 | 영향도 | 비고 |
|---------|---------|--------|------|
| **EncryptedDatabase** | ❌ 없음 | 0% | 그대로 사용 |
| **세션/메시지 관리** | ❌ 없음 | 0% | 기존 필드 활용 |
| **토큰 추적** | ❌ 없음 | 0% | 기존 로직 사용 |
| **LangChain Adapter** | ✅ 신규 | 10% | 래퍼만 추가 |
| **형식 변환** | ✅ 확장 | 5% | Dict ↔ BaseMessage |
| **RAG DB** | ✅ 신규 | 0% | 완전 분리 |

**총 영향도: 15%** (Adapter 추가만)

### 필요 작업

**1. LangChain Memory Adapter (신규 파일)**
```python
# core/chat/langchain_memory_adapter.py
class EncryptedChatMessageHistory(BaseChatMessageHistory):
    """기존 EncryptedDatabase를 LangChain Memory로 래핑"""
    
    def __init__(self, session_id: int, encrypted_db):
        self.session_id = session_id
        self.db = encrypted_db
    
    def add_message(self, message: BaseMessage):
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        self.db.add_message(self.session_id, role, message.content)
    
    @property
    def messages(self) -> List[BaseMessage]:
        msgs = self.db.get_messages(self.session_id)
        return [self._to_langchain_message(m) for m in msgs]
```

**2. 메시지 변환 유틸 (기존 파일 확장)**
```python
# core/chat/message_converter.py
class MessageConverter:
    @staticmethod
    def dict_to_langchain(msg_dict: Dict) -> BaseMessage:
        if msg_dict["role"] == "user":
            return HumanMessage(content=msg_dict["content"])
        return AIMessage(content=msg_dict["content"])
```

---

## 📊 Phase 0: LangChain 전환 (선행 작업, 1.5일)

### 0.1 LangChain Memory Adapter (0.5일)
- ✅ `core/chat/langchain_memory_adapter.py` 신규 생성
- ✅ 기존 EncryptedDatabase 래핑
- ✅ Dict ↔ BaseMessage 변환

### 0.2 메시지 변환 유틸 (0.5일)
- ✅ `core/chat/message_converter.py` 확장
- ✅ LangChain 형식 지원 추가

### 0.3 통합 테스트 (0.5일)
- ✅ 기존 DB 읽기/쓰기 테스트
- ✅ LangChain Memory 호환성 검증
- ✅ 암호화/복호화 정상 동작 확인

---

## 📊 Phase 1: 핵심 인프라 구축 (1-2일)

### 1.1 벡터 DB 추상화
```python
# core/rag/vector_store/base_vector_store.py
class BaseVectorStore(ABC):
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]
    @abstractmethod
    def search(self, query: str, k: int, filter: Dict) -> List[Document]
```

**구현체:** `lancedb_store.py`

### 1.2 임베딩 모델 추상화
```python
# core/rag/embeddings/base_embeddings.py
class BaseEmbeddings(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]
    @abstractmethod
    def embed_query(self, text: str) -> List[float]
```

**구현체:** `korean_embeddings.py` (dragonkue-KoEn-E5-Tiny)

### 1.3 메타데이터 추출 시스템
```python
METADATA_SCHEMA = {
    # 자동 추출
    "filename": str, "file_type": str, "upload_date": datetime,
    
    # AI 분석
    "doc_type": str, "summary": str, "topics": List[str],
    
    # 사용자 입력
    "category": str, "tags": List[str], "department": str
}
```

---

## 📊 Phase 2: 문서 처리 파이프라인 (2-3일)

### 2.1 문서 로더 시스템
- PDF, Word, Excel, CSV, TXT, PPT, Json
- 이미지 (OCR)
- 비정형 Excel (LLM 스키마 추론)

### 2.2 암호화 레이어
```
원본 문서 → 청크 분할 → 벡터화 → 원본 텍스트 암호화 → 저장
                                ↓
                        벡터 (평문, LanceDB)
```

### 2.3 청크 관리 시스템
- RecursiveCharacterTextSplitter
- 청크 메타데이터 관리
- 청크 CRUD 인터페이스

---

## 📊 Phase 3: Multi-Agent 시스템 (3-4일)

### 3.1 Agent 구현 (모두 LangChain 기반)

1. **RAGAgent** - ConversationalRetrievalChain
2. **PandasAgent** - create_pandas_dataframe_agent
3. **SQLAgent** - create_sql_agent
4. **PythonREPLAgent** - PythonREPLTool
5. **FileManagementAgent** - FileManagementToolkit
6. **MCPAgent** - BaseTool 래핑 (기존 MCP 도구)

### 3.2 Multi-Agent 오케스트레이터
```python
class ExecutionStrategy(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    HYBRID = "hybrid"
```

**Agent 선택:** LangChain LLM 기반 (하드코딩 금지)

### 3.3 하이브리드 분석 시스템
```
사용자 질의 → 질의 분석 (LLM) → Agent 선택 → 실행 → 결과 통합
```

---

## 📊 Phase 4: RAG 채팅 프로세서 (2일)

### 4.1 RAG 채팅 프로세서
```python
class RAGChatProcessor:
    def __init__(self, llm, vectorstore, mcp_client):
        self.retriever = MultiQueryRetriever.from_llm(...)
        self.chain = ConversationalRetrievalChain.from_llm(...)
        self.orchestrator = MultiAgentOrchestrator(...)
```

### 4.2 채팅 모드 통합
```python
class ChatMode(Enum):
    SIMPLE = "simple"  # LLM만
    TOOL = "tool"      # MCP 도구만
    RAG = "rag"        # RAG + Multi-Agent + MCP (통합)
```

---

## 📊 Phase 5: UI 구현 (2-3일)

### 5.1 RAG 문서 관리 UI
- 문서 업로드 (메타데이터 입력)
- 문서 목록 (필터링, 검색)
- 청크 뷰어/삭제
- 글래스모피즘 스타일 (theme.json 활용 - 기존 디자인 참고)

### 5.2 RAG 설정 UI
- 벡터 DB 선택
- 임베딩 모델 선택
- 청크 크기/오버랩
- 검색 설정

### 5.3 채팅 모드 선택 UI
- 모드 선택 콤보박스
- RAG 필터 입력
- Agent 선택 (자동/수동)

---

## 📊 Phase 6: 통합 및 테스트 (2-3일)

### 6.1 통합 테스트
1. 문서 업로드 → 벡터화 → 검색
2. RAG 모드 채팅
3. Multi-Agent 호출
4. 메타데이터 필터링
5. 암호화/복호화

### 6.2 기존 기능 호환성 검증
- ✅ MCP 도구 동작
- ✅ 일반/도구 채팅 모드
- ✅ 대화 히스토리
- ✅ 토큰 추적
- ✅ 세션 관리

---

## 📊 Phase 7: 최적화 및 배포 (1-2일)

### 7.1 성능 최적화
- 벡터 검색 속도 최적화
- 임베딩 캐싱
- Agent 실행 병렬화

### 7.2 에러 핸들링
- Agent 에러 처리
- Fallback 전략
- 사용자 친화적 에러 메시지

### 7.3 로깅 및 모니터링
- RAG 검색 로그
- Agent 실행 로그
- 성능 메트릭

---

## 📁 최종 디렉토리 구조

```
core/
├── rag/
│   ├── vector_store/      # LanceDB
│   ├── embeddings/        # 한국어 임베딩
│   ├── metadata/          # 메타데이터 추출
│   ├── loaders/           # 문서 로더
│   ├── security/          # 암호화
│   ├── chunking/          # 청크 관리
│   └── retrieval/         # Multi-Query Retriever
├── agents/
│   ├── base_agent.py
│   ├── rag_agent.py
│   ├── pandas_agent.py
│   ├── sql_agent.py
│   ├── python_repl_agent.py
│   ├── file_management_agent.py
│   ├── mcp_agent.py
│   ├── multi_agent_orchestrator.py
│   └── hybrid_analyzer.py
├── chat/
│   ├── langchain_memory_adapter.py  # 신규
│   ├── rag_chat_processor.py        # 신규
│   └── chat_mode_manager.py
ui/
├── rag/
│   ├── document_manager_dialog.py
│   ├── chunk_viewer_dialog.py
│   └── rag_settings_dialog.py
```

---

## 🎯 작업 순서 요약

### Week 1 (5일)
- Day 1: Phase 0 (LangChain Adapter)
- Day 2-3: Phase 1 (인프라)
- Day 4-5: Phase 2 (문서 처리)

### Week 2 (5일)
- Day 1-3: Phase 3 (Multi-Agent)
- Day 4-5: Phase 4 (RAG 프로세서)

### Week 3 (5일)
- Day 1-3: Phase 5 (UI)
- Day 4-5: Phase 6 (통합 테스트)

### Week 4 (2일)
- Day 1-2: Phase 7 (최적화 및 배포)

**총 소요 시간: 17일 (약 3.5주)**

---

## ⚠️ 주의사항

### 기존 기능 유지
- ✅ MCP 도구 완전 호환
- ✅ 일반/도구 채팅 모드 유지
- ✅ 대화 히스토리 유지
- ✅ 토큰 추적 유지
- ✅ 세션 관리 유지
- ✅ 암호화 로직 유지

### 점진적 마이그레이션
- 기존 코드 삭제 금지
- 새 기능은 별도 모듈로 추가
- 기존 기능과 병렬 운영
- 충분한 테스트 후 전환

---

## 📊 성공 지표

### 기능적 지표
- ✅ 모든 문서 형식 지원
- ✅ 메타데이터 필터링 정확도 > 90%
- ✅ Multi-Agent 성공률 > 95%
- ✅ 기존 기능 100% 호환

### 성능 지표
- ✅ 벡터 검색 < 100ms (10,000 문서)
- ✅ 문서 업로드 < 5초 (10MB)
- ✅ Agent 실행 < 30초
- ✅ 메모리 사용 < 2GB

---

---

## 📊 현재 구현 상태

### ✅ 완료된 Phase

| Phase | 상태 | 완료율 | 비고 |
|-------|------|--------|------|
| **Phase 0** | ✅ 완료 | 100% | LangChain Memory Adapter, 메시지 변환 |
| **Phase 1** | ✅ 완료 | 100% | 벡터DB, 임베딩, 메타데이터 |
| **Phase 2** | ✅ 완료 | 100% | 문서 로더, 청크 관리, 암호화 |
| **Phase 3** | ⚠️ 부분 | 50% | RAG/MCP Agent 완료, 4개 Agent 미구현 |
| **Phase 4** | ✅ 완료 | 100% | RAG 채팅 프로세서, 모드 관리 |
| **Phase 5** | ⚠️ 부분 | 80% | 문서 관리/설정 UI 완료, 청크 뷰어 미구현 |
| **Phase 6** | ❌ 미착수 | 0% | 통합 테스트 필요 |
| **Phase 7** | ❌ 미착수 | 0% | 최적화 필요 |

**전체 진행률: 약 70%**

---

## ❌ 미구현 기능 목록

### Phase 3: Multi-Agent 시스템 (50% 완료)

#### ✅ 구현 완료
- `core/agents/base_agent.py` - Agent 추상화
- `core/agents/rag_agent.py` - RAG Agent
- `core/agents/mcp_agent.py` - MCP 도구 래핑
- `core/agents/multi_agent_orchestrator.py` - Agent 오케스트레이터
- `core/agents/hybrid_analyzer.py` - 쿼리 라우팅

#### ❌ 미구현
1. **PandasAgent** (`core/agents/pandas_agent.py`)
   - LangChain `create_pandas_dataframe_agent` 사용
   - CSV/Excel 데이터 분석
   - 데이터 시각화 지원

2. **SQLAgent** (`core/agents/sql_agent.py`)
   - LangChain `create_sql_agent` 사용
   - 데이터베이스 쿼리 실행
   - 스키마 자동 인식

3. **PythonREPLAgent** (`core/agents/python_repl_agent.py`)
   - LangChain `PythonREPLTool` 사용
   - Python 코드 실행
   - 보안 샌드박스 적용

4. **FileManagementAgent** (`core/agents/file_management_agent.py`)
   - LangChain `FileManagementToolkit` 사용
   - 파일 읽기/쓰기/삭제
   - 디렉토리 관리

### Phase 5: UI 구현 (80% 완료)

#### ✅ 구현 완료
- `ui/dialogs/rag_document_manager.py` - 문서 업로드/관리
- `ui/dialogs/rag_settings_dialog.py` - RAG 설정
- 채팅 모드 선택 UI

#### ❌ 미구현
5. **청크 뷰어 UI** (`ui/dialogs/chunk_viewer_dialog.py`)
   - 문서별 청크 목록 표시
   - 청크 내용 미리보기
   - 개별 청크 삭제
   - 청크 메타데이터 편집

### Phase 1: 핵심 인프라 (추가 기능)

#### ❌ 미구현
6. **Multi-Query Retriever** (`core/rag/retrieval/`)
   - LangChain `MultiQueryRetriever` 사용
   - 쿼리 재작성으로 검색 품질 향상
   - 다중 쿼리 병렬 실행

### Phase 6: 통합 테스트 (0% 완료)

#### ❌ 미구현
7. **통합 테스트 스크립트**
   - 문서 업로드 → 벡터화 → 검색 테스트
   - Multi-Agent 호출 테스트
   - 메타데이터 필터링 테스트
   - 암호화/복호화 테스트
   - 성능 벤치마크

### Phase 7: 최적화 (0% 완료)

#### ❌ 미구현
8. **임베딩 캐싱**
   - 중복 임베딩 방지
   - 메모리/디스크 캐시
   - TTL 기반 캐시 무효화

9. **Agent 병렬 실행**
   - 독립적인 Agent 동시 실행
   - 결과 병합 로직
   - 타임아웃 관리

10. **성능 모니터링**
    - 벡터 검색 속도 측정
    - Agent 실행 시간 추적
    - 메모리 사용량 모니터링

---

## 🎯 우선순위별 작업 목록

### 🔴 High Priority (핵심 기능) - 즉시 구현 필요

#### 1. PandasAgent (1일)
**중요도:** ⭐⭐⭐⭐⭐  
**이유:** CSV/Excel 데이터 분석은 필수 기능  
**작업:**
- `core/agents/pandas_agent.py` 생성
- LangChain `create_pandas_dataframe_agent` 통합
- 데이터프레임 로딩 및 분석
- 오케스트레이터에 등록

#### 2. SQLAgent (1일)
**중요도:** ⭐⭐⭐⭐⭐  
**이유:** 데이터베이스 쿼리는 비즈니스 필수  
**작업:**
- `core/agents/sql_agent.py` 생성
- LangChain `create_sql_agent` 통합
- MySQL/PostgreSQL/SQLite 지원
- 오케스트레이터에 등록

#### 3. 청크 뷰어 UI (0.5일)
**중요도:** ⭐⭐⭐⭐  
**이유:** 사용자가 RAG 결과를 확인/관리 필요  
**작업:**
- `ui/dialogs/chunk_viewer_dialog.py` 생성
- 청크 목록 표시
- 청크 삭제 기능
- 메타데이터 표시

### 🟡 Medium Priority (확장 기능) - 2주 내 구현

#### 4. PythonREPLAgent (0.5일)
**중요도:** ⭐⭐⭐  
**이유:** 고급 사용자를 위한 코드 실행  
**작업:**
- `core/agents/python_repl_agent.py` 생성
- 보안 샌드박스 적용
- 실행 결과 포맷팅

#### 5. FileManagementAgent (0.5일)
**중요도:** ⭐⭐⭐  
**이유:** 파일 시스템 작업 자동화  
**작업:**
- `core/agents/file_management_agent.py` 생성
- 안전한 파일 작업 구현
- 권한 체크

#### 6. Multi-Query Retriever (1일)
**중요도:** ⭐⭐⭐  
**이유:** RAG 검색 품질 향상  
**작업:**
- `core/rag/retrieval/` 디렉토리 생성
- `multi_query_retriever.py` 구현
- RAG 프로세서에 통합

#### 7. 통합 테스트 (1일)
**중요도:** ⭐⭐⭐⭐  
**이유:** 품질 보증 필수  
**작업:**
- `tests/integration/` 디렉토리 생성
- 주요 시나리오 테스트 작성
- CI/CD 통합

### 🟢 Low Priority (최적화) - 1개월 내 구현

#### 8. 임베딩 캐싱 (0.5일)
**중요도:** ⭐⭐  
**이유:** 성능 향상  
**작업:**
- 캐시 레이어 추가
- LRU 캐시 구현

#### 9. Agent 병렬 실행 (1일)
**중요도:** ⭐⭐  
**이유:** 응답 속도 향상  
**작업:**
- 병렬 실행 로직 구현
- 결과 병합 최적화

#### 10. 성능 모니터링 (0.5일)
**중요도:** ⭐⭐  
**이유:** 성능 분석 및 개선  
**작업:**
- 메트릭 수집 시스템
- 대시보드 UI

---

## 📅 다음 작업 계획

### Week 1: 핵심 Agent 구현
- **Day 1**: PandasAgent 구현 및 테스트
- **Day 2**: SQLAgent 구현 및 테스트
- **Day 3**: 청크 뷰어 UI 구현

### Week 2: 확장 기능
- **Day 1**: PythonREPLAgent + FileManagementAgent
- **Day 2**: Multi-Query Retriever
- **Day 3**: 통합 테스트 작성

### Week 3: 최적화
- **Day 1**: 임베딩 캐싱
- **Day 2**: Agent 병렬 실행
- **Day 3**: 성능 모니터링

---

**다음 작업: PandasAgent 구현부터 시작합니다!** 🚀
