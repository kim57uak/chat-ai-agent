"""Table formatter for markdown tables"""

import re
from typing import List


class TableFormatter:
    """Handles markdown table formatting and detection"""
    
    def is_markdown_table(self, text: str) -> bool:
        """마크다운 테이블 정확한 감지 - Claude 응답 최적화"""
        # Claude 한줄 테이블 감지
        if '\n' not in text.strip() and '|' in text and text.count('|') >= 6:
            if any(pattern in text for pattern in ['---', ':--', '--:', '===']):
                print(f"[DEBUG] Claude single-line table detected")
                return True
        
        lines = text.strip().split('\n')
        table_lines = [line for line in lines if '|' in line and line.strip()]
        
        if len(table_lines) < 2:
            return False
        
        # 구분자 패턴 확장
        separator_patterns = ['---', ':--', '--:', '===', '___']
        has_separator = any(pattern in line for line in table_lines for pattern in separator_patterns)
        
        # 유효한 테이블 라인 감지 강화
        valid_table_lines = [line for line in table_lines if line.count('|') >= 2]
        
        # Claude 특화 테이블 감지
        claude_table_indicators = [
            any('코드' in line or 'Header' in line for line in table_lines[:2]),  # 헤더 키워드
            len([line for line in table_lines if line.count('|') >= 3]) >= 2,  # 3열 이상
            has_separator and len(valid_table_lines) >= 2,  # 표준 마크다운
            len(valid_table_lines) >= 4  # 충분한 데이터 행
        ]
        
        return any(claude_table_indicators)
    
    def has_mixed_content(self, text: str) -> bool:
        """테이블과 일반 텍스트가 혼재되어 있는지 확인"""
        # Claude 한줄 테이블 + 메타데이터 감지
        if '|' in text and text.count('|') >= 6 and any(pattern in text for pattern in ['---', ':--', '--:', '===']):
            # 테이블 앞에 일반 텍스트가 있거나 뒤에 메타데이터가 있는지 확인
            table_start = text.find('|')
            has_prefix = table_start > 0 and text[:table_start].strip() and not text[:table_start].strip().startswith('|')
            has_metadata = '*🤖' in text or '수)*' in text  # 메타데이터 감지
            
            if has_prefix or has_metadata:
                print(f"[DEBUG] Mixed content detected: Claude table with metadata")
                return True
        
        has_table = self.is_markdown_table(text)
        has_other_markdown = any([
            text.count('#') > 0,
            text.count('---') > text.count('|---'),
            text.count('- ') > 0 or text.count('* ') > 0,
            text.count('```') > 0,
        ])
        return has_table and has_other_markdown
    
    def format_markdown_table(self, text: str, model_name: str = None) -> str:
        """Format markdown table to HTML"""
        # Claude 모델에만 한줄 테이블 전처리 적용
        if model_name and 'claude' in model_name.lower() and '\n' not in text.strip():
            if '|' in text and text.count('|') >= 6:
                text = self._normalize_claude_table_for_claude(text)
                print(f"[DEBUG] Claude table normalized for model: {model_name}")
        
        # 테이블과 설명 텍스트 분리  
        table_text, description = self._separate_table_and_description(text)
        
        lines = table_text.strip().split('\n')
        table_lines = [line for line in lines if '|' in line and line.strip()]
        
        if len(table_lines) < 2:
            return text
        
        html = '<table style="border-collapse: collapse; width: 100%; margin: 12px 0; background-color: #2a2a2a; border-radius: 6px; overflow: hidden;">'
        
        header_processed = False
        separator_found = False
        
        for line in table_lines:
            # 구분자 라인 감지 및 건너뛰기
            if '---' in line or '===' in line or ':--' in line or '--:' in line:
                separator_found = True
                continue
                
            cells = [cell.strip() for cell in line.split('|')]
            if cells and cells[0] == '':
                cells.pop(0)
            if cells and cells[-1] == '':
                cells.pop()
            if not cells:
                continue
            
            # 헤더 처리 (구분자가 아직 나오지 않았으면 헤더로 처리)
            if not header_processed and not separator_found:
                html += '<thead><tr style="background-color: #3a3a3a;">'
                for cell in cells:
                    formatted_cell = self._format_cell_markdown(cell)
                    html += f'<th style="padding: 12px; border: 1px solid #555; color: #ffffff; font-weight: 600; text-align: left;">{formatted_cell}</th>'
                html += '</tr></thead><tbody>'
                header_processed = True
            else:
                # 데이터 행 처리
                if not header_processed:
                    html += '<tbody>'
                    header_processed = True
                    
                html += '<tr style="background-color: #2a2a2a;">'
                for cell in cells:
                    formatted_cell = self._format_cell_markdown(cell)
                    html += f'<td style="padding: 10px; border: 1px solid #555; color: #cccccc;">{formatted_cell}</td>'
                html += '</tr>'
        
        html += '</tbody></table>'
        
        # 설명 텍스트가 있으면 테이블 아래에 추가
        if description:
            html += f'<div style="margin-top: 12px; color: #cccccc; font-size: 14px; line-height: 1.5;">{description}</div>'
        
        return html
    
    def _format_cell_markdown(self, cell_text: str) -> str:
        """Format markdown within table cells"""
        cell_text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff; font-weight: 600;">\1</strong>', cell_text)
        cell_text = re.sub(r'(?<!\*)\*(.*?)\*(?!\*)', r'<em style="color: #ffffff; font-style: italic;">\1</em>', cell_text)
        cell_text = re.sub(r'~~(.*?)~~', r'<del style="color: #888; text-decoration: line-through;">\1</del>', cell_text)
        cell_text = re.sub(r'`(.*?)`', r'<code style="background-color: #444; padding: 2px 4px; border-radius: 3px; color: #fff;">\1</code>', cell_text)
        cell_text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #87CEEB; text-decoration: none; border-bottom: 1px dotted #87CEEB;" target="_blank">\1</a>', cell_text)
        
        return cell_text
    
    def _format_single_line_table(self, text: str) -> str:
        """Claude 한줄 테이블 포매팅"""
        print(f"[DEBUG] 한줄 테이블 원본: {text[:100]}...")
        
        # 파이프로 분리하여 셀 추출
        parts = text.split('|')
        cells = [part.strip() for part in parts if part.strip()]
        
        if len(cells) < 4:  # 최소 헤더 + 구분자 + 데이터
            return text
        
        # 구분자 찾기 (---, :-- 등)
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
        
        # 데이터를 행별로 그룹화 (헤더 수만큼)
        num_cols = len(headers)
        rows = []
        
        # 데이터 셀이 헤더보다 많은 경우 처리
        if len(data_cells) > num_cols:
            # 전체 데이터를 헤더 수로 나누어 행 생성
            for i in range(0, len(data_cells), num_cols):
                if i + num_cols <= len(data_cells):
                    rows.append(data_cells[i:i + num_cols])
        else:
            # 데이터가 헤더와 같거나 적은 경우 한 행으로 처리
            rows.append(data_cells[:num_cols])
        
        # 디버그 로그 추가
        print(f"[DEBUG] 헤더 개수: {len(headers)}, 데이터 셀 개수: {len(data_cells)}, 생성된 행 수: {len(rows)}")
        print(f"[DEBUG] 헤더: {headers}")
        print(f"[DEBUG] 첫 번째 행: {rows[0] if rows else 'None'}")
        
        if not rows:
            return text
        
        print(f"[DEBUG] 헤더: {headers}, 데이터 행 수: {len(rows)}")
        
        # HTML 테이블 생성
        html = '<table style="border-collapse: collapse; width: 100%; margin: 12px 0; background-color: #2a2a2a; border-radius: 6px; overflow: hidden;">'
        
        # 헤더
        html += '<thead><tr style="background-color: #3a3a3a;">'
        for header in headers:
            formatted_header = self._format_cell_markdown(header)
            html += f'<th style="padding: 12px; border: 1px solid #555; color: #ffffff; font-weight: 600; text-align: left;">{formatted_header}</th>'
        html += '</tr></thead><tbody>'
        
        # 데이터 행
        for row in rows:
            html += '<tr style="background-color: #2a2a2a;">'
            for cell in row:
                formatted_cell = self._format_cell_markdown(cell)
                html += f'<td style="padding: 10px; border: 1px solid #555; color: #cccccc;">{formatted_cell}</td>'
            html += '</tr>'
        
        html += '</tbody></table>'
        print(f"[DEBUG] HTML 테이블 생성 완료")
        return html
    
    def _normalize_claude_table_for_claude(self, text: str) -> str:
        """클로드 전용 테이블 정규화"""
        # 이미 다중라인이면 그대로 반환
        if '\n' in text and len([line for line in text.split('\n') if '|' in line]) >= 3:
            return text
            
        # 한줄 테이블인지 확인
        if '\n' in text.strip():
            return text
            
        # 테이블 부분 추출
        table_start = text.find('|')
        if table_start == -1:
            return text
            
        table_part = text[table_start:]
        if '※' in table_part:
            table_part = table_part[:table_part.find('※')]
            
        # 구분자 찾기 및 분리
        parts = table_part.split('|')
        cells = [p.strip() for p in parts if p.strip()]
        
        # 구분자 인덱스 찾기 (모든 구분자 셀 제거)
        headers = []
        data_cells = []
        
        i = 0
        # 헤더 수집
        while i < len(cells) and '---' not in cells[i]:
            headers.append(cells[i])
            i += 1
            
        # 구분자 건너뛰기
        while i < len(cells) and '---' in cells[i]:
            i += 1
            
        # 데이터 수집
        while i < len(cells):
            data_cells.append(cells[i])
            i += 1
        
        if not headers or not data_cells or len(data_cells) < len(headers):
            return text
            
        # 다중라인 테이블 생성
        lines = ['| ' + ' | '.join(headers) + ' |']
        lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        
        # 데이터 행 추가 (순서 유지)
        num_cols = len(headers)
        for i in range(0, len(data_cells), num_cols):
            if i + num_cols <= len(data_cells):
                row = data_cells[i:i + num_cols]
                lines.append('| ' + ' | '.join(row) + ' |')
                
        return '\n'.join(lines)
    
    def _separate_table_and_description(self, text: str) -> tuple:
        """테이블과 설명 텍스트를 구조적으로 분리"""
        lines = text.strip().split('\n')
        table_lines = []
        description_lines = []
        
        table_ended = False
        consecutive_non_table_lines = 0
        
        for line in lines:
            line = line.strip()
            
            if '|' in line and not table_ended:
                # 테이블 라인
                table_lines.append(line)
                consecutive_non_table_lines = 0
            elif line and not line.startswith('*') and not line.startswith('#'):
                # 비테이블 라인
                consecutive_non_table_lines += 1
                
                # 연속된 비테이블 라인이 2개 이상이면 테이블 종료로 판단
                if consecutive_non_table_lines >= 2 or len(line) > 50:
                    table_ended = True
                    description_lines.append(line)
                elif not table_ended:
                    # 짧은 비테이블 라인은 테이블에 포함 가능
                    table_lines.append(line)
            elif table_ended and line:
                description_lines.append(line)
        
        table_text = '\n'.join(table_lines)
        description_text = ' '.join(description_lines)
        
        return table_text, description_text