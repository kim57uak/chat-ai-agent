# 🔧 개발자 가이드 (Developer Guide)

Chat AI Agent 프로젝트의 개발자를 위한 상세 가이드입니다.

## 📁 프로젝트 구조 (Project Structure)

```
chat-ai-agent/
├── core/                              # 핵심 비즈니스 로직
│   ├── application/                   # 애플리케이션 라이프사이클
│   │   ├── app_initializer.py        # 앱 초기화 및 설정
│   │   ├── app_runner.py             # 앱 실행 관리
│   │   └── signal_handler.py         # 시그널 처리
│   ├── auth/                          # 인증 및 보안
│   │   └── auth_manager.py           # 사용자 인증 관리
│   ├── chat/                          # 채팅 처리 로직
│   │   ├── base_chat_processor.py    # 채팅 처리 기본 클래스
│   │   ├── simple_chat_processor.py  # 단순 대화 처리
│   │   └── tool_chat_processor.py    # 도구 연동 대화 처리
│   ├── client/                        # 클라이언트 계층
│   │   ├── chat_client.py            # 채팅 클라이언트
│   │   ├── conversation_manager.py   # 대화 히스토리 관리
│   │   └── prompt_manager.py         # 프롬프트 관리
│   ├── config/                        # 설정 관리
│   │   ├── ai_model_manager.py       # AI 모델 설정 관리
│   │   ├── config_manager.py         # 전역 설정 관리
│   │   └── model_config.py           # 모델별 설정
│   ├── formatters/                    # 포맷터
│   │   └── enhanced_markdown_parser.py # 마크다운 파싱
│   ├── llm/                           # LLM 제공자별 구현
│   │   ├── claude/                   # Anthropic Claude
│   │   ├── google/                   # Google Gemini
│   │   ├── openai/                   # OpenAI GPT
│   │   └── perplexity/               # Perplexity AI
│   ├── mcp/                           # MCP 서비스 계층
│   │   ├── interfaces.py             # MCP 인터페이스 정의
│   │   └── service_impl.py           # MCP 서비스 구현
│   ├── models/                        # AI 모델 전략 패턴
│   │   ├── base_model_strategy.py    # 전략 패턴 기본 클래스
│   │   ├── openai_strategy.py        # OpenAI 전략
│   │   ├── gemini_strategy.py        # Gemini 전략
│   │   ├── gemini_image_strategy.py  # Gemini 이미지 생성
│   │   ├── claude_strategy.py        # Claude 전략
│   │   ├── perplexity_strategy.py    # Perplexity 전략
│   │   ├── pollinations_strategy.py  # Pollinations 전략
│   │   ├── openrouter_strategy.py    # OpenRouter 전략
│   │   └── model_strategy_factory.py # 전략 팩토리
│   ├── news/                          # 뉴스 기능
│   │   └── rss_parser.py             # RSS 피드 파싱
│   ├── parsers/                       # 응답 파서
│   │   ├── claude_react_parser.py    # Claude ReAct 파싱
│   │   └── custom_react_parser.py    # 커스텀 ReAct 파싱
│   ├── processors/                    # 메시지 처리기
│   │   ├── complete_output_formatter.py # 출력 포맷팅
│   │   ├── image_processor.py        # 이미지 처리
│   │   ├── message_converter.py      # 메시지 변환
│   │   ├── tool_result_formatter.py  # 도구 결과 포맷팅
│   │   ├── simple_chat_processor.py  # 단순 채팅 처리
│   │   └── tool_chat_processor.py    # 도구 채팅 처리
│   ├── security/                      # 보안 계층
│   │   ├── auth_manager.py           # 인증 관리
│   │   ├── encrypted_config.py       # 설정 암호화
│   │   ├── encrypted_database.py     # DB 암호화
│   │   ├── encryption_manager.py     # 암호화 관리
│   │   ├── memory_security.py        # 메모리 보안
│   │   ├── secure_path_manager.py    # 경로 보안
│   │   ├── security_logger.py        # 보안 로깅
│   │   ├── session_security.py       # 세션 보안
│   │   ├── data_migration.py         # 데이터 마이그레이션
│   │   └── version_manager.py        # 버전 관리
│   ├── session/                       # 세션 관리
│   │   ├── message_manager.py        # 메시지 관리
│   │   ├── session_database.py       # 세션 DB
│   │   ├── session_exporter.py       # 세션 내보내기
│   │   └── session_manager.py        # 세션 관리자
│   └── strategies/                    # 전략 패턴
│       └── model_strategy.py         # 모델 전략
├── mcp/                               # MCP 프로토콜 구현
│   ├── client/                        # MCP 클라이언트
│   │   ├── mcp_client.py             # 메인 클라이언트
│   │   ├── mcp_simple.py             # 단순 클라이언트
│   │   ├── mcp_state.py              # 상태 관리
│   │   └── mcp_state_simple.py       # 단순 상태 관리
│   ├── servers/                       # MCP 서버 관리
│   │   └── mcp.py                    # 서버 제어
│   └── tools/                         # MCP 도구
│       └── tool_manager.py           # 도구 관리자
├── tools/                             # 외부 도구 통합
│   ├── langchain/                     # LangChain 통합
│   │   └── langchain_tools.py        # LangChain 도구 래퍼
│   └── strategies/                    # 도구 전략
├── ui/                                # GUI 인터페이스
│   ├── auth/                          # 인증 UI
│   │   └── login_dialog.py           # 로그인 대화상자
│   ├── components/                    # UI 컴포넌트
│   │   ├── ai_processor.py           # AI 처리 컴포넌트
│   │   ├── chat_display.py           # 채팅 디스플레이
│   │   ├── code_executor.py          # 코드 실행기
│   │   ├── file_handler.py           # 파일 핸들러
│   │   ├── model_manager.py          # 모델 관리 UI
│   │   ├── modern_progress_bar.py    # 진행바
│   │   ├── news_banner_simple.py     # 뉴스 배너
│   │   ├── progressive_display.py    # 점진적 표시
│   │   ├── status_display.py         # 상태 표시
│   │   ├── token_usage_display.py    # 토큰 사용량 표시
│   │   └── ui_manager.py             # UI 관리자
│   ├── handlers/                      # 이벤트 핸들러
│   │   └── dialog_handler.py         # 대화상자 핸들러
│   ├── menu/                          # 메뉴 시스템
│   │   └── menu_factory.py           # 메뉴 팩토리
│   ├── services/                      # UI 서비스
│   │   └── mcp_service.py            # MCP UI 서비스
│   ├── settings/                      # 설정 UI
│   │   └── settings.html             # 설정 페이지
│   ├── styles/                        # 테마 및 스타일
│   │   ├── material_design_system.py # Material Design
│   │   ├── material_stylesheet.py    # Material 스타일시트
│   │   ├── material_theme_manager.py # Material 테마 관리
│   │   ├── flat_theme.py             # Flat 테마
│   │   ├── modern_glass_theme.py     # Glass 테마
│   │   ├── qt_compatible_theme.py    # Qt 호환 테마
│   │   ├── scrollbar_fix.py          # 스크롤바 수정
│   │   └── theme_manager.py          # 테마 관리자
│   ├── main_window.py                 # 메인 윈도우
│   ├── chat_widget.py                 # 채팅 위젯
│   ├── session_panel.py               # 세션 패널
│   ├── settings_dialog.py             # 설정 대화상자
│   ├── mcp_dialog.py                  # MCP 설정 대화상자
│   ├── markdown_formatter.py          # 마크다운 포맷터
│   ├── syntax_highlighter.py          # 구문 강조
│   ├── template_dialog.py             # 템플릿 대화상자
│   ├── template_manager.py            # 템플릿 관리
│   └── prompts.py                     # 프롬프트 관리
├── scripts/                           # 유틸리티 스크립트
│   ├── migrate_data.py                # 데이터 마이그레이션
│   └── verify_migration.py            # 마이그레이션 검증
├── utils/                             # 유틸리티
│   ├── config_path.py                 # 설정 경로 관리
│   └── env_loader.py                  # 환경변수 로더
├── .github/workflows/                 # CI/CD
│   ├── build.yml                      # 빌드 워크플로우
│   └── build-release.yml              # 릴리즈 워크플로우
├── config.json                        # 메인 설정 파일
├── mcp.json                           # MCP 서버 설정
├── prompt_config.json                 # 프롬프트 설정
├── theme.json                         # 테마 설정
├── templates.json                     # 템플릿 설정
├── requirements.txt                   # Python 의존성
├── build_package.py                   # 패키징 스크립트
├── main.py                            # 애플리케이션 진입점
├── README.md                          # 사용자 가이드
└── DEVELOPER.md                       # 개발자 가이드
```

