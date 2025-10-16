#!/usr/bin/env python3
"""스크롤 로직 단순화 - 튕김 완전 제거"""

def fix_scroll_final():
    file_path = "ui/chat_widget.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 복잡한 _scroll_to_bottom을 간단하게 교체
    old_method = """    def _scroll_to_bottom(self):
        \"\"\"채팅 화면을 맨 하단으로 스크롤 - 최대 강화 버전\"\"\"
        # 사용자가 스크롤 중이면 중단
        import time
        if self._user_is_scrolling:
            if time.time() - self._last_scroll_time < 1.0:  # 1초 이내
                return
        
        try:
            self.chat_display_view.page().runJavaScript(\"\"\"
                // 전역 함수로 한 번만 선언
                if (!window.forceScrollToBottom) {
                    window.forceScrollToBottom = () => {
                        const heights = [
                            document.body.scrollHeight,
                            document.documentElement.scrollHeight,
                            document.body.offsetHeight,
                            document.documentElement.offsetHeight,
                            document.body.clientHeight,
                            document.documentElement.clientHeight
                        ];
                        
                        const maxScroll = Math.max(...heights.filter(h => h > 0));
                        const targetScroll = maxScroll + 1000;
                        
                        window.scrollTo(0, targetScroll);
                        window.scroll(0, targetScroll);
                        document.documentElement.scrollTop = targetScroll;
                        document.body.scrollTop = targetScroll;
                        
                        const messagesDiv = document.getElementById('messages');
                        if (messagesDiv) {
                            messagesDiv.scrollTop = messagesDiv.scrollHeight;
                        }
                        
                        setTimeout(() => {
                            window.scrollTo({
                                top: targetScroll,
                                left: 0,
                                behavior: 'smooth'
                            });
                        }, 10);
                    };
                }
                
                // 함수 실행
                window.forceScrollToBottom();
            \"\"\")
        except Exception as e:
            logger.debug(f\"스크롤 오류: {e}\")"""
    
    new_method = """    def _scroll_to_bottom(self):
        \"\"\"채팅 화면을 맨 하단으로 스크롤 - 단순화\"\"\"
        try:
            # 간단하고 확실한 방법
            self.chat_display_view.page().runJavaScript(\"\"\"
                window.scrollTo(0, document.body.scrollHeight);
            \"\"\")
        except Exception as e:
            logger.debug(f\"스크롤 오류: {e}\")"""
    
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("✅ 스크롤 로직 단순화")
    else:
        print("⚠️  패턴 불일치 - 수동 확인 필요")
        return False
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path} 수정 완료")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 스크롤 튕김 완전 제거")
    print("=" * 60)
    print()
    
    if fix_scroll_final():
        print()
        print("=" * 60)
        print("🎉 완료!")
        print("=" * 60)
        print("\n변경:")
        print("  - 복잡한 스크롤 로직 제거")
        print("  - 단순하고 확실한 방법 사용")
        print("  - 튕김 현상 완전 제거")
        print("\n테스트: python main.py")
    else:
        print("\n❌ 수동 수정 필요")
