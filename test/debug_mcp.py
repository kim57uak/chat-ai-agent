#!/usr/bin/env python3
"""MCP 도구 스키마 디버깅"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
from core.mcp import start_mcp_servers, get_all_mcp_tools, stop_mcp_servers
from core.mcp_client import mcp_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO)

def debug_mcp_tools():
    """MCP 도구 스키마 확인"""
    print("=== MCP 도구 스키마 디버깅 ===")
    
    # MCP 서버 시작
    print("MCP 서버 시작...")
    if not start_mcp_servers('mcp.json'):
        print("❌ MCP 서버 시작 실패")
        return
    
    try:
        # 모든 도구 조회 (서버별로 직접 list_tools 호출)
        for server_name, client in mcp_manager.clients.items():
            # 서버 이름에 'excel'이 포함된 경우에만 정보 출력
            if "excel" in server_name.lower():
                print(f"\n📦 서버: {server_name}")
                try:
                    # tools/list 응답 직접 확인
                    import time
                    start = time.time()
                    tools = client.list_tools()
                    elapsed = time.time() - start
                    print(f"   도구 개수: {len(tools)} (조회 시간: {elapsed:.2f}s)")
                    if not tools:
                        print("   (도구 없음)")
                    for i, tool in enumerate(tools):
                        print(f"\n🔧 도구 {i+1}: {tool.get('name', 'Unknown')}")
                        print(f"   설명: {tool.get('description', 'No description')}")
                        input_schema = tool.get('inputSchema', {})
                        if input_schema:
                            print(f"   입력 스키마:")
                            print(f"     타입: {input_schema.get('type', 'unknown')}")
                            properties = input_schema.get('properties', {})
                            if properties:
                                print(f"     속성들:")
                                for prop_name, prop_info in properties.items():
                                    prop_type = prop_info.get('type', 'unknown')
                                    required = prop_name in input_schema.get('required', [])
                                    print(f"       - {prop_name}: {prop_type} {'(필수)' if required else '(선택)'}")
                            else:
                                print(f"     속성: 없음")
                        else:
                            print(f"   입력 스키마: 없음")
                        print(f"\n   전체 스키마:")
                        import json
                        print(json.dumps(tool, indent=2, ensure_ascii=False))
                except Exception as e:
                    print(f"   [오류] tools/list 실패: {e}")
    finally:
        print("\nMCP 서버 종료...")
        stop_mcp_servers()
        print("✅ 디버깅 완료")

if __name__ == "__main__":
    debug_mcp_tools()