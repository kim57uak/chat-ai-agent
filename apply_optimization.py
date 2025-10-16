#!/usr/bin/env python3
"""성능 최적화 자동 적용 스크립트 (UI 변경 없음)"""

def optimize_session_panel():
    """session_panel.py 최적화"""
    file_path = "ui/session_panel.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 디바운서 초기화 추가
    old_code = """        self.setMouseTracking(True)
        self.stats_label.setMouseTracking(True)

        # 앱 시작 시 세션 DB에서 로드
        QTimer.singleShot(100, self.load_sessions_from_db)"""
    
    new_code = """        self.setMouseTracking(True)
        self.stats_label.setMouseTracking(True)

        # 성능 최적화 - 디바운서
        from ui.event_debouncer import get_event_debouncer
        self._debouncer = get_event_debouncer()

        # 앱 시작 시 세션 DB에서 로드
        self._debouncer.debounce("load_sessions", self.load_sessions_from_db, 100)"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ session_panel.py: 디바운서 초기화 추가")
    
    # 모델 업데이트 최적화
    content = content.replace(
        'QTimer.singleShot(200, self._update_current_model_display)',
        'self._debouncer.debounce("update_model", self._update_current_model_display, 200)'
    )
    print("✅ session_panel.py: 모델 업데이트 디바운싱")
    
    # 자동 선택 최적화
    content = content.replace(
        'QTimer.singleShot(500, self._auto_select_last_session)',
        'self._debouncer.debounce("auto_select", self._auto_select_last_session, 500)'
    )
    print("✅ session_panel.py: 자동 선택 디바운싱")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path} 최적화 완료\n")

def optimize_chat_widget():
    """chat_widget.py 최적화"""
    file_path = "ui/chat_widget.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # __init__에 통합 타이머 추가
    old_init = """    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_closing = False
        self._timers = []"""
    
    new_init = """    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_closing = False
        self._timers = []
        
        # 성능 최적화 - 통합 타이머
        from ui.unified_timer import get_unified_timer
        self._unified_timer = get_unified_timer()"""
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✅ chat_widget.py: 통합 타이머 추가")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path} 최적화 완료\n")

def optimize_main_window():
    """main_window.py 최적화"""
    file_path = "ui/main_window.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # __init__에 통합 타이머 추가
    old_init = """        # QTimer 멤버 변수 초기화 (업계 표준)
        self._mcp_init_timer = None"""
    
    new_init = """        # 성능 최적화 - 통합 타이머
        from ui.unified_timer import get_unified_timer
        self._unified_timer = get_unified_timer()
        
        # QTimer 멤버 변수 초기화 (업계 표준)
        self._mcp_init_timer = None"""
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✅ main_window.py: 통합 타이머 추가")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path} 최적화 완료\n")

def main():
    print("=" * 60)
    print("🚀 성능 최적화 적용 시작 (UI 변경 없음)")
    print("=" * 60)
    print()
    
    try:
        optimize_session_panel()
        optimize_chat_widget()
        optimize_main_window()
        
        print("=" * 60)
        print("🎉 2단계 최적화 완료!")
        print("=" * 60)
        print("\n변경 사항:")
        print("  - session_panel.py: 디바운싱 적용")
        print("  - chat_widget.py: 통합 타이머 추가")
        print("  - main_window.py: 통합 타이머 추가")
        print("\n다음: python main.py 실행하여 테스트")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
