#!/usr/bin/env python3
"""AI 에이전트 도구 테스트"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from core.mcp import start_mcp_servers
from core.ai_agent import AIAgent
from core.file_utils import load_model_api_key

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_tools():
    """AI 에이전트 도구 테스트"""
    
    # MCP 서버 시작
    print("🚀 MCP 서버 시작...")
    if not start_mcp_servers('mcp.json'):
        print("❌ MCP 서버 시작 실패")
        return
    
    # AI 에이전트 생성
    print("🤖 AI 에이전트 생성...")
    try:
        api_key = load_model_api_key('gpt-3.5-turbo')
        if not api_key:
            print("❌ API 키를 찾을 수 없습니다")
            return
        
        agent = AIAgent(api_key, 'gpt-3.5-turbo')
        
        # 등록된 도구 확인
        print(f"\n📋 AI 에이전트에 등록된 도구 수: {len(agent.tools)}")
        
        search_tools = []
        for tool in agent.tools:
            print(f"  🔧 {tool.name}: {tool.description[:60]}...")
            if 'search' in tool.name.lower():
                search_tools.append(tool.name)
        
        print(f"\n🔍 검색 관련 도구: {search_tools}")
        
        # 도구 사용 여부 테스트
        test_queries = [
            "낙산사 코인세탁소 검색해줘",
            "search for something",
            "웹 검색해줘"
        ]
        
        for query in test_queries:
            should_use = agent._should_use_tools(query)
            print(f"\n📝 '{query}'")
            print(f"   도구 사용: {should_use}")
        
        # 실제 검색 테스트
        print("\n🔍 실제 검색 테스트...")
        if search_tools:
            print(f"사용 가능한 검색 도구: {search_tools}")
        
        response, used_tools = agent.process_message("낙산사 코인세탁소를 웹에서 검색해줘")
        print(f"\n응답: {response}")
        print(f"도구 사용됨: {used_tools}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_tools()
