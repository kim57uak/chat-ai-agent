"""
Image Renderer - 리팩토링 완료
"""
from core.logging import get_logger
import re
import uuid

logger = get_logger("image_renderer")


class ImageRenderer:
    """이미지 URL 렌더링"""
    
    URL_PATTERN = r'(?<!src=")(https://image\.pollinations\.ai/[^\s<>")\]]+)(?!")'
    
    LOADER_STYLE = '''width: 100%; height: 400px; background: linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 100%); background-size: 200% 100%; animation: shimmer 2s ease-in-out infinite; border-radius: 12px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border); position: relative; overflow: hidden;'''
    
    IMG_STYLE = '''max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); display: none; animation: fadeIn 0.5s ease-in;'''
    
    ANIMATIONS = '''<style>
@keyframes shimmer{0%{background-position:-200% 0;}100%{background-position:200% 0;}}
@keyframes pulse{0%,100%{opacity:0.5;}50%{opacity:1;}}
@keyframes float{0%,100%{transform:translateY(0px);}50%{transform:translateY(-10px);}}
@keyframes dots{0%,20%{content:'';}40%{content:'.';}60%{content:'..';}80%,100%{content:'...';}}
@keyframes fadeIn{from{opacity:0;transform:scale(0.95);}to{opacity:1;transform:scale(1);}}
</style>'''
    
    def process(self, text: str) -> str:
        """이미지 URL 처리"""
        try:
            # 이미 변환된 경우 스킵
            if '<img' in text and 'pollinations' in text:
                return text
            
            return re.sub(self.URL_PATTERN, self._create_image_html, text)
        except Exception as e:
            logger.error(f"[IMAGE] 처리 오류: {e}")
            return text
    
    def _create_image_html(self, match) -> str:
        """이미지 HTML 생성"""
        url = match.group(1)
        img_id = f"img_{uuid.uuid4().hex[:8]}"
        
        return f'''<div style="margin: 20px 0; text-align: center;">
<div id="{img_id}_loader" style="{self.LOADER_STYLE}">
<div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at center, rgba(255,255,255,0.05) 0%, transparent 70%); animation: pulse 3s ease-in-out infinite;"></div>
<div style="text-align: center; z-index: 1;">
<div style="font-size: 64px; margin-bottom: 16px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3)); animation: float 3s ease-in-out infinite;">🖼️</div>
<div style="color: var(--text-dim); font-size: 15px; font-weight: 500; letter-spacing: 0.5px;">이미지 생성 중<span style="animation: dots 1.5s steps(4, end) infinite;">...</span></div>
</div>
</div>
<img id="{img_id}" src="{url}" style="{self.IMG_STYLE}" onload="var loader=document.getElementById('{img_id}_loader'); if(loader) loader.style.display='none'; this.style.display='block';" onerror="var loader=document.getElementById('{img_id}_loader'); if(loader) loader.innerHTML='<div style=color:var(--error);font-size:16px;font-weight:500>❌ 이미지 로드 실패</div>';" />
</div>{self.ANIMATIONS}'''
