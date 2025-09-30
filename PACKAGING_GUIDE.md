# 📦 ChatAI Agent 패키징 가이드

## 🚀 빠른 시작

### Windows
```bash
# 배치 파일 실행 (권장)
build_package.bat

# 또는 직접 실행
python build_package.py
```

### macOS/Linux
```bash
# 셸 스크립트 실행 (권장)
./build_package.sh

# 또는 직접 실행
python3 build_package.py
```

## 🔒 보안 기능

### 개인키 보호
- **config.json**: API 키들이 샘플 값으로 대체됨
- **mcp.json**: 모든 토큰과 패스워드가 플레이스홀더로 대체됨
- **news_config.json**: 빈 설정으로 초기화
- **prompt_config.json**: 기본 설정값으로 초기화

### 자동 백업/복구
```python
# 빌드 전: 원본 파일 자동 백업
backup_configs/
├── config.json
├── mcp.json
├── news_config.json
└── prompt_config.json

# 빌드 후: 원본 파일 자동 복구
```

## 🛠️ 패키징 과정

1. **백업**: 개인키 포함된 설정 파일들 백업
2. **샘플 생성**: 개인키 제거된 안전한 샘플 파일 생성
3. **빌드**: PyInstaller로 실행 파일 생성
4. **검증**: 필수 파일 포함 여부 확인
5. **패키지**: 플랫폼별 배포 패키지 생성
6. **복구**: 원본 설정 파일 자동 복구

## 📁 생성되는 파일들

### Windows
- `dist/ChatAIAgent.exe` - 실행 파일
- `dist/ChatAIAgent-Windows.zip` - 배포용 ZIP

### macOS
- `dist/ChatAIAgent.app` - 앱 번들
- `dist/ChatAIAgent-macOS.dmg` - 배포용 DMG

### Linux
- `dist/ChatAIAgent` - 실행 파일
- `dist/ChatAIAgent-Linux.tar.gz` - 배포용 TAR.GZ

## 🔧 문제 해결

### 설정 파일이 복구되지 않은 경우
```bash
# 긴급 복구 스크립트 실행
python restore_configs.py
```

### 빌드 실패 시 체크리스트
1. **가상환경 활성화** 확인
2. **필수 패키지** 설치 확인: `pip install -r requirements.txt`
3. **PyInstaller** 설치 확인: `pip install pyinstaller`
4. **Python 버전** 확인: Python 3.8 이상 권장

### 패키징된 앱 실행 시 주의사항
1. **config.json 설정**: 본인의 API 키로 교체 필요
2. **mcp.json 설정**: 사용할 MCP 서버 정보 입력 필요
3. **권한 설정**: Linux에서는 `chmod +x ChatAIAgent` 실행

## 📋 설정 파일 템플릿

### config.json 예시
```json
{
  "current_model": "gemini-2.0-flash",
  "models": {
    "gemini-2.0-flash": {
      "api_key": "YOUR_GOOGLE_API_KEY",
      "provider": "google"
    }
  }
}
```

### mcp.json 예시
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/your/path"]
    }
  }
}
```

## ⚠️ 중요 사항

1. **개인키 보안**: 패키징된 앱에는 개인키가 포함되지 않음
2. **테스트 연속성**: 빌드 후 자동으로 원본 설정 복구
3. **크로스 플랫폼**: Windows, macOS, Linux 모두 지원
4. **의존성 관리**: 모든 필요한 라이브러리 자동 포함

## 🔄 개발 워크플로우

```bash
# 1. 개발 및 테스트
python main.py

# 2. 패키징 (설정 파일 자동 백업/복구)
./build_package.sh

# 3. 계속 개발 (원본 설정으로 복구됨)
python main.py
```

이 가이드를 따르면 안전하고 효율적으로 ChatAI Agent를 패키징할 수 있습니다.