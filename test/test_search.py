#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from core.mcp import start_mcp_servers, stop_mcp_servers
from core.ai_agent import AIAgent
from core.file_utils import load_model_api_key

# 로깅 설정
logging.basicConfig(level=logging.WARNING)

def main():
    """검색 기능 테스트"""
    print("🔍 검색 기능 테스트")
    
    # MCP 서버 시작
    print("MCP 서버 시작 중...")
    start_mcp_servers('mcp.json')
    
    try:
        # AI 에이전트 생성
        api_key = load_model_api_key('gemini-2.0-flash-exp')
        agent = AIAgent(api_key, 'gemini-2.0-flash-exp')
        
        print(f"✅ 에이전트 준비 완료 ({len(agent.tools)}개 도구)")
        
        # 검색 테스트
        question = "낙산해수욕장 주변 코인빨래방 검색해줘"
        print(f"\n질문: {question}")
        
        # 도구 사용 여부 확인
        should_use = agent._should_use_tools(question)
        print(f"도구 사용 결정: {should_use}")
        
        # 실제 응답 생성
        try:
            response, used_tools = agent.process_message(question)
            print(f"도구 사용됨: {used_tools}")
            print(f"응답: {response[:500]}...")
        except Exception as e:
            print(f"오류: {e}")
            import traceback
            traceback.print_exc()
    
    finally:
        # 정리
        print("\nMCP 서버 종료 중...")
        stop_mcp_servers()
        print("✅ 테스트 완료")

if __name__ == "__main__":
    main()
