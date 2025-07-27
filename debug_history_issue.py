#!/usr/bin/env python3
"""대화 히스토리 문제 디버깅"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai_agent import AIAgent
from core.conversation_history import ConversationHistory
from core.file_utils import load_model_api_key, load_last_model
from ui.components.ai_processor import AIProcessor
from PyQt6.QtCore import QObject

class MockParent(QObject):
    """테스트용 부모 객체"""
    pass

def test_gui_history_flow():
    """GUI에서 사용하는 방식으로 대화 히스토리 테스트"""
    print("=== GUI 대화 히스토리 플로우 테스트 ===")
    
    # 모델 및 API 키 로드
    model = load_last_model()
    api_key = load_model_api_key(model)
    
    if not api_key:
        print("❌ API 키가 설정되지 않았습니다.")
        return
    
    print(f"✅ 모델: {model}")
    
    # 대화 히스토리 생성 (GUI와 동일한 방식)
    history = ConversationHistory()
    history.clear_session()
    
    # 첫 번째 메시지 추가
    user_msg1 = "안녕하세요, 저는 김병두입니다."
    history.add_message("user", user_msg1)
    
    # AI 응답 시뮬레이션
    ai_response1 = "안녕하세요, 김병두님!"
    history.add_message("assistant", ai_response1)
    
    # 두 번째 메시지 추가
    user_msg2 = "내가 누구지?"
    history.add_message("user", user_msg2)
    
    print(f"\n현재 히스토리 상태:")
    for i, msg in enumerate(history.current_session):
        print(f"  {i+1}. {msg['role']}: {msg['content']}")
    
    # GUI에서 사용하는 방식으로 컨텍스트 메시지 가져오기
    context_messages = history.get_context_messages()
    print(f"\n컨텍스트 메시지 ({len(context_messages)}개):")
    for i, msg in enumerate(context_messages):
        print(f"  {i+1}. {msg['role']}: {msg['content']}")
    
    # AI 에이전트 직접 테스트
    print(f"\n--- AI 에이전트 직접 테스트 ---")
    agent = AIAgent(api_key, model)
    
    # process_message_with_history 메서드 테스트
    response, used_tools = agent.process_message_with_history(user_msg2, context_messages, force_agent=False)
    print(f"AI 응답: {response}")
    print(f"사용된 도구: {used_tools}")
    
    # 결과 분석
    if "김병두" in response or "병두" in response:
        print("✅ 성공: AI가 이름을 기억했습니다!")
    else:
        print("❌ 실패: AI가 이름을 기억하지 못했습니다.")
        
        # 추가 디버깅: simple_chat_with_history 직접 테스트
        print(f"\n--- simple_chat_with_history 직접 테스트 ---")
        simple_response = agent.simple_chat_with_history(user_msg2, context_messages)
        print(f"Simple chat 응답: {simple_response}")
        
        if "김병두" in simple_response or "병두" in simple_response:
            print("✅ simple_chat_with_history는 작동합니다!")
        else:
            print("❌ simple_chat_with_history도 작동하지 않습니다.")

def test_ai_processor_flow():
    """AIProcessor를 통한 테스트"""
    print(f"\n=== AIProcessor 테스트 ===")
    
    model = load_last_model()
    api_key = load_model_api_key(model)
    
    if not api_key:
        print("❌ API 키가 설정되지 않았습니다.")
        return
    
    # 대화 히스토리 준비
    messages = [
        {"role": "user", "content": "안녕하세요, 저는 김병두입니다."},
        {"role": "assistant", "content": "안녕하세요, 김병두님!"}
    ]
    
    print(f"준비된 메시지:")
    for i, msg in enumerate(messages):
        print(f"  {i+1}. {msg['role']}: {msg['content']}")
    
    # AIProcessor 생성 및 테스트
    parent = MockParent()
    processor = AIProcessor(parent)
    
    # 응답 수신을 위한 플래그
    response_received = False
    final_response = ""
    
    def on_finished(sender, text, used_tools):
        nonlocal response_received, final_response
        response_received = True
        final_response = text
        print(f"AIProcessor 응답: {text}")
        
        if "김병두" in text or "병두" in text:
            print("✅ AIProcessor 성공: AI가 이름을 기억했습니다!")
        else:
            print("❌ AIProcessor 실패: AI가 이름을 기억하지 못했습니다.")
    
    def on_error(error_msg):
        nonlocal response_received
        response_received = True
        print(f"AIProcessor 오류: {error_msg}")
    
    # 시그널 연결
    processor.finished.connect(on_finished)
    processor.error.connect(on_error)
    
    # 요청 처리 (Ask 모드)
    user_text = "내가 누구지?"
    print(f"\n사용자 질문: {user_text}")
    processor.process_request(api_key, model, messages, user_text, agent_mode=False)
    
    # 응답 대기 (간단한 폴링)
    import time
    timeout = 30
    elapsed = 0
    while not response_received and elapsed < timeout:
        time.sleep(0.1)
        elapsed += 0.1
    
    if not response_received:
        print("❌ 타임아웃: AIProcessor에서 응답을 받지 못했습니다.")

if __name__ == "__main__":
    test_gui_history_flow()
    test_ai_processor_flow()