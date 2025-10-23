# 패키징 환경 코드블록 렌더링 수정 계획

## 현재 상태 (개발환경)
✅ 버튼 2개 생성
✅ window.copyCodeBlock/executeCode 함수 정의
✅ CSS 클래스 존재
✅ 인라인 스타일 적용

## 패키징 환경 문제 가능성

### 1. JavaScript 함수 로딩 타이밍
- **문제**: HTML 템플릿이 로드되기 전에 버튼 HTML이 삽입됨
- **해결**: 함수를 전역 스코프에 먼저 정의

### 2. CSS 변수 미적용
- **문제**: CSS 변수가 로드되지 않아 스타일 깨짐
- **해결**: 인라인 스타일 강화 (이미 적용됨)

### 3. 리소스 경로 문제
- **문제**: PyInstaller frozen 상태에서 리소스 경로 변경
- **해결**: 절대 경로 대신 상대 경로 사용

## 수정 방안

### A. HTML 템플릿에 즉시 실행 함수 추가
```javascript
(function() {
    window.copyCodeBlock = function(codeId) { ... };
    window.executeCode = function(codeId, language) { ... };
})();
```

### B. 버튼 생성 시 함수 존재 확인
```python
onclick="(window.copyCodeBlock || function(){})('{code_id}')"
```

### C. 로딩 완료 후 버튼 활성화
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // 버튼 활성화
});
```

## 권장 수정: 즉시 실행 함수 패턴
