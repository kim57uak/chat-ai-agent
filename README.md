# 🤖 Chat AI Agent

다양한 MCP(Model Context Protocol) 서버와 연동하여 도구를 사용할 수 있는 AI 채팅 에이전트입니다.

## ✨ 주요 기능

### 🔗 MCP 서버 연동
- **다양한 외부 도구**: 15개 이상의 MCP 서버 지원
- **실시간 도구 감지**: 동적으로 사용 가능한 도구 자동 인식
- **지능형 도구 선택**: AI가 상황에 맞는 최적의 도구 자동 선택

### 🧠 다중 LLM 지원
- **OpenAI**: GPT-3.5, GPT-4, GPT-4V
- **Google**: Gemini Pro, Gemini 2.0 Flash
- **Perplexity**: Sonar 시리즈, R1 모델
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

### 기타 서비스
- Gmail 이메일 관리
- 지도/위치 서비스 (OpenStreetMap)
- YouTube 트랜스크립트
- Notion API 연동

## 🚀 빠른 시작

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

### 2. 설정
`config.json` 파일에서 API 키 설정:
```json
{
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

### 3. 실행
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

### 일반적인 문제들

**MCP 서버 연결 실패**
- Node.js 및 필요한 패키지가 설치되어 있는지 확인
- `mcp.json` 설정이 올바른지 확인

**API 키 오류**
- `config.json`에 올바른 API 키가 설정되어 있는지 확인
- API 키에 충분한 크레딧이 있는지 확인

**도구 실행 오류**
- 해당 서비스가 접근 가능한지 확인
- 필요한 권한이 설정되어 있는지 확인

**테마 적용 오류**
- `theme.json` 파일이 올바른 형식인지 확인
- 앱 재시작 후 테마가 정상 적용되는지 확인
- 테마 메뉴에서 다른 테마로 변경 후 다시 시도

## 📞 지원

문제가 발생하거나 질문이 있으시면 GitHub Issues를 통해 문의해 주세요.