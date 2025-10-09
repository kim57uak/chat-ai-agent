"""스크롤바 테마 CSS 수정 패치"""
from core.logging import get_logger

logger = get_logger("scrollbar_fix")

def apply_scrollbar_fix():
    """스크롤바 스타일을 개선하는 패치 적용"""
    
    # material_theme_manager.py 파일 읽기
    file_path = "/Users/dolpaks/Downloads/project/chat-ai-agent/ui/styles/material_theme_manager.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 기존 스크롤바 스타일 찾기 및 교체
    old_scrollbar = """        ::-webkit-scrollbar {
            width: 8px !important;
            height: 8px !important;
        }
        
        ::-webkit-scrollbar-track {
            background: {colors.get('scrollbar_track', '#1e1e1e')} !important;
            border-radius: 4px !important;
        }
        
        ::-webkit-scrollbar-thumb {
            background: {colors.get('scrollbar', '#555555')} !important;
            border-radius: 4px !important;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: {colors.get('primary', '#bb86fc')} !important;
        }"""
    
    new_scrollbar = """        /* 스크롤바 스타일 - 웹킷 기반 브라우저 */
        ::-webkit-scrollbar {
            width: 12px !important;
            height: 12px !important;
            background: transparent !important;
        }
        
        ::-webkit-scrollbar-track {
            background: {colors.get('scrollbar_track', '#1e1e1e')} !important;
            border-radius: 6px !important;
            margin: 2px !important;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, {colors.get('scrollbar', '#555555')}, {colors.get('primary', '#bb86fc')}) !important;
            border-radius: 6px !important;
            border: 2px solid {colors.get('scrollbar_track', '#1e1e1e')} !important;
            min-height: 30px !important;
            transition: all 0.2s ease !important;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, {colors.get('primary', '#bb86fc')}, {colors.get('primary_variant', '#3700b3')}) !important;
            border-color: {colors.get('primary', '#bb86fc')} !important;
            box-shadow: 0 0 8px {colors.get('primary', '#bb86fc')}40 !important;
        }
        
        ::-webkit-scrollbar-thumb:active {
            background: {colors.get('primary_variant', '#3700b3')} !important;
        }
        
        ::-webkit-scrollbar-corner {
            background: {colors.get('scrollbar_track', '#1e1e1e')} !important;
        }
        
        /* Firefox 스크롤바 스타일 */
        * {
            scrollbar-width: thin !important;
            scrollbar-color: {colors.get('scrollbar', '#555555')} {colors.get('scrollbar_track', '#1e1e1e')} !important;
        }"""
    
    # 내용 교체
    if old_scrollbar in content:
        content = content.replace(old_scrollbar, new_scrollbar)
        
        # 파일에 다시 쓰기
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug("스크롤바 스타일 패치 적용 완료")
        return True
    else:
        logger.debug("기존 스크롤바 스타일을 찾을 수 없습니다")
        return False

if __name__ == "__main__":
    apply_scrollbar_fix()