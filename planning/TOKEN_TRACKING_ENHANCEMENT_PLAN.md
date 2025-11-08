# 🔢 Token Tracking System Enhancement Plan

## 📋 Overview

**Goal**: Implement comprehensive token tracking system with 4-dimensional analysis (Mode, Model, Agent, Time) and persistent storage.

**Current Issues**:
- No distinction between chat modes (SIMPLE/TOOL/RAG)
- No model-specific tracking (GPT-4 vs Gemini costs differ)
- No agent-level breakdown (RAGAgent vs MCPAgent)
- All statistics lost on app restart

**Target**: Complete tracking system with DB persistence, cost calculation, and historical analysis.

---

## 🎯 Tracking Dimensions

### 1. Chat Mode
- **SIMPLE**: LLM only (no tools)
- **TOOL**: MCP tools only
- **RAG**: RAG + Multi-Agent + MCP (integrated)

### 2. Model
- OpenAI: gpt-4, gpt-4-turbo, gpt-3.5-turbo
- Google: gemini-2.0-flash, gemini-2.5-flash, gemini-pro
- Perplexity: sonar-pro, sonar
- Pollinations: free models

### 3. Agent (RAG mode only)
- RAGAgent: Internal document retrieval
- MCPAgent: External tools/web services
- PythonREPLAgent: Python code execution
- FileSystemAgent: File operations (read/write/delete)
- PandasAgent: Data analysis (future)
- SQLAgent: Database queries (future)

### 4. Time
- Current session
- Last 7 days
- Last 30 days
- All time

---

## 📊 Database Schema

### New Tables

#### 1. token_usage
```sql
CREATE TABLE token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    message_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Tracking dimensions
    chat_mode TEXT NOT NULL,           -- 'simple', 'tool', 'rag'
    model_name TEXT NOT NULL,          -- 'gemini-2.0-flash'
    agent_name TEXT,                   -- 'RAGAgent', 'MCPAgent', NULL
    
    -- Token counts
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    
    -- Cost
    cost_usd REAL NOT NULL,
    
    -- Metadata
    duration_ms REAL,
    tool_calls TEXT,                   -- JSON array of tool names
    additional_info TEXT,              -- JSON for extra data
    
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL
);

CREATE INDEX idx_token_usage_session ON token_usage(session_id);
CREATE INDEX idx_token_usage_timestamp ON token_usage(timestamp);
CREATE INDEX idx_token_usage_mode ON token_usage(chat_mode);
CREATE INDEX idx_token_usage_model ON token_usage(model_name);
```

#### 2. session_token_summary
```sql
CREATE TABLE session_token_summary (
    session_id INTEGER PRIMARY KEY,
    
    -- Totals
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    
    -- Breakdowns (JSON)
    mode_breakdown TEXT,               -- {"simple": 100, "tool": 200, "rag": 300}
    model_breakdown TEXT,              -- {"gpt-4": 100, "gemini": 200}
    agent_breakdown TEXT,              -- {"RAGAgent": 100, "MCPAgent": 200}
    
    -- Timestamps
    first_message_at DATETIME,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
```

#### 3. global_token_stats
```sql
CREATE TABLE global_token_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date DATE UNIQUE NOT NULL,
    
    -- Daily totals
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    
    -- Breakdowns (JSON)
    mode_breakdown TEXT,
    model_breakdown TEXT,
    agent_breakdown TEXT,
    
    -- Metadata
    session_count INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_global_stats_date ON global_token_stats(stat_date);
```

---

## 🏗️ Architecture

### File Structure
```
core/
├── token_tracking/
│   ├── __init__.py
│   ├── unified_token_tracker.py      # Main tracker
│   ├── model_pricing.py              # Pricing database
│   ├── token_storage.py              # DB operations
│   └── token_statistics.py           # Statistics aggregation
ui/
├── components/
│   └── advanced_token_display.py     # Enhanced UI
```

### Core Components

