# Loguru 기반 중앙 집중식 로깅 시스템

## 📋 개요
Loguru 라이브러리를 사용한 간단하고 강력한 통합 로깅 시스템입니다.

## 🎯 현재 구조

### 파일 구성
```
core/logging/
├── __init__.py              # 로깅 모듈 진입점
├── loguru_setup.py         # Loguru 설정 및 초기화
├── unified_logger.py       # 통합 로거 (AI, Security, Token)
└── README.md              # 사용 가이드
```

### 로그 파일 구조
```
~/.chat-ai-agent/logs/
├── app.log                 # 전체 애플리케이션 로그
├── ai_interactions.log     # AI 상호작용 로그 (카테고리 필터링)
├── security.log            # 보안 이벤트 로그 (90일 보관)
└── token_usage.log         # 토큰 사용량 로그
```

## ✨ 주요 기능

### 1. Loguru 기반
- **Zero Configuration**: 기본 설정만으로 강력한 기능
- **간결한 API**: logger.info(), logger.debug() 등 직관적 사용
- **Thread Safe**: 멀티스레드 환경에서 안전

### 2. 비동기 로깅
- **enqueue=True**: 메인 스레드 블로킹 방지
- **성능 최적화**: I/O 작업을 백그라운드에서 처리

### 3. 자동 로테이션 & 압축
- **로테이션**: 10MB 단위 자동 파일 분할
- **압축**: 오래된 로그 자동 zip 압축
- **보관 기간**: 일반 로그 30일, 보안 로그 90일

### 4. 카테고리별 필터링
- **ai**: AI 상호작용 로그 → `ai_interactions.log`
- **security**: 보안 이벤트 → `security.log`
- **token**: 토큰 사용량 → `token_usage.log`

### 5. 컬러 출력
- **개발 환경**: 터미널에서 컬러로 로그 표시
- **자동 감지**: 터미널 지원 여부 자동 확인

### 6. 예외 추적
- **backtrace=True**: 상세한 스택 트레이스
- **diagnose=True**: 변수 값 포함 진단 정보

## 🚀 사용법

### 기본 로깅
```python
from core.logging import unified_logger

# 일반 로깅
unified_logger.info("Application started")
unified_logger.debug("Debug information")
unified_logger.warning("Warning message")
unified_logger.error("Error occurred", exc_info=True)
unified_logger.critical("Critical issue")
```

### AI 상호작용 로깅
```python
# AI 요청 로깅 (자동으로 ai_interactions.log에 기록)
request_id = unified_logger.log_ai_request(
    model="gpt-4",
    user_input="Hello, how are you?",
    system_prompt="You are a helpful assistant",
    conversation_history=[...],
    tools_available=["search", "calculator"],
    agent_mode=True
)

# AI 응답 로깅
unified_logger.log_ai_response(
    request_id=request_id,
    model="gpt-4",
    response="I'm doing well, thank you!",
    used_tools=["search"],
    token_usage={"input": 100, "output": 50},
    response_time=1.5
)

# 도구 호출 로깅
unified_logger.log_tool_call(
    request_id=request_id,
    tool_name="search",
    tool_input={"query": "weather"},
    tool_output="Sunny, 25°C",
    execution_time=0.3
)
```

### 토큰 사용량 로깅
```python
# 토큰 로깅 (자동으로 token_usage.log에 기록)
unified_logger.log_token_usage(
    model_name="gpt-4",
    input_tokens=100,
    output_tokens=50,
    operation="chat"
)
```

### 보안 이벤트 로깅
```python
# 로그인 시도 (자동으로 security.log에 기록)
unified_logger.log_login_attempt(
    success=True,
    details={"username": "user123", "ip": "192.168.1.1"}
)

# 로그아웃
unified_logger.log_logout(reason="user_initiated")

# 암호화 이벤트
unified_logger.log_encryption_event(
    event_type="encrypt",
    success=True,
    details="Session data encrypted"
)

# 보안 위반
unified_logger.log_security_violation(
    violation_type="unauthorized_access",
    details="Attempted access to restricted resource"
)
```

### Loguru 직접 사용
```python
from loguru import logger

# 직접 사용 가능
logger.info("Direct loguru usage")
logger.debug("Debug message")

# 카테고리 바인딩
logger.bind(category="ai").info("AI specific log")
logger.bind(category="security").warning("Security warning")
```

## 🔧 설정

