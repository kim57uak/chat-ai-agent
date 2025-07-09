#!/usr/bin/env python3
"""Gemini 모델 테스트"""

import logging
from core.mcp import start_mcp_servers, stop_mcp_servers
from core.ai_agent import AIAgent
from core.file_utils import load_config, load_model_api_key

logging.basicConfig(level=logging.INFO)

def test_gemini():
    """Gemini 모델 테스트"""
    print("=== Gemini 모델 테스트 ===")
    
    # MCP 서버 시작
    print("\n1. MCP 서버 시작...")
    if not start_mcp_servers('mcp.json'):
        print("❌ MCP 서버 시작 실패")
        return
    
    try:
        # 설정 로드
        config = load_config()
        current_model = config.get('current_model', 'gemini-2.5-pro')
        api_key = load_model_api_key(current_model)
        
        print(f"✅ 모델: {current_model}")
        
        if not api_key:
            print("❌ API 키 없음")
            return
        
        # 에이전트 생성
        agent = AIAgent(api_key, current_model)
        print(f"✅ 에이전트 생성 완료 ({len(agent.tools)}개 도구)")
        
        # 테스트 케이스
        test_cases = [
            "안녕하세요!",
            "인사동 맛집 검색해주세요",
            "MySQL 데이터베이스 목록 조회해주세요"
        ]
        
        for i, question in enumerate(test_cases, 1):
            print(f"\n--- 테스트 {i}: {question} ---")
            
            try:
                # 도구 사용 여부 결정
                should_use = agent._should_use_tools(question)
                print(f"도구 사용 결정: {should_use}")
                
                # 응답 생성
                if should_use:
                    response = agent.chat_with_tools(question)
                else:
                    response = agent.simple_chat(question)
                
                print(f"응답: {response[:200]}...")
                print("✅ 성공")
                
            except Exception as e:
                print(f"❌ 오류: {e}")
                # 대체 응답 시도
                try:
                    response = agent.simple_chat(question)
                    print(f"대체 응답: {response[:100]}...")
                except Exception as e2:
                    print(f"대체 응답도 실패: {e2}")
    
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")
    
    finally:
        # 정리
        try:
            stop_mcp_servers()
            print("\n✅ MCP 서버 종료")
        except:
            pass

if __name__ == "__main__":
    test_gemini()