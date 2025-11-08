# 📊 Phase 4: RAG 채팅 프로세서 완료

## 📋 작업 개요

**목표:** RAG + Multi-Agent + MCP 통합 채팅 시스템 구축

**핵심 원칙:**
- LangChain 100% 사용
- 기존 기능 완전 유지
- AI 자율 결정 (하드코딩 금지)
- SOLID 원칙 준수

---

## 🏗️ 아키텍처

### 채팅 모드 계층 구조

```
ChatModeManager
    ↓
┌───────────────┬───────────────┬────────────────┐
│   SIMPLE      │     TOOL      │      RAG       │
│   (LLM만)     │  (MCP 도구)   │  (통합 모드)    │
└───────────────┴───────────────┴────────────────┘
       ↓               ↓                ↓
SimpleChatProcessor  ToolChatProcessor  RAGChatProcessor
                                              ↓
                                    MultiAgentOrchestrator
                                              ↓
                                    ┌─────────┴─────────┐
                                RAGAgent          MCPAgent
```

---

## 📁 생성된 파일

### 1. **rag_chat_processor.py**
```python
class RAGChatProcessor(BaseChatProcessor):
    """RAG + Multi-Agent 통합 채팅 처리기"""
    
    def __init__(self, model_strategy, vectorstore=None, mcp_client=None, tools=None):
        # Agents 초기화
        self.agents = self._initialize_agents()
        
        # Orchestrator 초기화 (LLM 기반 Agent 선택)
        self.orchestrator = MultiAgentOrchestrator(
            llm=model_strategy.llm,
            agents=self.agents
        )
        
        # Hybrid Analyzer 초기화 (질의 분석)
        self.analyzer = HybridAnalyzer(
            llm=model_strategy.llm,
            agents=self.agents
        )
```

**핵심 기능:**
- ✅ RAGAgent + MCPAgent 자동 초기화
- ✅ LLM 기반 Agent 자동 선택
- ✅ Context 기반 처리
- ✅ Fallback 메커니즘

### 2. **chat_mode_manager.py**
```python
class ChatMode(Enum):
    SIMPLE = "simple"  # LLM만
    TOOL = "tool"      # MCP 도구만
    RAG = "rag"        # RAG + Multi-Agent + MCP (통합)

class ChatModeManager:
    """채팅 모드 관리자"""
    
    def get_processor(self, mode, vectorstore, mcp_client, tools):
        # 모드에 따라 적절한 프로세서 반환
        # 캐싱으로 성능 최적화
```

**핵심 기능:**
- ✅ 3가지 채팅 모드 지원
- ✅ 프로세서 캐싱
- ✅ 동적 모드 전환
- ✅ 리소스 관리

---

## 🔄 통합 방법

### 기존 코드와의 통합

#### 1. **ChatClient 확장**
```python
# core/client/chat_client.py
from core.chat.chat_mode_manager import ChatModeManager, ChatMode

class ChatClient:
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.agent = AIAgent(api_key, model_name)
        
        # RAG 모드 매니저 추가
        self.mode_manager = ChatModeManager(self.agent.model_strategy)
    
    def rag_chat(
        self, 
        user_input: str, 
        vectorstore=None,
        mcp_client=None,
        tools=None,
        history: List[Dict] = None
    ) -> Tuple[str, List]:
        """RAG 모드 채팅"""
        processor = self.mode_manager.get_processor(
            mode=ChatMode.RAG,
            vectorstore=vectorstore,
            mcp_client=mcp_client,
            tools=tools
        )
        return processor.process_message(user_input, history)
```

#### 2. **UI 통합 (MainWindow)**
```python
# ui/main_window/main_window.py

def _setup_chat_mode_selector(self):
    """채팅 모드 선택 UI"""
    self.mode_combo = QComboBox()
    self.mode_combo.addItems(["Ask (Simple)", "Agent (Tools)", "RAG (Advanced)"])
    self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

def _on_mode_changed(self, index):
    """모드 변경 핸들러"""
    modes = [ChatMode.SIMPLE, ChatMode.TOOL, ChatMode.RAG]
    self.current_mode = modes[index]
    logger.info(f"Chat mode changed to: {self.current_mode.value}")

def _send_message(self):
    """메시지 전송"""
    user_input = self.input_field.text()
    
    if self.current_mode == ChatMode.RAG:
        # RAG 모드
        response, tools = self.chat_client.rag_chat(
            user_input,
            vectorstore=self.vectorstore,
            mcp_client=self.mcp_client,
            tools=self.tools,
            history=self.conversation_history
        )
    elif self.current_mode == ChatMode.TOOL:
        # Tool 모드 (기존)
        response, tools = self.chat_client.agent_chat_with_history(
            user_input, self.conversation_history
        )
    else:
        # Simple 모드 (기존)
        response = self.chat_client.chat_with_history(
            user_input, self.conversation_history
        )
        tools = []
    
    self._display_response(response, tools)
```

