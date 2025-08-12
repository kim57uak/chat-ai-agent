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
            # 혼합 콘텐츠 처리 (테이블 + 일반 텍스트)
            if self.table_formatter.has_mixed_content(text):
                return self._format_mixed_content(text, sender)
            
            # 순수 테이블 처리 (마크다운 요소가 없는 경우만)
            if (self.table_formatter.is_markdown_table(text) and 
                not any(['**' in text, '*' in text and not '|*' in text,
                        '#' in text and not '|#' in text,
                        '- ' in text and not '|- ' in text,
                        '> ' in text, '---' in text and not '|---' in text])):
                model_name = None
                if sender and ('claude' in sender.lower() or 'sonnet' in sender.lower() or 'haiku' in sender.lower() or 'opus' in sender.lower()):
                    model_name = sender
                return self.table_formatter.format_markdown_table(text, model_name)
            
            # 기본: 모든 텍스트에 마크다운 포맷팅 적용
            return self.markdown_formatter.format_basic_markdown(text)
                
        except Exception as e:
            return self.markdown_formatter.format_basic_markdown(text)
    
    def _should_use_ai_formatting(self, text: str) -> bool:
        """Determine if AI formatting analysis is needed"""
        indicators = [
            len(text) > 500,
            text.count('\n') > 5,
            '|' in text and text.count('|') > 3,
            any(keyword in text.lower() for keyword in ['compare', 'vs', 'difference', 'feature', 'contrast', '비교', '차이', '특징']),
            re.search(r'\d+\.\s', text),
            text.count('**') > 2,
        ]
        return any(indicators)
    
    def _get_ai_formatting_decision(self, text: str) -> Dict[str, Any]:
        """Use AI to determine optimal formatting approach"""
        try:
            from ui.prompts import prompt_manager
            
            content_analysis_prompt = prompt_manager.get_prompt("formatting", "content_analysis")
            analysis_prompt = f"""Analyze this content and determine the optimal formatting approach:

Content: "{text[:1000]}..."

{content_analysis_prompt}

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
                system_prompt = prompt_manager.get_prompt("formatting", "content_analyst")
                messages = [
                    SystemMessage(content=system_prompt),
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
            r'(\w+)\s*compare\s*(\w+)',
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
            any(word in line.lower() for word in ['feature', 'advantage', 'disadvantage', 'compare', 'difference', 'summary', '특징', '장점', '단점', '비교', '차이점', '요약'])
        ]
        return sum(heading_indicators) >= 2
    
    def _format_mixed_content(self, text: str, sender: str = "AI") -> str:
        """테이블과 일반 텍스트가 혼재된 콘텐츠 처리"""
        # 코드블록이 있으면 바로 마크다운 포맷팅으로 처리
        if '```' in text:
            return self.markdown_formatter.format_basic_markdown(text)
        
        lines = text.split('\n')
        result_lines = []
        non_table_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if '|' in line and line.count('|') >= 2:
                # 이전에 누적된 일반 텍스트가 있으면 먼저 처리
                if non_table_lines:
                    non_table_text = '\n'.join(non_table_lines)
                    formatted_non_table = self.markdown_formatter.format_basic_markdown(non_table_text)
                    result_lines.append(formatted_non_table)
                    non_table_lines = []
                
                # 테이블 영역 처리
                table_lines = []
                while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 2:
                    table_lines.append(lines[i])
                    i += 1
                
                table_text = '\n'.join(table_lines)
                if self.table_formatter.is_markdown_table(table_text):
                    # Claude 모델 감지 개선
                    model_name = None
                    if sender and ('claude' in sender.lower() or 'sonnet' in sender.lower() or 'haiku' in sender.lower() or 'opus' in sender.lower()):
                        model_name = sender
                    html_table = self.table_formatter.format_markdown_table(table_text, model_name)
                    result_lines.append(html_table)
                else:
                    # 테이블이 아니면 일반 텍스트로 처리
                    non_table_lines.extend(table_lines)
            else:
                # 일반 텍스트는 누적
                non_table_lines.append(lines[i])
                i += 1
        
        # 마지막에 남은 일반 텍스트 처리
        if non_table_lines:
            non_table_text = '\n'.join(non_table_lines)
            formatted_non_table = self.markdown_formatter.format_basic_markdown(non_table_text)
            result_lines.append(formatted_non_table)
        
        return '\n'.join(result_lines)
    
    def _apply_pattern_based_formatting(self, text: str) -> str:
        """Apply pattern-based formatting as fallback"""
        # 코드블록이 있으면 바로 마크다운 포맷팅
        if '```' in text:
            return self.markdown_formatter.format_basic_markdown(text)
        
        # 테이블 처리
        if self.table_formatter.has_mixed_content(text):
            return self._format_mixed_content(text)
        if self.table_formatter.is_markdown_table(text):
            return self.table_formatter.format_markdown_table(text)
        
        # 모든 텍스트에 마크다운 포맷팅 적용
        return self.markdown_formatter.format_basic_markdown(text)
    
    def _apply_cached_formatting(self, text: str, cached_decision: Dict[str, Any]) -> str:
        """Apply previously cached formatting decision"""
        return self._apply_intelligent_formatting(text, cached_decision)
    
    def _is_claude_response(self, text: str, sender: str = "") -> bool:
        """Claude 모델 응답 감지"""
        # sender에서 Claude 모델 감지
        if 'claude' in sender.lower():
            return True
        
        # 텍스트 패턴으로 Claude 감지 (폴백)
        claude_indicators = [
            '|' in text and text.count('|') > 3,  # 테이블 패턴
            '코드' in text and '|' in text,  # 한글 테이블 헤더
            text.count('\n') > 3 and '|' in text,  # 다중 라인 테이블
        ]
        return any(claude_indicators)
    
    def _normalize_claude_table(self, text: str) -> str:
        """클로드 한줄 테이블을 다중라인으로 변환"""
        # 파이프로 분리
        parts = text.split('|')
        cells = [part.strip() for part in parts if part.strip()]
        
        if len(cells) < 4:
            return text
        
        # 구분자 찾기
        separator_idx = -1
        for i, cell in enumerate(cells):
            if any(pattern in cell for pattern in ['---', ':--', '--:', '===']):
                separator_idx = i
                break
        
        if separator_idx == -1:
            return text
        
        # 헤더와 데이터 분리
        headers = cells[:separator_idx]
        data_cells = cells[separator_idx + 1:]
        
        if not headers or not data_cells:
            return text
        
        # 다중라인 테이블로 변환
        result_lines = []
        
        # 헤더 라인
        result_lines.append('| ' + ' | '.join(headers) + ' |')
        
        # 구분자 라인
        result_lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        
        # 데이터 라인들
        num_cols = len(headers)
        for i in range(0, len(data_cells), num_cols):
            if i + num_cols <= len(data_cells):
                row = data_cells[i:i + num_cols]
                # <br> 태그를 줄바꿈으로 변환
                row = [cell.replace('<br>', '\n') for cell in row]
                result_lines.append('| ' + ' | '.join(row) + ' |')
        
        return '\n'.join(result_lines)
    
    def _format_claude_content(self, text: str) -> str:
        """Claude 모델 전용 콘텐츠 포맷팅"""
        print(f"[DEBUG] _format_claude_content called")
        
        # 테이블 감지 체크
        has_mixed = self.table_formatter.has_mixed_content(text)
        is_table = self.table_formatter.is_markdown_table(text)
        print(f"[DEBUG] has_mixed_content: {has_mixed}, is_markdown_table: {is_table}")
        
        # 혼합 콘텐츠 우선 처리 (테이블 + 일반 텍스트)
        if has_mixed:
            result = self._format_mixed_content(text)
            print(f"[DEBUG] Mixed content formatting result has HTML table: {'<table' in result}")
            return result
        
        # 순수 마크다운 테이블만 있는 경우
        if is_table:
            result = self.table_formatter.format_markdown_table(text)
            print(f"[DEBUG] Pure table formatting result has HTML table: {'<table' in result}")
            return result
        
        # 기본 마크다운 포맷팅
        result = self.markdown_formatter.format_basic_markdown(text)
        print(f"[DEBUG] Basic markdown formatting result has HTML table: {'<table' in result}")
        return result