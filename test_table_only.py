#!/usr/bin/env python3
"""
테이블 렌더링만 단독 테스트
"""

import re

def format_table_improved(text):
    """개선된 테이블 포맷팅"""
    # 테이블 패턴 매칭 (더 정확한 감지)
    table_pattern = r'((?:^.*\|.*$\n?)+)'
    
    def format_table_match(match):
        table_text = match.group(1).strip()
        return build_table_improved(table_text)
    
    # 테이블 변환
    text = re.sub(table_pattern, format_table_match, text, flags=re.MULTILINE)
    
    return text

def build_table_improved(table_text):
    """개선된 테이블 HTML 생성"""
    lines = table_text.strip().split('\n')
    if not lines:
        return table_text
    
    # 테이블 라인 필터링
    table_lines = []
    for line in lines:
        line = line.strip()
        if '|' in line and not re.match(r'^\s*\|?\s*[-:]+\s*\|', line):
            table_lines.append(line)
    
    if len(table_lines) < 1:
        return table_text
    
    html = '<table style="border-collapse:collapse;margin:16px 0;background:#2a2a2a;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.3);width:auto;">'
    
    for i, line in enumerate(table_lines):
        # 파이프로 분할
        cells = [cell.strip() for cell in line.split('|')]
        
        # 앞뒤 빈 셀 제거
        while cells and cells[0] == '':
            cells.pop(0)
        while cells and cells[-1] == '':
            cells.pop()
        
        if not cells:
            continue
        
        html += '<tr>'
        
        for cell in cells:
            if i == 0:  # 헤더 행
                html += f'<th style="padding:12px 16px;border:1px solid #444;color:#fff;background:linear-gradient(135deg,#3a3a3a,#4a4a4a);font-weight:700;font-size:13px;text-align:left;">{cell}</th>'
            else:  # 데이터 행
                bg_color = '#252525' if i % 2 == 0 else '#2a2a2a'
                html += f'<td style="padding:10px 16px;border:1px solid #444;color:#ccc;background:{bg_color};vertical-align:top;">{cell}</td>'
        
        html += '</tr>'
    
    html += '</table>'
    return html

# 테스트 데이터
test_table = """| 비교 항목 🏷️ | 비트코인 (Bitcoin, BTC) ₿ | 리플 (Ripple, XRP) 🌊 |
|-------------|---------------------------|----------------------|
| 목적 🎯 | 탈중앙화된 디지털 화폐 | 금융기관용 송금 솔루션 |
| 합의 방식 ⚙️ | 작업증명(PoW) | 합의 알고리즘(Consensus) |"""

print("=== 원본 테이블 ===")
print(test_table)
print("\n=== 변환된 HTML ===")
result = format_table_improved(test_table)
print(result)