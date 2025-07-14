import re
import json
import uuid
from typing import Dict, Any
from ui.intelligent_formatter import IntelligentContentFormatter


class ChatMessageFormatter:
    """Enhanced chat message formatter with AI-driven content analysis"""
    
    def __init__(self, llm=None):
        self.intelligent_formatter = IntelligentContentFormatter(llm)
    
    def format_text(self, text: str) -> str:
        """AI-enhanced text formatting with intelligent content analysis"""
        # Use intelligent formatter for complex content
        return self.intelligent_formatter.format_content(text)
        # 코드 블록 처리
        def format_code_block(match):
            lang = match.group(1).strip() if match.group(1) else 'code'
            code = match.group(2)
            code_id = f"code_{uuid.uuid4().hex[:8]}"
            
            # 들여쓰기 정리
            lines = code.split('\n')
            if lines and lines[0].strip() == '':
                lines = lines[1:]
            if lines and lines[-1].strip() == '':
                lines = lines[:-1]
            
            if lines:
                min_indent = float('inf')
                for line in lines:
                    if line.strip():
                        indent = len(line) - len(line.lstrip())
                        min_indent = min(min_indent, indent)
                
                if min_indent != float('inf') and min_indent > 0:
                    lines = [line[min_indent:] if len(line) > min_indent else line for line in lines]
                
                code = '\n'.join(lines)
            
            return f'<div style="background-color: #1e1e1e; border: 1px solid #444444; border-radius: 6px; margin: 12px 0; overflow: hidden;"><div style="background-color: #2d2d2d; padding: 6px 12px; font-size: 11px; color: #888888; border-bottom: 1px solid #444444; display: flex; justify-content: space-between; align-items: center;"><span>{lang}</span><button onclick="copyCode(\'{code_id}\')" style="background: #444; border: none; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 10px; cursor: pointer; opacity: 0.7; transition: opacity 0.2s;" onmouseover="this.style.opacity=\'1\'" onmouseout="this.style.opacity=\'0.7\'">복사</button></div><pre id="{code_id}" style="background: none; color: #f8f8f2; padding: 16px; margin: 0; font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.4; overflow-x: auto; white-space: pre;">{code}</pre></div>'
        
        # 코드 블록 처리 (복사 버튼 포함)
        text = re.sub(r'```([^\n]*)\n([\s\S]*?)```', format_code_block, text)
        
        # 헤딩 처리
        text = re.sub(r'^# (.*?)$', r'<h1 style="color: #ffffff; margin: 20px 0 10px 0; font-size: 20px; font-weight: 600;">\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2 style="color: #eeeeee; margin: 16px 0 8px 0; font-size: 18px; font-weight: 600;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.*?)$', r'<h3 style="color: #dddddd; margin: 14px 0 7px 0; font-size: 16px; font-weight: 600;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^#### (.*?)$', r'<h4 style="color: #cccccc; margin: 12px 0 6px 0; font-size: 14px; font-weight: 600;">\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^##### (.*?)$', r'<h5 style="color: #bbbbbb; margin: 10px 0 5px 0; font-size: 13px; font-weight: 600;">\1</h5>', text, flags=re.MULTILINE)
        text = re.sub(r'^###### (.*?)$', r'<h6 style="color: #aaaaaa; margin: 8px 0 4px 0; font-size: 12px; font-weight: 600;">\1</h6>', text, flags=re.MULTILINE)
        
        # 굵은 글씨
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff; font-weight: 600;">\1</strong>', text)
        
        # 번호 목록
        text = re.sub(r'^(\d+)\. (.*?)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #aaaaaa; margin-right: 6px;">\1.</span>\2</div>', text, flags=re.MULTILINE)
        
        # 불릿 포인트
        text = re.sub(r'^[•\-\*] (.*?)$', r'<div style="margin: 4px 0; margin-left: 16px; color: #cccccc;"><span style="color: #aaaaaa; margin-right: 6px;">•</span>\1</div>', text, flags=re.MULTILINE)
        
        # 인라인 코드
        text = re.sub(r'`([^`]+)`', r'<code style="background-color: #2d2d2d; color: #f8f8f2; padding: 3px 6px; border-radius: 4px; font-family: Consolas, Monaco, monospace; font-size: 13px; border: 1px solid #444444;">\1</code>', text)
        
        # 링크
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #bbbbbb; text-decoration: underline;" target="_blank">\1</a>', text)
        
        # This method is now handled by IntelligentContentFormatter
        # Keeping for backward compatibility
        return text
    
    @staticmethod
    def _format_table(table_text: str) -> str:
        """테이블 포맷팅"""
        lines = table_text.strip().split('\n')
        table_lines = [line for line in lines if '|' in line and line.strip()]
        
        if len(table_lines) < 2:
            return table_text
        
        # 테이블 HTML 생성
        html = '<table style="border-collapse: collapse; width: 100%; margin: 12px 0; background-color: #2a2a2a; border-radius: 6px; overflow: hidden;">'
        
        header_processed = False
        for line in table_lines:
            # 구분선 건너뛰기
            if '---' in line or '===' in line:
                continue
                
            # 파이프로 분할하고 앞뒤 빈 셀 제거
            cells = [cell.strip() for cell in line.split('|')]
            if cells and cells[0] == '':
                cells.pop(0)
            if cells and cells[-1] == '':
                cells.pop()
            if not cells:
                continue
            
            # 헤더 행 처리
            if not header_processed:
                html += '<thead><tr style="background-color: #3a3a3a;">'
                for cell in cells:
                    html += f'<th style="padding: 12px; border: 1px solid #555; color: #ffffff; font-weight: 600; text-align: left;">{cell}</th>'
                html += '</tr></thead><tbody>'
                header_processed = True
            else:
                # 데이터 행 처리
                html += '<tr style="background-color: #2a2a2a;">'
                for cell in cells:
                    html += f'<td style="padding: 10px; border: 1px solid #555; color: #cccccc;">{cell}</td>'
                html += '</tr>'
        
        html += '</tbody></table>'
        return html
    
    @staticmethod
    def _format_regular_text(text: str) -> str:
        """일반 텍스트 포맷팅 - 불필요한 줄바꿈 제거"""
        lines = text.split('\n')
        formatted_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.strip()
            if not line:
                if not prev_empty:  # 연속된 빈 줄 방지
                    formatted_lines.append('<br>')
                    prev_empty = True
            elif line.startswith('<'):
                formatted_lines.append(line)
                prev_empty = False
            else:
                formatted_lines.append(f'<div style="margin: 2px 0; line-height: 1.4; color: #cccccc;">{line}</div>')
                prev_empty = False
        
        return '\n'.join(formatted_lines)
    
    def create_message_html(self, sender: str, text: str) -> str:
        """Enhanced message HTML generation with intelligent formatting"""
        # 발신자별 스타일
        if sender == '사용자':
            bg_color = 'rgba(163,135,215,0.15)'
            border_color = 'rgb(163,135,215)'
            text_color = '#ffffff'
            icon = '💬'
            sender_color = 'rgb(163,135,215)'
        elif sender in ['AI', '에이전트'] or '에이전트' in sender:
            bg_color = 'rgba(135,163,215,0.15)'
            border_color = 'rgb(135,163,215)'
            text_color = '#ffffff'
            icon = '🤖'
            sender_color = 'rgb(135,163,215)'
        else:
            bg_color = 'rgba(215,163,135,0.15)'
            border_color = 'rgb(215,163,135)'
            text_color = '#ffffff'
            icon = '⚙️'
            sender_color = 'rgb(215,163,135)'
        
        formatted_text = self.format_text(text)
        
        return f"""
        <div style="
            margin: 12px 0;
            padding: 16px;
            background: linear-gradient(135deg, {bg_color}33, {bg_color}11);
            border-radius: 12px;
            border-left: 4px solid {border_color};
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        ">
            <div style="
                margin: 0 0 12px 0;
                font-weight: 700;
                color: {sender_color};
                font-size: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">
                <span style="font-size: 16px;">{icon}</span>
                <span>{sender}</span>
            </div>
            <div style="
                margin: 0;
                padding-left: 24px;
                line-height: 1.6;
                color: {text_color};
                font-size: 13px;
                word-wrap: break-word;
                font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            ">
                {formatted_text}
            </div>
        </div>
        """