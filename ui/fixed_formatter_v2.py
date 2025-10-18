"""완전히 새로운 포매터 - 서버 사이드 렌더링 전용"""
from core.logging import get_logger
import re
import uuid

logger = get_logger("fixed_formatter_v2")


class FixedFormatterV2:
    """서버 사이드 렌더링 전용 포매터"""
    
    def format_basic_markdown(self, text: str) -> str:
        if not text:
            return ""
        
        # 1. Mermaid 처리
        text = self._process_mermaid(text)
        
        # 2. 수식 처리
        text = self._process_math(text)
        
        # 3. 이미지 URL 변환
        text = self._convert_image_urls(text)
        
        # 4. 코드 블록 처리
        text = self._process_code_blocks(text)
        
        # 5. 기본 마크다운
        text = self._process_markdown(text)
        
        return text
    
    def _process_code_blocks(self, text):
        """코드 블록을 HTML로 변환 (서버 사이드 완전 처리)"""
        lines = text.split('\n')
        result = []
        in_code_block = False
        code_lines = []
        code_lang = ''
        
        for line in lines:
            if line.startswith('```') and not line.startswith('```mermaid'):
                if not in_code_block:
                    in_code_block = True
                    code_lang = line[3:].strip()
                    code_lines = []
                else:
                    # 코드 블록 종료 - HTML 생성
                    code_content = '\n'.join(code_lines)
                    html_block = self._create_code_block_html(code_content, code_lang)
                    result.append(html_block)
                    in_code_block = False
            elif in_code_block:
                clean_line = self._clean_html_code(line)
                code_lines.append(clean_line)
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _create_code_block_html(self, code_content, lang):
        """코드 블록 HTML 생성"""
        from utils.code_detector import CodeLanguageDetector
        
        # 언어 자동 감지
        if not lang:
            lang = CodeLanguageDetector.detect_language(code_content)
            logger.debug(f"[CODE] 자동 감지: {lang}")
        
        # 고유 ID 생성
        code_id = f"code_{uuid.uuid4().hex[:8]}"
        
        # 실행 가능 여부 판단
        lang_lower = lang.lower() if lang else ''
        is_executable = lang_lower in ['python', 'py', 'javascript', 'js']
        exec_lang = 'python' if lang_lower in ['python', 'py'] else 'javascript' if lang_lower in ['javascript', 'js'] else ''
        
        # HTML 이스케이프
        escaped_code = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # 버튼 생성
        lang_label = f'<div style="position: absolute; top: 8px; left: 12px; background: rgba(255,255,255,0.1); color: #aaa; padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; z-index: 10;">{lang or "code"}</div>'
        
        if is_executable:
            exec_btn = f'<button onclick="executeCode(\'{code_id}\', \'{exec_lang}\')" style="position: absolute; top: 8px; right: 8px; background: #4CAF50; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10; transition: all 0.2s;" onmouseover="this.style.background=\'#45a049\'; this.style.transform=\'scale(1.05)\';" onmouseout="this.style.background=\'#4CAF50\'; this.style.transform=\'scale(1)\';">▶️ 실행</button>'
            copy_btn = f'<button onclick="copyCodeBlock(\'{code_id}\')" style="position: absolute; top: 8px; right: 82px; background: #444 !important; color: #ffffff !important; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10; transition: all 0.2s;" onmouseover="this.style.background=\'#555\'; this.style.transform=\'scale(1.05)\';" onmouseout="this.style.background=\'#444\'; this.style.transform=\'scale(1)\';" class="code-copy-btn">📋 복사</button>'
        else:
            exec_btn = ''
            copy_btn = f'<button onclick="copyCodeBlock(\'{code_id}\')" style="position: absolute; top: 8px; right: 8px; background: #444 !important; color: #ffffff !important; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10; transition: all 0.2s;" onmouseover="this.style.background=\'#555\'; this.style.transform=\'scale(1.05)\';" onmouseout="this.style.background=\'#444\'; this.style.transform=\'scale(1)\';" class="code-copy-btn">📋 복사</button>'
        
        return f'<div style="position: relative; margin: 12px 0;">{lang_label}{copy_btn}{exec_btn}<pre style="background: #1e1e1e; color: #d4d4d4; padding: 16px; padding-top: 40px; border-radius: 8px; margin: 0; overflow-x: auto; line-height: 1.2; font-family: \'SF Mono\', Monaco, Consolas, monospace; font-size: 13px;"><code id="{code_id}" data-language="{lang}">{escaped_code}</code></pre></div>'
    
    def _process_mermaid(self, text):
        """Mermaid 다이어그램 처리"""
        # 기존 fixed_formatter의 _process_mermaid 로직 재사용
        from ui.fixed_formatter import FixedFormatter
        formatter = FixedFormatter()
        return formatter._process_mermaid(text)
    
    def _process_math(self, text):
        """수식 처리"""
        return text
    
    def _convert_image_urls(self, text):
        """이미지 URL 변환"""
        from ui.fixed_formatter import FixedFormatter
        formatter = FixedFormatter()
        return formatter._convert_image_urls(text)
    
    def _clean_html_code(self, text):
        """HTML 태그 제거"""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        text = text.replace('&quot;', '"').replace('&#x27;', "'")
        return text
    
    def _process_markdown(self, text):
        """기본 마크다운 처리"""
        lines = text.split('\n')
        result = []
        
        for line in lines:
            # placeholder 통과
            if '__MERMAID_PLACEHOLDER_' in line or '__MATH_PLACEHOLDER_' in line:
                result.append(line)
                continue
            
            # 헤더
            if line.startswith('# '):
                result.append(f'<h1 style="color: #fff; margin: 16px 0 8px 0;">{line[2:]}</h1>')
            elif line.startswith('## '):
                result.append(f'<h2 style="color: #eee; margin: 14px 0 6px 0;">{line[3:]}</h2>')
            elif line.startswith('### '):
                result.append(f'<h3 style="color: #ddd; margin: 12px 0 4px 0;">{line[4:]}</h3>')
            # 굵은 글씨
            elif '**' in line:
                line = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #fff;">\1</strong>', line)
                result.append(f'<p style="color: #ccc; margin: 4px 0;">{line}</p>')
            # 리스트
            elif line.startswith('- '):
                result.append(f'<div style="color: #ccc; margin: 2px 0;">• {line[2:]}</div>')
            # 빈 줄
            elif line.strip() == '':
                result.append('<br>')
            # 일반 텍스트
            else:
                if line.strip():
                    result.append(f'<p style="color: #ccc; margin: 4px 0; line-height: 1.6;">{line}</p>')
        
        html = '\n'.join(result)
        
        # placeholder 복원
        if hasattr(self, 'mermaid_blocks'):
            for placeholder, content in self.mermaid_blocks.items():
                html = html.replace(placeholder, content)
        
        return html
