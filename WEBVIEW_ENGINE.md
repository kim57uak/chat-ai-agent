# 🌐 웹뷰 엔진 (WebView Engine)

Chat AI Agent의 고급 텍스트 렌더링 시스템입니다.

## ✨ 주요 기능

### 🎨 마크다운 지원
- **굵은 텍스트**: `**텍스트**` → **텍스트** (노란색 강조)
- **불릿 포인트**: `• 항목` → • 항목 (초록색 불릿)
- **코드 블록**: 구문 강조와 다크 테마 스타일링

### 🖥️ 웹 기반 렌더링
- **QWebEngineView** 기반 고성능 렌더링
- **HTML/CSS** 완전 지원
- **반응형 레이아웃** 자동 조정

### 🌙 다크 테마
- 눈에 편한 어두운 배경 (#1a1a1a)
- 고대비 텍스트 색상 (#e8e8e8)
- 코드 블록 전용 스타일링 (#2d2d2d)

## 🔧 기술적 구현

### 텍스트 포맷팅 파이프라인

```python
def format_text(self, text):
    # 1. 코드 블록 추출 및 보호
    code_blocks = []
    text = re.sub(r'```[^\n]*\n([\s\S]*?)```', extract_code_block, text)
    
    # 2. HTML 이스케이프 처리
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # 3. 마크다운 요소 변환
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #FFD54F;">\\1</strong>', text)
    text = re.sub(r'^• (.*?)$', r'<div class="bullet">\\1</div>', text, flags=re.MULTILINE)
    
    # 4. 코드 블록 복원 및 스타일링
    # 5. 줄바꿈 및 레이아웃 처리
```

### CSS 스타일 시스템

```css
/* 기본 다크 테마 */
body {
    background-color: #1a1a1a;
    color: #e8e8e8;
    font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
}

/* 코드 블록 스타일링 */
.code-block {
    background-color: #2d2d2d;
    border: 1px solid #444444;
    border-radius: 6px;
    font-family: Consolas, Monaco, monospace;
}

/* 불릿 포인트 */
.bullet {
    margin-left: 20px;
    color: #81C784;
}
```

## 📊 성능 최적화

### 렌더링 최적화
- **청크 단위 처리**: 긴 텍스트를 작은 단위로 분할
- **지연 로딩**: 필요한 부분만 렌더링
- **메모리 효율성**: 불필요한 DOM 요소 최소화

### 타이핑 애니메이션
```python
def start_optimized_typing(self, sender, text):
    # 즉시 표시 모드 (성능 우선)
    self.append_chat(sender, text)
    
    # 또는 청크 단위 애니메이션
    self.typing_chunks = self._split_text_for_typing(text)
    self.typing_timer.start(200)
```

## 🛠️ 설치 및 설정

### 의존성 설치
```bash
pip install PyQt6-WebEngine
```

### 기본 사용법
```python
from ui.chat_widget import ChatWidget

# 채팅 위젯 생성
chat_widget = ChatWidget()

# 메시지 추가
chat_widget.append_chat('AI', '**안녕하세요!** 다음 기능들을 지원합니다:\n• 마크다운 포맷팅\n• 코드 하이라이팅')
```

## 🎯 지원되는 마크다운 요소

| 요소 | 마크다운 | 렌더링 결과 |
|------|----------|-------------|
| 굵은 텍스트 | `**텍스트**` | **텍스트** (노란색) |
| 불릿 포인트 | `• 항목` | • 항목 (초록색 불릿) |
| 코드 블록 | ` ```python\ncode\n``` ` | 구문 강조된 코드 블록 |
| 일반 텍스트 | `텍스트` | 기본 스타일 텍스트 |

## 🔍 테스트 및 디버깅

### 포맷팅 테스트
```bash
python test_format_standalone.py
```

### HTML 출력 확인
생성된 `webview_format_test.html` 파일을 브라우저에서 열어 렌더링 결과 확인

## 🚀 향후 개선 계획

### 추가 마크다운 지원
- [ ] 링크 (`[텍스트](URL)`)
- [ ] 이미지 (`![alt](src)`)
- [ ] 테이블 지원 확장
- [ ] 인라인 코드 (`` `code` ``)

### 성능 개선
- [ ] 가상 스크롤링
- [ ] 이미지 지연 로딩
- [ ] 캐싱 시스템

### 접근성 개선
- [ ] 키보드 네비게이션
- [ ] 스크린 리더 지원
- [ ] 고대비 모드

## 📝 라이선스

이 웹뷰 엔진은 Chat AI Agent 프로젝트의 일부로 MIT 라이선스 하에 배포됩니다.