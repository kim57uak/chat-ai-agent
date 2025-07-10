#!/usr/bin/env python3
"""간단한 검색 테스트"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from core.mcp import start_mcp_servers, stop_mcp_servers

logging.basicConfig(level=logging.INFO)

def simple_search_test():
    """간단한 검색 테스트"""
    print("=== 간단한 검색 테스트 ===")
    
    # MCP 서버 시작
    if not start_mcp_servers('mcp.json'):
        print("❌ MCP 서버 시작 실패")
        return
    
    try:
        from core.mcp_client import mcp_manager
        
        print("\n1. 검색 테스트...")
        result = mcp_manager.call_tool(
            "search-mcp-server", 
            "search", 
            {"query": "인사동 맛집"}
        )
        
        if result:
            print("✅ 검색 성공!")
            print(f"결과 타입: {type(result)}")
            print(f"결과 길이: {len(str(result))}")
            print(f"결과 미리보기: {str(result)[:200]}...")
        else:
            print("❌ 검색 결과 없음")
            
    except Exception as e:
        print(f"❌ 검색 실패: {e}")
        
        # 네이버 페이지 가져오기 테스트
        try:
            print("\n2. 네이버 페이지 가져오기 테스트...")
            result2 = mcp_manager.call_tool(
                "search-mcp-server", 
                "fetchUrl", 
                {"url": "https://www.naver.com"}
            )
            
            if result2:
                print("✅ 페이지 가져오기 성공!")
                print(f"결과 길이: {len(str(result2))}")
            else:
                print("❌ 페이지 가져오기 결과 없음")
                
        except Exception as e2:
            print(f"❌ 페이지 가져오기도 실패: {e2}")
    
    finally:
        try:
            stop_mcp_servers()
            print("\n✅ MCP 서버 종료")
        except:
            pass

if __name__ == "__main__":
    simple_search_test()
