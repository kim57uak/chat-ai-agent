#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from core.mcp import start_mcp_servers, stop_mcp_servers, get_all_mcp_tools

logging.basicConfig(level=logging.INFO)

def test_search_only():
    """검색 기능만 테스트"""
    print("=== 검색 기능 테스트 ===")
    
    # MCP 서버 시작
    print("\n1. MCP 서버 시작...")
    if not start_mcp_servers('mcp.json'):
        print("❌ MCP 서버 시작 실패")
        return
    
    try:
        # 도구 가져오기
        tools = get_all_mcp_tools()
        if tools:
            print(f"✅ {len(tools)}개 도구 로드됨")
        else:
            print("❌ 도구 로드 실패")
            return
        
        # 도구 구조 확인
        try:
            if tools and len(tools) > 0:
                print(f"\n도구 샘플: {str(tools[0])[:100]}...")
            else:
                print("\n도구 샘플: None")
        except Exception as e:
            print(f"\n도구 샘플 오류: {e}")
        
        # 검색 도구 찾기 생략 - 직접 테스트
        print(f"🔍 직접 검색 테스트 시작")
        
        # 직접 MCP 클라이언트로 테스트
        print(f"\n2. 직접 검색 테스트")
        try:
            from core.mcp_client import mcp_manager
            
            # search-mcp-server의 search 도구 직접 호출
            result = mcp_manager.call_tool(
                "search-mcp-server", 
                "search", 
                {"query": "인사동 맛집"}
            )
            if result:
                print(f"✅ 검색 성공!")
                print(f"결과 미리보기: {str(result)[:300]}...")
            else:
                print("❌ 검색 결과 없음")
        except Exception as e:
            print(f"❌ 검색 실패: {e}")
            print("대체 테스트 시도...")
            
            # 대체 테스트: fetchUrl
            try:
                result2 = mcp_manager.call_tool(
                    "search-mcp-server", 
                    "fetchUrl", 
                    {"url": "https://www.naver.com"}
                )
                if result2:
                    print(f"✅ URL 가져오기 성공!")
                else:
                    print("❌ URL 가져오기 결과 없음")
            except Exception as e2:
                print(f"❌ URL 가져오기도 실패: {e2}")
        
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            stop_mcp_servers()
            print("\n✅ MCP 서버 종료")
        except:
            pass

if __name__ == "__main__":
    test_search_only()
