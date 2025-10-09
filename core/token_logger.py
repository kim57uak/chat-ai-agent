"""
Token usage logging utility
"""

from core.logging import get_logger
from typing import List, Dict, Any, Optional

logger = get_logger("token_logger")


class TokenLogger:
    """토큰 사용량 로깅 유틸리티"""
    
    @staticmethod
    def estimate_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
        """텍스트의 토큰 수 추정 (통합된 방식)"""
        if not text:
            return 0
        
        try:
            # 모델별 토큰 계산 방식 통일
            # 한글과 영어가 섞인 텍스트를 고려한 정확한 추정
            korean_chars = sum(1 for char in text if ord(char) >= 0xAC00 and ord(char) <= 0xD7A3)
            english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
            other_chars = len(text) - korean_chars - english_chars
            
            # 한글: 1.5문자당 1토큰, 영어: 4문자당 1토큰, 기타: 3문자당 1토큰
            estimated_tokens = int(
                korean_chars / 1.5 + 
                english_chars / 4.0 + 
                other_chars / 3.0
            )
            
            # 최소 토큰 수 보장
            return max(1, estimated_tokens) if text.strip() else 0
            
        except Exception:
            # 폴백: 전체 길이 기반 추정
            return max(1, len(text) // 3) if text.strip() else 0
    
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
        """API 응답에서 실제 토큰 사용량 추출 (통합 버전)"""
        if not response_obj:
            return 0, 0
            
        try:
            # 1. OpenAI 직접 응답 형식
            if hasattr(response_obj, 'usage'):
                usage = response_obj.usage
                input_tokens = getattr(usage, 'prompt_tokens', getattr(usage, 'input_tokens', 0))
                output_tokens = getattr(usage, 'completion_tokens', getattr(usage, 'output_tokens', 0))
                if input_tokens > 0 or output_tokens > 0:
                    return input_tokens, output_tokens
            
            # 2. Langchain 응답 형식
            if hasattr(response_obj, 'response_metadata'):
                metadata = response_obj.response_metadata
                
                # token_usage 필드 확인
                if 'token_usage' in metadata:
                    token_usage = metadata['token_usage']
                    input_tokens = token_usage.get('prompt_tokens', token_usage.get('input_tokens', 0))
                    output_tokens = token_usage.get('completion_tokens', token_usage.get('output_tokens', 0))
                    if input_tokens > 0 or output_tokens > 0:
                        return input_tokens, output_tokens
                
                # usage_metadata 필드 확인
                if 'usage_metadata' in metadata:
                    usage_metadata = metadata['usage_metadata']
                    input_tokens = usage_metadata.get('input_tokens', usage_metadata.get('prompt_tokens', 0))
                    output_tokens = usage_metadata.get('output_tokens', usage_metadata.get('completion_tokens', 0))
                    if input_tokens > 0 or output_tokens > 0:
                        return input_tokens, output_tokens
            
            # 3. Google Gemini 직접 응답 형식
            if hasattr(response_obj, 'usage_metadata'):
                usage = response_obj.usage_metadata
                input_tokens = getattr(usage, 'prompt_token_count', getattr(usage, 'input_tokens', 0))
                output_tokens = getattr(usage, 'candidates_token_count', getattr(usage, 'output_tokens', 0))
                if input_tokens > 0 or output_tokens > 0:
                    return input_tokens, output_tokens
            
            # 4. 리스트 형태의 응답 (에이전트 응답 등)
            if isinstance(response_obj, list) and response_obj:
                total_input = 0
                total_output = 0
                for item in response_obj:
                    input_tokens, output_tokens = TokenLogger.extract_actual_tokens(item)
                    total_input += input_tokens
                    total_output += output_tokens
                if total_input > 0 or total_output > 0:
                    return total_input, total_output
            
            # 5. 딕셔너리 형태의 응답
            if isinstance(response_obj, dict):
                # 직접 usage 필드
                if 'usage' in response_obj:
                    usage = response_obj['usage']
                    input_tokens = usage.get('prompt_tokens', usage.get('input_tokens', 0))
                    output_tokens = usage.get('completion_tokens', usage.get('output_tokens', 0))
                    if input_tokens > 0 or output_tokens > 0:
                        return input_tokens, output_tokens
                
                # 중첩된 구조에서 토큰 정보 찾기
                for key, value in response_obj.items():
                    if isinstance(value, dict):
                        key_lower = str(key).lower()
                        if 'token' in key_lower or 'usage' in key_lower:
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