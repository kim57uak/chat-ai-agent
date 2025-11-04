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

**검토 후 승인되면 Phase 0부터 순차적으로 진행하겠습니다!** 🚀