## 🏗️ 아키텍처 원칙

### SOLID 원칙 적용

#### 1. Single Responsibility Principle (SRP)
각 클래스는 하나의 명확한 책임만 가집니다:
- `ChatClient`: 채팅 클라이언트 관리만 담당
- `ConversationManager`: 대화 히스토리 관리만 담당
- `ModelStrategy`: 특정 AI 모델 처리만 담당

#### 2. Open/Closed Principle (OCP)
확장에는 열려있고 수정에는 닫혀있는 구조:
```python
# 새로운 모델 전략 추가 시 기존 코드 수정 없이 확장
class NewModelStrategy(BaseModelStrategy):
    def create_llm(self):
        # 새로운 모델 구현
        pass
```

#### 3. Liskov Substitution Principle (LSP)
상위 타입을 하위 타입으로 완전히 대체 가능:
```python
# 모든 전략은 BaseModelStrategy를 완전히 구현
strategy: BaseModelStrategy = OpenAIStrategy()
strategy = GeminiStrategy()  # 완전히 대체 가능
```

#### 4. Interface Segregation Principle (ISP)
클라이언트가 사용하지 않는 인터페이스에 의존하지 않음:
```python
# 역할별로 인터페이스 분리
class ChatProcessor(ABC):
    @abstractmethod
    def process_chat(self, message): pass

class ToolManager(ABC):
    @abstractmethod
    def get_tools(self): pass
```

