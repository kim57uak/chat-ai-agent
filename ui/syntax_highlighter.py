"""Syntax highlighter for code blocks"""

import re
from typing import Dict, Callable


class SyntaxHighlighter:
    """Handles syntax highlighting for different programming languages"""
    
    def __init__(self):
        self._highlighters: Dict[str, Callable[[str], str]] = {
            'python': self._highlight_python,
            'py': self._highlight_python,
            'javascript': self._highlight_javascript,
            'js': self._highlight_javascript,
            'typescript': self._highlight_javascript,
            'ts': self._highlight_javascript,
            'java': self._highlight_java,
            'cpp': self._highlight_cpp,
            'c++': self._highlight_cpp,
            'c': self._highlight_cpp,
            'html': self._highlight_html,
            'xml': self._highlight_html,
            'css': self._highlight_css,
            'sql': self._highlight_sql,
            'json': self._highlight_json,
            'bash': self._highlight_bash,
            'shell': self._highlight_bash,
            'sh': self._highlight_bash,
        }
    
    def highlight(self, code: str, language: str) -> str:
        """Apply syntax highlighting to code"""
        # 항상 깨끗한 코드로 시작
        clean_code = self._extract_pure_code(code)
        
        # HTML 이스케이프 처리
        escaped_code = self._html_escape(clean_code)
        
        if not language:
            return escaped_code
        
        lang = language.lower()
        highlighter = self._highlighters.get(lang)
        
        if highlighter:
            return highlighter(escaped_code)
        
        return escaped_code
    
    def _extract_pure_code(self, code: str) -> str:
        """코드에서 순수 텍스트만 추출 - 단순화된 버전"""
        # 이미 깨끗한 마크다운 코드라면 그대로 반환
        if not ('<' in code and '>' in code):
            return code.strip()
        
        # HTML 태그 제거
        clean = re.sub(r'<[^>]*>', '', code)
        
        # HTML 엔티티 디코딩
        clean = clean.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        
        # 불필요한 공백 정리
        clean = re.sub(r'\n\s*\n\s*\n', '\n\n', clean)
        
        return clean.strip()
    
    def _html_escape(self, text: str) -> str:
        """HTML escape text"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def _highlight_python(self, code: str) -> str:
        """Python syntax highlighting - 개선된 버전"""
        # 문자열과 주석 먼저 처리
        strings = []
        comments = []
        
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        def store_comment(match):
            comments.append(match.group(0))
            return f'__COMMENT_{len(comments)-1}__'
        
        # 문자열 저장
        code = re.sub(r'"""[\s\S]*?"""', store_string, code)  # 삼중 따옴표 먼저
        code = re.sub(r"'''[\s\S]*?'''", store_string, code)
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        
        # 주석 저장
        code = re.sub(r'#.*$', store_comment, code, flags=re.MULTILINE)
        
        # 키워드
        keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'import', 'from', 'return', 'yield', 'lambda', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        # 함수 호출
        code = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()', r'<span style="color: #dcdcaa;">\1</span>', code)
        
        # 숫자
        code = re.sub(r'\b\d+(\.\d+)?\b', r'<span style="color: #b5cea8;">\g<0></span>', code)
        
        # 주석 복원
        for i, comment_content in enumerate(comments):
            code = code.replace(f'__COMMENT_{i}__', f'<span style="color: #6a9955;">{comment_content}</span>')
        
        # 문자열 복원
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_java(self, code: str) -> str:
        """Java syntax highlighting - 개선된 버전"""
        # 문자열 먼저 처리
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        
        # 키워드 (Java 특화)
        keywords = [
            'public', 'private', 'protected', 'static', 'final', 'abstract', 
            'class', 'interface', 'extends', 'implements', 'package', 'import',
            'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 
            'break', 'continue', 'return', 'try', 'catch', 'finally', 
            'throw', 'throws', 'new', 'this', 'super', 'void',
            'int', 'double', 'float', 'long', 'short', 'byte', 'char', 'boolean',
            'String', 'true', 'false', 'null'
        ]
        
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        # 메서드 호출 (System.out.println 등)
        code = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()', r'<span style="color: #dcdcaa;">\1</span>', code)
        
        # 클래스명 (대문자로 시작하는 식별자)
        code = re.sub(r'\b([A-Z][a-zA-Z0-9_]*)\b(?!\s*\()', r'<span style="color: #4ec9b0;">\1</span>', code)
        
        # 숫자
        code = re.sub(r'\b\d+(\.\d+)?[fFdDlL]?\b', r'<span style="color: #b5cea8;">\g<0></span>', code)
        
        # 주석
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.DOTALL)
        
        # 문자열 복원
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_javascript(self, code: str) -> str:
        """JavaScript syntax highlighting"""
        # 문자열 먼저 처리
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        code = re.sub(r'`[^`]*`', store_string, code)
        
        # 키워드
        keywords = ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'break', 'continue', 'return', 'try', 'catch', 'finally', 'throw', 'new', 'this', 'typeof', 'instanceof', 'true', 'false', 'null', 'undefined']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        # 숫자
        code = re.sub(r'\b\d+(\.\d+)?\b', r'<span style="color: #b5cea8;">\g<0></span>', code)
        
        # 주석
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.DOTALL)
        
        # 문자열 복원
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_cpp(self, code: str) -> str:
        """C/C++ syntax highlighting"""
        code = re.sub(r'"([^"]*)"', r'<span style="color: #ce9178;">"\1"</span>', code)
        code = re.sub(r'\b(int|char|float|double|void|bool|if|else|for|while|do|switch|case|default|break|continue|return|struct|class|public|private|protected|virtual|static|const|true|false|NULL)\b', r'<span style="color: #569cd6;">\1</span>', code)
        code = re.sub(r'#\w+', r'<span style="color: #c586c0;">\g<0></span>', code)
        return code
    
    def _highlight_sql(self, code: str) -> str:
        """SQL syntax highlighting"""
        code = re.sub(r"'([^']*)'", r'<span style="color: #ce9178;">\'\1\'</span>', code)
        code = re.sub(r'\b(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TABLE|INDEX|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP|BY|ORDER|HAVING|LIMIT|OFFSET|UNION|AND|OR|NOT|NULL|TRUE|FALSE)\b', r'<span style="color: #569cd6;">\1</span>', code, flags=re.IGNORECASE)
        return code
    
    def _highlight_json(self, code: str) -> str:
        """JSON syntax highlighting"""
        code = re.sub(r'"([^"]+)"\s*:', r'<span style="color: #9cdcfe;">"\1"</span>:', code)
        code = re.sub(r':\s*"([^"]*)"', r': <span style="color: #ce9178;">"\1"</span>', code)
        code = re.sub(r':\s*(\d+(\.\d+)?)', r': <span style="color: #b5cea8;">\1</span>', code)
        code = re.sub(r'\b(true|false|null)\b', r'<span style="color: #569cd6;">\1</span>', code)
        return code
    
    def _highlight_bash(self, code: str) -> str:
        """Bash syntax highlighting"""
        code = re.sub(r'"([^"]*)"', r'<span style="color: #ce9178;">"\1"</span>', code)
        code = re.sub(r"'([^']*)'", r'<span style="color: #ce9178;">\'\1\'</span>', code)
        code = re.sub(r'\b(ls|cd|pwd|mkdir|rm|cp|mv|grep|find|cat|echo|chmod|chown|sudo|git|npm|pip|python|node)\b', r'<span style="color: #569cd6;">\1</span>', code)
        code = re.sub(r'#.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        code = re.sub(r'\$\w+', r'<span style="color: #9cdcfe;">\g<0></span>', code)
        return code
    
    def _highlight_html(self, code: str) -> str:
        """HTML syntax highlighting"""
        code = re.sub(r'&lt;(/?)([a-zA-Z][a-zA-Z0-9]*)([^&]*?)&gt;', 
                     r'<span style="color: #569cd6;">&lt;\1\2</span>\3<span style="color: #569cd6;">&gt;</span>', code)
        code = re.sub(r'\s([a-zA-Z-]+)=', r' <span style="color: #9cdcfe;">\1</span>=', code)
        code = re.sub(r'="([^"]*)"', r'=<span style="color: #ce9178;">"\1"</span>', code)
        return code
    
    def _highlight_css(self, code: str) -> str:
        """CSS syntax highlighting"""
        code = re.sub(r'^([.#]?[a-zA-Z][a-zA-Z0-9-_]*)', r'<span style="color: #d7ba7d;">\1</span>', code, flags=re.MULTILINE)
        code = re.sub(r'\s*([a-zA-Z-]+)\s*:', r' <span style="color: #9cdcfe;">\1</span>:', code)
        code = re.sub(r':\s*([^;]+);', r': <span style="color: #ce9178;">\1</span>;', code)
        return code