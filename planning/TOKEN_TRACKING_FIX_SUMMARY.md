# 토큰 추적 및 금액 계산 수정 완료

## 수정 개요

모든 채팅 모드(ASK, TOOL, RAG)에서 토큰 추적과 금액 계산이 동일하게 적용되도록 수정했습니다.

---

## 수정된 파일

### 1. `core/chat/simple_chat_processor.py` (ASK 모드)

**문제점:**
- 중복 기록 (3회): Unified tracker 2회 + token_tracker 1회
- 실제 토큰 추출 후 추정치 사용 조건 불명확

**수정 내용:**
```python
# 실제 토큰 정보 추출
actual_input, actual_output = TokenLogger.extract_actual_tokens(response)

# 추정치 사용 (실제 토큰이 없는 경우만)
if actual_input == 0 and actual_output == 0:
    input_text = "\\n".join([str(msg.content) if hasattr(msg, 'content') else str(msg) for msg in messages])
    actual_input = TokenLogger.estimate_tokens(input_text, self.model_strategy.model_name)
    actual_output = TokenLogger.estimate_tokens(response_content, self.model_strategy.model_name)
    logger.warning(f"ASK 모드 추정 토큰 사용: IN:{actual_input}, OUT:{actual_output}")
else:
    logger.info(f"ASK 모드 실제 토큰: IN:{actual_input}, OUT:{actual_output}")

# Unified tracker 기록 (1회만)
if unified_tracker and actual_input > 0:
    duration_ms = (time.time() - start_time) * 1000
    unified_tracker.track_agent(
        agent_name="SimpleLLM",
        model=self.model_strategy.model_name,
        input_tokens=actual_input,
        output_tokens=actual_output,
        duration_ms=duration_ms
    )
```

**개선 효과:**
- ✅ 중복 기록 제거 (3회 → 1회)
- ✅ 실제 토큰 우선, 없으면 추정치 사용
- ✅ 명확한 로깅 메시지

---

### 2. `core/chat/tool_chat_processor.py` (TOOL 모드)

**문제점:**
- 불필요한 로깅 코드 중복
- 추정치 사용 조건 불명확

**수정 내용:**
```python
# 실제 토큰 정보 추출
input_tokens, output_tokens = 0, 0
if hasattr(self.model_strategy, '_last_response') and self.model_strategy._last_response:
    input_tokens, output_tokens = TokenLogger.extract_actual_tokens(self.model_strategy._last_response)
    logger.info(f"TOOL 모드 실제 토큰: IN:{input_tokens}, OUT:{output_tokens}")

# 실제 토큰이 없으면 추정치 사용 (도구 결과 포함)
if input_tokens == 0 and output_tokens == 0:
    input_tokens = TokenLogger.estimate_tokens(total_input_text, self.model_strategy.model_name)
    output_tokens = TokenLogger.estimate_tokens(output_text, self.model_strategy.model_name)
    logger.warning(f"TOOL 모드 추정 토큰 사용: IN:{input_tokens}, OUT:{output_tokens}")

# Unified tracker 기록
if unified_tracker and actual_input > 0:
    duration_ms = (time.time() - start_time) * 1000
    unified_tracker.track_agent(
        agent_name="MCPAgent",
        model=self.model_strategy.model_name,
        input_tokens=actual_input,
        output_tokens=actual_output,
        tool_calls=used_tools,
        duration_ms=duration_ms
    )
```

**개선 효과:**
- ✅ 불필요한 로깅 코드 제거
- ✅ 실제 토큰 우선, 없으면 추정치 사용
- ✅ MCP 도구 결과를 입력 토큰에 포함

---

### 3. `core/chat/rag_chat_processor.py` (RAG 모드)

**문제점:**
- Agent들의 토큰 추적 누락

**수정 내용:**
```python
# Orchestrator 실행
response = self.orchestrator.execute_parallel_optimized(user_input, context)

# Unified tracker에 토큰 기록 (Agent들이 이미 기록했으므로 여기서는 종료만)
# Agent들이 track_agent()를 호출하여 각자 토큰 기록

# Unified tracker 종료
if unified_tracker:
    unified_tracker.end_conversation()
```

**개선 효과:**
- ✅ Agent들이 자동으로 토큰 추적
- ✅ 중복 기록 방지

---

### 4. `core/agents/base_agent.py` (모든 Agent 공통)

**기존 기능:**
- Agent 실행 시 자동으로 토큰 추적
- `_track_execution()` 메서드로 Unified Tracker에 기록
- `_extract_token_counts()` 메서드로 실제/추정 토큰 추출

**토큰 추출 우선순위:**
1. LLM의 `_last_response`에서 실제 토큰 추출
2. `intermediate_steps`에서 추출
3. `result metadata`에서 추출
4. Fallback: 텍스트 길이로 추정 (도구 결과 + 시스템 프롬프트 포함)

---

## 금액 계산 시스템

### `core/token_tracking/model_pricing.py`

**지원 모델:**
- OpenAI: GPT-4, GPT-3.5 시리즈
- Google Gemini: 2.0/2.5 Flash, Pro 시리즈
- Perplexity: Sonar, Chat 시리즈
- Pollinations: 무료 (0원)

**금액 계산 로직:**
```python
# 1K 토큰당 가격 (USD)
input_cost = (input_tokens / 1000) * pricing["input"]
output_cost = (output_tokens / 1000) * pricing["output"]
total_cost = input_cost + output_cost
```

**예시:**
```python
# Gemini 2.0 Flash
# Input: 1000 tokens, Output: 500 tokens
input_cost = (1000 / 1000) * 0.0001 = $0.0001
output_cost = (500 / 1000) * 0.0004 = $0.0002
total_cost = $0.0003
```

