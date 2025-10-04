# 🤖 Chat AI Agent

다양한 MCP(Model Context Protocol) 서버와 연동하여 도구를 사용할 수 있는 AI 채팅 에이전트입니다.

## ✨ 주요 기능

### 🔗 MCP 서버 연동
- **다양한 외부 도구**: 15개 이상의 MCP 서버 지원
- **실시간 도구 감지**: 동적으로 사용 가능한 도구 자동 인식
- **지능형 도구 선택**: AI가 상황에 맞는 최적의 도구 자동 선택

### 🧠 다중 LLM 지원
- **OpenAI**: GPT-3.5, GPT-4, GPT-4V
- **Google**: Gemini Pro, Gemini 2.0 Flash, **Gemini 2.5 Flash Image Preview** 🎨
- **Perplexity**: Sonar 시리즈, R1 모델
- **Pollinations**: 무료 텍스트/이미지 생성 모델
- **확장 가능**: 새로운 모델 쉽게 추가 가능

### 💬 고급 채팅 인터페이스
- **PyQt6 기반**: 네이티브 데스크톱 앱 성능
- **웹뷰 엔진**: QWebEngineView 기반 고급 텍스트 렌더링
- **마크다운 지원**: 굵은 텍스트, 불릿 포인트, 코드 블록
- **Material Design 테마**: 5가지 아름다운 테마 지원
  - Material Light, Lighter, Palenight (밝은 테마)
  - Material Dark, Ocean (어두운 테마)

### 🔄 실시간 스트리밍
- **대용량 응답 처리**: 긴 응답도 끊김 없이 완전 수신
- **청크 단위 처리**: 메모리 효율적인 스트리밍
- **타이핑 애니메이션**: 자연스러운 대화 경험

### 🎨 Material Theme 시스템
- **5가지 테마**: Light, Lighter, Palenight, Dark, Ocean
- **실시간 테마 변경**: 페이지 새로고침 없이 즉시 적용
- **일관된 디자인**: 모든 UI 컴포넌트에 테마 자동 적용
- **테마별 로딩바**: 각 테마에 최적화된 로딩 애니메이션
- **접근성 고려**: 명도 대비와 가독성 최우선

### 🧠 대화 히스토리
- **문맥 유지**: 이전 대화 내용 자동 기억
- **토큰 최적화**: 비용 효율적인 히스토리 관리
- **영구 저장**: 앱 재시작 후에도 대화 연속성 유지

## 🛠️ 지원 도구

### 검색 및 웹
- 웹 검색 (Google, Bing, DuckDuckGo)
- URL 페이지 내용 가져오기
- Wikipedia 검색

### 데이터베이스
- MySQL 데이터베이스 조회
- 테이블 스키마 확인
- SQL 쿼리 실행

### 여행 서비스
- 하나투어 API 연동
- 여행 상품 검색
- 지역별 여행 정보 조회

### 오피스 도구
- Excel 파일 읽기/쓰기
- PowerPoint 프레젠테이션 생성/편집
- PDF, Word 문서 처리

### 개발 도구
- Bitbucket 저장소 관리
- Jira/Confluence 연동
- 파일 시스템 접근

### 이미지 생성
- **Gemini 2.5 Flash Image Preview**: Google의 최신 이미지 생성 모델
- **Pollinations**: 무료 이미지 생성 서비스
- 한글 프롬프트 자동 번역
- Base64 이미지 데이터 반환

### 기타 서비스
- Gmail 이메일 관리
- 지도/위치 서비스 (OpenStreetMap)
- YouTube 트랜스크립트
- Notion API 연동

## 🚀 빠른 시작

### 시스템 요구사항

#### 필수 소프트웨어
- **Python**: 3.9 이상 (3.11 권장)
- **Node.js**: 16.0 이상 (MCP 서버용)
- **Git**: 최신 버전

#### 운영체제
- **Windows**: Windows 10 이상
- **macOS**: macOS 10.15 (Catalina) 이상
- **Linux**: Ubuntu 18.04 이상 또는 동등한 배포판

#### 하드웨어
- **RAM**: 최소 4GB, 권장 8GB 이상
- **저장공간**: 최소 2GB 여유 공간
- **네트워크**: 인터넷 연결 (API 호출용)

### 1. 설치
```bash
# 저장소 클론
git clone <repository-url>
cd chat-ai-agent

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정
`config.json` 파일에서 API 키 설정:

```json
{
  "current_model": "gpt-3.5-turbo",
  "models": {
    "gpt-3.5-turbo": {
      "api_key": "your-openai-api-key",
      "provider": "openai"
    },
    "gemini-2.0-flash": {
      "api_key": "your-google-api-key",
      "provider": "google"
    }
  }
}
```

**API 키 획득 방법:**
- **OpenAI**: [platform.openai.com](https://platform.openai.com/) → API Keys
- **Google Gemini**: [makersuite.google.com](https://makersuite.google.com/) → API 키 생성
- **Perplexity**: [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)

### 3. MCP 서버 설정 (선택사항)

#### 필수 MCP 서버
```bash
# 검색 서버
npm install -g @modelcontextprotocol/server-search