#### 1. Model Pricing (`model_pricing.py`)
```python
MODEL_PRICING = {
    # OpenAI (per 1K tokens)
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    
    # Google Gemini 2.0 Flash Series (Pay-as-you-go pricing)
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-2.0-flash-exp": {"input": 0.0001, "output": 0.0004},
    "gemini-2.0-flash-001": {"input": 0.0001, "output": 0.0004},
    "gemini-2.0-flash-lite": {"input": 0.00005, "output": 0.0002},
    "gemini-2.0-flash-lite-001": {"input": 0.00005, "output": 0.0002},
    "gemini-2.0-flash-thinking-exp": {"input": 0.0001, "output": 0.0004},
    "gemini-flash-latest": {"input": 0.0001, "output": 0.0004},
    "gemini-flash-lite-latest": {"input": 0.00005, "output": 0.0002},
    
    # Google Gemini 2.0 Pro Series (Pay-as-you-go pricing)
    "gemini-2.0-pro-exp": {"input": 0.00125, "output": 0.005},
    "gemini-2.0-pro-exp-02-05": {"input": 0.00125, "output": 0.005},
    
    # Google Gemini 2.5 Flash Series (Pay-as-you-go pricing)
    "gemini-2.5-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-2.5-flash-lite": {"input": 0.00005, "output": 0.0002},
    "gemini-2.5-flash-preview-05-20": {"input": 0.0001, "output": 0.0004},
    "gemini-2.5-flash-lite-preview-06-17": {"input": 0.00005, "output": 0.0002},
    
    # Google Gemini 2.5 Pro Series (Pay-as-you-go pricing)
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-2.5-pro-preview-03-25": {"input": 0.00125, "output": 0.005},
    "gemini-2.5-pro-preview-05-06": {"input": 0.00125, "output": 0.005},
    "gemini-2.5-pro-preview-06-05": {"input": 0.00125, "output": 0.005},
    
    # Google Gemini Legacy (Pay-as-you-go pricing)
    "gemini-pro-latest": {"input": 0.000125, "output": 0.000375},
    "gemini-exp-1206": {"input": 0.000125, "output": 0.000375},
    
    # Perplexity (per 1K tokens)
    # Sonar Series (Online models with web search)
    "sonar": {"input": 0.001, "output": 0.001},
    "sonar-pro": {"input": 0.003, "output": 0.015},
    "sonar-reasoning": {"input": 0.001, "output": 0.005},
    
    # Chat Series (Offline models without web search)
    "llama-3.1-sonar-small-128k-chat": {"input": 0.0002, "output": 0.0002},
    "llama-3.1-sonar-large-128k-chat": {"input": 0.001, "output": 0.001},
    "llama-3.1-sonar-huge-128k-chat": {"input": 0.005, "output": 0.005},
    
    # Pollinations (Free)
    "pollinations": {"input": 0.0, "output": 0.0},
    "pollinations-mistral": {"input": 0.0, "output": 0.0}
}

class ModelPricing:
    @staticmethod
    def get_cost(model: str, input_tokens: int, output_tokens: int) -> float
    
    @staticmethod
    def get_pricing_info(model: str) -> Dict
    
    @staticmethod
    def update_pricing(model: str, input_price: float, output_price: float)
```

#### 2. Unified Token Tracker (`unified_token_tracker.py`)
```python
@dataclass
class AgentExecutionToken:
    agent_name: str
    model_name: str
    input_tokens: int
    output_tokens: int
    cost: float
    tool_calls: List[str]
    duration_ms: float
    timestamp: datetime

@dataclass
class ConversationToken:
    conversation_id: str
    mode: ChatModeType
    model_name: str
    agents: List[AgentExecutionToken]
    total_input: int
    total_output: int
    total_cost: float
    start_time: datetime
    end_time: Optional[datetime]

class UnifiedTokenTracker:
    def __init__(self, db_manager)
    
    # Conversation lifecycle
    def start_conversation(mode: ChatModeType, model: str) -> str
    def track_agent(agent_name, model, input_tokens, output_tokens)
    def end_conversation() -> ConversationToken
    
    # Persistence
    def _save_to_db(conversation: ConversationToken)
    def _load_from_db(session_id: int)
    
    # Statistics
    def get_session_stats() -> Dict
    def get_mode_breakdown() -> Dict[ChatModeType, TokenUsage]
    def get_model_breakdown() -> Dict[str, TokenUsage]
    def get_agent_breakdown() -> Dict[str, TokenUsage]
    def get_historical_stats(days: int) -> Dict
    
    # Cost analysis
    def get_total_cost() -> float
    def get_cost_by_model() -> Dict[str, float]
    def get_most_expensive_model() -> Tuple[str, float]
```

