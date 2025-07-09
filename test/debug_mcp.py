#!/usr/bin/env python3
"""MCP 도구 스키마 디버깅"""

import json
import logging
from core.mcp import start_mcp_servers, get_all_mcp_tools, stop_mcp_servers

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
        # 모든 도구 조회
        all_tools = get_all_mcp_tools()
        
        if not all_tools:
            print("❌ 사용 가능한 도구가 없습니다")
            return
        
        # 각 서버별 도구 정보 출력
        for server_name, tools in all_tools.items():
            print(f"\n📦 서버: {server_name}")
            print(f"   도구 개수: {len(tools)}")
            
            for i, tool in enumerate(tools[:3]):  # 처음 3개만
                print(f"\n🔧 도구 {i+1}: {tool.get('name', 'Unknown')}")
                print(f"   설명: {tool.get('description', 'No description')}")
                
                # 입력 스키마 확인
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
                
                # 전체 스키마 JSON 출력 (첫 번째 도구만)
                if i == 0:
                    print(f"\n   전체 스키마:")
                    print(json.dumps(tool, indent=2, ensure_ascii=False))
    
    finally:
        print("\nMCP 서버 종료...")
        stop_mcp_servers()
        print("✅ 디버깅 완료")

if __name__ == "__main__":
    debug_mcp_tools()