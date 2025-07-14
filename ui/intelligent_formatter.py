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
    
    def _apply_pattern_based_formatting(self, text: str) -> str:
        """Apply pattern-based formatting as fallback"""
        # Force table detection for markdown tables
        if '|' in text and ('---' in text or text.count('|') >= 6):
            return self._format_detected_table(text)
        return self._apply_basic_formatting(text)
    
    def _format_detected_table(self, text: str) -> str:
        """Format detected table content directly to HTML"""
        lines = text.strip().split('\n')
        table_lines = []
        
        for line in lines:
            if '|' in line and line.strip():
                cells = [cell.strip() for cell in line.split('|')]
                while cells and not cells[0]:
                    cells.pop(0)
                while cells and not cells[-1]:
                    cells.pop()
                
                if cells:
                    table_lines.append(cells)
        
        if len(table_lines) >= 2:
            # Generate HTML table directly
            html = '<table style="border-collapse: collapse; width: 100%; margin: 16px 0; background-color: #2a2a2a; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">'
            
            header_processed = False
            for row in table_lines:
                if '---' in ''.join(row):  # Skip separator rows
                    continue
                    
                if not header_processed:
                    html += '<thead><tr style="background: linear-gradient(135deg, #3a3a3a, #4a4a4a);">'
                    for cell in row:
                        html += f'<th style="padding: 14px 16px; border: 1px solid #555; color: #ffffff; font-weight: 700; text-align: left; font-size: 13px; white-space: nowrap;">{cell}</th>'
                    html += '</tr></thead><tbody>'
                    header_processed = True
                else:
                    html += '<tr style="background-color: #2a2a2a;">'
                    for cell in row:
                        html += f'<td style="padding: 12px 16px; border: 1px solid #444; color: #cccccc; font-size: 13px; line-height: 1.4; vertical-align: top;">{cell}</td>'
                    html += '</tr>'
            
            html += '</tbody></table>'
            return html
        
        return text
    
    def _apply_basic_formatting(self, text: str) -> str:
        """Apply basic markdown formatting"""
        # Headers
        text = re.sub(r'^# (.*?)$', r'<h1 style="color: #ffffff; margin: 20px 0 10px 0; font-size: 20px; font-weight: 600;">\\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2 style="color: #eeeeee; margin: 16px 0 8px 0; font-size: 18px; font-weight: 600;">\\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.*?)$', r'<h3 style="color: #dddddd; margin: 14px 0 7px 0; font-size: 16px; font-weight: 600;">\\1</h3>', text, flags=re.MULTILINE)
        
        # Bold text
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff; font-weight: 600;">\\1</strong>', text)
        
        # Lists
        text = re.sub(r'^(\d+)\. (.*?)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #aaaaaa; margin-right: 6px;">\\1.</span>\\2</div>', text, flags=re.MULTILINE)
        text = re.sub(r'^[•\-\*] (.*?)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #aaaaaa; margin-right: 6px;">•</span>\\1</div>', text, flags=re.MULTILINE)
        
        # Tables
        if '|' in text and ('---' in text or text.count('|') >= 6):
            text = self._format_markdown_table(text)
        
        return self._format_regular_text(text)
    
    def _format_markdown_table(self, text: str) -> str:
        """Format markdown table to HTML"""
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
                    html += f'<th style="padding: 12px; border: 1px solid #555; color: #ffffff; font-weight: 600; text-align: left;">{cell}</th>'
                html += '</tr></thead><tbody>'
                header_processed = True
            else:
                html += '<tr style="background-color: #2a2a2a;">'
                for cell in cells:
                    html += f'<td style="padding: 10px; border: 1px solid #555; color: #cccccc;">{cell}</td>'
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
    
    def _apply_cached_formatting(self, text: str, cached_decision: Dict[str, Any]) -> str:
        """Apply previously cached formatting decision"""
        return self._apply_intelligent_formatting(text, cached_decision)