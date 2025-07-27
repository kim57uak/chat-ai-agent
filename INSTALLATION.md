# 📦 설치 가이드 (Installation Guide)

Chat AI Agent 프로젝트의 상세 설치 및 설정 가이드입니다.

## 🔧 시스템 요구사항

### 운영체제
- **Windows**: Windows 10 이상
- **macOS**: macOS 10.15 (Catalina) 이상
- **Linux**: Ubuntu 18.04 이상 또는 동등한 배포판

### 소프트웨어 요구사항
- **Python**: 3.9 이상 (3.11 권장)
- **Node.js**: 16.0 이상 (MCP 서버용)
- **Git**: 최신 버전
- **Docker**: 선택사항 (일부 MCP 서버용)

### 하드웨어 요구사항
- **RAM**: 최소 4GB, 권장 8GB 이상
- **저장공간**: 최소 2GB 여유 공간
- **네트워크**: 인터넷 연결 (API 호출용)

## 🚀 빠른 설치

### 1. 저장소 클론
```bash
git clone <repository-url>
cd chat-ai-agent
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 설정 파일 구성
```bash
# config.json에 API 키 설정
# mcp.json에 MCP 서버 설정
```

### 5. 실행
```bash
python main.py
```

## 📋 상세 설치 과정

### Step 1: Python 환경 준비

#### Python 설치 확인
```bash
python --version
# 또는
python3 --version
```

#### Python 3.9 이상이 없는 경우:
- **Windows**: [python.org](https://www.python.org/downloads/)에서 다운로드
- **macOS**: `brew install python3` 또는 python.org에서 다운로드
- **Ubuntu/Debian**: `sudo apt update && sudo apt install python3 python3-pip python3-venv`
- **CentOS/RHEL**: `sudo yum install python3 python3-pip`

### Step 2: Node.js 환경 준비 (MCP 서버용)

#### Node.js 설치 확인
```bash
node --version
npm --version
```

#### Node.js 16+ 설치:
- **Windows/macOS**: [nodejs.org](https://nodejs.org/)에서 LTS 버전 다운로드
- **Ubuntu/Debian**: 
  ```bash
  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  sudo apt-get install -y nodejs
  ```
- **macOS (Homebrew)**: `brew install node`

### Step 3: 프로젝트 설정

#### 저장소 클론 및 이동
```bash
git clone <repository-url>
cd chat-ai-agent
```

#### 가상환경 생성
```bash
# Windows
python -m venv venv

# macOS/Linux
python3 -m venv venv
```

#### 가상환경 활성화
```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

#### Python 의존성 설치
```bash
# 기본 설치
pip install -r requirements.txt

# 개발 환경 설치 (선택사항)
pip install -r requirements-dev.txt
```

### Step 4: MCP 서버 설정

#### 필수 MCP 서버 설치
```bash
# 검색 서버
npm install -g @modelcontextprotocol/server-search

# 파일시스템 서버
npm install -g @modelcontextprotocol/server-filesystem

# MySQL 서버 (선택사항)
npm install -g mysql-mcp-server

# Gmail 서버 (선택사항)
npm install -g @gongrzhe/server-gmail-autoauth-mcp
```

#### Docker 기반 MCP 서버 (선택사항)
```bash
# Docker 설치 확인
docker --version

# MCP 서버 이미지 다운로드
docker pull mcp/wikipedia-mcp
docker pull mcp/youtube-transcript
docker pull mcp/duckduckgo
```

## ⚙️ 설정 파일 구성

### config.json 설정