### loguru_setup.py 주요 설정
```python
# 콘솔 출력 (개발 환경)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | ...",
    level="DEBUG",
    colorize=True,
    backtrace=True,
    diagnose=True
)

# 파일 출력 (비동기)
logger.add(
    log_dir / "app.log",
    level="DEBUG",
    rotation="10 MB",      # 10MB마다 로테이션
    retention="30 days",   # 30일 보관
    compression="zip",     # 자동 압축
    enqueue=True,         # 비동기 처리
    backtrace=True,
    diagnose=True
)

# 카테고리별 필터링
logger.add(
    log_dir / "ai_interactions.log",
    filter=lambda record: "ai" in record["extra"].get("category", "")
)
```

## 🛡️ 보안

### 민감 정보 자동 마스킹
```python
def _sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """민감 정보 자동 제거"""
    sensitive_keys = {'password', 'key', 'token', 'secret', 'api_key'}
    return {k: '[REDACTED]' if k.lower() in sensitive_keys else v 
            for k, v in data.items()}
```

### 보안 로그 장기 보관
- 일반 로그: 30일 보관
- 보안 로그: 90일 보관

## 📊 로그 형식

### 콘솔 출력 (컬러)
```
2024-01-15 10:30:45 | DEBUG    | mymodule:function:42 - Debug message
2024-01-15 10:30:46 | INFO     | mymodule:function:43 - Info message
2024-01-15 10:30:47 | WARNING  | mymodule:function:44 - Warning message
2024-01-15 10:30:48 | ERROR    | mymodule:function:45 - Error message
```

### 파일 출력
```
2024-01-15 10:30:45 | DEBUG    | mymodule:function:42 - Debug message
```

### AI 상호작용 로그 (JSON)
```json
{
  "type": "REQUEST",
  "request_id": "req_20240115_103045_123456",
  "timestamp": "2024-01-15T10:30:45.123456",
  "model": "gpt-4",
  "agent_mode": true,
  "user_input": "Hello...",
  "tools_available": ["search", "calculator"]
}
```

## 🎯 Loguru 장점

1. **Zero Configuration**: 복잡한 설정 불필요
2. **Thread Safe**: 멀티스레드 환경 안전
3. **Async Support**: 비동기 로깅으로 성능 향상
4. **Auto Rotation**: 파일 크기 기반 자동 로테이션
5. **Auto Compression**: 오래된 로그 자동 압축
6. **Rich Formatting**: 컬러, 시간, 위치 정보 자동 포함
7. **Exception Catching**: @logger.catch 데코레이터
8. **Lazy Evaluation**: 로그 레벨 체크 후 평가

## 🔄 마이그레이션

### 기존 코드 호환성
```python
# 기존 방식 (여전히 작동)
from core.logging import unified_logger
unified_logger.info("Message")

# Loguru 직접 사용 (권장)
from loguru import logger
logger.info("Message")

# 카테고리 바인딩
logger.bind(category="ai").info("AI log")
```

## 📈 성능 최적화

### 비동기 로깅
```python
# enqueue=True로 I/O 블로킹 방지
logger.add("app.log", enqueue=True)
```

### 카테고리 필터링
```python
# 불필요한 로그 제거
logger.add(
    "ai_interactions.log",
    filter=lambda record: "ai" in record["extra"].get("category", "")
)
```

### Lazy Evaluation
```python
# 로그 레벨 체크 후 평가
logger.debug("Data: {}", expensive_operation())  # DEBUG 레벨일 때만 실행
```

## 🐛 문제 해결

### 로그 파일 경로
1. `~/.chat-ai-agent/logs/` (기본)
2. 사용자 설정 경로 (config_path_manager)
3. `/tmp/chat-ai-agent/logs/` (fallback)

### 로그 확인
```bash
# 실시간 로그 확인
tail -f ~/.chat-ai-agent/logs/app.log

# AI 상호작용 로그
tail -f ~/.chat-ai-agent/logs/ai_interactions.log

# 보안 로그
tail -f ~/.chat-ai-agent/logs/security.log
```

## 📚 참고 자료

- [Loguru 공식 문서](https://loguru.readthedocs.io/)
- [Loguru GitHub](https://github.com/Delgan/loguru)

## 🎉 완료된 작업

- ✅ Loguru 기반 로깅 시스템 구축
- ✅ 비동기 로깅 (enqueue=True)
- ✅ 자동 로테이션 & 압축
- ✅ 카테고리별 필터링 (ai, security, token)
- ✅ 컬러 출력 (개발 환경)
- ✅ 예외 추적 (backtrace, diagnose)
- ✅ 민감 정보 자동 마스킹
- ✅ 통합 로거 (AI, Security, Token)
- ✅ Thread Safe 멀티스레드 지원

## 🚀 Next Steps

- [ ] 로그 분석 대시보드
- [ ] 로그 집계 및 통계
- [ ] 실시간 로그 모니터링
- [ ] Elasticsearch 연동 (선택사항)
- [ ] Grafana 대시보드 (선택사항)
