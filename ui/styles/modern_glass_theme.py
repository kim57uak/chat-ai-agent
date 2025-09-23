"""현대적 Glass Morphism 테마 적용"""

def apply_modern_glass_design():
    """현대적 Glass morphism 디자인을 적용하는 패치"""
    
    # material_theme_manager.py 파일 읽기
    file_path = "/Users/dolpaks/Downloads/project/chat-ai-agent/ui/styles/material_theme_manager.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 웹뷰 CSS에 현대적 스타일 추가
    modern_css_addition = '''
        
        /* 현대적 타이포그래피 */
        html, body {
            font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
            font-size: 15px !important;
            font-weight: 400 !important;
            line-height: 1.6 !important;
        }
        
        /* Glass Morphism 메시지 카드 */
        .message {
            backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(139, 92, 246, 0.1) !important;
            border-radius: 16px !important;
            margin: 16px 0 !important;
            padding: 20px !important;
        }
        
        .message:hover {
            transform: translateY(-2px) !important;
            border-color: rgba(139, 92, 246, 0.2) !important;
            box-shadow: 0 8px 32px rgba(139, 92, 246, 0.1) !important;
        }
        
        /* 현대적 코드 블록 */
        pre {
            backdrop-filter: blur(20px) !important;
            border-radius: 12px !important;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace !important;
            font-size: 13px !important;
            line-height: 1.5 !important;
        }
        
        code {
            background: rgba(139, 92, 246, 0.1) !important;
            border: 1px solid rgba(139, 92, 246, 0.2) !important;
            border-radius: 4px !important;
            color: #8b5cf6 !important;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace !important;
            font-size: 12px !important;
            padding: 2px 6px !important;
        }
        
        /* 미니멀 스크롤바 */
        ::-webkit-scrollbar {
            width: 6px !important;
            height: 6px !important;
            background: transparent !important;
        }
        
        ::-webkit-scrollbar-track {
            background: transparent !important;
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(139, 92, 246, 0.3) !important;
            border-radius: 3px !important;
            border: none !important;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(139, 92, 246, 0.6) !important;
        }
        '''
    
    # CSS 끝부분에 추가
    if '        \"\"\"\n    \n    def get_available_themes(self) -> Dict[str, str]:' in content:
        content = content.replace(
            '        \"\"\"\n    \n    def get_available_themes(self) -> Dict[str, str]:',
            f'        {modern_css_addition}\n        \"\"\"\n    \n    def get_available_themes(self) -> Dict[str, str]:'
        )
        
        # 파일에 다시 쓰기
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("현대적 Glass morphism 디자인 적용 완료")
        return True
    else:
        print("CSS 삽입 위치를 찾을 수 없습니다")
        return False

if __name__ == "__main__":
    apply_modern_glass_design()