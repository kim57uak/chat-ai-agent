"""
Content Renderer - 단일 진입점 (Facade Pattern)
"""
from core.logging import get_logger
from .code_renderer import CodeRenderer
from .markdown_renderer import MarkdownRenderer
from .mermaid_renderer import MermaidRenderer
from .image_renderer import ImageRenderer
import re

logger = get_logger("content_renderer")


class ContentRenderer:
    """콘텐츠 렌더링 통합 (Facade Pattern)"""
    
    def __init__(self):
        self.code_renderer = CodeRenderer()
        self.markdown_renderer = MarkdownRenderer()
        self.mermaid_renderer = MermaidRenderer()
        self.image_renderer = ImageRenderer()
    
    def render(self, text: str) -> str:
        """텍스트를 HTML로 렌더링"""
        if not text:
            return ""
        
        try:
            # 1단계: 특수 콘텐츠를 placeholder로 변환
            text = self.image_renderer.process(text)
            text = self._clean_html_blocks(text)
            text = self.mermaid_renderer.process(text)  # Mermaid → placeholder
            text = self.code_renderer.process(text)     # Code → placeholder
            
            # 2단계: 마크다운 처리 (placeholder는 보호됨)
            text = self.markdown_renderer.process(text)
            
            # 3단계: placeholder를 실제 HTML로 복원
            text = self.code_renderer.restore(text)
            text = self.mermaid_renderer.restore(text)
            return text
        except Exception as e:
            logger.error(f"[CONTENT] 렌더링 오류: {e}")
            return text
    
    def _clean_html_blocks(self, text: str) -> str:
        """HTML 코드 블록 정리"""
        if '__MERMAID_PLACEHOLDER_' in text:
            return text
        
        def clean(match):
            content = match.group(1)
            content = re.sub(r'<[^>]+>', '', content)
            content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            content = content.replace('&quot;', '"').replace('&#x27;', "'")
            
            # 빈 줄 정리
            lines = []
            prev_empty = False
            for line in content.split('\n'):
                is_empty = not line.strip()
                if is_empty and prev_empty:
                    continue
                lines.append(line.rstrip())
                prev_empty = is_empty
            
            return f'```\n{"\n".join(lines)}\n```'
        
        return re.sub(
            r'<div class="highlight"><pre><span></span><code>(.*?)</code></pre></div>',
            clean,
            text,
            flags=re.DOTALL
        )
