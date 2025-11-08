# 코드 블록 렌더링 환경별 일관성 분석

## 🔴 발견된 문제점

### 1. JavaScript 동적 삽입의 타이밍 이슈
**위치**: `ui/fixed_formatter.py` (Line 71-95)

**문제**:
- 코드 블록 종료 후 `<script>` 태그로 실행 버튼을 동적 추가
- DOM 로딩 타이밍에 의존하여 불안정
- 패키징 환경에서 리소스 로딩 순서 변경 시 버튼 미표시 가능

**영향**:
- 테스트 환경: 정상 동작 (로컬 파일 빠른 로딩)
- 패키징 환경: 간헐적 실패 (리소스 번들링으로 로딩 지연)

### 2. 이중 감지 시스템의 충돌
**위치**: 
- 서버: `ui/fixed_formatter.py` (Python 언어 감지)
- 클라이언트: `ui/components/chat_display/html_template_builder.py:235-280` (JavaScript 언어 감지)

**문제**:
- 동일한 코드 블록을 두 번 처리
- 버튼 중복 생성 또는 충돌 가능
- 언어 감지 결과 불일치 시 혼란

**영향**:
- 실행 버튼이 2개 생기거나 위치가 어긋남
- 복사 버튼 위치 조정 로직 충돌

### 3. Pygments 의존성 누락
**위치**: `utils/code_detector.py` (Line 42-56)

**문제**:
- Pygments 라이브러리를 동적 import
- `chat_ai_agent.spec`의 `hiddenimports`에 미포함
- 패키징 시 Pygments 누락 가능

**영향**:
- 테스트 환경: Pygments 설치되어 정상 동작
- 패키징 환경: Pygments 없어 정규식 폴백만 사용 (정확도 하락)

### 4. 코드 ID 생성의 비결정성
**위치**: `ui/fixed_formatter.py` (Line 38)

**문제**:
```python
current_code_id = f"code_{uuid.uuid4().hex[:8]}"
```
- UUID 기반 ID 생성으로 매번 다른 ID
- 클라이언트 JavaScript가 ID를 찾지 못할 수 있음

**영향**:
- 동적 버튼 추가 시 잘못된 ID 참조 가능

## ✅ 권장 해결 방안

### 방안 1: 서버 사이드 렌더링 통합 (권장)
**장점**:
- 단일 렌더링 경로로 일관성 보장
- 타이밍 이슈 완전 제거
- 패키징 환경에서도 동일한 결과

**구현**:
1. `fixed_formatter.py`에서 모든 버튼을 HTML로 직접 생성
2. JavaScript 동적 삽입 제거
3. 클라이언트 감지 시스템 비활성화

### 방안 2: Pygments를 hiddenimports에 추가
**spec 파일 수정**:
```python
hiddenimports=[
    # 기존 imports...
    'pygments',
    'pygments.lexers',
    'pygments.lexers.python',
    'pygments.lexers.javascript',
]
```

### 방안 3: 결정적 ID 생성
**개선**:
```python
# 코드 내용 기반 해시 ID
import hashlib
code_hash = hashlib.md5(code_content.encode()).hexdigest()[:8]
current_code_id = f"code_{code_hash}"
```

## 🎯 즉시 적용 가능한 수정

### 1단계: spec 파일 수정
```python
hiddenimports=[
    # ... 기존 imports
    'pygments',
    'pygments.lexers',
]
```

### 2단계: 이중 감지 제거
`html_template_builder.py`의 `detectAndAddExecuteButtons()` 함수 비활성화:
```javascript
// 주석 처리 또는 조건부 실행
// function detectAndAddExecuteButtons() { ... }
```

### 3단계: 서버 사이드 렌더링 강화
`fixed_formatter.py`에서 JavaScript 동적 삽입 제거하고 직접 HTML 생성

## 📊 테스트 체크리스트

### 테스트 환경
- [ ] Python 코드 블록 실행 버튼 표시
- [ ] JavaScript 코드 블록 실행 버튼 표시
- [ ] 언어 미지정 코드 블록 자동 감지
- [ ] 복사 버튼 위치 정확성
- [ ] 버튼 중복 생성 없음

### 패키징 환경
- [ ] PyInstaller로 빌드 후 동일 테스트
- [ ] Pygments 정상 동작 확인
- [ ] 리소스 로딩 지연 시나리오 테스트
- [ ] 다양한 코드 언어 테스트

## 🔧 우선순위

1. **긴급**: Pygments를 spec 파일에 추가
2. **높음**: 이중 감지 시스템 제거
3. **중간**: JavaScript 동적 삽입을 서버 사이드로 이전
4. **낮음**: 결정적 ID 생성 (선택사항)

## 📝 결론

현재 코드 블록 렌더링은 **테스트 환경에서는 정상 동작하지만 패키징 환경에서 불안정**합니다.

**핵심 원인**:
- 타이밍 의존적인 JavaScript 동적 삽입
- 이중 감지 시스템의 충돌
- Pygments 의존성 누락

**해결책**:
- 서버 사이드 렌더링으로 통합
- spec 파일에 Pygments 추가
- 클라이언트 감지 시스템 제거
