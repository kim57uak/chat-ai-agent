#!/usr/bin/env python3
"""검색 도구 테스트"""

import logging
from core.mcp import start_mcp_servers, stop_mcp_servers, get_all_mcp_tools
from core.langchain_tools import tool_registry

# 로깅 설정
logging.basicConfig(level=logging.INFO)

def main():
    print("🔍 검색 도구 테스트")
    
    # MCP 서버 시작
    print("MCP 서버 시작 중...")
    start_mcp_servers('mcp.json')
    
    try:
        # MCP 도구 로드 및 등록
        all_mcp_tools = get_all_mcp_tools()
        tools = tool_registry.register_mcp_tools(all_mcp_tools)
        
        # 정확한 search 도구 찾기
        search_tool = None
        for tool in tools:
            if tool.name == 'search-mcp-server_search':
                search_tool = tool
                break
        
        if not search_tool:
            print("❌ search 도구를 찾을 수 없습니다")
            return
        
        print(f"✅ 검색 도구 발견: {search_tool.name}")
        
        # 다양한 방식으로 검색 테스트
        test_cases = [
            {"query": "낙산해변 코인세탁소"},
            {"query": "낙산해변 코인세탁소", "engineName": "Naver"},
            {"query": "낙산해변 코인세탁소", "languageCode": "ko"},
        ]
        
        for i, test_data in enumerate(test_cases, 1):
            print(f"\n=== 테스트 케이스 {i} ===")
            print(f"입력: {test_data}")
            
            try:
                # _run 메서드 테스트
                result = search_tool._run(**test_data)
                print(f"✅ _run 성공: {str(result)[:100]}...")
                
                # invoke 메서드 테스트
                result = search_tool.invoke(test_data)
                print(f"✅ invoke 성공: {str(result)[:100]}...")
                
            except Exception as e:
                print(f"❌ 실패: {e}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    finally:
        print("\nMCP 서버 종료 중...")
        stop_mcp_servers()
        print("✅ 테스트 완료")

if __name__ == "__main__":
    main()