"""Table formatter for markdown tables"""

import re
from typing import List


class TableFormatter:
    """Handles markdown table formatting and detection"""
    
    def is_markdown_table(self, text: str) -> bool:
        """마크다운 테이블 정확한 감지"""
        lines = text.strip().split('\n')
        table_lines = [line for line in lines if '|' in line and line.strip()]
        
        if len(table_lines) < 2:
            return False
        
        has_separator = any('---' in line or ':--' in line or '--:' in line for line in table_lines)
        valid_table_lines = [line for line in table_lines if line.count('|') >= 2]
        
        return len(valid_table_lines) >= 2 and (has_separator or len(valid_table_lines) >= 3)
    
    def has_mixed_content(self, text: str) -> bool:
        """테이블과 일반 텍스트가 혼재되어 있는지 확인"""
        has_table = self.is_markdown_table(text)
        has_other_markdown = any([
            text.count('#') > 0,
            text.count('---') > text.count('|---'),
            text.count('- ') > 0 or text.count('* ') > 0,
            text.count('```') > 0,
        ])
        return has_table and has_other_markdown
    
    def format_markdown_table(self, text: str) -> str:
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
    
    def _format_cell_markdown(self, cell_text: str) -> str:
        """Format markdown within table cells"""
        cell_text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff; font-weight: 600;">\1</strong>', cell_text)
        cell_text = re.sub(r'(?<!\*)\*(.*?)\*(?!\*)', r'<em style="color: #ffffff; font-style: italic;">\1</em>', cell_text)
        cell_text = re.sub(r'~~(.*?)~~', r'<del style="color: #888; text-decoration: line-through;">\1</del>', cell_text)
        cell_text = re.sub(r'`(.*?)`', r'<code style="background-color: #444; padding: 2px 4px; border-radius: 3px; color: #fff;">\1</code>', cell_text)
        cell_text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;" target="_blank">\1</a>', cell_text)
        
        return cell_text