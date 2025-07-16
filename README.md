# 🤖 Chat AI Agent

다양한 MCP(Model Context Protocol) 서버와 연동하여 도구를 사용할 수 있는 AI 채팅 에이전트입니다.

## ✨ 주요 기능

- **MCP 서버 연동**: 다양한 외부 도구와 API 연동
- **지능형 도구 선택**: 사용자 질의에 따라 적절한 도구 자동 선택
- **GUI 인터페이스**: PyQt6 기반의 사용자 친화적 인터페이스
- **다중 LLM 지원**: OpenAI GPT, Google Gemini 등 다양한 모델 지원
- **실시간 스트리밍**: 대용량 AI 응답을 실시간으로 스트리밍하여 표시
- **대용량 응답 처리**: 긴 응답도 끊김 없이 완전하게 수신 및 표시
- **MCP 서버 관리**: 실시간 서버 상태 모니터링 및 제어
- **개선된 UI/UX**: 어두운 테마와 가독성 좋은 채팅 인터페이스
- **웹뷰 엔진**: QWebEngineView 기반의 고급 텍스트 렌더링
- **마크다운 지원**: 굵은 텍스트, 불릿 포인트, 코드 블록 포맷팅
- **대화 히스토리**: 이전 대화 문맥을 기억하여 연속적인 대화 지원

## 🛠️ 지원 도구

### 검색 도구
- 웹 검색 (Google, Bing 등)
- URL 페이지 내용 가져오기

### 데이터베이스 도구
- MySQL 데이터베이스 조회
- 테이블 스키마 확인
- SQL 쿼리 실행

### 여행 서비스 도구
- 하나투어 API 연동
- 여행 상품 검색
- 지역별 여행 정보 조회

### 웹뷰 엔진 도구
- QWebEngineView 기반 렌더링
- 실시간 스트리밍 응답 표시
- 대용량 응답 청크 단위 처리
- 마크다운 포맷팅 (굵은 텍스트, 불릿 포인트)
- 코드 블록 신택스 하이라이팅
- 다크 테마 지원
- 반응형 레이아웃

### 기타 도구
- 파일 시스템 접근
- 이메일 관리
- 지도/위치 서비스

## 📦 설치 및 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 설정 파일 구성

#### config.json
```json
{
  "models": {
    "gpt-3.5-turbo": {
      "api_key": "your-openai-api-key"
    },
    "gemini-pro": {
      "api_key": "your-google-api-key"
    }
  },
  "default_model": "gpt-3.5-turbo"
}
```

#### mcp.json
```json
{
  "servers": {
    "search-mcp-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-search"],
      "env": {}
    },
    "mysql": {
      "command": "uvx",
      "args": ["mcp-server-mysql", "--host", "localhost", "--user", "root"],
      "env": {}
    }
  }
}
```

### 3. 환경 변수 설정 (선택사항)
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 환경 변수 설정
```

## 🚀 실행 방법

### GUI 모드
```bash
python main.py
```

### 테스트 실행
```bash
# AI 에이전트 테스트
python test/test_agent.py

# MCP 연결 테스트
python test/test_mcp.py

# 대화 히스토리 테스트
python test_conversation_history.py

# 스트리밍 기능 테스트
python test_streaming.py

# 기타 테스트 파일들
python test/quick_test.py
```

## 📁 프로젝트 구조

```
chat-ai-agent/
├── core/                   # 핵심 모듈
│   ├── ai_agent.py        # AI 에이전트 메인 클래스
│   ├── ai_client.py       # LLM 클라이언트
│   ├── mcp_client.py      # MCP 클라이언트 관리
│   ├── mcp.py             # MCP 서버 제어
│   ├── tool_manager.py    # 도구 관리
│   ├── langchain_tools.py # LangChain 도구 래퍼
│   ├── conversation_history.py # 대화 히스토리 관리
│   └── file_utils.py      # 파일 유틸리티
├── ui/                     # GUI 인터페이스
│   ├── main_window.py     # 메인 윈도우
│   ├── chat_widget.py     # 채팅 위젯
│   ├── settings_dialog.py # 설정 대화상자
│   ├── mcp_dialog.py      # MCP 설정 대화상자
│   └── mcp_manager_dialog.py # MCP 서버 관리 대화상자
├── test/                   # 테스트 파일들
│   ├── test_agent.py      # AI 에이전트 테스트
│   ├── test_mcp.py        # MCP 연결 테스트
│   ├── debug_*.py         # 디버그 파일들
│   └── quick_test.py      # 빠른 테스트
├── config.json            # 설정 파일
├── mcp.json              # MCP 서버 설정
├── main.py               # GUI 실행 파일
├── test_conversation_history.py # 대화 히스토리 테스트
├── setup_env.sh          # 가상환경 설정 스크립트
└── run.sh                # 실행 스크립트
```

## 🔧 사용법

### 1. GUI에서 사용
1. `python main.py` 실행
2. 설정에서 API 키와 모델 선택
3. MCP 서버 연결 확인
4. 채팅창에서 질문 입력

### MCP 서버 관리
- **설정 > MCP 서버 관리** 메뉴로 접근
- 서버 상태 실시간 모니터링
- 개별 서버 시작/중지/재시작 기능
- 사용 가능한 도구 목록 확인

### 대화 히스토리 관리
- **설정 > 대화 기록 초기화** 메뉴로 접근
- 이전 대화 내용을 자동으로 기억
- 연속적인 대화에서 문맥 유지
- 필요시 대화 기록 완전 초기화 가능

### 2. 프로그래밍 방식 사용
```python
from core.ai_agent import AIAgent
from core.mcp import start_mcp_servers
from core.file_utils import load_model_api_key

# MCP 서버 시작
start_mcp_servers('mcp.json')

# AI 에이전트 생성
api_key = load_model_api_key('gpt-3.5-turbo')
agent = AIAgent(api_key, 'gpt-3.5-turbo')

# 메시지 처리
response, used_tools = agent.process_message("MySQL 데이터베이스 목록을 보여주세요")
print(f"응답: {response}")
print(f"도구 사용됨: {used_tools}")
```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🐛 문제 해결

### 일반적인 문제들

1. **MCP 서버 연결 실패**
   - Node.js 및 필요한 패키지가 설치되어 있는지 확인
   - `mcp.json` 설정이 올바른지 확인

2. **API 키 오류**
   - `config.json`에 올바른 API 키가 설정되어 있는지 확인
   - API 키에 충분한 크레딧이 있는지 확인

3. **도구 실행 오류**
   - 해당 서비스(MySQL, 웹 검색 등)가 접근 가능한지 확인
   - 필요한 권한이 설정되어 있는지 확인

4. **스트리밍 응답 문제**
   - 네트워크 연결 상태 확인
   - `config.json`의 `response_settings`에서 `max_tokens` 값 조정
   - 방화벽이나 프록시 설정 확인

5. **대용량 응답 처리 문제**
   - 메모리 사용량 확인 (8GB 이상 권장)
   - `config.json`의 `max_response_length` 설정 조정
   - 브라우저 캐시 정리

### 로그 확인
프로그램 실행 시 콘솔에 출력되는 로그를 확인하여 문제를 진단할 수 있습니다.

### 스트리밍 기능 테스트
```bash
# 스트리밍 기능이 정상 작동하는지 테스트
python test_streaming.py
```

이 테스트는 다음을 확인합니다:
- 실시간 스트리밍 응답 수신
- 대용량 응답 완전 수신
- 청크 단위 응답 처리
- 네트워크 타임아웃 처리

## 📞 지원

문제가 발생하거나 질문이 있으시면 GitHub Issues를 통해 문의해 주세요.