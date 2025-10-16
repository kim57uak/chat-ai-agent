#!/usr/bin/env python3
"""스크롤 튕김 문제 해결"""

def fix_scroll_bounce():
    """chat_widget.py 스크롤 튕김 수정"""
    file_path = "ui/chat_widget.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. __init__에 스크롤 상태 플래그 추가
    old_init = """        self._unified_timer = get_unified_timer()
        
        self.layout = QVBoxLayout(self)"""
    
    new_init = """        self._unified_timer = get_unified_timer()
        
        # 스크롤 상태 추적
        self._user_is_scrolling = False
        self._last_scroll_time = 0
        
        self.layout = QVBoxLayout(self)"""
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✅ 스크롤 상태 플래그 추가")
    
    # 2. _scroll_to_bottom에 사용자 스크롤 체크 추가
    old_scroll = """    def _scroll_to_bottom(self):
        \"\"\"채팅 화면을 맨 하단으로 스크롤 - 최대 강화 버전\"\"\"
        try:
            self.chat_display_view.page().runJavaScript(\"\"\"
                // 전역 함수로 한 번만 선언
                if (!window.forceScrollToBottom) {"""
    
    new_scroll = """    def _scroll_to_bottom(self):
        \"\"\"채팅 화면을 맨 하단으로 스크롤 - 최대 강화 버전\"\"\"
        # 사용자가 스크롤 중이면 중단
        import time
        if self._user_is_scrolling:
            if time.time() - self._last_scroll_time < 1.0:  # 1초 이내
                return
        
        try:
            self.chat_display_view.page().runJavaScript(\"\"\"
                // 전역 함수로 한 번만 선언
                if (!window.forceScrollToBottom) {"""
    
    if old_scroll in content:
        content = content.replace(old_scroll, new_scroll)
        print("✅ 사용자 스크롤 체크 추가")
    
    # 3. 스크롤 이벤트 리스너 추가
    old_setup = """    def _setup_scroll_listener(self):
        \"\"\"스크롤 리스너 설정\"\"\"
        try:"""
    
    new_setup = """    def _setup_scroll_listener(self):
        \"\"\"스크롤 리스너 설정\"\"\"
        # 사용자 스크롤 감지
        self.chat_display_view.page().runJavaScript(\"\"\"
            let scrollTimeout;
            window.addEventListener('scroll', function() {
                window.userIsScrolling = true;
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    window.userIsScrolling = false;
                }, 500);
            }, true);
        \"\"\")
        
        try:"""
    
    if old_setup in content:
        content = content.replace(old_setup, new_setup)
        print("✅ 스크롤 이벤트 리스너 추가")
    
    # 4. 반복 스크롤 호출 줄이기 (디바운싱)
    # 여러 번 호출되는 부분을 한 번만 호출하도록
    content = content.replace(
        """safe_single_shot(300, self._scroll_to_bottom, self)
        safe_single_shot(700, self._scroll_to_bottom, self)""",
        """self._debouncer.debounce("scroll_bottom", self._scroll_to_bottom, 500)"""
    )
    
    content = content.replace(
        """safe_single_shot(300, self._scroll_to_bottom, self)
        safe_single_shot(800, self._scroll_to_bottom, self)
        safe_single_shot(1500, self._scroll_to_bottom, self)  # 최종 확인""",
        """self._debouncer.debounce("scroll_bottom", self._scroll_to_bottom, 800)"""
    )
    
    content = content.replace(
        """safe_single_shot(400, self._scroll_to_bottom, self)
                safe_single_shot(1000, self._scroll_to_bottom, self)
                safe_single_shot(1800, self._scroll_to_bottom, self)  # 최종 확인""",
        """self._debouncer.debounce("scroll_bottom", self._scroll_to_bottom, 1000)"""
    )
    
    print("✅ 반복 스크롤 호출 디바운싱")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path} 스크롤 튕김 수정 완료\n")

def main():
    print("=" * 60)
    print("🔧 스크롤 튕김 문제 해결")
    print("=" * 60)
    print()
    
    try:
        fix_scroll_bounce()
        
        print("=" * 60)
        print("🎉 스크롤 튕김 수정 완료!")
        print("=" * 60)
        print("\n변경 사항:")
        print("  - 사용자 스크롤 중 자동 스크롤 중단")
        print("  - 반복 스크롤 호출 디바운싱")
        print("  - 스크롤 이벤트 리스너 추가")
        print("\n테스트:")
        print("  1. python main.py 실행")
        print("  2. 세션 선택하여 메시지 로드")
        print("  3. 스크롤 위로 올리기")
        print("  4. 튕김 없이 부드럽게 스크롤되는지 확인")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
