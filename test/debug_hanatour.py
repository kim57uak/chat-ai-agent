#!/usr/bin/env python3
"""
하나투어 API 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai_agent import AIAgent
from core.mcp import start_mcp_servers
from core.file_utils import load_model_api_key
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_area_codes():
    """지역 코드 확인"""
    print("=== 지역 코드 확인 ===")
    
    try:
        # MCP 서버 시작
        start_mcp_servers('mcp.json')
        
        # AI 에이전트 생성
        api_key = load_model_api_key('gemini-2.5-pro')
        if not api_key:
            print("API 키를 찾을 수 없습니다.")
            return
            
        agent = AIAgent(api_key, 'gemini-2.5-pro')
        
        # 지역 코드 조회
        response, used_tools = agent.process_message("하나투어에서 사용 가능한 지역 코드를 모두 보여주세요")
        print(f"응답: {response}")
        
    except Exception as e:
        print(f"테스트 오류: {e}")

def test_recent_dates():
    """최근 날짜로 테스트"""
    print("\n=== 최근 날짜 테스트 ===")
    
    try:
        # MCP 서버 시작
        start_mcp_servers('mcp.json')
        
        # AI 에이전트 생성
        api_key = load_model_api_key('gemini-2.5-pro')
        if not api_key:
            print("API 키를 찾을 수 없습니다.")
            return
            
        agent = AIAgent(api_key, 'gemini-2.5-pro')
        
        # 2024년 12월로 테스트 (더 가까운 날짜)
        response, used_tools = agent.process_message("2024년 12월 동남아 여행 상품을 찾아주세요")
        print(f"응답: {response}")
        
    except Exception as e:
        print(f"테스트 오류: {e}")

def test_different_areas():
    """다른 지역으로 테스트"""
    print("\n=== 다른 지역 테스트 ===")
    
    try:
        # MCP 서버 시작
        start_mcp_servers('mcp.json')
        
        # AI 에이전트 생성
        api_key = load_model_api_key('gemini-2.5-pro')
        if not api_key:
            print("API 키를 찾을 수 없습니다.")
            return
            
        agent = AIAgent(api_key, 'gemini-2.5-pro')
        
        # 유럽 여행으로 테스트
        response, used_tools = agent.process_message("2024년 12월 유럽 여행 상품을 찾아주세요")
        print(f"응답: {response}")
        
    except Exception as e:
        print(f"테스트 오류: {e}")

if __name__ == "__main__":
    test_area_codes()
    test_recent_dates()
    test_different_areas()
