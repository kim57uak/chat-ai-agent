"""Syntax highlighter for code blocks"""

import re
from typing import Dict, Callable


class SyntaxHighlighter:
    """Handles syntax highlighting for different programming languages"""
    
    def __init__(self):
        self._highlighters: Dict[str, Callable[[str], str]] = {
            # Top 20 Programming Languages
            'python': self._highlight_python,
            'py': self._highlight_python,
            'javascript': self._highlight_javascript,
            'js': self._highlight_javascript,
            'typescript': self._highlight_javascript,
            'ts': self._highlight_javascript,
            'java': self._highlight_java,
            'cpp': self._highlight_cpp,
            'c++': self._highlight_cpp,
            'c': self._highlight_c,
            'csharp': self._highlight_csharp,
            'cs': self._highlight_csharp,
            'c#': self._highlight_csharp,
            'php': self._highlight_php,
            'ruby': self._highlight_ruby,
            'rb': self._highlight_ruby,
            'go': self._highlight_go,
            'golang': self._highlight_go,
            'rust': self._highlight_rust,
            'rs': self._highlight_rust,
            'swift': self._highlight_swift,
            'kotlin': self._highlight_kotlin,
            'kt': self._highlight_kotlin,
            'scala': self._highlight_scala,
            'r': self._highlight_r,
            'matlab': self._highlight_matlab,
            'm': self._highlight_matlab,
            'perl': self._highlight_perl,
            'pl': self._highlight_perl,
            'dart': self._highlight_dart,
            'lua': self._highlight_lua,
            'haskell': self._highlight_haskell,
            'hs': self._highlight_haskell,
            # Web & Markup
            'html': self._highlight_html,
            'xml': self._highlight_html,
            'css': self._highlight_css,
            'scss': self._highlight_css,
            'sass': self._highlight_css,
            # Data & Config
            'sql': self._highlight_sql,
            'json': self._highlight_json,
            'yaml': self._highlight_yaml,
            'yml': self._highlight_yaml,
            'toml': self._highlight_toml,
            # Shell
            'bash': self._highlight_bash,
            'shell': self._highlight_bash,
            'sh': self._highlight_bash,
            'powershell': self._highlight_powershell,
            'ps1': self._highlight_powershell,
        }
    
    def highlight(self, code: str, language: str) -> str:
        """Apply syntax highlighting to code"""
        # 항상 깨끗한 코드로 시작
        clean_code = self._extract_pure_code(code)
        
        # HTML 이스케이프 처리
        escaped_code = self._html_escape(clean_code)
        
        if not language:
            return self._apply_default_highlighting(escaped_code)
        
        lang = language.lower()
        highlighter = self._highlighters.get(lang)
        
        if highlighter:
            return highlighter(escaped_code)
        
        # 지원하지 않는 언어의 경우 기본 하이라이팅 적용
        return self._apply_default_highlighting(escaped_code)
    
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
    
    def _apply_default_highlighting(self, code: str) -> str:
        """Apply basic highlighting for unsupported languages"""
        # 이미 HTML 태그가 있는지 확인
        if '<span' in code or '<div' in code:
            return code
        
        # 문자열 하이라이팅 (다양한 인용부호 지원)
        code = re.sub(r'"[^"]*"', r'<span style="color: #ce9178;">\g<0></span>', code)
        code = re.sub(r"'[^']*'", r'<span style="color: #ce9178;">\g<0></span>', code)
        code = re.sub(r'`[^`]*`', r'<span style="color: #ce9178;">\g<0></span>', code)
        
        # 숫자 하이라이팅
        code = re.sub(r'\b\d+(\.\d+)?\b', r'<span style="color: #b5cea8;">\g<0></span>', code)
        
        # 주석 하이라이팅 (다양한 주석 스타일 지원)
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        code = re.sub(r'#.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        code = re.sub(r'--.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.DOTALL)
        
        # 일반적인 키워드 하이라이팅 (대부분의 언어에서 공통적으로 사용되는 키워드)
        common_keywords = ['if', 'else', 'for', 'while', 'do', 'function', 'return', 'true', 'false', 'null', 'undefined', 'var', 'let', 'const', 'class', 'def', 'import', 'export', 'from', 'as', 'try', 'catch', 'finally', 'throw', 'new', 'this', 'super', 'extends', 'implements']
        for keyword in common_keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        # 괄호와 연산자 하이라이팅
        code = re.sub(r'([\(\)\[\]\{\}])', r'<span style="color: #ffd700;">\1</span>', code)
        code = re.sub(r'([+\-*/=<>!&|%^~])', r'<span style="color: #d4d4d4;">\1</span>', code)
        
        return code
    
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
        """C++ syntax highlighting"""
        strings = []
        comments = []
        
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        def store_comment(match):
            comments.append(match.group(0))
            return f'__COMMENT_{len(comments)-1}__'
        
        # 문자열과 주석을 먼저 저장
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        code = re.sub(r'//.*$', store_comment, code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', store_comment, code, flags=re.DOTALL)
        
        # 전처리기 지시어 먼저 처리 (키워드와 충돌 방지)
        preprocessor_directives = []
        def store_preprocessor(match):
            preprocessor_directives.append(match.group(0))
            return f'__PREPROCESSOR_{len(preprocessor_directives)-1}__'
        
        code = re.sub(r'#\w+', store_preprocessor, code)
        
        # 키워드 처리
        keywords = ['auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while', 'class', 'private', 'protected', 'public', 'virtual', 'friend', 'inline', 'template', 'this', 'operator', 'new', 'delete', 'namespace', 'using', 'try', 'catch', 'throw', 'true', 'false', 'nullptr']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        # 전처리기 지시어 복원
        for i, preprocessor_content in enumerate(preprocessor_directives):
            code = code.replace(f'__PREPROCESSOR_{i}__', f'<span style="color: #c586c0;">{preprocessor_content}</span>')
        
        # 숫자 하이라이팅
        code = re.sub(r'\b\d+(\.\d+)?[fFdDlL]?\b', r'<span style="color: #b5cea8;">\g<0></span>', code)
        
        # 주석 복원
        for i, comment_content in enumerate(comments):
            code = code.replace(f'__COMMENT_{i}__', f'<span style="color: #6a9955;">{comment_content}</span>')
        
        # 문자열 복원
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_c(self, code: str) -> str:
        """C syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        
        keywords = ['auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'#\w+', r'<span style="color: #c586c0;">\g<0></span>', code)
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_csharp(self, code: str) -> str:
        """C# syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        
        keywords = ['abstract', 'as', 'base', 'bool', 'break', 'byte', 'case', 'catch', 'char', 'checked', 'class', 'const', 'continue', 'decimal', 'default', 'delegate', 'do', 'double', 'else', 'enum', 'event', 'explicit', 'extern', 'false', 'finally', 'fixed', 'float', 'for', 'foreach', 'goto', 'if', 'implicit', 'in', 'int', 'interface', 'internal', 'is', 'lock', 'long', 'namespace', 'new', 'null', 'object', 'operator', 'out', 'override', 'params', 'private', 'protected', 'public', 'readonly', 'ref', 'return', 'sbyte', 'sealed', 'short', 'sizeof', 'stackalloc', 'static', 'string', 'struct', 'switch', 'this', 'throw', 'true', 'try', 'typeof', 'uint', 'ulong', 'unchecked', 'unsafe', 'ushort', 'using', 'virtual', 'void', 'volatile', 'while']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_php(self, code: str) -> str:
        """PHP syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        
        keywords = ['abstract', 'and', 'array', 'as', 'break', 'callable', 'case', 'catch', 'class', 'clone', 'const', 'continue', 'declare', 'default', 'die', 'do', 'echo', 'else', 'elseif', 'empty', 'enddeclare', 'endfor', 'endforeach', 'endif', 'endswitch', 'endwhile', 'eval', 'exit', 'extends', 'final', 'finally', 'for', 'foreach', 'function', 'global', 'goto', 'if', 'implements', 'include', 'include_once', 'instanceof', 'insteadof', 'interface', 'isset', 'list', 'namespace', 'new', 'or', 'print', 'private', 'protected', 'public', 'require', 'require_once', 'return', 'static', 'switch', 'throw', 'trait', 'try', 'unset', 'use', 'var', 'while', 'xor', 'yield', 'true', 'false', 'null']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'\$\w+', r'<span style="color: #9cdcfe;">\g<0></span>', code)
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_ruby(self, code: str) -> str:
        """Ruby syntax highlighting"""
        strings = []
        comments = []
        
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        def store_comment(match):
            comments.append(match.group(0))
            return f'__COMMENT_{len(comments)-1}__'
        
        # 문자열과 주석을 먼저 저장 (키워드 처리 전에)
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        code = re.sub(r'#.*$', store_comment, code, flags=re.MULTILINE)
        
        # 키워드 처리
        keywords = ['alias', 'and', 'begin', 'break', 'case', 'class', 'def', 'defined?', 'do', 'else', 'elsif', 'end', 'ensure', 'false', 'for', 'if', 'in', 'module', 'next', 'nil', 'not', 'or', 'redo', 'rescue', 'retry', 'return', 'self', 'super', 'then', 'true', 'undef', 'unless', 'until', 'when', 'while', 'yield']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        # 숫자 하이라이팅
        code = re.sub(r'\b\d+(\.\d+)?\b', r'<span style="color: #b5cea8;">\g<0></span>', code)
        
        # 주석 복원
        for i, comment_content in enumerate(comments):
            code = code.replace(f'__COMMENT_{i}__', f'<span style="color: #6a9955;">{comment_content}</span>')
        
        # 문자열 복원
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_go(self, code: str) -> str:
        """Go syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r'`[^`]*`', store_string, code)
        
        keywords = ['break', 'case', 'chan', 'const', 'continue', 'default', 'defer', 'else', 'fallthrough', 'for', 'func', 'go', 'goto', 'if', 'import', 'interface', 'map', 'package', 'range', 'return', 'select', 'struct', 'switch', 'type', 'var', 'true', 'false', 'nil']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_rust(self, code: str) -> str:
        """Rust syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        
        keywords = ['as', 'break', 'const', 'continue', 'crate', 'else', 'enum', 'extern', 'false', 'fn', 'for', 'if', 'impl', 'in', 'let', 'loop', 'match', 'mod', 'move', 'mut', 'pub', 'ref', 'return', 'self', 'Self', 'static', 'struct', 'super', 'trait', 'true', 'type', 'unsafe', 'use', 'where', 'while']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_swift(self, code: str) -> str:
        """Swift syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        
        keywords = ['associatedtype', 'class', 'deinit', 'enum', 'extension', 'fileprivate', 'func', 'import', 'init', 'inout', 'internal', 'let', 'open', 'operator', 'private', 'protocol', 'public', 'static', 'struct', 'subscript', 'typealias', 'var', 'break', 'case', 'continue', 'default', 'defer', 'do', 'else', 'fallthrough', 'for', 'guard', 'if', 'in', 'repeat', 'return', 'switch', 'where', 'while', 'as', 'catch', 'false', 'is', 'nil', 'rethrows', 'super', 'self', 'Self', 'throw', 'throws', 'true', 'try']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_kotlin(self, code: str) -> str:
        """Kotlin syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        
        keywords = ['as', 'break', 'class', 'continue', 'do', 'else', 'false', 'for', 'fun', 'if', 'in', 'interface', 'is', 'null', 'object', 'package', 'return', 'super', 'this', 'throw', 'true', 'try', 'typealias', 'val', 'var', 'when', 'while', 'by', 'catch', 'constructor', 'delegate', 'dynamic', 'field', 'file', 'finally', 'get', 'import', 'init', 'param', 'property', 'receiver', 'set', 'setparam', 'where', 'actual', 'abstract', 'annotation', 'companion', 'const', 'crossinline', 'data', 'enum', 'expect', 'external', 'final', 'infix', 'inline', 'inner', 'internal', 'lateinit', 'noinline', 'open', 'operator', 'out', 'override', 'private', 'protected', 'public', 'reified', 'sealed', 'suspend', 'tailrec', 'vararg']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_scala(self, code: str) -> str:
        """Scala syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        
        keywords = ['abstract', 'case', 'catch', 'class', 'def', 'do', 'else', 'extends', 'false', 'final', 'finally', 'for', 'forSome', 'if', 'implicit', 'import', 'lazy', 'match', 'new', 'null', 'object', 'override', 'package', 'private', 'protected', 'return', 'sealed', 'super', 'this', 'throw', 'trait', 'try', 'true', 'type', 'val', 'var', 'while', 'with', 'yield']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_r(self, code: str) -> str:
        """R syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        
        keywords = ['if', 'else', 'repeat', 'while', 'function', 'for', 'in', 'next', 'break', 'TRUE', 'FALSE', 'NULL', 'Inf', 'NaN', 'NA', 'NA_integer_', 'NA_real_', 'NA_complex_', 'NA_character_']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'#.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_matlab(self, code: str) -> str:
        """MATLAB syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r"'[^']*'", store_string, code)
        
        keywords = ['break', 'case', 'catch', 'continue', 'else', 'elseif', 'end', 'for', 'function', 'global', 'if', 'otherwise', 'persistent', 'return', 'switch', 'try', 'while']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'%.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_perl(self, code: str) -> str:
        """Perl syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        
        keywords = ['if', 'unless', 'while', 'until', 'for', 'foreach', 'do', 'else', 'elsif', 'given', 'when', 'default', 'sub', 'my', 'our', 'local', 'use', 'require', 'package', 'return', 'last', 'next', 'redo', 'goto', 'die', 'exit', 'eval']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'#.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        code = re.sub(r'\$\w+', r'<span style="color: #9cdcfe;">\g<0></span>', code)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_dart(self, code: str) -> str:
        """Dart syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        
        keywords = ['abstract', 'as', 'assert', 'async', 'await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'default', 'deferred', 'do', 'dynamic', 'else', 'enum', 'export', 'extends', 'external', 'factory', 'false', 'final', 'finally', 'for', 'get', 'if', 'implements', 'import', 'in', 'is', 'library', 'new', 'null', 'operator', 'part', 'rethrow', 'return', 'set', 'static', 'super', 'switch', 'sync', 'this', 'throw', 'true', 'try', 'typedef', 'var', 'void', 'while', 'with', 'yield']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_lua(self, code: str) -> str:
        """Lua syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        
        keywords = ['and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function', 'if', 'in', 'local', 'nil', 'not', 'or', 'repeat', 'return', 'then', 'true', 'until', 'while']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'--.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_haskell(self, code: str) -> str:
        """Haskell syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        
        keywords = ['case', 'class', 'data', 'default', 'deriving', 'do', 'else', 'if', 'import', 'in', 'infix', 'infixl', 'infixr', 'instance', 'let', 'module', 'newtype', 'of', 'then', 'type', 'where']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        code = re.sub(r'--.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_yaml(self, code: str) -> str:
        """YAML syntax highlighting"""
        code = re.sub(r'^(\s*)(\w+):', r'\1<span style="color: #9cdcfe;">\2</span>:', code, flags=re.MULTILINE)
        code = re.sub(r':\s*"([^"]*)"', r': <span style="color: #ce9178;">"\1"</span>', code)
        code = re.sub(r':\s*([^\s"]+)$', r': <span style="color: #b5cea8;">\1</span>', code, flags=re.MULTILINE)
        code = re.sub(r'#.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        return code
    
    def _highlight_toml(self, code: str) -> str:
        """TOML syntax highlighting"""
        code = re.sub(r'^\[([^\]]+)\]', r'[<span style="color: #9cdcfe;">\1</span>]', code, flags=re.MULTILINE)
        code = re.sub(r'^(\w+)\s*=', r'<span style="color: #9cdcfe;">\1</span> =', code, flags=re.MULTILINE)
        code = re.sub(r'=\s*"([^"]*)"', r'= <span style="color: #ce9178;">"\1"</span>', code)
        code = re.sub(r'#.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        return code
    
    def _highlight_powershell(self, code: str) -> str:
        """PowerShell syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        
        keywords = ['begin', 'break', 'catch', 'continue', 'data', 'do', 'dynamicparam', 'else', 'elseif', 'end', 'exit', 'filter', 'finally', 'for', 'foreach', 'from', 'function', 'if', 'in', 'param', 'process', 'return', 'switch', 'throw', 'trap', 'try', 'until', 'while']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code, flags=re.IGNORECASE)
        
        code = re.sub(r'#.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        code = re.sub(r'\$\w+', r'<span style="color: #9cdcfe;">\g<0></span>', code)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
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
        strings = []
        comments = []
        
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        def store_comment(match):
            comments.append(match.group(0))
            return f'__COMMENT_{len(comments)-1}__'
        
        # 문자열과 주석을 먼저 저장 (키워드 처리 전에)
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        code = re.sub(r'#.*$', store_comment, code, flags=re.MULTILINE)
        
        # 키워드 처리
        keywords = ['ls', 'cd', 'pwd', 'mkdir', 'rm', 'cp', 'mv', 'grep', 'find', 'cat', 'echo', 'chmod', 'chown', 'sudo', 'git', 'npm', 'pip', 'python', 'node', 'if', 'then', 'else', 'elif', 'fi', 'for', 'while', 'do', 'done', 'case', 'esac', 'function', 'return', 'exit', 'break', 'continue', 'read', 'export', 'source', 'bash', 'sh']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span style="color: #569cd6;">{keyword}</span>', code)
        
        # 변수 하이라이팅 (문자열 밖의 변수)
        code = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', r'<span style="color: #9cdcfe;">$\1</span>', code)
        code = re.sub(r'\$\{([^}]+)\}', r'<span style="color: #9cdcfe;">${\1}</span>', code)
        
        # 주석 복원
        for i, comment_content in enumerate(comments):
            code = code.replace(f'__COMMENT_{i}__', f'<span style="color: #6a9955;">{comment_content}</span>')
        
        # 문자열 복원
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code
    
    def _highlight_html(self, code: str) -> str:
        """HTML syntax highlighting"""
        code = re.sub(r'&lt;(/?)([a-zA-Z][a-zA-Z0-9]*)([^&]*?)&gt;', 
                     r'<span style="color: #569cd6;">&lt;\1\2</span>\3<span style="color: #569cd6;">&gt;</span>', code)
        code = re.sub(r'\s([a-zA-Z-]+)=', r' <span style="color: #9cdcfe;">\1</span>=', code)
        code = re.sub(r'="([^"]*)"', r'=<span style="color: #ce9178;">"\1"</span>', code)
        return code
    
    def _highlight_css(self, code: str) -> str:
        """CSS/SCSS/SASS syntax highlighting"""
        strings = []
        def store_string(match):
            strings.append(match.group(0))
            return f'__STRING_{len(strings)-1}__'
        
        code = re.sub(r'"[^"]*"', store_string, code)
        code = re.sub(r"'[^']*'", store_string, code)
        
        # Selectors
        code = re.sub(r'^([.#]?[a-zA-Z][a-zA-Z0-9-_]*)', r'<span style="color: #d7ba7d;">\1</span>', code, flags=re.MULTILINE)
        # Properties
        code = re.sub(r'\s*([a-zA-Z-]+)\s*:', r' <span style="color: #9cdcfe;">\1</span>:', code)
        # Comments
        code = re.sub(r'/\*.*?\*/', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.DOTALL)
        code = re.sub(r'//.*$', lambda m: f'<span style="color: #6a9955;">{m.group()}</span>', code, flags=re.MULTILINE)
        
        for i, string_content in enumerate(strings):
            code = code.replace(f'__STRING_{i}__', f'<span style="color: #ce9178;">{string_content}</span>')
        
        return code