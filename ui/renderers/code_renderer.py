"""
Code Renderer - 최적화 완료
"""
from core.logging import get_logger
import re
import uuid
import html

logger = get_logger("code_renderer")


class CodeRenderer:
    """코드 블록 렌더링"""
    
    EXECUTABLE_LANGS = {'python', 'py', 'javascript', 'js'}
    
    def __init__(self):
        self.code_blocks = {}
    
    def process(self, text: str) -> str:
        """코드 블록을 placeholder로 변환"""
        try:
            return re.sub(r'```[\s\S]*?```', self._to_placeholder, text)
        except Exception as e:
            logger.error(f"[CODE] 처리 오류: {e}")
            return text
    
    def restore(self, text: str) -> str:
        """Placeholder를 HTML로 복원"""
        for placeholder, html_content in self.code_blocks.items():
            text = text.replace(placeholder, html_content)
        return text
    
    def _to_placeholder(self, match):
        """코드 블록을 HTML로 변환 후 placeholder 반환"""
        try:
            full_match = match.group(0)
            
            # Mermaid placeholder가 이미 있으면 건너뛰기
            if '__MERMAID_PLACEHOLDER_' in full_match:
                return full_match
            
            content = full_match[3:-3]  # ``` 제거
            
            # 언어 추출
            lines = content.split('\n', 1)
            if len(lines) > 1 and lines[0].strip().isalpha():
                lang, code = lines[0].strip(), lines[1]
            else:
                lang, code = '', content
            
            # Mermaid 블록은 건너뛰기 (MermaidRenderer가 놓친 경우 대비)
            if lang.lower() == 'mermaid':
                logger.debug(f"[CODE] Mermaid 블록 건너뛰기 (lang=mermaid)")
                return full_match
            
            # HTML 정리 및 언어 감지
            raw_lines = [self._clean_html(line) for line in code.split('\n')]
            
            # 연속된 빈 줄 제거
            code_lines = []
            prev_empty = False
            for line in raw_lines:
                is_empty = not line.strip()
                if is_empty and prev_empty:
                    continue
                code_lines.append(line.rstrip())
                prev_empty = is_empty
            
            if not lang:
                lang = self._detect_language('\n'.join(code_lines))
            
            # HTML 생성
            code_id = f"code_{uuid.uuid4().hex[:8]}"
            html_content = self._create_html(code_id, lang, code_lines)
            
            # Placeholder 저장
            placeholder = f"__CODE_BLOCK_{code_id}__"
            self.code_blocks[placeholder] = html_content
            return placeholder
        except Exception as e:
            logger.error(f"[CODE] 블록 처리 오류: {e}")
            return match.group(0)
    
    def _detect_language(self, code: str) -> str:
        """언어 자동 감지"""
        try:
            from utils.code_detector import CodeLanguageDetector
            return CodeLanguageDetector.detect_language(code)
        except Exception as e:
            logger.warning(f"[CODE] 언어 감지 실패: {e}")
            return 'python'
    
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거 및 엔티티 디코딩"""
        text = re.sub(r'<[^>]+>', '', text)
        prev = None
        while prev != text:
            prev = text
            text = html.unescape(text)
        return text
    
    def _create_html(self, code_id: str, lang: str, code_lines: list) -> str:
        """코드 블록 HTML 생성"""
        code_content = '\n'.join(code_lines)
        escaped_code = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        lang_lower = lang.lower() if lang else ''
        is_executable = lang_lower in self.EXECUTABLE_LANGS
        exec_lang = 'python' if lang_lower in {'python', 'py'} else 'javascript'
        
        # 버튼 생성
        lang_label = f'<div style="position: absolute; top: 8px; left: 12px; background: rgba(255,255,255,0.1); color: #aaa; padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; z-index: 10;">{lang or "code"}</div>'
        
        btn_style = "position: absolute; top: 8px; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"
        
        copy_right = "82px" if is_executable else "8px"
        copy_btn = f'<button onclick="copyCodeBlock(\'{code_id}\')" class="code-btn code-copy-btn" style="{btn_style} right: {copy_right}; background: #444 !important; color: #fff !important;">📋 복사</button>'
        
        exec_btn = f'<button onclick="executeCode(\'{code_id}\', \'{exec_lang}\')" class="code-btn code-exec-btn" style="{btn_style} right: 8px; background: #4CAF50 !important; color: #fff !important;">▶️ 실행</button>' if is_executable else ''
        
        return f'<div style="position: relative; margin: 12px 0;">{lang_label}{copy_btn}{exec_btn}<pre style="background: #1e1e1e; color: #d4d4d4; padding: 16px; padding-top: 40px; border-radius: 8px; margin: 0; overflow-x: auto; line-height: 1.5; font-family: \'SF Mono\', Monaco, Consolas, monospace; font-size: 13px;"><code id="{code_id}" data-language="{lang}">{escaped_code}</code></pre></div>'
