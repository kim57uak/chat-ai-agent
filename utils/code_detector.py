"""
Code Language Detector
코드 패턴으로 프로그래밍 언어 감지
"""

import re
import html


class CodeLanguageDetector:
    """코드 언어 자동 감지 (Pygments + 정규식 폴백)"""
    
    # 정규식 패턴 (폴백용)
    PATTERNS = {
        'python': [
            r'\bdef\s+\w+\s*\(',
            r'\bclass\s+\w+',
            r'\bimport\s+\w+',
            r'\bfrom\s+\w+\s+import',
            r'print\s*\(',
        ],
        'javascript': [
            r'\bfunction\s+\w+\s*\(',
            r'\bconst\s+\w+\s*=',
            r'\blet\s+\w+\s*=',
            r'\bvar\s+\w+\s*=',
            r'console\.log\s*\(',
            r'=>\s*\{',
            r'\.push\s*\(',
            r'\.includes\s*\(',
            r'Math\.\w+\s*\(',
        ],
    }
    
    @staticmethod
    def detect_language(code: str) -> str:
        """
        Pygments로 코드 언어 감지, 실패 시 정규식 폴백
        
        Returns:
            'python', 'javascript', 또는 감지된 언어명 (소문자)
        """
        if not code or not code.strip():
            return 'unknown'
        
        # HTML 태그 및 엔티티 정제
        clean_code = CodeLanguageDetector._clean_html(code)
        
        # 1차: Pygments 감지
        pygments_result = None
        try:
            from pygments.lexers import guess_lexer
            lexer = guess_lexer(clean_code)
            lang_name = lexer.name.lower()
            
            if 'python' in lang_name:
                return 'python'
            elif 'javascript' in lang_name or 'js' in lang_name or 'node' in lang_name:
                return 'javascript'
            elif 'text' not in lang_name:
                pygments_result = lang_name
        except Exception:
            pass
        
        # 2차: 정규식 패턴 매칭
        pattern_result = CodeLanguageDetector._detect_by_pattern(clean_code)
        
        # 정규식이 감지했으면 우선
        if pattern_result != 'unknown':
            return pattern_result
        
        # Pygments 결과 반환
        return pygments_result if pygments_result else 'unknown'
    
    @staticmethod
    def _clean_html(code: str) -> str:
        """HTML 태그 및 엔티티 제거"""
        # HTML 엔티티 디코딩
        decoded = html.unescape(code)
        # HTML 태그 제거
        clean = re.sub(r'<[^>]+>', '', decoded)
        return clean.strip()
    
    @staticmethod
    def _detect_by_pattern(code: str) -> str:
        """정규식 패턴으로 언어 감지"""
        scores = {}
        
        for lang, patterns in CodeLanguageDetector.PATTERNS.items():
            score = sum(1 for pattern in patterns if re.search(pattern, code, re.MULTILINE))
            if score > 0:
                scores[lang] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return 'unknown'
