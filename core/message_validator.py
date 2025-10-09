"""
Message format validator for Perplexity API compliance
"""

from core.logging import get_logger

_logger = get_logger("message_validator")


class MessageValidator:
    """Validates and fixes message format for Perplexity API"""
    
    logger = _logger
    
    @staticmethod
    def validate_and_fix_messages(messages):
        """
        Validates and fixes message format to comply with Perplexity API rules:
        - system message (optional, only at the beginning)
        - user and assistant messages must alternate
        """
        if not messages:
            return messages
            
        MessageValidator.logger.debug(f"MessageValidator] 검증 시작 - 원본 메시지 수: {len(messages)}")
        
        # 간단한 해결책: user-assistant 패턴만 유지
        fixed_messages = []
        
        # 시스템 메시지 처리
        system_msg = None
        for msg in messages:
            if msg.get('role') == 'system':
                system_msg = msg
                break
        
        if system_msg:
            fixed_messages.append(system_msg)
        
        # user와 assistant 메시지만 추출
        user_assistant_msgs = []
        for msg in messages:
            role = msg.get('role')
            if role in ['user', 'assistant']:
                user_assistant_msgs.append(msg)
        
        # user로 시작하도록 보장
        if user_assistant_msgs and user_assistant_msgs[0].get('role') == 'assistant':
            MessageValidator.logger.debug(f"MessageValidator] 첫 메시지가 assistant, user 더미 삽입")
            dummy_user = {'role': 'user', 'content': 'Hello'}
            fixed_messages.append(dummy_user)
        
        # 교대 패턴 유지
        last_role = 'system' if system_msg else None
        for msg in user_assistant_msgs:
            current_role = msg.get('role')
            
            if current_role == last_role:
                if current_role == 'user':
                    fixed_messages.append({'role': 'assistant', 'content': 'I understand.'})
                    MessageValidator.logger.debug(f"MessageValidator] 더미 assistant 삽입")
                elif current_role == 'assistant':
                    # 이전 assistant 메시지와 병합
                    if fixed_messages and fixed_messages[-1]['role'] == 'assistant':
                        fixed_messages[-1]['content'] += '\n' + msg.get('content', '')
                        continue
            
            fixed_messages.append(msg)
            last_role = current_role
        
        MessageValidator.logger.debug(f"MessageValidator] 검증 완료 - 수정된 메시지 수: {len(fixed_messages)}")
        return fixed_messages
    
    @staticmethod
    def ensure_alternating_pattern(messages):
        """Ensure messages follow user->assistant->user pattern"""
        # 이미 validate_and_fix_messages에서 처리되므로 그대로 반환
        return messages