#### 5. Dependency Inversion Principle (DIP)
추상화에 의존하고 구체화에 의존하지 않음:
```python
# 구체 클래스가 아닌 추상화에 의존
class AIAgent:
    def __init__(self, strategy: BaseModelStrategy):
        self.strategy = strategy  # 추상화에 의존
```

### GoF 디자인 패턴

#### 1. Strategy Pattern
AI 모델별 처리 전략:
```python
class ModelStrategyFactory:
    @classmethod
    def get_strategy(cls, model_name: str) -> BaseModelStrategy:
        if 'gpt' in model_name:
            return OpenAIStrategy()
        elif 'gemini' in model_name:
            return GeminiStrategy()
        # ...
```

#### 2. Factory Pattern
객체 생성을 팩토리로 캡슐화:
```python
class LLMFactory:
    @staticmethod
    def create_llm(model_name: str, api_key: str):
        # 모델별 LLM 인스턴스 생성
        pass
```

#### 3. Observer Pattern
UI 상태 변경 알림:
```python
class UIStateManager:
    def __init__(self):
        self.observers = []
    
    def notify_observers(self, event):
        for observer in self.observers:
            observer.update(event)
```

#### 4. Chain of Responsibility Pattern
파일 처리기 체인:
```python
class FileProcessor:
    def __init__(self):
        self.next_processor = None
    
    def process(self, file_path):
        if self.can_process(file_path):
            return self.do_process(file_path)
        elif self.next_processor:
            return self.next_processor.process(file_path)
```

## 🔧 개발 가이드

### 새로운 AI 모델 추가

#### 1단계: 전략 클래스 생성
```python
# core/models/new_model_strategy.py
from core.models.base_model_strategy import BaseModelStrategy

class NewModelStrategy(BaseModelStrategy):
    def get_model_type(self) -> str:
        return "new_model"
    
    def supports_model(self, model_name: str) -> bool:
        return 'new_model' in model_name.lower()
    
    def create_llm(self, api_key: str, model_name: str):
        # 새 모델의 LLM 인스턴스 생성
        pass
    
    def create_messages(self, user_input: str, system_prompt: str = None):
        # 모델별 메시지 형식 구현
        pass
```

#### 2단계: 팩토리에 등록
```python
# core/models/model_strategy_factory.py
from .new_model_strategy import NewModelStrategy

class ModelStrategyFactory:
    _strategies = {
        'new_model': NewModelStrategy,
        # 기존 전략들...
    }
```

#### 3단계: 설정 파일 업데이트
```json
{
  "models": {
    "new-model-name": {
      "api_key": "your-api-key",
      "provider": "new_model"
    }
  }
}
```

### 새로운 MCP 서버 추가

#### 1단계: MCP 설정 추가
```json
{
  "mcpServers": {
    "new-server": {
      "command": "node",
      "args": ["/path/to/server.js"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

#### 2단계: 도구 매핑 (선택사항)
```python
# tools/langchain/langchain_tools.py
TOOL_EMOJI_MAP = {
    'new_tool_name': '🆕',
    # 기존 매핑들...
}
```

### 새로운 UI 컴포넌트 추가

#### 1단계: 컴포넌트 클래스 생성
```python
# ui/components/new_component.py
from PyQt6.QtWidgets import QWidget

