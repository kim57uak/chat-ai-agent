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
            f"Input: {input_tokens:,} tokens ({input_kb:.2f}KB), "
            f"Output: {output_tokens:,} tokens ({output_kb:.2f}KB), "
            f"Total: {total_tokens:,} tokens ({total_kb:.2f}KB)"
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
    
    @staticmethod
    def extract_actual_tokens(response_obj) -> tuple[int, int]:
        """API 응답에서 실제 토큰 사용량 추출"""
        try:
            if not response_obj:
                return 0, 0
            
            # OpenAI 직접 응답 형식
            if hasattr(response_obj, 'usage'):
                usage = response_obj.usage
                return getattr(usage, 'prompt_tokens', 0), getattr(usage, 'completion_tokens', 0)
            
            # Langchain 응답 형식
            if hasattr(response_obj, 'response_metadata'):
                metadata = response_obj.response_metadata
                if 'token_usage' in metadata:
                    token_usage = metadata['token_usage']
                    return token_usage.get('prompt_tokens', 0), token_usage.get('completion_tokens', 0)
                if 'usage_metadata' in metadata:
                    usage_metadata = metadata['usage_metadata']
                    return usage_metadata.get('input_tokens', 0), usage_metadata.get('output_tokens', 0)
            
            # Google Gemini 응답 형식
            if hasattr(response_obj, 'usage_metadata'):
                usage = response_obj.usage_metadata
                return getattr(usage, 'prompt_token_count', 0), getattr(usage, 'candidates_token_count', 0)
            
            # Anthropic Claude 응답 형식
            if hasattr(response_obj, 'usage'):
                usage = response_obj.usage
                return getattr(usage, 'input_tokens', 0), getattr(usage, 'output_tokens', 0)
            
            # Perplexity 응답 형식
            if hasattr(response_obj, 'model_extra') and 'usage' in response_obj.model_extra:
                usage = response_obj.model_extra['usage']
                return usage.get('prompt_tokens', 0), usage.get('completion_tokens', 0)
            
            # 리스트 형태의 응답 (에이전트 응답 등)
            if isinstance(response_obj, list) and response_obj:
                for item in response_obj:
                    input_tokens, output_tokens = TokenLogger.extract_actual_tokens(item)
                    if input_tokens > 0 or output_tokens > 0:
                        return input_tokens, output_tokens
            
            # 딕셔너리 형태의 응답
            if isinstance(response_obj, dict):
                # 직접 토큰 정보가 있는 경우
                if 'usage' in response_obj:
                    usage = response_obj['usage']
                    return usage.get('prompt_tokens', usage.get('input_tokens', 0)), usage.get('completion_tokens', usage.get('output_tokens', 0))
                
                # 중첩된 구조에서 토큰 정보 찾기
                for key, value in response_obj.items():
                    if isinstance(value, dict) and ('tokens' in str(key).lower() or 'usage' in str(key).lower()):
                        input_tokens, output_tokens = TokenLogger.extract_actual_tokens(value)
                        if input_tokens > 0 or output_tokens > 0:
                            return input_tokens, output_tokens
            
            return 0, 0
        except Exception as e:
            logger.debug(f"토큰 추출 실패: {e}")
            return 0, 0
    
    @staticmethod
    def log_actual_token_usage(
        model_name: str,
        response_obj,
        operation: str = "chat"
    ):
        """실제 API 응답에서 토큰 사용량 로깅"""
        input_tokens, output_tokens = TokenLogger.extract_actual_tokens(response_obj)
        
        if input_tokens > 0 or output_tokens > 0:
            total_tokens = input_tokens + output_tokens
            logger.info(
                f"🔢 Actual Token Usage [{model_name}] {operation}: "
                f"Input: {input_tokens:,} tokens, "
                f"Output: {output_tokens:,} tokens, "
                f"Total: {total_tokens:,} tokens"
            )
            return input_tokens, output_tokens
        
        return 0, 0