#### 3. Token Storage (`token_storage.py`)
```python
class TokenStorage:
    def __init__(self, db_path: str)
    
    # Insert operations
    def insert_token_usage(session_id, mode, model, agent, tokens, cost)
    def update_session_summary(session_id, totals, breakdowns)
    def update_global_stats(date, totals, breakdowns)
    
    # Query operations
    def get_session_tokens(session_id) -> List[TokenUsage]
    def get_session_summary(session_id) -> Dict
    def get_global_stats(start_date, end_date) -> List[Dict]
    def get_model_usage_history(model, days) -> List[Dict]
    
    # Aggregation
    def aggregate_by_mode(session_id) -> Dict
    def aggregate_by_model(session_id) -> Dict
    def aggregate_by_agent(session_id) -> Dict
```

---

## 🔄 Integration Points

### 1. Chat Processors
```python
# base_chat_processor.py
class BaseChatProcessor:
    def process_message(self, user_input, history):
        # Start tracking
        unified_tracker.start_conversation(
            mode=self.mode,
            model=self.model_strategy.model_name
        )
        
        # Process
        response = self._process(user_input, history)
        
        # End tracking
        unified_tracker.end_conversation()
        
        return response
```

### 2. Base Agent
```python
# base_agent.py
class BaseAgent:
    def execute(self, query, context):
        start_time = time.time()
        
        # Execute
        result = executor.invoke(inputs)
        
        # Extract tokens
        input_tokens, output_tokens = extract_tokens(result)
        
        # Track
        unified_tracker.track_agent(
            agent_name=self.get_name(),
            model=self.llm.model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        return result
```

### 3. Multi-Agent Orchestrator
```python
# multi_agent_orchestrator.py
class MultiAgentOrchestrator:
    def execute_parallel_optimized(self, query, context):
        # Track orchestrator decision
        unified_tracker.track_agent(
            agent_name="Orchestrator",
            model=self.llm.model_name,
            input_tokens=decision_tokens.input,
            output_tokens=decision_tokens.output
        )
        
        # Execute agents (each tracks itself)
        results = parallel_execute(agents)
        
        return merge_results(results)
```

---

## 🎨 UI Components

### Enhanced Token Display
```
┌─────────────────────────────────────────────────────┐
│ Token Usage Dashboard                               │
├─────────────────────────────────────────────────────┤
│ [Current] [7 Days] [30 Days] [All Time]            │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📊 Overview                                         │
│  Total Tokens: 50,000                              │
│  Total Cost: $0.080                                │
│  Average per conversation: 500 tokens              │
│                                                     │
│ 📈 Mode Breakdown                                   │
│  ├─ SIMPLE: 10,000 tokens (20%) - $0.010          │
│  ├─ TOOL:   15,000 tokens (30%) - $0.020          │
│  └─ RAG:    25,000 tokens (50%) - $0.050          │
│                                                     │
│ 💰 Model Breakdown                                  │
│  ├─ gemini-2.0-flash: 30,000 tokens - $0.006      │
│  ├─ gpt-4:            10,000 tokens - $0.060       │
│  └─ sonar-pro:        10,000 tokens - $0.014       │
│                                                     │
│ 🤖 Agent Breakdown (RAG Mode)                      │
│  ├─ RAGAgent:         12,000 tokens - $0.024      │
│  ├─ MCPAgent:         10,000 tokens - $0.020      │
│  ├─ PythonREPLAgent:   5,000 tokens - $0.010      │
│  ├─ FileSystemAgent:   3,000 tokens - $0.006      │
│  └─ Orchestrator:      3,000 tokens - $0.006      │
│                                                     │
│ 📉 Cost Analysis                                    │
│  Most Expensive: gpt-4 ($0.060)                    │
│  Most Used: gemini-2.0-flash (30,000 tokens)      │
│  Cost per 1K tokens: $0.0016                       │
│                                                     │
│ [Export CSV] [Export JSON] [Clear History]         │
└─────────────────────────────────────────────────────┘
```

### Features
- Real-time updates via PyQt6 signals
- Interactive charts (bar, pie, line)
- Drill-down capability (click to see details)
- Export to CSV/JSON
- Date range filtering
- Model comparison view

---

## 📅 Implementation Plan

### Phase 1: Database Schema (0.5 days) ✅ COMPLETED
**Files**: `core/token_tracking/migrations/001_add_token_tables.sql`

- [x] Create migration script
- [x] Add token_usage table
- [x] Add session_token_summary table
- [x] Add global_token_stats table
- [x] Create indexes
- [x] Test migration on existing DB

### Phase 2: Model Pricing System (0.5 days) ✅ COMPLETED
**Files**: `core/token_tracking/model_pricing.py`

- [x] Define MODEL_PRICING dictionary (33 models)
- [x] Implement ModelPricing class
- [x] Add get_cost() method
- [x] Add pricing update mechanism
- [x] Add comparison methods (cheapest/most expensive)
- [x] Write unit tests