class NewComponent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        # UI 설정
        pass
```

#### 2단계: 메인 윈도우에 통합
```python
# ui/main_window.py
from ui.components.new_component import NewComponent

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.new_component = NewComponent(self)
        # 레이아웃에 추가
```

## 🧪 테스트 가이드

### 테스트 환경 설정
```bash
# 테스트 의존성 설치
pip install pytest pytest-cov pytest-mock

# 테스트 실행
pytest tests/

# 커버리지 포함 테스트
pytest --cov=core --cov=ui tests/
```

### 단위 테스트 작성
```python
# tests/test_model_strategy.py
import unittest
from core.models.openai_strategy import OpenAIStrategy

class TestOpenAIStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = OpenAIStrategy()
    
    def test_supports_model(self):
        self.assertTrue(self.strategy.supports_model('gpt-3.5-turbo'))
        self.assertFalse(self.strategy.supports_model('gemini-pro'))
    
    def test_create_llm(self):
        llm = self.strategy.create_llm('test-key', 'gpt-3.5-turbo')
        self.assertIsNotNone(llm)
```

### 통합 테스트
```python
# tests/test_integration.py
from core.ai_agent import AIAgent
import pytest

class TestIntegration:
    @pytest.fixture
    def agent(self):
        return AIAgent(api_key='test-key', model='gpt-3.5-turbo')
    
    def test_full_conversation_flow(self, agent):
        response, tools = agent.process_message("Hello")
        assert response is not None
        assert isinstance(response, str)
    
    def test_tool_execution(self, agent):
        response, tools = agent.process_message("Search for Python")
        assert tools is not None
```

### UI 테스트
```python
# tests/test_ui.py
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow

class TestMainWindow:
    def test_window_creation(self, qtbot):
        window = MainWindow()
        qtbot.addWidget(window)
        assert window.isVisible()
    
    def test_send_message(self, qtbot):
        window = MainWindow()
        qtbot.addWidget(window)
        qtbot.keyClicks(window.input_field, "Hello")
        qtbot.keyClick(window.input_field, Qt.Key.Key_Return)
```

### 테스트 커버리지 목표
- **Core 모듈**: 80% 이상
- **UI 모듈**: 60% 이상
- **전체**: 70% 이상

## 🔍 디버깅 가이드

### 로깅 시스템

#### 기본 로깅 설정
```python
import logging
from core.logging.loguru_setup import setup_loguru

# Loguru 초기화 (중복 방지)
setup_loguru()

# 로거 사용
from loguru import logger
logger.info("Application started")
logger.debug("Debug information")
logger.error("Error occurred")
```

#### 로그 파일 위치
```
~/.chat-ai-agent/logs/
├── app.log              # 메인 애플리케이션 로그
├── mcp.log              # MCP 서버 로그
├── security.log         # 보안 이벤트 로그
├── error.log            # 에러 로그
└── token_usage.log      # 토큰 사용량 로그
```

#### 로거 핸들러 중복 방지
```python
# core/logging/loguru_setup.py
_loguru_initialized = False

def setup_loguru():
    global _loguru_initialized
    if _loguru_initialized:
        return  # 이미 초기화됨
    
    # 핸들러 등록
    logger.add("app.log", rotation="10 MB")
    _loguru_initialized = True
```

**중요**: 로거 핸들러가 중복 등록되면 파일 디스크립터(FD) 누수가 발생하여 시스템 크래시를 유발할 수 있습니다.

### MCP 서버 디버깅

#### 서버 상태 확인
```bash
# 서버 상태 확인
python -c "from mcp.client.mcp_client import MCPClient; print(MCPClient().get_server_status())"

# 서버 로그 확인
tail -f ~/.chat-ai-agent/logs/mcp.log

# 특정 서버 디버깅
export MCP_DEBUG=1
python main.py
```

#### 도구 실행 디버깅
```python
# tools/langchain/langchain_tools.py
import logging
logger = logging.getLogger(__name__)

def execute_tool(tool_name, input_data):
    logger.debug(f"Executing tool: {tool_name}")
    logger.debug(f"Input: {input_data}")
    result = tool.run(input_data)
    logger.debug(f"Result: {result}")
    return result
