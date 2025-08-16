import markdown
from typing import Optional


class EnhancedMarkdownParser:
    """AI 응답에 최적화된 마크다운 파서"""
    
    def __init__(self):
        """모든 AI 마크다운 패턴을 지원하는 파서 초기화"""
        try:
            # 기본 확장 기능들
            extensions = [
                'tables', 'fenced_code', 'codehilite', 'toc', 
                'footnotes', 'attr_list', 'def_list', 'abbr',
                'admonition', 'nl2br', 'sane_lists'
            ]
            
            extension_configs = {
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True
                },
                'toc': {
                    'permalink': True
                },
                'sane_lists': {
                    'nested_indent': 2,
                    'ordered_list_start': 1
                }
            }
            
            # pymdown-extensions 확인 및 추가
            try:
                import pymdownx
                extensions.extend([
                    'pymdownx.tasklist',      # 체크박스
                    'pymdownx.tilde',         # 취소선
                    'pymdownx.mark',          # 하이라이트
                    'pymdownx.superfences',   # 고급 코드 블록
                    'pymdownx.highlight',     # 구문 강조
                    'pymdownx.emoji',         # 이모지
                    'pymdownx.betterem',      # 개선된 강조
                    'pymdownx.caret',         # 위첨자
                    'pymdownx.keys',          # 키보드 키
                    'pymdownx.smartsymbols'   # 스마트 심볼
                ])
                
                extension_configs.update({
                    'pymdownx.tasklist': {
                        'custom_checkbox': True,
                        'clickable_checkbox': False
                    },
                    'pymdownx.highlight': {
                        'anchor_linenums': True,
                        'line_spans': '__span',
                        'pygments_lang_class': True
                    },
                    'pymdownx.superfences': {
                        'custom_fences': [
                            {
                                'name': 'mermaid',
                                'class': 'mermaid',
                                'format': lambda source: f'<div class="mermaid">{source}</div>'
                            }
                        ]
                    }
                })
            except ImportError:
                pass
            
            # 수학 공식 지원
            try:
                import mdx_math
                extensions.append('mdx_math')
                extension_configs['mdx_math'] = {
                    'enable_dollar_delimiter': True,
                    'add_preview': True
                }
            except ImportError:
                pass
            
            self.md = markdown.Markdown(
                extensions=extensions,
                extension_configs=extension_configs
            )
            
        except Exception as e:
            # 기본 파서로 폴백
            self.md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    
    def convert(self, text: str) -> str:
        """마크다운을 HTML로 변환"""
        if not text:
            return ""
        
        try:
            # 한글 헤더 전처리
            text = self._preprocess_korean_headers(text)
            
            # 마크다운 변환
            result = self.md.convert(text)
            self.md.reset()
            
            # 다크 테마 스타일 적용
            result = self._apply_dark_theme_styles(result)
            return result
        except Exception as e:
            # 변환 실패 시 원본 텍스트 반환
            return text
    
    def _preprocess_korean_headers(self, text: str) -> str:
        """한글 헤더 전처리 - 마크다운 라이브러리가 한글 헤더를 제대로 처리하지 못하는 문제 해결"""
        import re
        
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # 헤더 패턴 감지 (### 한글 헤더)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # 한글이 포함된 헤더인 경우 공백 추가로 안정성 향상
                if any('\u3131' <= char <= '\u318e' or '\uac00' <= char <= '\ud7a3' for char in title):
                    # 헤더 전후에 공백 라인 추가
                    processed_lines.append('')  # 전 공백
                    processed_lines.append(f'{"".join(["#"] * level)} {title}')
                    processed_lines.append('')  # 후 공백
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _apply_dark_theme_styles(self, html: str) -> str:
        """다크 테마에 맞는 스타일 적용"""
        # 테이블 스타일
        html = html.replace('<table>', 
            '<table style="border-collapse: collapse; width: 100%; margin: 12px 0; background-color: #2a2a2a; border-radius: 6px; overflow: hidden;">')
        html = html.replace('<th>', 
            '<th style="padding: 12px; border: 1px solid #555; color: #ffffff; font-weight: 600; text-align: left; background-color: #3a3a3a;">')
        html = html.replace('<td>', 
            '<td style="padding: 10px; border: 1px solid #555; color: #cccccc;">')
        
        # 코드 블록 스타일
        html = html.replace('<pre>', 
            '<pre style="background-color: #1e1e1e; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0;">')
        html = html.replace('<code>', 
            '<code style="background-color: #444; padding: 2px 4px; border-radius: 3px; color: #fff; font-family: \'Consolas\', \'Monaco\', monospace;">')
        
        # 인용문 스타일
        html = html.replace('<blockquote>', 
            '<blockquote style="margin: 12px 0; padding: 12px 16px; border-left: 4px solid #87CEEB; background-color: rgba(135, 206, 235, 0.1); color: #dddddd; font-style: italic;">')
        
        # 헤더 스타일 (한글 헤더 지원 강화)
        for i in range(1, 7):
            size = 24 - (i * 2)
            html = html.replace(f'<h{i}>', 
                f'<h{i} style="color: #ffffff; margin: {20-i*2}px 0 {10-i}px 0; font-size: {size}px; font-weight: 600; line-height: 1.4; word-break: keep-all;">')
        
        # 리스트 스타일
        html = html.replace('<ul>', 
            '<ul style="color: #cccccc; margin: 8px 0; padding-left: 20px;">')
        html = html.replace('<ol>', 
            '<ol style="color: #cccccc; margin: 8px 0; padding-left: 20px;">')
        html = html.replace('<li>', 
            '<li style="margin: 4px 0; line-height: 1.6;">')
        
        # 링크 스타일
        import re
        html = re.sub(r'<a href="([^"]*)"([^>]*)', 
            r'<a href="\1" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;" target="_blank"\2', html)
        
        # 강조 스타일
        html = html.replace('<strong>', '<strong style="color: #ffffff; font-weight: 600;">')
        html = html.replace('<em>', '<em style="color: #ffffff; font-style: italic;">')
        
        # 수평선 스타일
        html = html.replace('<hr>', 
            '<hr style="border: none; border-top: 2px solid #555; margin: 20px 0; background: linear-gradient(to right, transparent, #555, transparent);">')
        
        # 일반 텍스트 스타일 (한글 지원)
        html = re.sub(r'<p>([^<]*(?:<[^>]*>[^<]*)*)</p>', 
            r'<p style="color: #cccccc; line-height: 1.6; margin: 8px 0; word-break: keep-all;">\1</p>', html)
        
        return html
    
    def is_fully_compatible(self) -> bool:
        """모든 AI 마크다운 패턴 지원 여부 확인"""
        test_patterns = {
            "~~취소선~~": "<del>",
            "- [x] 체크박스": "checkbox",
            "==하이라이트==": "<mark>",
            "$E=mc^2$": "math/tex",
            "**굵게**": "<strong>",
            "*기울임*": "<em>",
            "`코드`": "<code>"
        }
        
        for pattern, expected in test_patterns.items():
            result = self.convert(pattern)
            if expected not in result:
                return False
        
        return True
    
    def get_supported_features(self) -> list:
        """지원되는 기능 목록 반환"""
        features = [
            "헤더 (H1-H6)",
            "텍스트 서식 (굵게, 기울임)",
            "리스트 (순서있는/없는, 중첩)",
            "코드 블록 (구문 강조)",
            "테이블 (정렬 포함)",
            "링크 및 이미지",
            "인용문",
            "각주",
            "HTML 태그"
        ]
        
        # 확장 기능 확인
        test_cases = {
            "~~test~~": "취소선",
            "- [x] test": "체크박스 리스트",
            "==test==": "하이라이트",
            "$x^2$": "수학 공식"
        }
        
        for pattern, feature in test_cases.items():
            result = self.convert(pattern)
            if pattern not in result:
                features.append(feature)
        
        return features