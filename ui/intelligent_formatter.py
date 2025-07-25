"""Intelligent content formatter that uses AI to determine optimal formatting"""

import re
import json
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .markdown_formatter import MarkdownFormatter
from .table_formatter import TableFormatter

try:
    from core.enhanced_system_prompts import SystemPrompts
except ImportError:
    class SystemPrompts:
        @staticmethod
        def get_content_formatting_prompt():
            return "Analyze content and determine optimal formatting approach."


class IntelligentContentFormatter:
    """AI-driven content formatter that adapts to content type and structure"""
    
    def __init__(self, llm=None):
        self.llm = llm
        self._formatting_cache = {}
        self.markdown_formatter = MarkdownFormatter()
        self.table_formatter = TableFormatter()
    
    def format_content(self, text: str, sender: str = "AI") -> str:
        """Intelligently format content based on AI analysis"""
        try:
            if self.table_formatter.has_mixed_content(text):
                return self._format_mixed_content(text)
            
            if self.table_formatter.is_markdown_table(text):
                return self.table_formatter.format_markdown_table(text)
            
            content_hash = hash(text[:200])
            if content_hash in self._formatting_cache:
                return self._apply_cached_formatting(text, self._formatting_cache[content_hash])
            
            if self.llm and self._should_use_ai_formatting(text):
                formatting_decision = self._get_ai_formatting_decision(text)
                self._formatting_cache[content_hash] = formatting_decision
                return self._apply_intelligent_formatting(text, formatting_decision)
            else:
                return self._apply_pattern_based_formatting(text)
                
        except Exception as e:
            return self.markdown_formatter.format_basic_markdown(text)
    
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
        
        return self.markdown_formatter.format_basic_markdown(formatted_text)
    
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
    
    def _create_intelligent_table(self, text: str, suggested_headers: list) -> str:
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
    
    def _format_mixed_content(self, text: str) -> str:
        """테이블과 일반 텍스트가 혼재된 콘텐츠 처리"""
        lines = text.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if '|' in line and line.count('|') >= 2:
                table_lines = []
                while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 2:
                    table_lines.append(lines[i])
                    i += 1
                
                table_text = '\n'.join(table_lines)
                if self.table_formatter.is_markdown_table(table_text):
                    html_table = self.table_formatter.format_markdown_table(table_text)
                    result_lines.append(html_table)
                else:
                    result_lines.extend(table_lines)
            else:
                result_lines.append(lines[i])
                i += 1
        
        combined_text = '\n'.join(result_lines)
        return self.markdown_formatter.format_basic_markdown(combined_text)
    
    def _apply_pattern_based_formatting(self, text: str) -> str:
        """Apply pattern-based formatting as fallback"""
        if self.table_formatter.has_mixed_content(text):
            return self._format_mixed_content(text)
        if self.table_formatter.is_markdown_table(text):
            return self.table_formatter.format_markdown_table(text)
        return self.markdown_formatter.format_basic_markdown(text)
    
    def _apply_cached_formatting(self, text: str, cached_decision: Dict[str, Any]) -> str:
        """Apply previously cached formatting decision"""
        return self._apply_intelligent_formatting(text, cached_decision)