```

### UI 디버깅

#### Qt 디버그 모드
```python
# Qt 디버그 정보 출력
import os
os.environ['QT_LOGGING_RULES'] = '*=true'
os.environ['QT_DEBUG_PLUGINS'] = '1'
```

#### WebEngine 디버깅
```python
# ui/components/chat_display.py
from PyQt6.QtWebEngineCore import QWebEngineSettings

settings = self.page().settings()
settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
```

#### 메모리 누수 감지
```python
import tracemalloc

# 메모리 추적 시작
tracemalloc.start()

# 코드 실행

# 메모리 사용량 확인
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 10**6}MB, Peak: {peak / 10**6}MB")
tracemalloc.stop()
```

### 성능 프로파일링

#### cProfile 사용
```bash
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats
```

#### line_profiler 사용
```python
from line_profiler import LineProfiler

lp = LineProfiler()
lp.add_function(process_message)
lp.run('process_message("test")')
lp.print_stats()
```

## 📊 시스템 모니터링 및 안정성

### 리소스 모니터링 도구

#### 실시간 모니터링
```bash
# 기본 모니터링 (2초 간격)
python monitor_chatai.py

# 커스텀 간격 (5초)
python monitor_chatai.py 5

# 현재 상태 요약
python monitor_chatai.py summary
```

#### 모니터링 지표

**메모리 관리**
- **실시간 메모리 사용량**: RSS 메모리 추적
- **메모리 증가율**: MB/분 단위 증가율 계산
- **GC 작동 감지**: 10MB 이상 감소 시 GC 감지
- **메모리 범위**: 최소/최대/평균 메모리 사용량

**파일 디스크립터(FD) 관리**
- **FD 사용량**: 현재 열린 파일/소켓 개수
- **FD 제한**: 시스템 제한 대비 사용률
- **FD 누수 감지**: 50개 이상 증가 시 경고
- **FD 범위**: 최소/최대/평균 FD 개수

**프로세스 관리**
- **CPU 사용률**: 메인 + 자식 프로세스 합계
- **자식 프로세스**: MCP 서버 개수 추적
- **프로세스 상태**: 실행/대기/종료 상태

#### 모니터링 출력 예시
```
[17:45:03] CPU:   0.0% | 메모리:  670.3MB ( 4.1%) | 자식:  6개 
📊 증가중 +14.0MB/분 (GC: 73회) [-16MB] | FD: 354/104857555
```

#### 종료 시 최종 분석
```
📊 모니터링 종료 - 최종 분석
총 모니터링 시간: 11.6분
메모리 변화: -181.4MB
평균 증가율: -15.57MB/분
메모리 범위: 322.2MB ~ 926.4MB (변동폭: 604.2MB)

GC 작동 감지: 13회
GC 평균 주기: 0.9분마다

FD 변화: +0 (범위: 352~374, 평균: 357)
✅ FD 안정: 0.034% 사용

✅ 우수: 메모리 안정적으로 관리됨
   → GC가 효과적으로 작동 중
```

### 자동 메모리 정리

#### 메모리 클린업 설정
```python
# memory_cleanup.py
class MemoryCleanup:
    def __init__(self, interval=60):
        self.interval = interval  # 60초마다 정리
        self.running = False
    
    def cleanup(self):
        """메모리 정리 실행"""
        # 가비지 컬렉션 강제 실행
        collected = gc.collect()
        
        # 메모리 사용량 확인
        process = psutil.Process()
        mem_info = process.memory_info()
        
        # FD 사용량 확인
        fd_count = self.get_fd_count()
        fd_limit = self.get_fd_limit()
        
        logger.info(f"Cleanup: {collected} objects, "
                   f"Memory: {mem_info.rss / 1024 / 1024:.1f}MB, "
                   f"FD: {fd_count}/{fd_limit}")
```

#### 자동 정리 활성화
```python
# main.py
from memory_cleanup import MemoryCleanup

cleanup = MemoryCleanup(interval=60)
cleanup.start()  # 백그라운드에서 60초마다 정리
```

### 안정성 검증 결과

#### 장시간 안정성 테스트

**테스트 환경**
- **플랫폼**: macOS
- **Python**: 3.11
- **테스트 시간**: 51분 연속 실행

**테스트 결과**
```
✅ 메모리 누수: 없음 (-189.8MB 감소)
✅ FD 누수: 없음 (+0개 변화)
✅ GC 동작: 정상 (83회, 0.6분마다)
✅ CPU 사용: 안정적 (평균 0.0%)
✅ 크래시: 없음
```

**주요 개선 사항**
1. **로거 핸들러 중복 해결**: 3x 중복 → 1x (FD 누수 원인 제거)
2. **FD 모니터링 추가**: 실시간 FD 사용량 추적
3. **자동 메모리 정리**: 60초마다 GC 실행
4. **프롬프트 경고 해결**: 존재하지 않는 프롬프트 요청 제거

### 문제 해결 가이드

#### 메모리 누수 의심 시

**증상**
- 메모리 사용량이 지속적으로 증가 (+2MB/분 이상)
- GC가 작동하지 않음 (0회)
- 장시간 사용 시 느려짐

**진단**
```bash
# 1. 모니터링 시작
python monitor_chatai.py

