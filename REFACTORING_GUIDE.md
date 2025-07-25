# 🔧 리팩토링 가이드

## 📋 개요

이 프로젝트는 SOLID 원칙과 디자인 패턴을 적용하여 AI 모델 확장성, 유지보수성, 가독성을 중심으로 리팩토링되었습니다.

## 🏗️ 아키텍처 개선사항

### 1. **SOLID 원칙 적용**

#### SRP (Single Responsibility Principle)
- `SimpleChatProcessor`: 단순 채팅 처리만 담당
- `ToolChatProcessor`: 도구 사용 채팅만 담당
- `MessageConverter`: 메시지 변환만 담당
- `ImageProcessor`: 이미지 처리만 담당
- `ToolResultFormatter`: 도구 결과 포맷팅만 담당

#### OCP (Open/Closed Principle)
- `ModelStrategy`: 새로운 AI 모델 추가 시 기존 코드 수정 없이 확장 가능
- `ModelStrategyFactory`: 전략 등록을 통한 확장

#### LSP (Liskov Substitution Principle)
- 모든 전략 클래스는 `ModelStrategy` 인터페이스를 완전히 구현
- 하위 클래스로 상위 클래스를 완전히 대체 가능

#### ISP (Interface Segregation Principle)
- `ChatProcessor`, `MessageConverter`, `ImageProcessor` 등 역할별 인터페이스 분리

#### DIP (Dependency Inversion Principle)
- 구체 클래스가 아닌 추상화에 의존
- Factory 패턴을 통한 의존성 주입

### 2. **디자인 패턴 적용**

#### Strategy Pattern
```python
# AI 모델별 처리 전략
class ModelStrategy(ABC):
    @abstractmethod
    def process_tool_chat(self, ...): pass

class GPTModelStrategy(ModelStrategy): ...
class GeminiModelStrategy(ModelStrategy): ...
class PerplexityModelStrategy(ModelStrategy): ...
```

#### Factory Pattern
```python
class ModelStrategyFactory:
    @classmethod
    def get_strategy(cls, model_name: str) -> ModelStrategy:
        # 모델명에 따른 적절한 전략 반환
```

#### Template Method Pattern
```python
class SimpleChatProcessor:
    def process_chat(self, ...):
        # 공통 처리 흐름 정의
        # 각 단계별로 전문화된 컴포넌트 사용
```

## 📁 새로운 디렉토리 구조

```
core/
├── processors/                 # 처리기 모듈들
│   ├── message_converter.py   # 메시지 변환
│   ├── image_processor.py     # 이미지 처리
│   ├── tool_result_formatter.py # 도구 결과 포맷팅
│   ├── simple_chat_processor.py # 단순 채팅 처리
│   └── tool_chat_processor.py # 도구 채팅 처리
├── strategies/                 # 전략 패턴 구현
│   ├── model_strategy.py      # 모델 전략 인터페이스
│   └── claude_model_strategy.py # 새 모델 추가 예시
├── chat_processor_refactored.py # 리팩토링된 메인 프로세서
└── chat_processor.py          # 하위 호환성 유지
```

## 🚀 새로운 AI 모델 추가 방법

### 1단계: 새로운 전략 클래스 생성

```python
# core/strategies/new_model_strategy.py
from core.strategies.model_strategy import ModelStrategy

class NewModelStrategy(ModelStrategy):
    def get_model_type(self) -> str:
        return "new_model"
    
    def supports_model(self, model_name: str) -> bool:
        return 'new_model' in model_name.lower()
    
    def process_tool_chat(self, user_input, llm, tools, agent_executor_factory, agent_executor=None):
        # 새 모델 특화 로직 구현
        pass
```

### 2단계: 전략 등록

```python
# 자동 등록
def register_new_model_strategy():
    from core.strategies.model_strategy import ModelStrategyFactory
    ModelStrategyFactory.register_strategy(NewModelStrategy())

register_new_model_strategy()
```

### 3단계: 사용

```python
# 기존 코드 수정 없이 자동으로 새 모델 지원
processor = ToolChatProcessor(tools, agent_executor_factory)
result = processor.process_chat("질문", new_model_llm)
```

## 🔄 하위 호환성

기존 코드는 수정 없이 그대로 작동합니다:

```python
# 기존 코드 - 그대로 작동
from core.chat_processor import SimpleChatProcessor, ToolChatProcessor

simple_processor = SimpleChatProcessor()
tool_processor = ToolChatProcessor(tools, factory)
```

## 📈 확장성 개선사항

### 1. **AI 모델 추가**
- 새로운 AI 모델 지원 시 기존 코드 수정 불필요
- 전략 패턴을 통한 모델별 특화 처리

### 2. **처리기 확장**
- 새로운 처리 방식 추가 시 기존 처리기에 영향 없음
- 각 처리기는 독립적으로 확장 가능

### 3. **포맷터 확장**
- 도구 결과 포맷팅 방식을 쉽게 변경/확장 가능
- AI 기반 포맷팅으로 하드코딩 제거

## 🛠️ 유지보수성 개선

### 1. **단일 책임**
- 각 클래스가 하나의 명확한 책임만 가짐
- 버그 수정 시 영향 범위 최소화

### 2. **의존성 분리**
- 컴포넌트 간 느슨한 결합
- 테스트 용이성 향상

### 3. **코드 재사용**
- 공통 로직의 중복 제거
- 모듈화를 통한 재사용성 증대

## 📖 가독성 개선

### 1. **명확한 네이밍**
- 클래스와 메서드명이 역할을 명확히 표현
- 의도를 쉽게 파악 가능

### 2. **구조화된 코드**
- 관련 기능별로 모듈 분리
- 계층적 구조로 이해하기 쉬움

### 3. **문서화**
- 각 컴포넌트의 역할과 사용법 명시
- 확장 방법 가이드 제공

## 🎯 사용 예시

### 기본 사용법
```python
from core.processors.simple_chat_processor import SimpleChatProcessor
from core.processors.tool_chat_processor import ToolChatProcessor

# 단순 채팅
simple_processor = SimpleChatProcessor()
response = simple_processor.process_chat("안녕하세요", llm, history)

# 도구 사용 채팅
tool_processor = ToolChatProcessor(tools, agent_factory)
response, used_tools = tool_processor.process_chat("파일 목록 보여줘", llm)
```

### 새 모델 전략 추가
```python
# 1. 전략 클래스 생성
class MyModelStrategy(ModelStrategy):
    # 구현...

# 2. 등록
ModelStrategyFactory.register_strategy(MyModelStrategy())

# 3. 자동으로 지원됨
```

이 리팩토링을 통해 코드의 확장성, 유지보수성, 가독성이 크게 향상되었으며, 새로운 AI 모델 추가가 매우 간단해졌습니다.