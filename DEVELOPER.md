# 🔧 개발자 가이드 (Developer Guide)

Chat AI Agent 프로젝트의 개발자를 위한 상세 가이드입니다.

## 📁 프로젝트 구조 (Project Structure)

```
chat-ai-agent/
├── core/                           # 핵심 비즈니스 로직
│   ├── application/               # 애플리케이션 초기화 및 실행
│   │   ├── app_initializer.py    # 앱 초기화
│   │   ├── app_runner.py         # 앱 실행기
│   │   └── signal_handler.py     # 시그널 처리
│   ├── chat/                     # 채팅 처리기
│   │   ├── base_chat_processor.py    # 기본 채팅 처리기
│   │   ├── simple_chat_processor.py  # 단순 채팅 처리
│   │   └── tool_chat_processor.py    # 도구 사용 채팅 처리
│   ├── client/                   # 클라이언트 관리
│   │   ├── chat_client.py        # 채팅 클라이언트
│   │   ├── conversation_manager.py   # 대화 관리
│   │   └── prompt_manager.py     # 프롬프트 관리
│   ├── config/                   # 설정 관리
│   │   ├── config_manager.py     # 설정 관리자
│   │   └── model_config.py       # 모델 설정
│   ├── llm/                      # LLM 제공자별 구현
│   │   ├── google/               # Google Gemini
│   │   ├── openai/               # OpenAI GPT
│   │   └── perplexity/           # Perplexity
│   ├── mcp/                      # MCP 서비스
│   │   ├── interfaces.py         # MCP 인터페이스
│   │   └── service_impl.py       # MCP 서비스 구현
│   ├── models/                   # AI 모델 전략 패턴
│   │   ├── base_model_strategy.py    # 기본 모델 전략
│   │   ├── openai_strategy.py        # OpenAI 전략
│   │   ├── gemini_strategy.py        # Gemini 전략
│   │   ├── perplexity_strategy.py    # Perplexity 전략
│   │   ├── claude_strategy.py        # Claude 전략
│   │   └── model_strategy_factory.py # 전략 팩토리
│   ├── processors/               # 메시지 처리기
│   │   ├── message_converter.py  # 메시지 변환
│   │   ├── image_processor.py    # 이미지 처리
│   │   └── tool_result_formatter.py # 도구 결과 포맷팅
│   ├── ai_agent.py              # 메인 AI 에이전트
│   ├── ai_agent_v2.py           # 리팩토링된 AI 에이전트
│   ├── conversation_history.py   # 대화 히스토리 관리
│   └── file_utils.py            # 파일 유틸리티
├── mcp/                         # MCP 관련 모든 기능
│   ├── client/                  # MCP 클라이언트
│   │   ├── mcp_client.py        # 메인 MCP 클라이언트
│   │   ├── mcp_simple.py        # 단순 MCP 클라이언트
│   │   └── mcp_state.py         # MCP 상태 관리
│   ├── servers/                 # MCP 서버 관리
│   │   └── mcp.py               # MCP 서버 제어
│   └── tools/                   # MCP 도구 관리
│       └── tool_manager.py      # 도구 관리자
├── tools/                       # 독립적인 도구들
│   ├── langchain/               # LangChain 도구 래퍼
│   │   └── langchain_tools.py   # LangChain 도구 통합
│   └── strategies/              # 도구 선택 전략
│       └── tool_decision_strategy.py # 도구 결정 전략
├── ui/                          # GUI 인터페이스
│   ├── components/              # UI 컴포넌트
│   │   ├── ai_processor.py      # AI 처리 컴포넌트
│   │   ├── chat_display.py      # 채팅 디스플레이
│   │   ├── file_handler.py      # 파일 핸들러
│   │   └── ui_manager.py        # UI 관리자
│   ├── handlers/                # 이벤트 핸들러
│   │   └── dialog_handler.py    # 대화상자 핸들러
│   ├── menu/                    # 메뉴 시스템
│   │   └── menu_factory.py      # 메뉴 팩토리
│   ├── services/                # UI 서비스
│   │   └── mcp_service.py       # MCP UI 서비스
│   ├── styles/                  # 스타일 관리
│   │   └── theme_manager.py     # 테마 관리자
│   ├── main_window.py           # 메인 윈도우
│   ├── chat_widget.py           # 채팅 위젯
│   ├── settings_dialog.py       # 설정 대화상자
│   └── mcp_dialog.py            # MCP 설정 대화상자
├── config.json                  # 설정 파일
├── mcp.json                     # MCP 서버 설정
├── requirements.txt             # Python 의존성
└── main.py                      # 애플리케이션 진입점
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
```

### 통합 테스트
```python
# tests/test_integration.py
from core.ai_agent import AIAgent

class TestIntegration(unittest.TestCase):
    def test_full_conversation_flow(self):
        agent = AIAgent(api_key, 'gpt-3.5-turbo')
        response, tools = agent.process_message("Hello")
        self.assertIsNotNone(response)
```

## 🔍 디버깅 가이드

### 로깅 설정
```python
import logging

# 개발 시 디버그 로깅 활성화
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### MCP 서버 디버깅
```bash
# MCP 서버 상태 확인
python -c "from mcp.client.mcp_client import MCPClient; print(MCPClient().get_server_status())"
```

### UI 디버깅
```python
# Qt 디버그 정보 출력
import os
os.environ['QT_LOGGING_RULES'] = '*=true'
```

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

## 📚 참고 자료

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython-6/)
- [LangChain Documentation](https://python.langchain.com/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [GoF Design Patterns](https://en.wikipedia.org/wiki/Design_Patterns)

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