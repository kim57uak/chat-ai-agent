#!/usr/bin/env python3
"""AI 에이전트 테스트"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from core.mcp import start_mcp_servers, stop_mcp_servers
from core.ai_agent import AIAgent
from core.file_utils import load_config, load_model_api_key

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_ai_agent():
    """AI 에이전트 테스트"""
    print("=== AI 에이전트 테스트 ===")
    
    # 1. MCP 서버 시작
    print("\n1. MCP 서버 시작...")
    if not start_mcp_servers('mcp.json'):
        print("❌ MCP 서버 시작 실패")
        return
    
    try:
        # 2. 설정 로드
        config = load_config()
        print(f"✅ 설정 로드 성공")
        
        # 현재 설정된 모델 사용
        current_model = config.get('current_model', 'gemini-2.5-flash')
        api_key = load_model_api_key(current_model)
        print(f"✅ 모델: {current_model}")
        print(f"✅ API 키 확인: {'설정됨' if api_key else '없음'}")
        
        if not api_key:
            print("❌ API 키가 설정되지 않았습니다. config.json을 확인하세요.")
            return
        
        # 3. AI 에이전트 생성
        print("\n3. AI 에이전트 생성...")
        agent = AIAgent(api_key, current_model)
        print(f"✅ 에이전트 생성 완료 ({len(agent.tools)}개 도구 로드됨)")
        
        # 도구 목록 출력
        if agent.tools:
            print("📋 로드된 도구들:")
            for tool in agent.tools[:5]:  # 처음 5개만 표시
                print(f"  - {tool.name}: {tool.description[:50]}...")
            if len(agent.tools) > 5:
                print(f"  ... 외 {len(agent.tools) - 5}개 더")
        else:
            print("⚠️ 로드된 도구가 없습니다")
        
        # 4. 테스트 케이스들
        test_cases = [
            # 일반 대화 (도구 사용 안함)
            ("안녕하세요! 어떻게 지내세요?", False),
            ("태즈메이니아에 대해 설명해주세요", False),
            
            # 도구 사용이 필요한 질문들
            ("낙산해수욕장 동전빨래방 검색해주세요", True),
            ("MySQL 데이터베이스 목록을 조회해주세요", True),
            ("도구 목록을 보여주세요", True),  # 특별 처리
        ]
        
        print("\n3. 테스트 케이스 실행...")
        success_count = 0
        
        for i, (question, expected_tool_use) in enumerate(test_cases, 1):
            print(f"\n--- 테스트 {i}: {question} ---")
            
            # 도구 사용 여부 결정 테스트
            try:
                should_use = agent._should_use_tools(question)
                print(f"도구 사용 결정: {should_use} (예상: {expected_tool_use})")
                
                if should_use == expected_tool_use:
                    print("✅ 결정 로직 정확")
                    success_count += 1
                else:
                    print("⚠️ 결정 로직 불일치")
            except Exception as e:
                print(f"❌ 도구 사용 결정 실패: {e}")
            
            # 실제 응답 생성 (처음 2개만)
            if i <= 2:
                try:
                    response, used_tools = agent.process_message(question)
                    print(f"응답 (도구 사용: {used_tools}): {response[:100]}...")
                    print("✅ 응답 생성 성공")
                except Exception as e:
                    print(f"❌ 응답 생성 실패: {e}")
                    # 오류 발생 시에도 간단한 응답 시도
                    try:
                        simple_response = agent.simple_chat(question)
                        print(f"대체 응답: {simple_response[:100]}...")
                    except Exception as e2:
                        print(f"대체 응답도 실패: {e2}")
        
        print(f"\n📊 테스트 결과: {success_count}/{len(test_cases)} 성공")
    
    finally:
        # 5. 정리
        print("\n4. MCP 서버 종료...")
        try:
            stop_mcp_servers()
            print("✅ MCP 서버 종료 완료")
        except Exception as e:
            print(f"⚠️ MCP 서버 종료 중 오류: {e}")
    
    print("\n🎉 AI 에이전트 테스트 완료!")

if __name__ == "__main__":
    test_ai_agent()
