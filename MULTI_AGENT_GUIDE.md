# 🤖 Multi-Agent Orchestrator 가이드

## 📋 등록된 Agent 목록

### 1. RAGAgent
- **역할**: 문서 검색 및 RAG 기반 답변
- **조건**: vectorstore가 있을 때만 등록
- **사용 예**: "문서에서 정보 찾아줘"

### 2. MCPAgent  
- **역할**: MCP 도구 실행 (검색, Gmail, MySQL 등)
- **조건**: mcp_client 또는 tools가 있을 때만 등록
- **사용 예**: "웹 검색해줘", "이메일 보내줘"

### 3. PandasAgent
- **역할**: CSV/Excel 데이터 분석
- **조건**: 항상 등록
- **사용 예**: "sales.csv 월별 매출 분석해줘"

### 4. SQLAgent (선택)
- **역할**: 데이터베이스 쿼리
- **조건**: 수동 추가 필요
- **사용 예**: "users 테이블 조회해줘"

### 5. PythonREPLAgent (선택)
- **역할**: Python 코드 실행
- **조건**: 수동 추가 필요
- **사용 예**: "피보나치 수열 계산해줘"

### 6. FileManagementAgent (선택)
- **역할**: 파일 시스템 관리
- **조건**: 수동 추가 필요
- **사용 예**: "파일 목록 보여줘"

---

## 🔄 실행 흐름

```
사용자 질문
    ↓
RAGChatProcessor.process_message()
    ↓
MultiAgentOrchestrator.run()
    ↓
┌─────────────────────────────────┐
│ 1. LLM 기반 Agent 선택          │
│    _select_agent_with_llm()     │
│    - Agent 정보 수집             │
│    - LLM에게 선택 요청           │
│    - 가장 적합한 Agent 반환      │
└─────────────────────────────────┘
    ↓ (실패 시)
┌─────────────────────────────────┐
│ 2. Fallback: 규칙 기반 선택     │
│    _select_agent_fallback()     │
│    - 우선순위: Pandas > SQL >   │
│      RAG > MCP                   │
│    - can_handle() 메서드 호출   │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 3. 선택된 Agent 실행            │
│    agent.execute(query, context)│
└─────────────────────────────────┘
    ↓
결과 반환
```

---

## 💡 Agent 선택 로직

### LLM 기반 선택 (우선)
```python
# Orchestrator가 LLM에게 질문
prompt = """
Query: {사용자 질문}

Available Agents:
- RAGAgent: 문서 검색
- MCPAgent: 외부 도구
- PandasAgent: 데이터 분석

가장 적합한 Agent는?
"""

# LLM 응답: "PandasAgent"
# → PandasAgent 선택
```

### Fallback: 규칙 기반 선택
```python
# 우선순위 순서로 can_handle() 체크
1. PandasAgent.can_handle(query) → LLM 판단
2. SQLAgent.can_handle(query) → LLM 판단
3. RAGAgent.can_handle(query) → LLM 판단
4. MCPAgent.can_handle(query) → LLM 판단

# 첫 번째로 True 반환한 Agent 선택
```

---

## 🎯 실제 사용 예시

### 예시 1: CSV 분석
```
사용자: "sales_data.csv 월별 매출 알려줘"

1. Orchestrator가 LLM에게 질문
   → LLM: "PandasAgent"
   
2. PandasAgent.can_handle() 호출
   → 파일 경로 감지 (.csv)
   → 파일 자동 로드
   → LLM 판단: "YES"
   
3. PandasAgent.execute() 실행
   → create_pandas_dataframe_agent 사용
   → 데이터 분석 수행
   
4. 결과 반환
```

### 예시 2: 문서 검색
```
사용자: "프로젝트 문서에서 일정 찾아줘"

1. Orchestrator가 LLM에게 질문
   → LLM: "RAGAgent"
   
2. RAGAgent.can_handle() 호출
   → LLM 판단: "YES" (문서 검색 필요)
   
3. RAGAgent.execute() 실행
   → vectorstore에서 검색
   → ConversationalRetrievalChain 사용
   
4. 결과 반환
```

### 예시 3: 웹 검색
```
사용자: "최신 뉴스 검색해줘"

1. Orchestrator가 LLM에게 질문
   → LLM: "MCPAgent"
   
2. MCPAgent.can_handle() 호출
   → 사용 가능한 도구 확인
   → LLM 판단: "YES"
   
3. MCPAgent.execute() 실행
   → MCP 검색 도구 호출
   
4. 결과 반환
```

---

## 🔧 Agent 추가 방법

### RAGChatProcessor에 Agent 추가
```python
# core/chat/rag_chat_processor.py

def _initialize_agents(self) -> List:
    agents = []
    
    # 기존 Agent들...
    
    # SQL Agent 추가
    try:
        from core.agents.sql_agent import SQLAgent
        sql_agent = SQLAgent(
            llm=self.model_strategy.llm,
            db_uri="sqlite:///mydb.db"
        )
        agents.append(sql_agent)
        logger.info("SQL Agent initialized")
    except Exception as e:
        logger.warning(f"SQL Agent failed: {e}")
    
    return agents
```

---

## 📊 Agent 우선순위

### Fallback 선택 시 우선순위
1. **PandasAgent** - 데이터 분석 (가장 높음)
2. **SQLAgent** - 데이터베이스
3. **RAGAgent** - 문서 검색
4. **MCPAgent** - 외부 도구 (가장 낮음)

### 이유
- 데이터 분석은 명확한 의도
- 문서 검색은 광범위
- 외부 도구는 마지막 수단

---

## 🚀 병렬 실행

### 여러 Agent 동시 실행
```python
# 병렬 실행
results = orchestrator.execute_parallel(
    query="복잡한 질문",
    agent_names=["PandasAgent", "RAGAgent"],
    timeout=30
)

# 최적화된 병렬 실행 (자동 Agent 선택)
result = orchestrator.execute_parallel_optimized(
    query="복잡한 질문",
    context={"key": "value"}
)
```

---

## 🎓 핵심 포인트

1. **AI 기반 선택**: 하드코딩 없이 LLM이 context 파악
2. **자동 Fallback**: LLM 실패 시 규칙 기반으로 전환
3. **동적 로딩**: 파일 경로 감지 시 자동 로드
4. **확장 가능**: 새 Agent 추가 용이
5. **안전성**: 각 Agent의 can_handle()로 이중 검증

---

## 📝 로그 확인

```bash
# Agent 선택 로그
INFO - Orchestrator initialized with 3 agents
INFO -   - RAGAgent: RAG (Retrieval-Augmented Generation) Agent
INFO -   - MCPAgent: MCP Agent
INFO -   - PandasAgent: Pandas 데이터 분석 Agent

# 실행 로그
INFO - LLM selected agent: PandasAgent
INFO - Loaded dataframe: (300, 5)
INFO - Executing pandas query: 월별 매출 분석
```

---

## 🔍 디버깅

### Agent가 선택되지 않을 때
1. 로그 확인: `LLM selected agent: ???`
2. can_handle() 로직 확인
3. LLM 프롬프트 개선

### Agent 실행 실패 시
1. Agent.execute() 에러 로그 확인
2. 입력 데이터 검증
3. LLM 응답 확인
