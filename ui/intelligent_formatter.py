"""Intelligent content formatter that uses AI to determine optimal formatting"""

import re
import json
import uuid
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.enhanced_system_prompts import SystemPrompts
except ImportError:
    # Fallback if import fails
    class SystemPrompts:
        @staticmethod
        def get_content_formatting_prompt():
            return "Analyze content and determine optimal formatting approach."


class IntelligentContentFormatter:
    """AI-driven content formatter that adapts to content type and structure"""
    
    def __init__(self, llm=None):
        self.llm = llm
        self._formatting_cache = {}
    
    def format_content(self, text: str, sender: str = "AI") -> str:
        """Intelligently format content based on AI analysis"""
        try:
            # 혼합 콘텐츠 처리 - 테이블과 일반 텍스트 모두 처리
            if self._has_mixed_content(text):
                return self._format_mixed_content(text)
            
            # 순수 테이블만 있는 경우
            if self._is_markdown_table(text):
                return self._format_markdown_table(text)
            
            # Quick cache check for similar content
            content_hash = hash(text[:200])
            if content_hash in self._formatting_cache:
                return self._apply_cached_formatting(text, self._formatting_cache[content_hash])
            
            # AI-driven formatting decision
            if self.llm and self._should_use_ai_formatting(text):
                formatting_decision = self._get_ai_formatting_decision(text)
                self._formatting_cache[content_hash] = formatting_decision
                return self._apply_intelligent_formatting(text, formatting_decision)
            else:
                # Fallback to pattern-based formatting
                return self._apply_pattern_based_formatting(text)
                
        except Exception as e:
            # Graceful fallback
            return self._apply_basic_formatting(text)
    
    def _should_use_ai_formatting(self, text: str) -> bool:
        """Determine if AI formatting analysis is needed"""
        indicators = [
            len(text) > 500,
            text.count('\n') > 5,
            '|' in text and text.count('|') > 3,
            any(keyword in text.lower() for keyword in ['비교', 'vs', '차이', '특징', 'compare']),
            re.search(r'\d+\.\s', text),
            text.count('**') > 2,
        ]
        return any(indicators)
    
    def _get_ai_formatting_decision(self, text: str) -> Dict[str, Any]:
        """Use AI to determine optimal formatting approach"""
        try:
            analysis_prompt = f"""Analyze this content and determine the optimal formatting approach:

Content: "{text[:1000]}..."

{SystemPrompts.get_content_formatting_prompt()}

Respond with a JSON object containing:
{{
    "format_type": "table|list|structured|simple",
    "use_table": true/false,
    "table_headers": ["header1", "header2", ...] or null,
    "emphasis_words": ["word1", "word2", ...],
    "section_breaks": [position1, position2, ...],
    "reasoning": "brief explanation"
}}"""

            if self.llm:
                from langchain.schema import HumanMessage, SystemMessage
                messages = [
                    SystemMessage(content="You are an expert content formatting analyst."),
                    HumanMessage(content=analysis_prompt)
                ]
                response = self.llm.invoke(messages)
                
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
            
        except Exception as e:
            pass
        
        return {
            "format_type": "simple",
            "use_table": False,
            "table_headers": None,
            "emphasis_words": [],
            "section_breaks": [],
            "reasoning": "fallback formatting"
        }
    
    def _apply_intelligent_formatting(self, text: str, decision: Dict[str, Any]) -> str:
        """Apply AI-determined formatting"""
        formatted_text = text
        
        if decision.get("use_table", False) and self._detect_table_content(text):
            formatted_text = self._create_intelligent_table(text, decision.get("table_headers", []))
        
        for word in decision.get("emphasis_words", []):
            formatted_text = re.sub(
                rf'\b{re.escape(word)}\b',
                f'**{word}**',
                formatted_text,
                flags=re.IGNORECASE
            )
        
        if decision.get("format_type") == "structured":
            formatted_text = self._add_intelligent_structure(formatted_text)
        
        return self._apply_basic_formatting(formatted_text)
    
    def _detect_table_content(self, text: str) -> bool:
        """Intelligently detect if content should be formatted as a table"""
        comparison_patterns = [
            r'(\w+)\s*vs\s*(\w+)',
            r'(\w+)\s*대\s*(\w+)',
            r'(\w+)\s*비교\s*(\w+)',
            r'\|.*\|.*\|',
        ]
        
        for pattern in comparison_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        lines = text.split('\n')
        structured_lines = [line for line in lines if ':' in line or '|' in line]
        return len(structured_lines) >= 3
    
    def _create_intelligent_table(self, text: str, suggested_headers: List[str]) -> str:
        """Create a well-formatted table from content"""
        lines = text.split('\n')
        table_data = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if '|' in line:
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if cells:
                    table_data.append(cells)
        
        if len(table_data) > 1:
            headers = table_data[0] if not suggested_headers else suggested_headers[:len(table_data[0])]
            
            table_md = '| ' + ' | '.join(headers) + ' |\n'
            table_md += '| ' + ' | '.join(['---'] * len(headers)) + ' |\n'
            
            for row in table_data[1:]:
                if len(row) == len(headers):
                    table_md += '| ' + ' | '.join(row) + ' |\n'
            
            return table_md
        
        return text
    
    def _add_intelligent_structure(self, text: str) -> str:
        """Add intelligent structure with headings and sections"""
        lines = text.split('\n')
        structured_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                structured_lines.append('')
                continue
            
            if self._is_potential_heading(line):
                structured_lines.append(f'## {line}')
            elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
                structured_lines.append(f'### {line}')
            else:
                structured_lines.append(line)
        
        return '\n'.join(structured_lines)
    
    def _is_potential_heading(self, line: str) -> bool:
        """Detect if a line should be a heading"""
        heading_indicators = [
            len(line) < 50,
            line.endswith(':'),
            not line.endswith('.'),
            any(word in line.lower() for word in ['특징', '장점', '단점', '비교', '차이점', '요약'])
        ]
        return sum(heading_indicators) >= 2
    
    def _is_markdown_table(self, text: str) -> bool:
        """마크다운 테이블 정확한 감지"""
        lines = text.strip().split('\n')
        table_lines = [line for line in lines if '|' in line and line.strip()]
        
        if len(table_lines) < 2:
            return False
        
        # 구분선 확인
        has_separator = any('---' in line or ':--' in line or '--:' in line for line in table_lines)
        
        # 최소 2개 이상의 파이프가 있는 라인이 2개 이상
        valid_table_lines = [line for line in table_lines if line.count('|') >= 2]
        
        return len(valid_table_lines) >= 2 and (has_separator or len(valid_table_lines) >= 3)
    
    def _has_mixed_content(self, text: str) -> bool:
        """테이블과 일반 텍스트가 혼재되어 있는지 확인"""
        has_table = self._is_markdown_table(text)
        has_other_markdown = any([
            text.count('#') > 0,  # 헤더
            text.count('---') > text.count('|---'),  # 구분선 (테이블 구분선 제외)
            text.count('- ') > 0 or text.count('* ') > 0,  # 리스트
            text.count('```') > 0,  # 코드 블록
        ])
        return has_table and has_other_markdown
    
    def _format_mixed_content(self, text: str) -> str:
        """테이블과 일반 텍스트가 혼재된 콘텐츠 처리"""
        lines = text.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 테이블 시작 감지
            if '|' in line and line.count('|') >= 2:
                # 테이블 라인들 수집
                table_lines = []
                while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 2:
                    table_lines.append(lines[i])
                    i += 1
                
                # 테이블 HTML 생성
                table_text = '\n'.join(table_lines)
                if self._is_markdown_table(table_text):
                    html_table = self._format_markdown_table(table_text)
                    result_lines.append(html_table)
                else:
                    result_lines.extend(table_lines)
            else:
                result_lines.append(lines[i])
                i += 1
        
        # 전체 텍스트에 기본 마크다운 적용
        combined_text = '\n'.join(result_lines)
        return self._apply_basic_formatting(combined_text)
    
    def _apply_pattern_based_formatting(self, text: str) -> str:
        """Apply pattern-based formatting as fallback"""
        # 혼합 콘텐츠 처리
        if self._has_mixed_content(text):
            return self._format_mixed_content(text)
        # 순수 테이블 처리
        if self._is_markdown_table(text):
            return self._format_markdown_table(text)
        return self._apply_basic_formatting(text)
    
    def _format_detected_table(self, text: str) -> str:
        """Format detected table content - simplified"""
        return self._format_markdown_table(text)
    
    def _apply_basic_formatting(self, text: str) -> str:
        """Apply basic markdown formatting"""
        # Headers
        text = re.sub(r'^# (.*?)$', r'<h1 style="color: #ffffff; margin: 20px 0 10px 0; font-size: 20px; font-weight: 600;">\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2 style="color: #eeeeee; margin: 16px 0 8px 0; font-size: 18px; font-weight: 600;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.*?)$', r'<h3 style="color: #dddddd; margin: 14px 0 7px 0; font-size: 16px; font-weight: 600;">\1</h3>', text, flags=re.MULTILINE)
        
        # Bold text
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff; font-weight: 600;">\1</strong>', text)
        
        # Italic text (avoid conflict with bold)
        text = re.sub(r'(?<!\*)\*(.*?)\*(?!\*)', r'<em style="color: #ffffff; font-style: italic;">\1</em>', text)
        
        # Strikethrough
        text = re.sub(r'~~(.*?)~~', r'<del style="color: #888; text-decoration: line-through;">\1</del>', text)
        
        # Code inline
        text = re.sub(r'`(.*?)`', r'<code style="background-color: #444; padding: 2px 4px; border-radius: 3px; color: #fff;">\1</code>', text)
        
        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;" target="_blank">\1</a>', text)
        
        # Horizontal rule
        text = re.sub(r'^---+$', r'<hr style="border: none; border-top: 1px solid #555; margin: 16px 0;">', text, flags=re.MULTILINE)
        
        # Lists
        text = re.sub(r'^(\d+)\. (.*?)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #aaaaaa; margin-right: 6px;">\1.</span>\2</div>', text, flags=re.MULTILINE)
        text = re.sub(r'^[•\-\*] (.*?)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #aaaaaa; margin-right: 6px;">•</span>\1</div>', text, flags=re.MULTILINE)
        
        # Tables - 마크다운 테이블 우선 처리
        if self._is_markdown_table(text):
            return self._format_markdown_table(text)
        
        return self._format_regular_text(text)
    
    def _format_markdown_table(self, text: str) -> str:
        """Format markdown table to HTML with cell markdown parsing"""
        lines = text.strip().split('\n')
        table_lines = [line for line in lines if '|' in line and line.strip()]
        
        if len(table_lines) < 2:
            return text
        
        html = '<table style="border-collapse: collapse; width: 100%; margin: 12px 0; background-color: #2a2a2a; border-radius: 6px; overflow: hidden;">'
        
        header_processed = False
        for line in table_lines:
            if '---' in line or '===' in line:
                continue
                
            cells = [cell.strip() for cell in line.split('|')]
            if cells and cells[0] == '':
                cells.pop(0)
            if cells and cells[-1] == '':
                cells.pop()
            if not cells:
                continue
            
            if not header_processed:
                html += '<thead><tr style="background-color: #3a3a3a;">'
                for cell in cells:
                    formatted_cell = self._format_cell_markdown(cell)
                    html += f'<th style="padding: 12px; border: 1px solid #555; color: #ffffff; font-weight: 600; text-align: left;">{formatted_cell}</th>'
                html += '</tr></thead><tbody>'
                header_processed = True
            else:
                html += '<tr style="background-color: #2a2a2a;">'
                for cell in cells:
                    formatted_cell = self._format_cell_markdown(cell)
                    html += f'<td style="padding: 10px; border: 1px solid #555; color: #cccccc;">{formatted_cell}</td>'
                html += '</tr>'
        
        html += '</tbody></table>'
        return html
    
    def _format_regular_text(self, text: str) -> str:
        """Format regular text with proper line breaks"""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('<br>')
            elif line.startswith('<'):
                formatted_lines.append(line)
            else:
                formatted_lines.append(f'<div style="margin: 2px 0; line-height: 1.4; color: #cccccc;">{line}</div>')
        
        return '\n'.join(formatted_lines)
    
    def _format_cell_markdown(self, cell_text: str) -> str:
        """Format markdown within table cells"""
        # Bold text
        cell_text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff; font-weight: 600;">\1</strong>', cell_text)
        
        # Italic text (avoid conflict with bold)
        cell_text = re.sub(r'(?<!\*)\*(.*?)\*(?!\*)', r'<em style="color: #ffffff; font-style: italic;">\1</em>', cell_text)
        
        # Strikethrough
        cell_text = re.sub(r'~~(.*?)~~', r'<del style="color: #888; text-decoration: line-through;">\1</del>', cell_text)
        
        # Code inline
        cell_text = re.sub(r'`(.*?)`', r'<code style="background-color: #444; padding: 2px 4px; border-radius: 3px; color: #fff;">\1</code>', cell_text)
        
        # Links
        cell_text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;" target="_blank">\1</a>', cell_text)
        
        # Emojis and special characters are preserved
        return cell_text
    
    def _apply_cached_formatting(self, text: str, cached_decision: Dict[str, Any]) -> str:
        """Apply previously cached formatting decision"""
        return self._apply_intelligent_formatting(text, cached_decision)