# 2. 10분 이상 관찰
# - 메모리 증가율 확인
# - GC 작동 횟수 확인

# 3. Ctrl+C로 종료 후 최종 분석 확인
```

**해결 방법**
```python
# 1. 명시적 GC 호출
import gc
gc.collect()

# 2. 대용량 객체 삭제
del large_object
gc.collect()

# 3. 약한 참조 사용
import weakref
weak_ref = weakref.ref(obj)
```

#### FD 누수 의심 시

**증상**
- FD 개수가 지속적으로 증가 (+50개 이상)
- "Too many open files" 에러
- 파일/소켓 열기 실패

**진단**
```bash
# macOS/Linux: 열린 파일 확인
lsof -p <PID> | wc -l

# 파일 종류별 개수
lsof -p <PID> | awk '{print $5}' | sort | uniq -c
```

**해결 방법**
```python
# 1. 파일 자동 닫기 (with 문 사용)
with open('file.txt', 'r') as f:
    content = f.read()
# 자동으로 닫힘

# 2. 명시적 닫기
file = open('file.txt', 'r')
try:
    content = file.read()
finally:
    file.close()

# 3. 로거 핸들러 중복 방지
from core.logging.loguru_setup import setup_loguru
setup_loguru()  # 한 번만 호출
```

#### GC 작동하지 않을 때

**증상**
- 메모리 증가하지만 GC 횟수 0회
- 메모리가 감소하지 않음

**해결 방법**
```python
# 1. 순환 참조 확인
import gc
gc.set_debug(gc.DEBUG_SAVEALL)
gc.collect()
print(f"Uncollectable: {len(gc.garbage)}")

# 2. 강제 GC 실행
import gc
gc.collect(0)  # 세대 0
gc.collect(1)  # 세대 1
gc.collect(2)  # 세대 2

# 3. 약한 참조로 변경
import weakref
self.cache = weakref.WeakValueDictionary()
```

### 성능 최적화 팁

#### 메모리 최적화
```python
# 1. 제너레이터 사용 (대용량 데이터)
def process_large_data():
    for item in large_list:
        yield process(item)  # 한 번에 하나씩 처리

# 2. __slots__ 사용 (클래스 메모리 절약)
class Message:
    __slots__ = ['content', 'timestamp', 'role']
    
# 3. 캐시 크기 제한
from functools import lru_cache
@lru_cache(maxsize=100)  # 최대 100개만 캐시
def expensive_function(arg):
    pass
```

#### FD 최적화
```python
# 1. 연결 풀 사용
from urllib3 import PoolManager
http = PoolManager(maxsize=10)  # 최대 10개 연결

# 2. 파일 핸들 재사용
class FileCache:
    def __init__(self):
        self.handles = {}
    
    def get_handle(self, path):
        if path not in self.handles:
            self.handles[path] = open(path, 'r')
        return self.handles[path]
    
    def close_all(self):
        for handle in self.handles.values():
            handle.close()

# 3. 타임아웃 설정
import socket
socket.setdefaulttimeout(10)  # 10초 타임아웃
```

### 모니터링 베스트 프랙티스

#### 개발 환경
```bash
# 개발 중 항상 모니터링 실행
python monitor_chatai.py &

# 로그 확인
tail -f ~/.chat-ai-agent/logs/app.log
```

#### 프로덕션 환경
```bash
# 백그라운드 모니터링
nohup python monitor_chatai.py > monitor.log 2>&1 &