# 파일시스템 서버
npm install -g @modelcontextprotocol/server-filesystem
```

#### 추가 MCP 서버
```bash
# MySQL 서버
npm install -g mysql-mcp-server

# Gmail 서버
npm install -g @gongrzhe/server-gmail-autoauth-mcp

# Python 기반 서버 (uvx 필요)
pip install uvx
uvx install excel-mcp-server
uvx install office-powerpoint-mcp-server
uvx install osm-mcp-server
```

#### Docker 기반 MCP 서버
```bash
# Docker 설치 확인
docker --version

# MCP 서버 이미지 다운로드
docker pull mcp/wikipedia-mcp
docker pull mcp/youtube-transcript
docker pull mcp/duckduckgo
```

### 4. 실행
```bash
python main.py
```

## 📖 사용법

### 기본 대화
- 채팅창에 질문을 입력하면 AI가 응답합니다
- 필요시 자동으로 적절한 도구를 선택하여 사용합니다

### 도구 사용 예시
```
사용자: "MySQL 데이터베이스 목록을 보여주세요"
AI: [MySQL 도구 사용] → 데이터베이스 목록 표시

사용자: "파리 여행 상품을 찾아주세요"
AI: [하나투어 API 사용] → 파리 여행 상품 검색 결과

사용자: "아름다운 일몰 풍경을 그려주세요"
AI: [Gemini 이미지 생성] → 고품질 일몰 이미지 생성

사용자: "이 Excel 파일의 내용을 요약해주세요"
AI: [Excel 도구 사용] → 파일 분석 후 요약 제공
```

### MCP 서버 관리
- **설정 > MCP 서버 관리**에서 서버 상태 확인
- 개별 서버 시작/중지/재시작 가능
- 사용 가능한 도구 목록 실시간 확인

### 테마 변경
- **테마 메뉴**에서 원하는 테마 선택
- 앱 전체에 즉시 적용 (배경, 텍스트, 버튼, 로딩바 등)
- 설정 자동 저장으로 재시작 시에도 유지

## 🔧 고급 설정

### MCP 서버 설정 (mcp.json)

#### 기본 설정
```json
{
  "mcpServers": {
    "search-mcp-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-search"]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/allowed/directory"
      ]
    }
  }
}
```

#### MySQL 서버 설정
```json
{
  "mcpServers": {
    "mysql": {
      "command": "npx",
      "args": ["mysql-mcp-server"],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "your-username",
        "MYSQL_PASSWORD": "your-password",
        "MYSQL_DATABASE": "your-database"
      },
      "disabled": false
    }
  }
}
```

#### Docker 기반 서버 설정
```json
{
  "mcpServers": {
    "youtube_transcript": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/youtube-transcript"]
    },
    "wikipedia-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/wikipedia-mcp"]
    }
  }
}
```

### 대화 히스토리 설정
```json
{
  "conversation_settings": {
    "enable_history": true,
    "max_history_pairs": 5,
    "max_tokens_estimate": 20000
  }
}
```

### 응답 설정
```json
{
  "response_settings": {
    "max_tokens": 4096,
    "enable_streaming": true,
    "streaming_chunk_size": 100
  }
}
```

### 테마 설정
```json
{
  "current_theme": "material_dark",
  "themes": {
    "material_light": {
      "name": "Material Light",
      "type": "light",
      "colors": {
        "primary": "#1976d2",
        "secondary": "#03dac6",
        "background": "#ffffff",
        "text_primary": "#212121"
      },
      "loading_bar": {
        "chunk": "linear-gradient(90deg, #1976d2 0%, #03dac6 100%)",
        "glow": "rgba(25, 118, 210, 0.3)"
      }
    }
  }
}
```

### 🎯 프롬프트 시스템 관리

#### 프롬프트 중앙 관리
모든 AI 모델의 프롬프트를 중앙에서 관리할 수 있습니다:

```python
from ui.prompts import prompt_manager, ModelType

# 전체 프롬프트 가져오기
full_prompt = prompt_manager.get_full_prompt(ModelType.OPENAI.value)

# 특정 프롬프트만 가져오기
system_prompt = prompt_manager.get_system_prompt(ModelType.GOOGLE.value)
tool_prompt = prompt_manager.get_tool_prompt(ModelType.PERPLEXITY.value)

