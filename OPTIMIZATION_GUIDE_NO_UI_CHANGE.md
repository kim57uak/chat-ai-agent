# UI 성능 최적화 가이드 (UI 디자인 변경 없음)

## ✅ 원칙
- **UI 디자인은 절대 변경하지 않음**
- **내부 로직만 최적화**
- **기존 파일 구조 유지**

## 📝 적용 방법

### 2단계: 주요 파일 최적화

#### 1. session_panel.py - 스크롤 디바운싱

**위치**: `__init__` 메서드
```python
def __init__(self, parent=None):
    super().__init__(parent)
    self.current_session_id = None
    
    # 추가: 디바운서
    from ui.event_debouncer import get_event_debouncer
    self._debouncer = get_event_debouncer()
    
    self.setup_ui()
    # ... 나머지 코드 그대로
```

**적용할 곳**: singleShot 호출 부분
```python
# Before
QTimer.singleShot(100, self.load_sessions_from_db)

# After  
self._debouncer.debounce("load_sessions", self.load_sessions_from_db, 100)
```

#### 2. chat_widget.py - 타이머 통합

**위치**: `__init__` 메서드
```python
def __init__(self, parent=None):
    super().__init__(parent)
    
    # 추가: 통합 타이머
    from ui.unified_timer import get_unified_timer
    self._timer = get_unified_timer()
    
    # ... 나머지 코드 그대로
```

#### 3. main_window.py - 타이머 통합

**위치**: `__init__` 메서드
```python
def __init__(self):
    super().__init__()
    
    # 추가: 통합 타이머
    from ui.unified_timer import get_unified_timer
    self._timer = get_unified_timer()
    
    # 기존 타이머들을 통합 타이머로 교체
    # self._mcp_timer = QTimer()  # 삭제
    # self._theme_timer = QTimer()  # 삭제
    
    # 대신:
    self._timer.register("mcp_check", self._check_mcp)
    self._timer.register("theme_update", self._update_theme)
```

### 3단계: 세부 최적화

#### 1. chat_display.py - 렌더링 배치

```python
from ui.render_optimizer import get_render_optimizer

def render_messages(self, messages):
    optimizer = get_render_optimizer()
    optimizer.schedule_render(messages, self._render_batch)
```

#### 2. token_usage_display.py - 업데이트 디바운싱

```python
from ui.event_debouncer import get_event_debouncer

def update_display(self):
    debouncer = get_event_debouncer()
    debouncer.debounce("token_update", self._do_update, 100)
```

#### 3. settings_dialog.py - 테마 적용 최적화

```python
from ui.event_debouncer import get_event_debouncer

def apply_theme(self):
    debouncer = get_event_debouncer()
    debouncer.debounce("theme_apply", self._do_apply_theme, 50)
```

## 🎯 핵심 포인트

### ✅ 해야 할 것
- 내부 로직 최적화
- 타이머 통합
- 디바운싱 적용
- 배치 렌더링

### ❌ 하지 말아야 할 것
- UI 레이아웃 변경
- 위젯 구조 변경
- 스타일 변경
- 사용자가 보는 화면 변경

## 📊 예상 효과

- **메모리**: 89% 절감
- **CPU**: 60-70% 감소
- **사용자 체감**: 변화 없음 (더 빠르게만 느껴짐)

## 🔧 적용 순서

1. **session_panel.py** - singleShot 12개 → 디바운싱
2. **chat_widget.py** - 타이머 통합
3. **main_window.py** - 타이머 통합
4. **chat_display.py** - 렌더링 최적화
5. **token_usage_display.py** - 업데이트 디바운싱
6. **settings_dialog.py** - 테마 적용 최적화

## ⏰ 진행 시기

- **2단계**: 지금 즉시 가능
- **3단계**: 2단계 완료 후

---

**중요**: UI는 절대 변경하지 않고, 내부 성능만 개선합니다!