### Phase 3: Token Storage Layer (1 day) ✅ COMPLETED
**Files**: `core/token_tracking/token_storage.py`

- [x] Implement TokenStorage class
- [x] Add insert methods (token_usage, summaries)
- [x] Add query methods (session, global stats)
- [x] Add aggregation methods (mode/model/agent)
- [x] Add error handling and logging
- [x] Write integration tests

### Phase 4: Unified Token Tracker (1.5 days) ✅ COMPLETED
**Files**: `core/token_tracking/unified_token_tracker.py`

- [x] Define data classes (AgentExecutionToken, ConversationToken)
- [x] Implement UnifiedTokenTracker class
- [x] Add conversation lifecycle methods (start/track/end)
- [x] Implement 4-dimensional tracking (Mode/Model/Agent/Time)
- [x] Add persistence logic (save/load)
- [x] Implement statistics methods
- [x] Add cost calculation integration
- [x] Add PyQt6 signals for UI updates
- [x] Write comprehensive tests

### Phase 5: Integration (1 day) ✅ COMPLETED
**Files**: Multiple processor and agent files

- [x] Update SimpleChatProcessor (unified tracker integration)
- [x] Update ToolChatProcessor (unified tracker integration)
- [x] Update RAGChatProcessor (unified tracker integration)
- [x] Update BaseAgent.execute() (automatic token tracking)
- [x] Add _track_execution() method to BaseAgent
- [x] Add _extract_token_counts() method
- [x] Add model name propagation via context
- [x] Create migration application script
- [ ] Test all chat modes (pending)
- [ ] Test multi-agent scenarios (pending)
- [ ] Test UI data compatibility (pending)

### Phase 6: UI Dashboard Enhancement (1.5 days)
**Files**: `ui/components/token_usage_display.py` (기존 파일 수정 + 확장)

#### 6.1 기존 UI 데이터 호환성 수정 (0.5 days)

**문제점 분석**:
```python
# 현재 코드가 의존하는 데이터 구조
token_tracker.get_conversation_stats()  # ❌ unified_tracker와 다름
token_tracker.conversation_history      # ❌ 구조 변경 필요
token_accumulator.get_session_total()   # ❌ 통합 필요
```

**수정 작업**:
- [ ] **데이터 소스 전환**:
  - [ ] `token_tracker` → `unified_tracker` 전환
  - [ ] `token_accumulator` 통합 (중복 제거)
  - [ ] 데이터 구조 매핑 레이어 추가

- [ ] **Current 탭 수정**:
  - [ ] `conversation_id` → `conversation_id` (동일)
  - [ ] `model_name` → `model_name` (동일)
  - [ ] `steps_count` → `len(agents)` (Agent 기반으로 변경)
  - [ ] `total_actual_tokens` → `total_input + total_output`
  - [ ] **비용 정보 추가**: `total_cost` 표시
  - [ ] **모드 정보 추가**: `mode` (SIMPLE/TOOL/RAG) 표시

- [ ] **Steps 탭 수정**:
  - [ ] 기존: 단계별 토큰 (StepType 기반)
  - [ ] 신규: Agent별 토큰 (AgentExecutionToken 기반)
  - [ ] 테이블 컬럼 추가: "Agent", "Cost"
  - [ ] 테이블 컬럼 제거: "Type" (불필요)

- [ ] **Stats 탭 수정**:
  - [ ] 기존: 모델별 통계만
  - [ ] 신규: 모드별 + 모델별 + Agent별 통계
  - [ ] `model_stats` → `get_model_breakdown()` 전환
  - [ ] 정확도 계산 제거 (추정 토큰 사용 안 함)

- [ ] **Signal 연결 수정**:
  - [ ] `token_accumulator.token_updated` → `unified_tracker.token_updated`
  - [ ] Signal 데이터 구조 변경 대응

#### 6.2 새 기능 추가 (1 day)

**추가 기능**:
- [ ] **Stats 탭 확장**:
  - [ ] Mode Breakdown 섹션 (SIMPLE/TOOL/RAG)
  - [ ] Model Breakdown 섹션 (비용 포함)
  - [ ] Agent Breakdown 섹션 (RAG 모드)
  - [ ] Cost Analysis 섹션 (총 비용, 가장 비싼 모델)

- [ ] **Time Range 필터**:
  - [ ] 드롭다운 추가: Current/7D/30D/All
  - [ ] 필터 변경 시 데이터 재로드
  - [ ] DB 쿼리 연동

