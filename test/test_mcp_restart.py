#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
MCP 서버 재시작 및 연결 테스트
"""

import logging
from core.mcp import start_mcp_servers, get_all_mcp_tools

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mcp_restart():
    """MCP 서버 재시작 테스트"""
    print("=== MCP 서버 재시작 테스트 ===")
    
    try:
        # MCP 서버 시작
        print("MCP 서버 시작 중...")
        start_mcp_servers('mcp.json')
        
        # 도구 목록 확인
        print("도구 목록 조회 중...")
        all_tools = get_all_mcp_tools()
        
        if all_tools:
            print(f"✅ 총 {sum(len(tools) for tools in all_tools.values())}개 도구 로드됨")
            for server_name, tools in all_tools.items():
                print(f"  📦 {server_name}: {len(tools)}개 도구")
        else:
            print("❌ 도구를 찾을 수 없습니다")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_mcp_restart()
