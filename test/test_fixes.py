#!/usr/bin/env python3
"""
수정사항 테스트 스크립트
1. 도구 목록 동적 생성 테스트
2. 날짜 파라미터 타입 변환 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai_agent import AIAgent
from core.mcp import start_mcp_servers
from core.file_utils import load_model_api_key
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tool_list():
    """도구 목록 동적 생성 테스트"""
    print("=== 도구 목록 테스트 ===")
    
    try:
        # MCP 서버 시작
        start_mcp_servers('mcp.json')
        
        # AI 에이전트 생성
        api_key = load_model_api_key('gemini-pro')
        if not api_key:
            print("API 키를 찾을 수 없습니다.")
            return
            
        agent = AIAgent(api_key, 'gemini-pro')
        
        # 도구 목록 요청
        response, used_tools = agent.process_message("사용 가능한 도구 목록을 보여주세요")
        print(f"응답: {response}")
        print(f"도구 사용됨: {used_tools}")
        
    except Exception as e:
        print(f"테스트 오류: {e}")

def test_date_conversion():
    """날짜 파라미터 변환 테스트"""
    print("\n=== 날짜 파라미터 변환 테스트 ===")
    
    try:
        # MCP 서버 시작
        start_mcp_servers('mcp.json')
        
        # AI 에이전트 생성
        api_key = load_model_api_key('gemini-2.5-flash')
        if not api_key:
            print("API 키를 찾을 수 없습니다.")
            return
            
        agent = AIAgent(api_key, 'gemini-2.5-flash')
        
        # 하나투어 상품 검색 (날짜 파라미터 포함)
        response, used_tools = agent.process_message("2025년 1월 동남아 여행 상품을 찾아주세요")
        print(f"응답: {response}")
        print(f"도구 사용됨: {used_tools}")
        
    except Exception as e:
        print(f"테스트 오류: {e}")

if __name__ == "__main__":
    test_tool_list()
    test_date_conversion()