# 프롬프트 업데이트
prompt_manager.update_prompt(ModelType.OPENAI.value, "custom_key", "새로운 프롬프트")
```

#### 프롬프트 설정 파일 편집
`ui/prompt_config.json` 파일을 직접 편집하여 프롬프트를 수정할 수 있습니다:

```json
{
  "openai": {
    "system_enhancement": "OpenAI 모델 전용 시스템 프롬프트",
    "tool_calling": "도구 호출 관련 프롬프트",
    "conversation_style": "대화 스타일 프롬프트"
  },
  "google": {
    "react_pattern": "ReAct 패턴 프롬프트"
  },
  "common": {
    "system_base": "모든 모델에서 공통으로 사용하는 기본 프롬프트"
  }
}
```

#### 지원하는 AI 모델
- **OpenAI**: GPT 시리즈 모델 최적화
- **Google**: Gemini 모델의 ReAct 패턴 지원
- **Perplexity**: 연구 중심 접근법 최적화
- **Common**: 모든 모델에서 공통 사용

### 프롬프트 커스터마이징

#### 새로운 모델 프롬프트 추가
```python
# 새로운 모델 타입 추가
class ModelType(Enum):
    CUSTOM_MODEL = "custom_model"

# 프롬프트 설정
prompt_manager.update_prompt(
    ModelType.CUSTOM_MODEL.value, 
    "system_enhancement", 
    "커스텀 모델 전용 프롬프트"
)
```

#### 프롬프트 파일 저장/로드
```python
# 프롬프트를 파일로 저장
prompt_manager.save_prompts_to_file("custom_prompts.json")

# 파일에서 프롬프트 로드
prompt_manager.load_prompts_from_file("custom_prompts.json")
```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

### MIT 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

```
MIT License

Copyright (c) 2024 Chat AI Agent Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 오픈소스 사용 허가

✅ **상업적 사용**: 상업적 목적으로 자유롭게 사용 가능  
✅ **수정**: 소스 코드 수정 및 개선 가능  
✅ **배포**: 원본 또는 수정된 버전 배포 가능  
✅ **사적 사용**: 개인적 용도로 자유롭게 사용 가능  
✅ **특허 사용**: 기여자의 특허 권리 부여  

### 의무사항

📋 **라이선스 고지**: 소프트웨어 배포 시 라이선스 전문 포함 필수  
📋 **저작권 고지**: 원저작자 정보 유지 필수  

### 면책사항

⚠️ **보증 없음**: 소프트웨어는 "있는 그대로" 제공되며 어떠한 보증도 하지 않음  
⚠️ **책임 제한**: 사용으로 인한 손해에 대해 개발자는 책임지지 않음

## 🐛 문제 해결

### 설치 관련 문제

#### Python 버전 문제
```bash
# Python 버전 확인
python --version
# 또는
python3 --version

# 3.9 미만인 경우 업그레이드 필요
```

#### 가상환경 활성화 실패
```bash
# Windows PowerShell 실행 정책 오류
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# macOS/Linux 권한 문제
chmod +x venv/bin/activate
```

#### 의존성 설치 실패
```bash
# pip 업그레이드
pip install --upgrade pip

# 개별 패키지 설치 시도
pip install PyQt6
pip install PyQt6-WebEngine
pip install langchain
```

### MCP 서버 문제

#### 서버 연결 실패
```bash
# Node.js 설치 확인
node --version
npm --version

# 전역 패키지 확인
npm list -g

# 포트 충돌 확인
netstat -an | grep :3000
```

#### 서버 시작 실패
- `mcp.json` 설정 파일 문법 확인
- 서버 경로가 올바른지 확인
- 환경변수가 제대로 설정되었는지 확인

### API 관련 문제

#### API 키 오류
- `config.json`에 올바른 API 키 설정 확인
- API 키 형식 확인 (공백, 특수문자 없음)
- API 키 크레딧 잔액 확인
- API 키 권한 확인

#### 응답 타임아웃
```json
{
  "response_settings": {
    "timeout": 60,
    "max_retries": 3
  }
}
```

### UI 관련 문제

#### 테마 적용 오류
- `theme.json` 파일 JSON 문법 확인
- 앱 재시작
- 테마 메뉴에서 다른 테마로 변경 후 재시도

#### 화면이 깨지는 경우
- PyQt6-WebEngine 재설치
- 그래픽 드라이버 업데이트
- 하드웨어 가속 비활성화

### 플랫폼별 문제

#### Windows
```bash
# Visual C++ 빌드 도구 필요
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 긴 경로명 문제
git config --system core.longpaths true
```

