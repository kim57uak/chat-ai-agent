# 🔧 RAG Mode 초기화 문제 해결

## 📋 문제 분석

### 발견된 문제
1. **RAG Processor 미초기화**: `ai_agent_v2.py`에서 RAG 모드 로직이 없음
2. **ChatModeManager 미사용**: 구현은 되어있지만 실제로 사용되지 않음
3. **모드 전환 메서드 없음**: RAG 모드로 전환하는 API가 없음

### 근본 원인
```python
# 기존 코드 (ai_agent_v2.py)
def _process_with_tools(self, user_input: str, ...):
    # 항상 ToolChatProcessor만 사용
    if not self.tool_processor:
        self.tool_processor = ToolChatProcessor(...)
    return self.tool_processor.process_message(...)
```

**문제**: RAG 모드 체크 로직이 없어서 항상 TOOL 모드로만 동작

---

## ✅ 해결 방법

### 1. ChatModeManager 통합 (ai_agent_v2.py)

#### 변경 사항
```python
# Before
self.simple_processor = SimpleChatProcessor(self.model_strategy)
self.tool_processor = None

# After
self.mode_manager = ChatModeManager(self.model_strategy)
self.simple_processor = SimpleChatProcessor(self.model_strategy)
self.tool_processor = None
self.rag_processor = None  # RAG 프로세서 추가

# RAG 관련 속성
self.vectorstore = None
self.mcp_client = None
```

### 2. 모드 설정 메서드 추가

```python
def set_chat_mode(self, mode: str):
    """채팅 모드 설정 (simple/tool/rag)"""
    try:
        chat_mode = ChatMode(mode)
        self.mode_manager.set_mode(chat_mode)
        self.logger.info(f"채팅 모드 변경: {mode}")
    except ValueError:
        self.logger.error(f"잘못된 채팅 모드: {mode}")

def set_vectorstore(self, vectorstore):
    """벡터 스토어 설정 (RAG용)"""
    self.vectorstore = vectorstore
    self.logger.info("벡터 스토어 설정됨")

def set_mcp_client(self, mcp_client):
    """MCP 클라이언트 설정 (RAG용)"""
    self.mcp_client = mcp_client
    self.logger.info("MCP 클라이언트 설정됨")
```

### 3. RAG 모드 처리 로직 추가

```python
def _should_use_tools(self, user_input: str) -> bool:
    # RAG 모드면 항상 RAG 프로세서 사용
    if self.mode_manager.current_mode == ChatMode.RAG:
        return True
    
    # 기존 로직...

def _process_with_tools(self, user_input: str, ...):
    # RAG 모드 체크
    if self.mode_manager.current_mode == ChatMode.RAG:
        processor = self.mode_manager.get_processor(
            mode=ChatMode.RAG,
            vectorstore=self.vectorstore,
            mcp_client=self.mcp_client,
            tools=self.tools
        )
        return processor.process_message(user_input, conversation_history)
    
    # TOOL 모드 (기존 로직)
    if not self.tool_processor:
        self.tool_processor = ToolChatProcessor(...)
    return self.tool_processor.process_message(...)
```

### 4. AIAgent 래퍼에 메서드 추가

```python
# core/ai_agent.py
def set_chat_mode(self, mode: str):
    """채팅 모드 설정 (simple/tool/rag)"""
    return self._agent_v2.set_chat_mode(mode)

def set_vectorstore(self, vectorstore):
    """벡터 스토어 설정 (RAG용)"""
    return self._agent_v2.set_vectorstore(vectorstore)

def set_mcp_client(self, mcp_client):
    """MCP 클라이언트 설정 (RAG용)"""
    return self._agent_v2.set_mcp_client(mcp_client)
```

---

## 🚀 사용 방법

