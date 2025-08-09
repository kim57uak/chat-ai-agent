"""
Token usage logging utility
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class TokenLogger:
    """토큰 사용량 로깅 유틸리티"""
    
    @staticmethod
    def estimate_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
        """텍스트의 토큰 수 추정 (간단한 방식)"""
        try:
            # 간단한 토큰 추정: 1토큰 ≈ 4문자 (영어 기준)
            # 한글의 경우 더 적은 문자 수로 토큰이 구성됨
            if any(ord(char) > 127 for char in text):  # 한글/특수문자 포함
                return len(text) // 2  # 한글은 대략 2문자당 1토큰
            else:
                return len(text) // 4  # 영어는 대략 4문자당 1토큰
        except Exception:
            return len(text) // 3  # 기본 추정
    
    @staticmethod
    def tokens_to_kb(tokens: int) -> float:
        """토큰을 KB로 변환 (대략적)"""
        # 1토큰 ≈ 4바이트로 추정
        return (tokens * 4) / 1024
    
    @staticmethod
    def log_token_usage(
        model_name: str,
        input_text: str,
        output_text: str,
        operation: str = "chat"
    ):
        """토큰 사용량 로깅"""
        input_tokens = TokenLogger.estimate_tokens(input_text, model_name)
        output_tokens = TokenLogger.estimate_tokens(output_text, model_name)
        total_tokens = input_tokens + output_tokens
        
        input_kb = TokenLogger.tokens_to_kb(input_tokens)
        output_kb = TokenLogger.tokens_to_kb(output_tokens)
        total_kb = TokenLogger.tokens_to_kb(total_tokens)
        
        logger.info(
            f"🔢 Token Usage [{model_name}] {operation}: "
            f"Input: {input_tokens} tokens ({input_kb:.2f}KB), "
            f"Output: {output_tokens} tokens ({output_kb:.2f}KB), "
            f"Total: {total_tokens} tokens ({total_kb:.2f}KB)"
        )
    
    @staticmethod
    def log_messages_token_usage(
        model_name: str,
        messages: List[Any],
        output_text: str,
        operation: str = "chat"
    ):
        """메시지 리스트의 토큰 사용량 로깅"""
        input_text = ""
        for msg in messages:
            if hasattr(msg, 'content'):
                if isinstance(msg.content, str):
                    input_text += msg.content + "\n"
                elif isinstance(msg.content, list):
                    for item in msg.content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            input_text += item.get('text', '') + "\n"
        
        TokenLogger.log_token_usage(model_name, input_text, output_text, operation)