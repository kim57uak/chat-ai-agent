#!/usr/bin/env python3
"""MCP STDIO 클라이언트 테스트"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from core.mcp import start_mcp_servers, get_all_mcp_tools, call_mcp_tool, stop_mcp_servers

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_mcp_client():
    """MCP 클라이언트 기본 테스트"""
    print("=== MCP STDIO 클라이언트 테스트 ===")
    
    # 1. MCP 서버 시작
    print("\n1. MCP 서버 시작...")
    if start_mcp_servers('mcp.json'):
        print("✅ MCP 서버 시작 성공")
    else:
        print("❌ MCP 서버 시작 실패")
        return
    
    # 2. 도구 목록 조회
    print("\n2. 도구 목록 조회...")
    all_tools = get_all_mcp_tools()
    
    if all_tools:
        print(f"✅ 총 {len(all_tools)}개 서버에서 도구 발견:")
        for server_name, tools in all_tools.items():
            print(f"  📦 {server_name}: {len(tools)}개 도구")
            for tool in tools[:3]:  # 처음 3개만 표시
                print(f"    🔧 {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            if len(tools) > 3:
                print(f"    ... 및 {len(tools) - 3}개 더")
    else:
        print("❌ 사용 가능한 도구가 없습니다")
    
    # 3. 간단한 도구 호출 테스트
    print("\n3. 도구 호출 테스트...")
    
    # search 테스트
    if 'search-mcp-server' in all_tools:
        tools = all_tools['search-mcp-server']
        search_tool = next((t for t in tools if t['name'] == 'search'), None)
        if search_tool:
            print(f"  🔧 search 호출 테스트...")
            try:
                result = call_mcp_tool('search-mcp-server', 'search', {
                    "query": "낙산해수욕장 동전빨래방"
                })
                if result:
                    print(f"  ✅ 호출 성공: {str(result)[:200]}...")
                else:
                    print("  ❌ 호출 실패")
            except Exception as e:
                print(f"  ❌ 호출 오류: {e}")
    
    # MySQL 테스트
    if 'mysql' in all_tools:
        print(f"  🔧 MySQL list_databases 호출 테스트...")
        try:
            result = call_mcp_tool('mysql', 'list_databases')
            if result:
                print(f"  ✅ 호출 성공: {str(result)[:200]}...")
            else:
                print("  ❌ 호출 실패")
        except Exception as e:
            print(f"  ❌ 호출 오류: {e}")
    
    # 4. 정리
    print("\n4. MCP 서버 종료...")
    try:
        stop_mcp_servers()
        print("✅ MCP 서버 종료 완료")
    except Exception as e:
        print(f"⚠️ MCP 서버 종료 중 오류: {e}")
    
    print("🎉 테스트 완료")

if __name__ == "__main__":
    test_mcp_client()