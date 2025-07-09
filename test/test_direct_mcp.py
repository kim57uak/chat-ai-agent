#!/usr/bin/env python3
"""직접 MCP 도구 호출 테스트"""

import logging
from core.mcp import start_mcp_servers, stop_mcp_servers, call_mcp_tool, get_all_mcp_tools
from core.langchain_tools import tool_registry, MCPTool

# 로깅 설정
logging.basicConfig(level=logging.INFO)

def test_langchain_tool():
    """LangChain 도구 래퍼 테스트"""
    print("\n4. LangChain 도구 래퍼 테스트")
    
    # MCP 도구 로드
    all_mcp_tools = get_all_mcp_tools()
    if not all_mcp_tools:
        print("❌ MCP 도구를 찾을 수 없습니다")
        return
    
    # LangChain 도구 등록
    tools = tool_registry.register_mcp_tools(all_mcp_tools)
    print(f"등록된 도구 수: {len(tools)}")
    
    # search 도구 찾기
    search_tool = None
    for tool in tools:
        if 'search' in tool.name.lower() and 'server' in tool.name.lower():
            search_tool = tool
            break
    
    if not search_tool:
        print("❌ 검색 도구를 찾을 수 없습니다")
        return
    
    print(f"검색 도구 발견: {search_tool.name}")
    
    # 다양한 방식으로 도구 호출 테스트
    test_cases = [
        # 케이스 1: kwargs만 사용
        {"query": "낙산해변 코인세탁소"},
        # 케이스 2: run_manager와 함께
        {"query": "낙산해변 코인세탁소", "run_manager": None},
    ]
    
    for i, kwargs in enumerate(test_cases, 1):
        try:
            print(f"\n  테스트 케이스 {i}: {kwargs}")
            result = search_tool._run(**kwargs)
            print(f"  ✅ 성공: {str(result)[:100]}...")
        except Exception as e:
            print(f"  ❌ 실패: {e}")
    
    # 위치 인수 테스트
    try:
        print(f"\n  테스트 케이스 3: 위치 인수 방식")
        result = search_tool._run(None, query="낙산해변 코인세탁소")
        print(f"  ✅ 성공: {str(result)[:100]}...")
    except Exception as e:
        print(f"  ❌ 실패: {e}")

def main():
    """직접 MCP 도구 호출 테스트"""
    print("🔧 직접 MCP 도구 호출 테스트")
    
    # MCP 서버 시작
    print("MCP 서버 시작 중...")
    start_mcp_servers('mcp.json')
    
    try:
        # search 도구 직접 호출
        print("\n1. search 도구 직접 호출 테스트")
        result = call_mcp_tool('search-mcp-server', 'search', {
            'query': '낙산해수욕장 주변 코인빨래방'
        })
        
        if result:
            print("✅ 검색 성공!")
            print(f"결과: {str(result)[:300]}...")
        else:
            print("❌ 검색 실패")
        
        # MySQL 도구 호출
        print("\n2. MySQL list_databases 호출 테스트")
        result = call_mcp_tool('mysql', 'list_databases', {})
        
        if result:
            print("✅ MySQL 호출 성공!")
            print(f"결과: {result}")
        else:
            print("❌ MySQL 호출 실패")
            
        # 빈 arguments로 MySQL 호출
        print("\n3. MySQL list_databases 빈 arguments 호출 테스트")
        result = call_mcp_tool('mysql', 'list_databases', None)
        
        if result:
            print("✅ MySQL 빈 arguments 호출 성공!")
            print(f"결과: {result}")
        else:
            print("❌ MySQL 빈 arguments 호출 실패")
        
        # LangChain 도구 래퍼 테스트
        test_langchain_tool()
    
    finally:
        # 정리
        print("\nMCP 서버 종료 중...")
        stop_mcp_servers()
        print("✅ 테스트 완료")

if __name__ == "__main__":
    main()