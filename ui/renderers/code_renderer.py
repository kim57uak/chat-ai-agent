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
    
    EXECUTABLE_LANGS = {'python', 'py', 'javascript', 'js', 'java'}
    
    def __init__(self):
        self.code_blocks = {}
        # 패키징 환경 감지
        import sys
        self.is_packaged = getattr(sys, 'frozen', False)
        if self.is_packaged:
            logger.info(f"[PACKAGED] CodeRenderer 초기화 - 패키징 모드 활성화")
    
    def process(self, text: str) -> str:
        """코드 블록을 placeholder로 변환"""
        try:
            if self.is_packaged:
                logger.info(f"[PACKAGED] process() 시작 - 텍스트 길이: {len(text)}")
                logger.info(f"[PACKAGED] 코드블록 포함: {'```' in text}")
                logger.info(f"[PACKAGED] HTML 코드 포함: {'<pre>' in text or '<code' in text}")
                logger.info(f"[PACKAGED] 텍스트 샘플 (100자): {text[:100]}")
                print(f"\n[PACKAGED DEBUG] AI 원본 응답 (500자):\n{text[:500]}\n")
            
            # HTML 코드블록을 마크다운으로 변환 (패키징 환경 전용)
            if self.is_packaged and '<pre>' in text and '<code' in text:
                logger.info(f"[PACKAGED] HTML 코드블록 감지 - 마크다운으로 변환 시도")
                text = self._convert_html_to_markdown(text)
            
            result = re.sub(r'```[\s\S]*?```', self._to_placeholder, text)
            
            if self.is_packaged:
                logger.info(f"[PACKAGED] process() 완료 - placeholder 개수: {len(self.code_blocks)}")
                if len(self.code_blocks) == 0 and '```' in text:
                    logger.error(f"[PACKAGED] 코드블록이 있지만 placeholder 생성 실패!")
            
            return result
        except Exception as e:
            logger.error(f"[CODE] 처리 오류: {e}")
            return text
    
    def restore(self, text: str) -> str:
        """Placeholder를 HTML로 복원"""
        if self.is_packaged:
            logger.info(f"[PACKAGED] restore() 시작 - placeholder 개수: {len(self.code_blocks)}")
        
        for placeholder, html_content in self.code_blocks.items():
            if placeholder in text:
                text = text.replace(placeholder, html_content)
                if self.is_packaged:
                    logger.info(f"[PACKAGED] placeholder 복원 성공")
            elif self.is_packaged:
                logger.warning(f"[PACKAGED] placeholder 찾을 수 없음")
        
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
            
            # CRITICAL: HTML 정리 - 코드 블록만 처리 (Mermaid는 이미 위에서 제외됨)
            raw_lines = [self._clean_html(line) for line in code.split('\n')]
            code_lines = [line.rstrip() for line in raw_lines]
            
            if not lang:
                lang = self._detect_language('\n'.join(code_lines))
            
            # HTML 생성
            code_id = f"code_{uuid.uuid4().hex[:8]}"
            html_content = self._create_html(code_id, lang, code_lines)
            
            # Placeholder 저장 - 마크다운 파싱에서 보호되도록 특수 형식 사용
            placeholder = f"\x00CODE_BLOCK_{code_id}\x00"
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
        """코드 블록 HTML 생성 - 환경별 처리"""
        logger.info(f"[CODE] _create_html 호출 - is_packaged={self.is_packaged}, code_id={code_id}, lang={lang}")
        if self.is_packaged:
            logger.info(f"[PACKAGED] _create_html_packaged 호출")
            result = self._create_html_packaged(code_id, lang, code_lines)
            logger.info(f"[PACKAGED] HTML 생성 완료 - 길이: {len(result)}")
            return result
        return self._create_html_dev(code_id, lang, code_lines)
    
    def _create_html_dev(self, code_id: str, lang: str, code_lines: list) -> str:
        """개발 환경용 코드블록 HTML (기존 로직)"""
        code_content = '\n'.join(code_lines)
        escaped_code = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        lang_lower = lang.lower() if lang else ''
        is_executable = lang_lower in self.EXECUTABLE_LANGS
        if lang_lower in {'python', 'py'}:
            exec_lang = 'python'
        elif lang_lower in {'javascript', 'js'}:
            exec_lang = 'javascript'
        elif lang_lower == 'java':
            exec_lang = 'java'
        else:
            exec_lang = 'python'
        
        lang_label = f'<div style="position: absolute; top: 8px; left: 12px; background: rgba(255,255,255,0.1); color: #aaa; padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; z-index: 10;">{lang or "code"}</div>'
        
        copy_right = "82px" if is_executable else "8px"
        copy_btn = f'<button onclick="copyCodeBlock(\'{code_id}\')" class="code-btn code-copy-btn" style="position: absolute; top: 8px; right: {copy_right}; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2); background: #444 !important; color: #fff !important;">📋 복사</button>'
        exec_btn = f'<button onclick="executeCode(\'{code_id}\', \'{exec_lang}\')" class="code-btn code-exec-btn" style="position: absolute; top: 8px; right: 8px; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2); background: #4CAF50 !important; color: #fff !important;">▶️ 실행</button>' if is_executable else ''
        
        return f'<div style="position: relative; margin: 12px 0;">{lang_label}{copy_btn}{exec_btn}<pre style="background: #1e1e1e; color: #d4d4d4; padding: 16px; padding-top: 40px; border-radius: 8px; margin: 0; overflow-x: auto; line-height: 1.5; font-family: \'SF Mono\', Monaco, Consolas, monospace; font-size: 13px;"><code id="{code_id}" data-language="{lang}">{escaped_code}</code></pre></div>'
    
    def _create_html_packaged(self, code_id: str, lang: str, code_lines: list) -> str:
        """패키징 환경용 코드블록 HTML (이중 인코딩 방지, 빈줄 제거, 버튼 강제 표시)"""
        code_content = '\n'.join(code_lines)
        
        # 패키징 환경 디버깅 강화
        print(f"\n=== [PACKAGED] 코드블록 생성 ===")
        print(f"ID: {code_id}")
        print(f"언어: {lang}")
        print(f"라인 수: {len(code_lines)}")
        print(f"원본 코드 (첫 200자): {code_content[:200]}")
        print(f"=================================\n")
        
        logger.info(f"[PACKAGED] 코드블록 생성: id={code_id}, lang={lang}, lines={len(code_lines)}")
        logger.debug(f"[PACKAGED] 원본 코드 (첫 100자): {code_content[:100]}")
        
        # 이중 인코딩 방지
        if '&amp;' in code_content or '&lt;' in code_content:
            escaped_code = code_content
            logger.debug(f"[PACKAGED] 이미 인코딩됨 - 건너뛰기")
        else:
            escaped_code = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            logger.debug(f"[PACKAGED] HTML 인코딩 완료")
        
        lang_lower = lang.lower() if lang else ''
        is_executable = lang_lower in self.EXECUTABLE_LANGS
        if lang_lower in {'python', 'py'}:
            exec_lang = 'python'
        elif lang_lower in {'javascript', 'js'}:
            exec_lang = 'javascript'
        elif lang_lower == 'java':
            exec_lang = 'java'
        else:
            exec_lang = 'python'
        
        logger.info(f"[PACKAGED] 실행 가능: {is_executable}, 언어: {exec_lang}")
        
        # 버튼 display 강제
        lang_label = f'<div class="code-lang-label" style="position: absolute; top: 8px; left: 12px; background: rgba(255,255,255,0.1); color: #aaa; padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; z-index: 10; display: block !important; visibility: visible !important;">{lang or "code"}</div>'
        
        copy_right = "82px" if is_executable else "8px"
        copy_btn = f'<button onclick="copyCodeBlock(\'{code_id}\')" class="code-btn code-copy-btn" style="position: absolute; top: 8px; right: {copy_right}; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2); background: #444 !important; color: #fff !important; display: block !important; visibility: visible !important;">📋 복사</button>'
        exec_btn = f'<button onclick="executeCode(\'{code_id}\', \'{exec_lang}\')" class="code-btn code-exec-btn" style="position: absolute; top: 8px; right: 8px; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; z-index: 10; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2); background: #4CAF50 !important; color: #fff !important; display: block !important; visibility: visible !important;">▶️ 실행</button>' if is_executable else ''
        
        html_result = f'<div style="position: relative; margin: 12px 0; display: block;">{lang_label}{copy_btn}{exec_btn}<pre style="background: #1e1e1e; color: #d4d4d4; padding: 16px; padding-top: 40px; border-radius: 8px; margin: 0; overflow-x: auto; line-height: 1.5; font-family: \'SF Mono\', Monaco, Consolas, monospace; font-size: 13px; white-space: pre !important; display: block;"><code id="{code_id}" data-language="{lang}" style="white-space: pre !important; display: block;">{escaped_code}</code></pre></div>'
        
        print(f"[PACKAGED] HTML 생성 완료 - 길이: {len(html_result)}")
        print(f"[PACKAGED] HTML 샘플 (첫 300자): {html_result[:300]}")
        
        logger.debug(f"[PACKAGED] HTML 생성 완료 (길이: {len(html_result)})")
        return html_result
    
    def _convert_html_to_markdown(self, text: str) -> str:
        """패키징 환경에서 HTML 코드블록을 마크다운으로 변환"""
        import re
        
        def html_to_md(match):
            full = match.group(0)
            # language-xxx 추출
            lang_match = re.search(r'language-(\w+)', full)
            lang = lang_match.group(1) if lang_match else ''
            
            # 코드 내용 추출
            code_match = re.search(r'<code[^>]*>(.*?)</code>', full, re.DOTALL)
            if code_match:
                code = code_match.group(1)
                # HTML 엔티티 디코딩
                code = code.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                return f"```{lang}\n{code}\n```"
            return full
        
        # <pre><code>...</code></pre> 패턴 변환
        result = re.sub(r'<pre>\s*<code[^>]*>.*?</code>\s*</pre>', html_to_md, text, flags=re.DOTALL)
        logger.info(f"[PACKAGED] HTML->Markdown 변환 완료")
        return result
