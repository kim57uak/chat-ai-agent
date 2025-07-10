#!/usr/bin/env python3
"""
청크 응답 처리 테스트
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

def test_chunked_response():
    """청크 응답 처리 테스트"""
    print("=== 청크 응답 처리 테스트 ===")
    
    try:
        # MCP 서버 시작
        start_mcp_servers('mcp.json')
        
        # AI 에이전트 생성
        api_key = load_model_api_key('gemini-2.5-flash')
        if not api_key:
            print("API 키를 찾을 수 없습니다.")
            return
            
        agent = AIAgent(api_key, 'gemini-2.5-flash')
        
        # 대용량 응답이 예상되는 쿼리 테스트 (search 도구 사용)
        response, used_tools = agent.process_message("최신 AI 영어,중국어,일본어로 기술 동향에 대해 검색해주세요")
        print(f"응답 길이: {len(response)}자")
        print(f"도구 사용됨: {used_tools}")
        print(f"응답 미리보기: {response[:500]}...")
        
    except Exception as e:
        print(f"테스트 오류: {e}")

if __name__ == "__main__":
    test_chunked_response()
