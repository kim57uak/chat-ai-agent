#!/usr/bin/env python3
"""스크롤 최적화 - 1번만 호출"""

def fix_scroll():
    file_path = "ui/chat_widget.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 모든 반복 스크롤을 1번으로 통합
    replacements = [
        # 패턴 1
        ("""safe_single_shot(200, self._scroll_to_bottom, self)
        safe_single_shot(500, self._scroll_to_bottom, self)  # 추가 시도""",
         """safe_single_shot(500, self._scroll_to_bottom, self)"""),
        
        # 패턴 2
        ("""self._debouncer.debounce("scroll_bottom", self._scroll_to_bottom, 500)""",
         """safe_single_shot(500, self._scroll_to_bottom, self)"""),
        
        # 패턴 3
        ("""self._debouncer.debounce("scroll_bottom", self._scroll_to_bottom, 800)""",
         """safe_single_shot(800, self._scroll_to_bottom, self)"""),
        
        # 패턴 4
        ("""self._debouncer.debounce("scroll_bottom", self._scroll_to_bottom, 1000)""",
         """safe_single_shot(1000, self._scroll_to_bottom, self)"""),
        
        # 패턴 5
        ("""safe_single_shot(600, self._scroll_to_bottom, self)
        safe_single_shot(1200, self._scroll_to_bottom, self)
        safe_single_shot(2000, self._scroll_to_bottom, self)  # 최종 확인""",
         """safe_single_shot(1000, self._scroll_to_bottom, self)"""),
    ]
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ 반복 제거: {old[:50]}...")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ {file_path} 최적화 완료")

if __name__ == "__main__":
    print("🔧 스크롤 최적화 (1번만 호출)\n")
    fix_scroll()
    print("\n🎉 완료! 이제 스크롤이 1번만 실행됩니다.")
