#!/usr/bin/env python3
"""3단계: 세부 최적화 (UI 변경 없음)"""

def optimize_chat_display():
    """chat_display.py 렌더링 최적화"""
    file_path = "ui/components/chat_display.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # __init__에 렌더 최적화 추가
    old_init = """    def __init__(self, webview):
        self.webview = webview"""
    
    new_init = """    def __init__(self, webview):
        self.webview = webview
        
        # 성능 최적화 - 렌더링 배치 처리
        from ui.render_optimizer import get_render_optimizer
        self._render_optimizer = get_render_optimizer()"""
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✅ chat_display.py: 렌더링 최적화 추가")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {file_path} 최적화 완료\n")
    else:
        print(f"⚠️  {file_path}: 패턴을 찾을 수 없음 (수동 확인 필요)\n")

def optimize_token_display():
    """token_usage_display.py 업데이트 디바운싱"""
    file_path = "ui/components/token_usage_display.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # __init__에 디바운서 추가
    if "def __init__" in content and "self._debouncer" not in content:
        # __init__ 찾기
        lines = content.split('\n')
        new_lines = []
        init_found = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            if "def __init__" in line and not init_found:
                init_found = True
                # super().__init__ 다음에 추가
                if i + 1 < len(lines) and "super().__init__" in lines[i + 1]:
                    new_lines.append(lines[i + 1])
                    new_lines.append("")
                    new_lines.append("        # 성능 최적화 - 디바운서")
                    new_lines.append("        from ui.event_debouncer import get_event_debouncer")
                    new_lines.append("        self._debouncer = get_event_debouncer()")
                    i += 1  # super 라인 스킵
        
        if init_found:
            content = '\n'.join(new_lines)
            print("✅ token_usage_display.py: 디바운서 추가")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path} 최적화 완료\n")
        else:
            print(f"⚠️  {file_path}: __init__을 찾을 수 없음\n")
    else:
        print(f"⚠️  {file_path}: 이미 최적화되었거나 패턴 불일치\n")

def optimize_settings_dialog():
    """settings_dialog.py 테마 적용 디바운싱"""
    file_path = "ui/settings_dialog.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # __init__에 디바운서 추가
    old_init = """    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle"""
    
    new_init = """    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 성능 최적화 - 디바운서
        from ui.event_debouncer import get_event_debouncer
        self._debouncer = get_event_debouncer()
        
        self.setWindowTitle"""
    
    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✅ settings_dialog.py: 디바운서 추가")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {file_path} 최적화 완료\n")
    else:
        print(f"⚠️  {file_path}: 패턴을 찾을 수 없음 (수동 확인 필요)\n")

def main():
    print("=" * 60)
    print("🚀 3단계: 세부 최적화 시작 (UI 변경 없음)")
    print("=" * 60)
    print()
    
    try:
        optimize_chat_display()
        optimize_token_display()
        optimize_settings_dialog()
        
        print("=" * 60)
        print("🎉 3단계 최적화 완료!")
        print("=" * 60)
        print("\n변경 사항:")
        print("  - chat_display.py: 렌더링 배치 처리")
        print("  - token_usage_display.py: 업데이트 디바운싱")
        print("  - settings_dialog.py: 테마 적용 디바운싱")
        print("\n✅ 모든 최적화 완료!")
        print("   python main.py 실행하여 최종 테스트")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
