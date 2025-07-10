#!/usr/bin/env python3
"""
날짜 및 지역 코드 수정 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai_agent import AIAgent
from datetime import datetime

def test_date_helper():
    """날짜 헬퍼 함수 테스트"""
    print("=== 날짜 헬퍼 함수 테스트 ===")
    
    # 임시 에이전트 생성 (API 키 없이)
    agent = AIAgent("dummy", "gpt-3.5-turbo")
    
    # 다양한 입력 테스트
    test_inputs = [
        "2025년 8월 동남아 여행",
        "2024년 12월 유럽 여행", 
        "내년 1월 일본 여행",
        "동남아 여행 상품"
    ]
    
    for user_input in test_inputs:
        start_date, end_date = agent._get_realistic_date_range(user_input)
        area_code = agent._get_area_code(user_input)
        print(f"입력: {user_input}")
        print(f"  -> 시작일: {start_date}, 종료일: {end_date}, 지역: {area_code}")
        print()

if __name__ == "__main__":
    test_date_helper()