# 주기적 상태 확인 (cron)
*/10 * * * * python monitor_chatai.py summary >> status.log
```

#### 경고 임계값

**메모리**
- 🟢 정상: -0.5 ~ +0.5 MB/분
- 🟡 주의: +0.5 ~ +1.5 MB/분
- 🔴 경고: +1.5 MB/분 이상

**FD 사용률**
- 🟢 정상: 0 ~ 60%
- 🟡 주의: 60 ~ 80%
- 🔴 경고: 80% 이상

**GC 주기**
- 🟢 정상: 0.5 ~ 2분마다
- 🟡 주의: 2 ~ 5분마다
- 🔴 경고: 5분 이상 또는 0회

## 📦 배포 가이드

### 실행 파일 생성
```bash
# PyInstaller 사용
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

### Docker 컨테이너
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

## 🔒 보안 고려사항

### API 키 관리
- 환경 변수 사용 권장
- 설정 파일은 `.gitignore`에 추가
- 프로덕션에서는 암호화된 저장소 사용

### 입력 검증
```python
def validate_user_input(user_input: str) -> bool:
    # 악성 입력 검증
    if len(user_input) > MAX_INPUT_LENGTH:
        return False
    # 추가 검증 로직
    return True
```

## 🚀 성능 최적화

### 메모리 관리
```python
# 대용량 응답 처리 시 청크 단위로 처리
def process_large_response(response: str):
    chunk_size = 1000
    for i in range(0, len(response), chunk_size):
        chunk = response[i:i + chunk_size]
        yield chunk
```

### 비동기 처리
```python
import asyncio

async def async_tool_execution(tool, input_data):
    # 비동기 도구 실행
    result = await tool.execute_async(input_data)
    return result
```

## 📊 주요 모듈 설명

### Core 모듈
- **application**: 앱 라이프사이클 관리
- **auth**: 사용자 인증 및 권한 관리
- **security**: 암호화, 보안 로깅, 데이터 보호
- **session**: 대화 세션 및 메시지 관리
- **models**: Strategy 패턴 기반 AI 모델 추상화
- **mcp**: Model Context Protocol 서비스 계층

### UI 모듈
- **components**: 재사용 가능한 UI 컴포넌트
- **styles**: Material Design 기반 테마 시스템
- **auth**: 로그인 및 인증 UI
- **settings**: 설정 관리 인터페이스

### MCP 모듈
- **client**: MCP 서버와의 통신 클라이언트
- **servers**: MCP 서버 프로세스 관리
- **tools**: 외부 도구 통합 및 관리

## 📦 패키징 및 배포

### 빌드 환경 설정

#### 필수 도구 설치
```bash
# 가상환경 설정
python -m venv venv
source venv/bin/activate

# 빌드 도구 설치
pip install -r requirements.txt
pip install pyinstaller

# macOS: DMG 생성 도구
brew install create-dmg

# Windows: NSIS 인스톨러 (선택사항)
# https://nsis.sourceforge.io/Download
```

### PyInstaller 설정

#### Spec 파일 생성
```python
# chat_ai_agent.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('theme.json', '.'),
        ('image/', 'image/'),
    ],
    hiddenimports=[
        'PyQt6.QtWebEngineCore',
        'langchain',
        'anthropic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
```

### 플랫폼별 빌드

#### macOS 빌드
```bash
# 앱 번들 생성
pyinstaller chat_ai_agent.spec --clean --noconfirm

# DMG 생성
create-dmg \
  --volname "Chat AI Agent" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  "ChatAIAgent.dmg" \
  "dist/ChatAIAgent.app"

# 코드 서명 (선택사항)
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name" \
  ChatAIAgent.app

# 공증 (선택사항)
xcrun notarytool submit ChatAIAgent.dmg \
  --keychain-profile "notarytool-profile" \
  --wait
```

#### Windows 빌드
```bash
# EXE 생성
pyinstaller chat_ai_agent.spec --clean --noconfirm

# 코드 서명 (선택사항)
signtool sign /f certificate.p12 /p password \
  /t http://timestamp.digicert.com \
  ChatAIAgent.exe

# ZIP 압축
compress-archive -Path dist/ChatAIAgent -DestinationPath ChatAIAgent-Windows.zip
```

#### Linux 빌드
```bash
# 실행파일 생성
pyinstaller chat_ai_agent.spec --clean --noconfirm

# 실행 권한 부여
chmod +x dist/ChatAIAgent

# TAR.GZ 압축
tar -czf ChatAIAgent-Linux.tar.gz -C dist ChatAIAgent
```

### 빌드 결과물
```
build_output/
├── darwin/
│   ├── ChatAIAgent.app         # macOS 앱 번들
│   └── ChatAIAgent.dmg         # 배포용 DMG
├── windows/
│   ├── ChatAIAgent.exe         # Windows 실행파일
│   └── ChatAIAgent-Setup.exe   # 인스톨러
└── linux/
    └── ChatAIAgent             # Linux 실행파일
```

