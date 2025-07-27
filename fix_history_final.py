#!/usr/bin/env python3
"""대화 히스토리 문제 최종 수정"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fix_chat_widget():
    """ChatWidget의 대화 히스토리 처리 방식을 수정"""
    
    # ChatWidget 파일 읽기
    chat_widget_path = "ui/chat_widget.py"
    
    with open(chat_widget_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # _process_new_message 메서드에서 히스토리 추가 순서 수정
    old_pattern = """        self.chat_display.append_message('사용자', user_text)
        self.input_text.clear()
        
        # 히스토리에 추가
        self.conversation_history.add_message('user', user_text)
        self.conversation_history.save_to_file()
        self.messages.append({'role': 'user', 'content': user_text})"""
    
    new_pattern = """        self.chat_display.append_message('사용자', user_text)
        self.input_text.clear()
        
        # 히스토리에 추가 (AI 요청 전에 추가하지 않음 - 응답 받은 후에 추가)
        # self.conversation_history.add_message('user', user_text)
        # self.conversation_history.save_to_file()
        self.messages.append({'role': 'user', 'content': user_text})"""
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("✅ _process_new_message 메서드 수정 완료")
    else:
        print("❌ _process_new_message 패턴을 찾을 수 없습니다")
    
    # on_ai_response 메서드에서 히스토리 추가 방식 수정
    old_response_pattern = """        # 히스토리 저장
        self.conversation_history.add_message('assistant', text)
        self.conversation_history.save_to_file()
        self.messages.append({'role': 'assistant', 'content': text})"""
    
    new_response_pattern = """        # 히스토리 저장 (사용자 메시지와 AI 응답을 함께 저장)
        # 마지막 사용자 메시지 추가 (아직 추가되지 않았다면)
        if self.messages and self.messages[-1]['role'] == 'user':
            last_user_msg = self.messages[-1]['content']
            self.conversation_history.add_message('user', last_user_msg)
        
        self.conversation_history.add_message('assistant', text)
        self.conversation_history.save_to_file()
        self.messages.append({'role': 'assistant', 'content': text})"""
    
    if old_response_pattern in content:
        content = content.replace(old_response_pattern, new_response_pattern)
        print("✅ on_ai_response 메서드 수정 완료")
    else:
        print("❌ on_ai_response 패턴을 찾을 수 없습니다")
    
    # 파일 저장
    with open(chat_widget_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {chat_widget_path} 파일 수정 완료")

def create_simple_test():
    """간단한 테스트 파일 생성"""
    
    test_content = '''#!/usr/bin/env python3
"""대화 히스토리 수정 후 테스트"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai_agent import AIAgent
from core.conversation_history import ConversationHistory
from core.file_utils import load_model_api_key, load_last_model

def test_fixed_history():
    """수정된 대화 히스토리 테스트"""
    print("=== 수정된 대화 히스토리 테스트 ===")
    
    # 모델 및 API 키 로드
    model = load_last_model()
    api_key = load_model_api_key(model)
    
    if not api_key:
        print("❌ API 키가 설정되지 않았습니다.")
        return
    
    print(f"✅ 모델: {model}")
    
    # AI 에이전트 생성
    agent = AIAgent(api_key, model)
    
    # 대화 히스토리 시뮬레이션 (GUI와 동일한 방식)
    history = ConversationHistory()
    history.clear_session()
    
    # 첫 번째 대화
    print("\\n--- 첫 번째 대화 ---")
    user_msg1 = "안녕하세요, 저는 이철수입니다."
    print(f"사용자: {user_msg1}")
    
    # AI 응답 (히스토리 없이)
    response1, _ = agent.process_message(user_msg1)
    print(f"AI: {response1}")
    
    # 히스토리에 추가 (GUI의 on_ai_response와 동일)
    history.add_message("user", user_msg1)
    history.add_message("assistant", response1)
    
    # 두 번째 대화
    print("\\n--- 두 번째 대화 ---")
    user_msg2 = "내가 누구인지 기억하시나요?"
    print(f"사용자: {user_msg2}")
    
    # 이전 대화 히스토리 가져오기
    context_messages = history.get_context_messages()
    print(f"\\n전달되는 컨텍스트 ({len(context_messages)}개):")
    for i, msg in enumerate(context_messages):
        print(f"  {i+1}. {msg['role']}: {msg['content'][:50]}...")
    
    # AI 응답 (히스토리 포함)
    response2, _ = agent.process_message_with_history(user_msg2, context_messages)
    print(f"\\nAI: {response2}")
    
    # 결과 분석
    if "이철수" in response2 or "철수" in response2:
        print("\\n✅ 성공: AI가 이전 대화에서 언급된 이름을 기억했습니다!")
    else:
        print("\\n❌ 실패: AI가 이전 대화 내용을 기억하지 못했습니다.")

if __name__ == "__main__":
    test_fixed_history()
'''
    
    with open("test_fixed_history.py", 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("✅ test_fixed_history.py 파일 생성 완료")

if __name__ == "__main__":
    print("대화 히스토리 문제 최종 수정 시작...")
    fix_chat_widget()
    create_simple_test()
    print("\\n수정 완료! 다음 명령으로 테스트하세요:")
    print("python test_fixed_history.py")