- [ ] **Cost 정보 표시**:
  - [ ] Current 탭: 현재 대화 비용
  - [ ] Stats 탭: 총 비용, 평균 비용
  - [ ] 모델별 비용 차트

- [ ] **Export 기능 확장**:
  - [ ] CSV export 추가
  - [ ] 필터링된 데이터만 export
  - [ ] 비용 정보 포함

- [ ] **차트 추가** (선택적):
  - [ ] 모델별 사용량 파이 차트
  - [ ] 시간별 토큰 사용량 라인 차트
  - [ ] 비용 비교 바 차트

### Phase 7: Testing & Optimization (0.5 days)

- [ ] End-to-end testing (all modes)
- [ ] Performance testing (DB queries)
- [ ] Memory leak testing
- [ ] UI responsiveness testing
- [ ] Export/import testing
- [ ] Migration testing (existing data)
- [ ] Documentation updates

---

## 📊 Success Metrics

### Functional Requirements
- ✅ Track tokens across all 3 chat modes
- ✅ Track tokens for all models
- ✅ Track tokens per agent (RAG mode)
- ✅ Calculate accurate costs
- ✅ Persist data across app restarts
- ✅ Display historical statistics

### Performance Requirements
- DB insert < 10ms (async)
- Statistics query < 100ms
- UI update < 50ms
- Memory usage < 50MB (cache)

### Data Integrity
- No token loss on app crash
- Accurate cost calculation (±1%)
- Consistent aggregation
- Safe concurrent access

---

## 🚀 Deployment

### Migration Steps
1. Backup existing database
2. Run migration script
3. Verify table creation
4. Test with sample data
5. Deploy new code
6. Monitor logs for errors

### Rollback Plan
1. Restore database backup
2. Revert code changes
3. Clear token cache
4. Restart application

---

## 📝 Notes

### Design Decisions
- **Async DB writes**: Prevent UI blocking
- **Hybrid caching**: Fast access + persistence
- **JSON breakdowns**: Flexible schema
- **Separate tables**: Optimized queries
- **기존 UI 확장**: 새 위젯 생성 대신 기존 token_usage_display.py 확장
- **점진적 마이그레이션**: token_tracker → unified_tracker 단계적 전환
- **하위 호환성**: 기존 데이터 구조 매핑 레이어로 호환성 유지
- **데이터 중복 제거**: token_accumulator 기능을 unified_tracker로 통합

### Future Enhancements
- Cost alerts (budget limits)
- Token usage predictions
- Model recommendation (cost-effective)
- Batch export for accounting
- API for external analytics

---

## 🔧 Data Structure Mapping

### 기존 → 신규 매핑

```python
# 기존 token_tracker 구조
class ConversationTokenUsage:
    conversation_id: str
    model_name: str
    steps: List[TokenUsageStep]  # StepType 기반
    total_tokens: int
    total_estimated_tokens: int

# 신규 unified_tracker 구조
class ConversationToken:
    conversation_id: str
    mode: ChatModeType           # ✨ 새로 추가
    model_name: str
    agents: List[AgentExecutionToken]  # ✨ Agent 기반으로 변경
    total_input: int
    total_output: int
    total_cost: float            # ✨ 새로 추가

# 매핑 레이어
class DataAdapter:
    @staticmethod
    def convert_to_legacy_format(new_data: ConversationToken) -> dict:
        """신규 → 기존 형식 변환 (UI 호환성)"""
        return {
            'conversation_id': new_data.conversation_id,
            'model_name': new_data.model_name,
            'steps_count': len(new_data.agents),
            'total_actual_tokens': new_data.total_input + new_data.total_output,
            'steps': [
                {
                    'step_name': agent.agent_name,
                    'actual_tokens': agent.input_tokens + agent.output_tokens,
                    'duration_ms': agent.duration_ms,
                    'tool_name': ', '.join(agent.tool_calls)
                }
                for agent in new_data.agents
            ]
        }
```

## 📚 References

- LangChain token counting: https://python.langchain.com/docs/modules/model_io/llms/token_usage_tracking
- OpenAI pricing: https://openai.com/pricing
- Google Gemini pricing: https://ai.google.dev/pricing
- Perplexity pricing: https://docs.perplexity.ai/docs/pricing
- SQLite best practices: https://www.sqlite.org/bestpractice.html

---

**Total Estimated Time**: 6.5 days
**Priority**: High
**Status**: Planning Complete ✅