### 기본 사용
```python
from core.ai_agent import AIAgent

# 1. Agent 초기화
agent = AIAgent(api_key="sk-...", model_name="gpt-4")

# 2. RAG 모드 설정
agent.set_chat_mode("rag")

# 3. 벡터 스토어 설정
from core.rag.vector_store.lancedb_store import LanceDBVectorStore
from core.rag.embeddings.korean_embeddings import KoreanEmbeddings

embeddings = KoreanEmbeddings()
vectorstore = LanceDBVectorStore(
    db_path="./data/lancedb",
    embeddings=embeddings
)
agent.set_vectorstore(vectorstore)

# 4. MCP 클라이언트 설정 (선택사항)
from mcp.servers.mcp import MCPClient
mcp_client = MCPClient()
agent.set_mcp_client(mcp_client)

# 5. RAG 채팅 실행
response, tools = agent.process_message("문서 요약해줘")
```

### UI 통합 (예정)
```python
# ui/main_window/main_window.py
def setup_rag_mode(self):
    """RAG 모드 설정"""
    # 벡터 스토어 초기화
    self.vectorstore = self._init_vectorstore()
    
    # Agent에 설정
    self.agent.set_chat_mode("rag")
    self.agent.set_vectorstore(self.vectorstore)
    self.agent.set_mcp_client(self.mcp_client)
```

---

## 📊 모드별 동작

| 모드 | 프로세서 | 사용 도구 | 용도 |
|------|---------|----------|------|
| **SIMPLE** | SimpleChatProcessor | 없음 | 일반 대화 |
| **TOOL** | ToolChatProcessor | MCP 도구 | 도구 사용 대화 |
| **RAG** | RAGChatProcessor | RAG + MCP + Multi-Agent | 문서 기반 대화 |

---

## ✅ 검증 방법

### 1. 모드 설정 확인
```python
agent.set_chat_mode("rag")
print(agent._agent_v2.mode_manager.current_mode)  # ChatMode.RAG
```

### 2. 프로세서 생성 확인
```python
# RAG 모드에서 메시지 처리
response, tools = agent.process_message("테스트")

# 로그 확인
# INFO: 채팅 모드 변경: rag
# INFO: 벡터 스토어 설정됨
# INFO: RAG 프로세서 사용
```

### 3. 에러 처리 확인
```python
# 벡터 스토어 없이 RAG 모드 사용
agent.set_chat_mode("rag")
response, tools = agent.process_message("테스트")
# 에러 메시지: "RAG 모드는 vectorstore가 필요합니다"
```

---

## 🎯 다음 단계

### 1. UI 통합 (High Priority)
- [ ] 메인 윈도우에 모드 선택 콤보박스 추가
- [ ] RAG 설정 다이얼로그 연동
- [ ] 모드별 UI 상태 표시

### 2. 에러 처리 강화
- [ ] 벡터 스토어 없을 때 fallback
- [ ] MCP 클라이언트 없을 때 경고
- [ ] 모드 전환 시 상태 검증

### 3. 테스트 작성
- [ ] 모드 전환 테스트
- [ ] RAG 프로세서 초기화 테스트
- [ ] 통합 테스트

---

## 📝 변경 파일 목록

### 수정된 파일
1. `core/ai_agent_v2.py` - RAG 모드 로직 추가
2. `core/ai_agent.py` - 래퍼 메서드 추가

### 신규 파일
1. `examples/rag_mode_example.py` - 사용 예제
2. `RAG_MODE_FIX.md` - 이 문서

### 기존 파일 (변경 없음)
- `core/chat/chat_mode_manager.py` - 이미 구현됨
- `core/chat/rag_chat_processor.py` - 이미 구현됨

---

## 🔍 핵심 개선 사항

### Before (문제)
```
사용자 입력
    ↓
AIAgent → AIAgentV2 → _process_with_tools
    ↓
ToolChatProcessor (항상 이것만 사용)
    ↓
응답
```

### After (해결)
```
사용자 입력
    ↓
AIAgent → AIAgentV2 → _should_use_tools (모드 체크)
    ↓
ChatModeManager.get_processor()
    ↓
├─ SIMPLE → SimpleChatProcessor
├─ TOOL → ToolChatProcessor
└─ RAG → RAGChatProcessor (벡터 스토어 + MCP + Multi-Agent)
    ↓
응답
```

---

**결론**: RAG 모드가 이제 정상적으로 초기화되고 사용 가능합니다! 🎉
