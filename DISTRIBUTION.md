# ChatAI Agent - 배포 가이드

## 📦 Standalone 실행 파일

### macOS
- **파일**: `ChatAIAgent.app` 또는 `ChatAIAgent-macOS.dmg`
- **크기**: ~407MB
- **요구사항**: macOS 10.14 이상
- **설치**: DMG 파일을 다운로드하여 Applications 폴더로 드래그

### Windows  
- **파일**: `ChatAIAgent.exe`
- **크기**: ~400MB
- **요구사항**: Windows 10 이상
- **설치**: EXE 파일을 다운로드하여 실행

## 🚀 첫 실행 설정

### 1. API 키 설정
앱 실행 후 **설정 > 환경설정**에서 사용할 AI 모델의 API 키를 입력하세요.

### 2. 설정 파일 경로 지정
**설정 > 설정 파일 경로 설정**에서 설정 파일을 저장할 폴더를 선택하세요.
- `config.json`: AI 모델 설정
- `mcp.json`: MCP 서버 설정  
- `news_config.json`: 뉴스 설정
- `prompt_config.json`: 프롬프트 설정

### 3. MCP 서버 설정 (선택사항)
외부 도구를 사용하려면 다음을 설치하세요:
- **Node.js**: npm 기반 MCP 서버용
- **Docker**: Docker 기반 MCP 서버용
- **Python**: Python 기반 MCP 서버용

## 📁 포함된 파일들

### 자동 포함 (패키징됨)
- Python 런타임
- PyQt6 라이브러리
- SQLite 데이터베이스
- 앱 아이콘 및 이미지
- 기본 설정 파일들

### 사용자 설정 (별도 생성)
- `config.json`: API 키 및 모델 설정
- `mcp.json`: MCP 서버 설정
- `news_config.json`: 뉴스 소스 설정
- `prompt_config.json`: 프롬프트 설정

## 🔧 문제 해결

### 실행 안됨
- **macOS**: 시스템 환경설정 > 보안 및 개인정보보호에서 앱 허용
- **Windows**: Windows Defender에서 예외 추가

### MCP 서버 오류
- Node.js, Docker, Python 설치 확인
- 방화벽 설정 확인

### 설정 파일 오류
- 설정 파일 경로가 올바른지 확인
- JSON 문법 오류 확인

## 📞 지원

문제 발생 시 GitHub Issues에 문의하세요:
https://github.com/kim57uak/chat-ai-agent/issues