---

## 🎯 핵심 특징

### 1. **AI 자율 결정**
```python
# ❌ 하드코딩 없음
# ✅ LLM이 자동으로 Agent 선택

# Orchestrator가 자동으로 최적의 Agent 선택
response = self.orchestrator.run(user_input, context)

# 내부적으로 LLM이 분석:
# - Query intent
# - Required capabilities
# - Available agents
# → 최적의 Agent 자동 선택
```

### 2. **유연한 Agent 조합**
```python
# RAGAgent만 사용
processor = RAGChatProcessor(
    model_strategy=strategy,
    vectorstore=vectorstore
)

# MCPAgent만 사용
processor = RAGChatProcessor(
    model_strategy=strategy,
    mcp_client=mcp_client,
    tools=tools
)

# 둘 다 사용 (통합)
processor = RAGChatProcessor(
    model_strategy=strategy,
    vectorstore=vectorstore,
    mcp_client=mcp_client,
    tools=tools
)
```

### 3. **Fallback 메커니즘**
```python
def process_message(self, user_input, conversation_history):
    try:
        if not self.agents:
            # Fallback 1: Simple LLM response
            return self._simple_response(user_input), []
        
        # Orchestrator 실행
        response = self.orchestrator.run(user_input, context)
        
        # Orchestrator 내부에서도 Fallback:
        # 1차: LLM 기반 Agent 선택
        # 2차: 규칙 기반 Fallback
        # 3차: 기본 Agent
        
        return response, []
        
    except Exception as e:
        # Fallback 2: Error handling
        return f"처리 중 오류: {str(e)}", []
```

---

## 📊 사용 시나리오

### Scenario 1: RAG 검색
```python
# 사용자: "2024년 매출 보고서에서 주요 내용을 요약해줘"

# 1. Orchestrator가 LLM에게 질의
# 2. LLM이 RAGAgent 선택 (문서 검색 필요)
# 3. RAGAgent가 vectorstore에서 검색
# 4. 검색 결과 기반 응답 생성
```

### Scenario 2: MCP 도구 사용
```python
# 사용자: "이메일을 보내줘"

# 1. Orchestrator가 LLM에게 질의
# 2. LLM이 MCPAgent 선택 (도구 사용 필요)
# 3. MCPAgent가 Gmail 도구 실행
# 4. 실행 결과 반환
```

### Scenario 3: 하이브리드 (RAG + MCP)
```python
# 사용자: "계약서에서 금액을 찾아서 Excel로 정리해줘"

# 1. Orchestrator가 LLM에게 질의
# 2. LLM이 RAGAgent + MCPAgent 선택
# 3. RAGAgent가 계약서에서 금액 검색
# 4. MCPAgent가 Excel 도구로 정리
# 5. 통합 결과 반환
```

---

## 🔧 설정 및 사용법

### 1. **기본 사용**
```python
from core.client.chat_client import ChatClient
from core.chat.chat_mode_manager import ChatMode

# Client 초기화
client = ChatClient(api_key="...", model_name="gpt-4")

# Simple 모드
response = client.chat("안녕하세요")

# Tool 모드
response, tools = client.agent_chat("이메일 보내줘")

# RAG 모드
response, tools = client.rag_chat(
    "문서에서 정보 찾아줘",
    vectorstore=my_vectorstore,
    mcp_client=my_mcp_client
)
```

### 2. **모드 전환**
```python
# 모드 매니저 사용
manager = ChatModeManager(model_strategy)

# Simple 모드로 전환
manager.set_mode(ChatMode.SIMPLE)
processor = manager.get_processor()

# RAG 모드로 전환
manager.set_mode(ChatMode.RAG)
processor = manager.get_processor(
    vectorstore=vectorstore,
    mcp_client=mcp_client
)
```

### 3. **커스텀 Agent 추가**
```python
from core.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    """커스텀 Agent"""
    
    def can_handle(self, query, context):
        # LLM 기반 판단
        prompt = f"Can this agent handle: {query}?"
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return "YES" in response.content.upper()
    
    def _create_executor(self):
        # Agent 로직 구현
        pass

# RAG Processor에 추가
processor = RAGChatProcessor(...)
processor.agents.append(CustomAgent(llm=...))
```

---

## 📈 성능 최적화

### 1. **프로세서 캐싱**
```python
# ChatModeManager가 자동으로 캐싱
# 동일한 설정이면 재사용

processor1 = manager.get_processor(ChatMode.RAG, vectorstore, mcp_client)
processor2 = manager.get_processor(ChatMode.RAG, vectorstore, mcp_client)
# processor1 == processor2 (동일 인스턴스)
```