### 보안 기능

#### API 키 보호
```python
# build_package.py
def sanitize_config(config_path):
    """API 키를 샘플 값으로 대체"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    for model in config.get('models', {}).values():
        if 'api_key' in model:
            model['api_key'] = 'YOUR_API_KEY_HERE'
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
```

#### 자동 백업/복구
```python
# 빌드 전 백업
backup_configs = [
    'config.json',
    'mcp.json',
    'prompt_config.json',
    'theme.json'
]

for config in backup_configs:
    shutil.copy(config, f'backup/{config}')

# 빌드 후 복구
for config in backup_configs:
    shutil.copy(f'backup/{config}', config)
```

### CI/CD 파이프라인

#### GitHub Actions 설정
```yaml
# .github/workflows/build-release.yml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build
        run: python build_package.py
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ChatAIAgent-${{ matrix.os }}
          path: build_output/
```

### 배포 체크리스트

#### 빌드 전
- [ ] 모든 기능 테스트 완료
- [ ] 버전 번호 업데이트
- [ ] 라이선스 파일 포함
- [ ] README 업데이트
- [ ] 변경사항 (CHANGELOG) 작성

#### 빌드 후
- [ ] 각 플랫폼에서 실행 테스트
- [ ] API 연동 확인
- [ ] MCP 서버 연결 확인
- [ ] UI 테마 적용 확인
- [ ] 메모리 사용량 확인

#### 배포 전
- [ ] 릴리즈 노트 작성
- [ ] 설치 가이드 업데이트
- [ ] 사용자 문서 업데이트
- [ ] 다운로드 링크 테스트
- [ ] 코드 서명 완료 (선택사항)

## 🧠 코드 블록 기능

### 주요 기능
- **원클릭 복사**: 클립보드에 코드 복사
- **언어별 구문 강조**: 20개 이상 언어 지원
- **코드 실행**: Python, JavaScript 코드 즉시 실행

### 사용 방법
```python
# AI에게 요청
"""
Python으로 1부터 10까지 출력하는 코드 작성해줘
"""

# 코드 블록에 표시되는 버튼
# - 언어 라벨 (좌측 상단): PYTHON
# - 📋 복사 (우측)
# - ▶️ 실행 (우측, 녹색)
```

### 보안 고려사항
- **타임아웃**: 10초 제한
- **임시 파일**: 실행 후 자동 삭제
- **샌드박스**: 시스템 명령 직접 실행 방지

## 🔒 데이터 보안 및 마이그레이션

### 암호화 기능
- **데이터베이스 암호화**: 모든 대화 내용 암호화 저장
- **설정 파일 암호화**: API 키 및 민감 정보 보호
- **메모리 보안**: 사용 후 민감 데이터 자동 삭제

### 마이그레이션 절차
```bash
# 1. 백업 생성
cp ~/.chat-ai-agent/chat_sessions.db ~/.chat-ai-agent/chat_sessions_backup.db

# 2. 마이그레이션 실행
python scripts/migrate_data.py \
  --old-db ~/.chat-ai-agent/chat_sessions.db \
  --new-db ~/.chat-ai-agent/chat_sessions_encrypted.db

# 3. 검증
python scripts/verify_migration.py \
  --db ~/.chat-ai-agent/chat_sessions_encrypted.db
```

### 롤백 절차
```bash
# 자동 롤백 스크립트 사용
./rollback_script.sh

# 또는 수동 복구
cp backups/chat_sessions_backup_*.db ~/.chat-ai-agent/chat_sessions.db
```

## 📚 참고 자료

### 프로토콜 및 프레임워크
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython-6/)
- [LangChain Documentation](https://python.langchain.com/)

### 디자인 패턴 및 원칙
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [GoF Design Patterns](https://en.wikipedia.org/wiki/Design_Patterns)

### AI 모델 API
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Google Gemini API](https://ai.google.dev/docs)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Perplexity API](https://docs.perplexity.ai/)

## 🤝 기여 가이드

### 코딩 스타일
- PEP 8 준수
- Type hints 사용
- Docstring 작성 (Google 스타일)

### 커밋 메시지 규칙
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 스타일 변경
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 기타 작업
```

### Pull Request 가이드
1. 기능별로 브랜치 생성
2. 테스트 코드 작성
3. 문서 업데이트
4. 코드 리뷰 요청