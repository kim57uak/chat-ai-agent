#!/usr/bin/env python3
"""대화 히스토리 기능 테스트"""

from core.conversation_history import ConversationHistory
from core.ai_agent import AIAgent
from core.file_utils import load_model_api_key, load_last_model
import os

def test_conversation_history():
    """대화 히스토리 기본 기능 테스트"""
    print("=== 대화 히스토리 기본 기능 테스트 ===")
    
    # 테스트용 히스토리 파일
    test_file = "test_history.json"
    
    # 기존 테스트 파일 삭제
    if os.path.exists(test_file):
        os.remove(test_file)
    
    # 히스토리 객체 생성
    history = ConversationHistory(test_file)
    
    # 메시지 추가 테스트
    history.add_message("user", "안녕하세요!")
    history.add_message("assistant", "안녕하세요! 무엇을 도와드릴까요?")
    history.add_message("user", "오늘 날씨는 어때요?")
    history.add_message("assistant", "죄송하지만 실시간 날씨 정보는 제공할 수 없습니다.")
    
    print(f"추가된 메시지 수: {len(history.current_session)}")
    
    # 최근 메시지 가져오기
    recent = history.get_recent_messages(2)
    print(f"최근 2개 메시지:")
    for msg in recent:
        print(f"  {msg['role']}: {msg['content']}")
    
    # 파일 저장 테스트
    history.save_to_file()
    print(f"히스토리 파일 저장됨: {test_file}")
    
    # 새 객체로 로드 테스트
    new_history = ConversationHistory(test_file)
    new_history.load_from_file()
    print(f"로드된 메시지 수: {len(new_history.current_session)}")
    
    # 정리
    os.remove(test_file)
    print("테스트 완료!")

def test_ai_agent_with_history():
    """AI 에이전트 대화 히스토리 테스트"""
    print("\n=== AI 에이전트 대화 히스토리 테스트 ===")
    
    # API 키 로드
    model = load_last_model()
    api_key = load_model_api_key(model)
    
    if not api_key:
        print("API 키가 설정되지 않았습니다. config.json을 확인하세요.")
        return
    
    # AI 에이전트 생성
    agent = AIAgent(api_key, model)
    
    # 대화 시뮬레이션
    conversations = [
        "안녕하세요! 저는 김철수입니다.",
        "제 이름을 기억하시나요?",
        "저에 대해 뭘 알고 계신가요?"
    ]
    
    for i, user_input in enumerate(conversations, 1):
        print(f"\n--- 대화 {i} ---")
        print(f"사용자: {user_input}")
        
        response, used_tools = agent.process_message(user_input)
        print(f"AI: {response}")
        print(f"도구 사용: {'예' if used_tools else '아니오'}")
        
        # 히스토리 상태 확인
        history_count = len(agent.conversation_history.current_session)
        print(f"현재 히스토리 메시지 수: {history_count}")

if __name__ == "__main__":
    test_conversation_history()
    test_ai_agent_with_history()