#### 기본 템플릿
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
    },
    "sonar": {
      "api_key": "your-perplexity-api-key",
      "provider": "perplexity"
    }
  },
  "conversation_settings": {
    "enable_history": true,
    "max_history_pairs": 5,
    "max_tokens_estimate": 20000
  },
  "response_settings": {
    "max_tokens": 4096,
    "enable_streaming": true,
    "streaming_chunk_size": 100
  }
}
```

#### API 키 획득 방법

**OpenAI API 키:**
1. [OpenAI Platform](https://platform.openai.com/) 방문
2. 계정 생성 또는 로그인
3. API Keys 섹션에서 새 키 생성
4. 결제 정보 등록 (사용량에 따른 과금)

**Google Gemini API 키:**
1. [Google AI Studio](https://makersuite.google.com/) 방문
2. Google 계정으로 로그인
3. API 키 생성
4. 무료 할당량 확인

**Perplexity API 키:**
1. [Perplexity API](https://www.perplexity.ai/settings/api) 방문
2. 계정 생성 또는 로그인
3. API 키 생성
4. 크레딧 구매 (유료)

### mcp.json 설정

#### 기본 MCP 서버 설정
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
    },
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

#### 고급 MCP 서버 설정
```json
{
  "mcpServers": {
    "gmail": {
      "command": "npx",
      "args": ["@gongrzhe/server-gmail-autoauth-mcp"]
    },
    "excel-stdio": {
      "command": "uvx",
      "args": ["excel-mcp-server", "stdio"]
    },
    "ppt": {
      "command": "uvx",
      "args": ["--from", "office-powerpoint-mcp-server", "ppt_mcp_server"]
    },
    "osm-mcp-server": {
      "command": "uvx",
      "args": ["osm-mcp-server"]
    },
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

## 🔧 추가 도구 설치

### uvx 설치 (Python 도구용)
```bash
pip install uvx
```

### 특정 MCP 서버 설치

#### Excel MCP 서버
```bash
uvx install excel-mcp-server
```

#### PowerPoint MCP 서버
```bash
uvx install office-powerpoint-mcp-server
```

#### OpenStreetMap MCP 서버
```bash
uvx install osm-mcp-server
```

## 🐛 설치 문제 해결

### 일반적인 문제들

#### 1. Python 버전 문제
```bash
# 에러: Python 3.9+ required
# 해결: Python 업그레이드
python --version
# 3.8 이하인 경우 최신 Python 설치
```

#### 2. 가상환경 활성화 실패
```bash
# Windows PowerShell 실행 정책 오류
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# macOS/Linux 권한 문제
chmod +x venv/bin/activate
```

#### 3. 의존성 설치 실패
```bash
# pip 업그레이드
pip install --upgrade pip

# 개별 패키지 설치 시도
pip install PyQt6
pip install PyQt6-WebEngine
```

#### 4. Node.js 패키지 설치 실패
```bash
# npm 캐시 정리
npm cache clean --force

# 권한 문제 (macOS/Linux)
sudo npm install -g <package-name>
```

#### 5. MCP 서버 연결 실패
```bash
# 서버 상태 확인
node --version
npm list -g

# 포트 충돌 확인
netstat -an | grep :3000
```

### 플랫폼별 특정 문제

#### Windows
```bash
# Visual C++ 빌드 도구 필요한 경우
# Microsoft C++ Build Tools 설치
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 긴 경로명 문제
git config --system core.longpaths true
```

#### macOS
```bash
# Xcode Command Line Tools 설치
xcode-select --install

# Homebrew 설치 (권장)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Linux
```bash
# 추가 시스템 패키지 설치 (Ubuntu/Debian)
sudo apt update
sudo apt install build-essential python3-dev python3-venv

# Qt 관련 패키지
sudo apt install qt6-base-dev qt6-webengine-dev
```

## ✅ 설치 검증

### 1. Python 환경 확인
```bash
python --version
pip list | grep PyQt6
pip list | grep langchain
```

### 2. Node.js 환경 확인
```bash
node --version
npm list -g | grep mcp
```

### 3. 애플리케이션 실행 테스트
```bash
python main.py
```

### 4. MCP 서버 연결 테스트
```bash
# GUI에서 설정 > MCP 서버 관리 확인
# 또는 프로그래밍 방식으로 확인
python -c "from mcp.client.mcp_client import MCPClient; print('MCP OK')"
```

## 🔄 업데이트 가이드

### 프로젝트 업데이트
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### MCP 서버 업데이트
```bash
npm update -g @modelcontextprotocol/server-search
npm update -g @modelcontextprotocol/server-filesystem
```

### Docker 이미지 업데이트
```bash
docker pull mcp/wikipedia-mcp:latest
docker pull mcp/youtube-transcript:latest
```

## 🚀 성능 최적화

### 시스템 최적화
```bash
# Python 바이트코드 컴파일
python -m compileall .

# 가상환경 최적화
pip install --upgrade pip setuptools wheel
```

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

## 📚 추가 리소스

### 공식 문서
- [MCP Protocol](https://modelcontextprotocol.io/)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython-6/)
- [LangChain Documentation](https://python.langchain.com/)

### 커뮤니티
- GitHub Issues: 버그 리포트 및 기능 요청
- Discord/Slack: 실시간 지원 (링크 제공 시)

### 예제 및 튜토리얼
- `examples/` 디렉토리의 샘플 코드
- `docs/` 디렉토리의 상세 가이드

이 가이드를 따라 설치하면 Chat AI Agent를 성공적으로 실행할 수 있습니다. 문제가 발생하면 GitHub Issues를 통해 도움을 요청하세요.