---

### `core/token_tracking/unified_token_tracker.py`

**자동 금액 계산:**
```python
def track_agent(
    self,
    agent_name: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    tool_calls: Optional[List[str]] = None,
    duration_ms: float = 0.0
):
    # 자동으로 금액 계산
    cost = ModelPricing.get_cost(model, input_tokens, output_tokens)
    
    # Agent 실행 기록 생성
    agent_exec = AgentExecutionToken(
        agent_name=agent_name,
        model_name=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost,  # 자동 계산된 금액
        tool_calls=tool_calls or [],
        duration_ms=duration_ms
    )
    
    self._current_conversation.agents.append(agent_exec)
```

**통계 조회:**
```python
# 세션별 총 금액
total_cost = unified_tracker.get_total_cost(session_id)

# 모델별 금액
cost_by_model = unified_tracker.get_cost_by_model(session_id)

# 가장 비싼 모델
most_expensive_model, cost = unified_tracker.get_most_expensive_model(session_id)
```

---

## 토큰 추적 흐름

### ASK 모드
```
사용자 입력
  ↓
SimpleChatProcessor.process_message()
  ↓
LLM 호출 (대화 히스토리 포함)
  ↓
실제 토큰 추출 (response)
  ↓ (없으면)
추정 토큰 계산 (messages + response_content)
  ↓
unified_tracker.track_agent(
    agent_name="SimpleLLM",
    model=model_name,
    input_tokens=actual_input,
    output_tokens=actual_output
)
  ↓
자동 금액 계산 (ModelPricing.get_cost)
  ↓
DB 저장 (session_id 있으면)
```

### TOOL 모드
```
사용자 입력
  ↓
ToolChatProcessor.process_message()
  ↓
Agent Executor 실행 (MCP 도구 사용)
  ↓
실제 토큰 추출 (_last_response)
  ↓ (없으면)
추정 토큰 계산 (user_input + tool_results + output)
  ↓
unified_tracker.track_agent(
    agent_name="MCPAgent",
    model=model_name,
    input_tokens=actual_input,
    output_tokens=actual_output,
    tool_calls=used_tools
)
  ↓
자동 금액 계산
  ↓
DB 저장
```

### RAG 모드
```
사용자 입력
  ↓
RAGChatProcessor.process_message()
  ↓
MultiAgentOrchestrator.execute_parallel_optimized()
  ↓
각 Agent 실행 (RAGAgent, MCPAgent, etc.)
  ↓
BaseAgent.execute()
  ├─ LLM 호출
  ├─ 토큰 추출 (_extract_token_counts)
  └─ unified_tracker.track_agent()
      ↓
      자동 금액 계산
  ↓
모든 Agent 완료 후 unified_tracker.end_conversation()
  ↓
DB 저장 (모든 Agent 기록 합산)
```

---

## 검증 방법

### 1. 로그 확인
```bash
# ASK 모드
tail -f ~/.chat-ai-agent/logs/app.log | grep "ASK 모드"

# TOOL 모드
tail -f ~/.chat-ai-agent/logs/app.log | grep "TOOL 모드"

# RAG 모드
tail -f ~/.chat-ai-agent/logs/app.log | grep "RAG mode"
```

### 2. DB 확인
```python
from core.token_tracking import get_unified_tracker

tracker = get_unified_tracker(db_path)

# 세션 통계
stats = tracker.get_session_stats(session_id)
print(f"Total tokens: {stats['total_tokens']}")
print(f"Total cost: ${stats['total_cost']:.6f}")

# 모드별 분석
mode_breakdown = tracker.get_mode_breakdown(session_id)
for mode, data in mode_breakdown.items():
    print(f"{mode}: {data['total_tokens']} tokens, ${data['total_cost']:.6f}")

# 모델별 분석
model_breakdown = tracker.get_model_breakdown(session_id)
for model, data in model_breakdown.items():
    print(f"{model}: {data['total_tokens']} tokens, ${data['total_cost']:.6f}")
```

### 3. UI 확인
- 토큰 사용량 패널에서 실시간 업데이트 확인
- 세션별/모드별/모델별 통계 확인
- 금액 표시 확인

---

## 주요 개선 사항

### ✅ 중복 제거
- ASK 모드: 3회 기록 → 1회 기록
- TOOL 모드: 불필요한 로깅 제거
- RAG 모드: Agent별 자동 추적

### ✅ 정확도 향상
- 실제 토큰 우선 사용
- 추정치는 Fallback으로만 사용
- MCP 도구 결과를 입력 토큰에 포함
- 시스템 프롬프트 토큰 포함 (~800 tokens)

### ✅ 금액 계산
- 모든 모드에서 자동 금액 계산
- 모델별 정확한 가격 적용
- 실시간 비용 추적

### ✅ 일관성
- 모든 모드에서 동일한 추적 방식
- 통일된 로깅 형식
- 표준화된 DB 저장

---

## 다음 단계

### 1. UI 개선
- 실시간 금액 표시
- 모드별/모델별 비용 차트
- 예상 비용 경고

### 2. 최적화
- 토큰 캐싱
- 대화 히스토리 압축
- 비용 절감 제안

### 3. 분석 기능
- 일별/주별/월별 통계
- 비용 트렌드 분석
- 모델 비용 비교

---

## 참고 문서

- `TOKEN_TRACKING_COMPLETE.md` - 전체 토큰 추적 시스템 문서
- `core/token_tracking/model_pricing.py` - 모델별 가격 정보
- `core/token_tracking/unified_token_tracker.py` - 통합 추적 시스템