#### macOS
```bash
# Xcode Command Line Tools 설치
xcode-select --install

# Homebrew 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Linux
```bash
# 추가 시스템 패키지 (Ubuntu/Debian)
sudo apt update
sudo apt install build-essential python3-dev python3-venv
sudo apt install qt6-base-dev qt6-webengine-dev
```

## 📦 배포 및 설치

### Standalone 실행 파일

#### macOS
- **파일**: `ChatAIAgent.app` 또는 `ChatAIAgent-macOS.dmg`
- **설치**: DMG 파일을 다운로드하여 Applications 폴더로 드래그
- **보안 설정**: "확인되지 않은 개발자" 경고 시 시스템 환경설정 > 보안 및 개인정보보호에서 허용

#### Windows
- **파일**: `ChatAIAgent.exe`
- **설치**: EXE 파일을 다운로드하여 실행
- **보안 경고**: Windows Defender 경고 시 "추가 정보" → "실행" 클릭

#### Linux
- **파일**: `ChatAIAgent`
- **설치**: 실행 권한 부여 후 실행
  ```bash
  chmod +x ChatAIAgent
  ./ChatAIAgent
  ```

### 첫 실행 설정
1. **API 키 설정**: 설정 > 환경설정에서 사용할 AI 모델의 API 키 입력
2. **설정 파일 경로**: 설정 > 설정 파일 경로 설정에서 저장 폴더 선택
3. **MCP 서버 설정**: 외부 도구 사용 시 Node.js, Docker, Python 설치

## 🔄 업데이트 가이드

### 프로젝트 업데이트
```bash
# 최신 코드 가져오기
git pull origin main

# 의존성 업데이트
pip install -r requirements.txt --upgrade
```

### MCP 서버 업데이트
```bash
# npm 패키지 업데이트
npm update -g @modelcontextprotocol/server-search
npm update -g @modelcontextprotocol/server-filesystem

# Docker 이미지 업데이트
docker pull mcp/wikipedia-mcp:latest
docker pull mcp/youtube-transcript:latest
```

### 설정 파일 마이그레이션
```bash
# 기존 설정 백업
cp config.json config.json.backup

# 새 설정 형식으로 마이그레이션
python scripts/migrate_config.py
```

## 🚀 성능 최적화

### 메모리 사용량 최적화
```json
{
  "response_settings": {
    "max_tokens": 2048,
    "streaming_chunk_size": 50,
    "enable_length_limit": true,
    "max_response_length": 10000
  }
}
```

### 대화 히스토리 최적화
```json
{
  "conversation_settings": {
    "enable_history": true,
    "max_history_pairs": 3,
    "max_tokens_estimate": 10000,
    "auto_summarize": true
  }
}
```

### 캐싱 설정
```json
{
  "cache_settings": {
    "enable_cache": true,
    "cache_ttl": 3600,
    "max_cache_size": 100
  }
}
```

## 📞 지원

### 문의 채널
- **GitHub Issues**: 버그 리포트 및 기능 요청
- **Discussions**: 일반적인 질문 및 토론
- **Wiki**: 상세한 문서 및 튜토리얼

### 자주 묻는 질문 (FAQ)

**Q: API 키는 어디서 발급받나요?**
A: README의 "API 키 획득 방법" 섹션을 참조하세요.

**Q: MCP 서버가 시작되지 않아요.**
A: Node.js 설치 확인 및 `mcp.json` 설정을 점검하세요.

**Q: 대화 내용이 저장되나요?**
A: 네, 암호화되어 로컬 데이터베이스에 저장됩니다.

**Q: 여러 AI 모델을 동시에 사용할 수 있나요?**
A: 한 번에 하나의 모델만 사용 가능하며, 설정에서 전환할 수 있습니다.

## 📊 사용 통계 및 모니터링

### 토큰 사용량 추적
- 실시간 토큰 사용량 표시
- 세션별 토큰 통계
- 비용 추정 기능

### 로그 확인
```bash
# 애플리케이션 로그
tail -f ~/.chat-ai-agent/logs/app.log

# MCP 서버 로그
tail -f ~/.chat-ai-agent/logs/mcp.log

# 보안 로그
tail -f ~/.chat-ai-agent/logs/security.log
```

### 데이터베이스 관리
```bash
# 데이터베이스 백업
cp ~/.chat-ai-agent/chat_sessions.db backup/

# 데이터베이스 최적화
python scripts/optimize_database.py

# 오래된 세션 정리
python cleanup_inactive_sessions.py
```

---

## 🌐 English Documentation

For English documentation, please refer to the inline comments and code documentation. The main features include:

- **Multi-LLM Support**: OpenAI GPT, Google Gemini, Perplexity, Pollinations
- **MCP Integration**: 15+ external tool servers
- **Advanced UI**: PyQt6-based desktop app with Material Design themes
- **Real-time Streaming**: Efficient chunk-based response processing
- **Conversation History**: Context-aware chat with token optimization

### Quick Start (English)
```bash
# Clone and setup
git clone <repository-url>
cd chat-ai-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure API keys in config.json
# Run the application
python main.py
```