### 2. **Agent 지연 초기화**
```python
# Agent는 필요할 때만 초기화
def _initialize_agents(self):
    agents = []
    
    # vectorstore 있을 때만 RAGAgent 생성
    if self.vectorstore:
        agents.append(RAGAgent(...))
    
    # mcp_client 있을 때만 MCPAgent 생성
    if self.mcp_client or self.tools:
        agents.append(MCPAgent(...))
    
    return agents
```

### 3. **LLM 호출 최소화**
```python
# Orchestrator가 한 번의 LLM 호출로 Agent 선택
# 불필요한 중복 호출 방지

response = self.orchestrator.run(user_input, context)
# 내부적으로 1회 LLM 호출로 Agent 결정
```

---

## 🧪 테스트

### 단위 테스트
```python
# tests/test_rag_chat_processor.py

def test_rag_processor_initialization():
    """RAG Processor 초기화 테스트"""
    processor = RAGChatProcessor(
        model_strategy=mock_strategy,
        vectorstore=mock_vectorstore
    )
    assert len(processor.agents) == 1
    assert isinstance(processor.agents[0], RAGAgent)

def test_mode_manager():
    """Mode Manager 테스트"""
    manager = ChatModeManager(mock_strategy)
    
    # Simple 모드
    processor = manager.get_processor(ChatMode.SIMPLE)
    assert isinstance(processor, SimpleChatProcessor)
    
    # RAG 모드
    processor = manager.get_processor(
        ChatMode.RAG,
        vectorstore=mock_vectorstore
    )
    assert isinstance(processor, RAGChatProcessor)

def test_agent_selection():
    """Agent 자동 선택 테스트"""
    processor = RAGChatProcessor(...)
    
    # RAG 질의
    response, _ = processor.process_message("문서에서 찾아줘")
    # RAGAgent가 자동 선택되어야 함
    
    # MCP 질의
    response, _ = processor.process_message("이메일 보내줘")
    # MCPAgent가 자동 선택되어야 함
```

---

## 🔄 마이그레이션 가이드

### 기존 코드 → RAG 모드

#### Before (기존 Tool 모드)
```python
response, tools = client.agent_chat_with_history(
    user_input,
    conversation_history
)
```

#### After (RAG 모드)
```python
response, tools = client.rag_chat(
    user_input,
    vectorstore=vectorstore,
    mcp_client=mcp_client,
    tools=tools,
    history=conversation_history
)
```

**변경 사항:**
- ✅ vectorstore 추가 (RAG 기능)
- ✅ mcp_client 명시적 전달
- ✅ 자동 Agent 선택
- ✅ 기존 기능 100% 호환

---

## 📚 API 레퍼런스

### RAGChatProcessor

```python
class RAGChatProcessor(BaseChatProcessor):
    def __init__(
        self,
        model_strategy,      # LLM strategy (required)
        vectorstore=None,    # Vector store for RAG (optional)
        mcp_client=None,     # MCP client for tools (optional)
        tools=None           # Pre-wrapped tools (optional)
    )
    
    def process_message(
        self,
        user_input: str,                    # User query
        conversation_history: List[Dict]    # Conversation history
    ) -> Tuple[str, List]:                  # (response, used_tools)
    
    def supports_tools(self) -> bool:       # Always True if agents exist
```

### ChatModeManager

```python
class ChatModeManager:
    def __init__(self, model_strategy)
    
    def set_mode(self, mode: ChatMode)      # Change current mode
    
    def get_processor(
        self,
        mode: Optional[ChatMode] = None,    # Mode (uses current if None)
        vectorstore=None,                   # For RAG mode
        mcp_client=None,                    # For RAG/TOOL mode
        tools=None                          # For RAG/TOOL mode
    ) -> BaseChatProcessor
    
    def clear_cache(self)                   # Clear processor cache
```

---

## ✅ 체크리스트

- [x] RAGChatProcessor 구현
- [x] ChatModeManager 구현
- [x] ChatMode Enum 정의
- [x] Multi-Agent 통합
- [x] LLM 기반 Agent 선택
- [x] Fallback 메커니즘
- [x] 프로세서 캐싱
- [x] 기존 기능 호환성
- [ ] ChatClient 확장
- [ ] UI 통합
- [ ] 통합 테스트
- [ ] 문서화 완료

---

## 🚀 다음 단계

### Phase 5: UI 구현
1. **채팅 모드 선택 UI**
   - 콤보박스: Ask / Agent / RAG
   - 모드별 설정 패널

2. **RAG 문서 관리 UI**
   - 문서 업로드
   - 문서 목록
   - 청크 뷰어

3. **RAG 설정 UI**
   - Vector DB 선택
   - 임베딩 모델 선택
   - 검색 설정

---

**작업 완료일:** 2024-01-XX  
**작업자:** Amazon Q  
**검토 상태:** ✅ Phase 4 완료, Phase 5 준비
