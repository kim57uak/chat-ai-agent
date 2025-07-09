#!/usr/bin/env python3
"""빠른 테스트"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from core.mcp import start_mcp_servers
from core.ai_agent import AIAgent
from core.file_utils import load_model_api_key

logging.basicConfig(level=logging.INFO)

def quick_test():
    print("🚀 MCP 서버 시작...")
    start_mcp_servers('mcp.json')
    
    print("🤖 AI 에이전트 생성...")
    api_key = load_model_api_key('gemini-2.5-pro')
    agent = AIAgent(api_key, 'gemini-2.5-pro')
    
    print(f"📋 등록된 도구 수: {len(agent.tools)}")
    search_tools = [tool.name for tool in agent.tools if 'search' in tool.name.lower()]
    print(f"🔍 검색 도구: {search_tools}")
    
    print("\n🔍 검색 테스트...")
    response, used = agent.process_message("낙산사 코인세탁소 검색해줘")
    print(f"응답: {response[:200]}...")
    print(f"도구 사용: {used}")

if __name__ == "__main__":
    quick_test()