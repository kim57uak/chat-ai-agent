# 패키징 환경 코드블록 렌더링 문제 분석

## 문제 증상
- 개발환경: 정상 동작 (코드블록, 복사/실행 버튼 표시)
- 패키징환경: 마크다운 문자 렌더링, 버튼 미표시, 불필요한 줄간격

## 원인 분석

### 1. JavaScript 함수 정의 타이밍
패키징 환경에서 `copyCodeBlock()`, `executeCode()` 함수가 정의되기 전에 HTML이 삽입됨

### 2. CSS 인라인 스타일 우선순위
패키징 환경에서 CSS 변수가 제대로 로드되지 않아 버튼 스타일 미적용

### 3. HTML 이스케이프 이중 처리
패키징 환경에서 HTML 엔티티가 이중으로 인코딩됨

## 해결 방안

### A. JavaScript 함수를 HTML 템플릿에 먼저 정의
`html_template_builder.py`의 `<script>` 태그 안에 코드블록 관련 함수 추가

### B. 버튼 스타일을 CSS 클래스로 변경
인라인 스타일 대신 CSS 클래스 사용으로 일관성 확보

### C. 코드 블록 생성 시점 지연
WebEngine 완전 로드 후 코드 블록 삽입

## 권장 수정 사항

1. `html_template_builder.py`: JavaScript 함수 정의 추가
2. `chat_theme_vars.py`: 코드 블록 버튼 CSS 클래스 추가
3. `fixed_formatter.py`: 버튼 생성 시 클래스 사용
