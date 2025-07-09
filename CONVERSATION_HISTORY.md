# 🧠 대화 히스토리 기능 상세 설명

## 개요

Chat AI Agent의 대화 히스토리 기능은 이전 대화 내용을 기억하여 연속적이고 자연스러운 대화를 가능하게 합니다.

## 🔄 작동 원리

### 1. 기본 구조

```python
class ConversationHistory:
    def __init__(self, history_file: str = "conversation_history.json"):
        self.current_session = []  # 메모리에 대화 저장
        self.max_history_length = 50  # 최대 50개 메시지만 유지
```

### 2. 메시지 저장 방식

- **메모리**: 현재 세션 동안 `current_session` 리스트에 저장
- **파일**: `conversation_history.json`에 영구 저장
- **구조**: 
  ```json
  {
    "role": "user/assistant",
    "content": "메시지 내용",
    "timestamp": "2025-01-01T12:00:00.000000"
  }
  ```

### 3. AI 에이전트 통합

```python
def process_message(self, user_input: str):
    # 1. 사용자 메시지를 히스토리에 추가
    self.conversation_history.add_message("user", user_input)
    
    # 2. 최근 10개 메시지를 컨텍스트로 사용
    recent_history = self.conversation_history.get_recent_messages(10)
    
    # 3. 히스토리와 함께 AI에게 전달
    response = self.simple_chat_with_history(user_input, recent_history)
    
    # 4. AI 응답도 히스토리에 추가
    self.conversation_history.add_message("assistant", response)
    
    # 5. 파일에 저장
    self.conversation_history.save_to_file()
```

## 🚀 실제 작동 흐름

### 대화 예시
```
사용자: "안녕하세요! 저는 김철수입니다."
AI: "안녕하세요, 김철수님! 무엇을 도와드릴까요?"

사용자: "제 이름을 기억하시나요?"
AI: "네, 기억하고 있습니다. 김철수님이시죠."
```

### 내부 처리 과정

#### 첫 번째 대화
```python
# LLM API 호출
messages = [
    SystemMessage("당신은 도움이 되는 AI 어시스턴트입니다."),
    HumanMessage("안녕하세요! 저는 김철수입니다.")
]
```

#### 두 번째 대화
```python
# LLM API 호출 (이전 대화 포함)
messages = [
    SystemMessage("당신은 도움이 되는 AI 어시스턴트입니다."),
    HumanMessage("안녕하세요! 저는 김철수입니다."),      # 1번째 대화
    AIMessage("안녕하세요, 김철수님! 무엇을 도와드릴까요?"),  # 1번째 응답
    HumanMessage("제 이름을 기억하시나요?")              # 2번째 질문
]
```

## 💰 토큰 사용량과 최적화

### 토큰 사용량 증가 패턴
- **1번째 질문**: 시스템 프롬프트 + 첫 질문 = 적은 토큰
- **2번째 질문**: 시스템 프롬프트 + 1번째 대화 + 2번째 질문 = 더 많은 토큰
- **3번째 질문**: 시스템 프롬프트 + 1,2번째 대화 + 3번째 질문 = 훨씬 많은 토큰

### 최적화 전략

#### 1. 메시지 개수 제한
```python
# 최근 10개 메시지만 전송
recent_history = self.conversation_history.get_recent_messages(10)
```

#### 2. 토큰 수 제한
```python
def _limit_by_tokens(self, history):
    total_tokens = 0
    limited_history = []
    
    for msg in reversed(history):
        msg_tokens = self._estimate_tokens(msg['content'])
        if total_tokens + msg_tokens > 2000:  # 2000토큰 제한
            break
        limited_history.insert(0, msg)
        total_tokens += msg_tokens
    
    return limited_history
```

#### 3. 토큰 추정 알고리즘
```python
def _estimate_tokens(self, text: str) -> int:
    korean_chars = sum(1 for c in text if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3)
    english_words = len([w for w in text.split() if w.isascii()])
    other_chars = len(text) - korean_chars
    
    # 한글 1자 = 1.5토큰, 영어 1단어 = 1.3토큰
    estimated_tokens = int(korean_chars * 1.5 + english_words * 1.3 + other_chars * 0.8)
    return max(estimated_tokens, len(text) // 4)
```

## 📁 파일 저장 구조

### conversation_history.json
```json
{
  "last_updated": "2025-01-01T12:00:00.000000",
  "messages": [
    {
      "role": "user",
      "content": "안녕하세요! 저는 김철수입니다.",
      "timestamp": "2025-01-01T12:00:00.000000"
    },
    {
      "role": "assistant",
      "content": "안녕하세요, 김철수님! 무엇을 도와드릴까요?",
      "timestamp": "2025-01-01T12:00:01.000000"
    }
  ]
}
```

## 🎯 핵심 특징

### 자동 관리
- ✅ **자동 저장**: 매 대화마다 자동으로 파일에 저장
- ✅ **메모리 효율**: 최대 50개 메시지만 유지 (오래된 것은 자동 삭제)
- ✅ **컨텍스트 제한**: AI에게는 최근 10개 메시지만 전달 (토큰 절약)

### 영구 보존
- ✅ **앱 재시작**: 프로그램을 다시 시작해도 이전 대화 기억
- ✅ **세션 유지**: 여러 날에 걸친 대화도 연속성 유지

### 사용자 제어
- ✅ **초기화 기능**: 메뉴에서 언제든 대화 기록 삭제 가능
- ✅ **확인 대화상자**: 실수로 삭제하지 않도록 확인 절차

## 🔧 사용 방법

### GUI에서 사용
1. 일반적인 대화를 하면 자동으로 기억됩니다
2. **설정 > 대화 기록 초기화**로 기록 삭제 가능

### 프로그래밍에서 사용
```python
from core.conversation_history import ConversationHistory

# 히스토리 객체 생성
history = ConversationHistory()

# 메시지 추가
history.add_message("user", "안녕하세요!")
history.add_message("assistant", "안녕하세요! 무엇을 도와드릴까요?")

# 최근 메시지 조회
recent = history.get_recent_messages(5)

# 파일 저장
history.save_to_file()

# 파일에서 로드
history.load_from_file()

# 세션 초기화
history.clear_session()
```

## ⚠️ 주의사항

### 토큰 비용
- 대화가 길어질수록 매번 더 많은 토큰을 사용합니다
- 최적화 설정으로 비용을 제어할 수 있습니다

### 개인정보
- 대화 내용이 로컬 파일에 저장됩니다
- 민감한 정보는 대화 기록 초기화로 삭제하세요

### 성능
- 매우 긴 대화는 응답 속도에 영향을 줄 수 있습니다
- 정기적인 기록 초기화를 권장합니다

## 🚀 향후 개선 계획

- [ ] 대화 주제별 분류 기능
- [ ] 중요한 대화만 선별 저장
- [ ] 대화 검색 기능
- [ ] 대화 내보내기/가져오기
- [ ] 더 정교한 토큰 최적화