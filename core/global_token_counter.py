"""
from core.logging import get_logger

logger = get_logger("global_token_counter")
전역 토큰 카운터 - 사용자 입력부터 대화 완료까지 모든 토큰 누적
"""

class GlobalTokenCounter:
    def __init__(self):
        self.reset()
        self.user_input_detected = False
    
    def on_user_input(self):
        """사용자 입력 감지 - 토큰 카운터 초기화"""
        self.reset()
        self.user_input_detected = True
        logger.debug(f"GlobalTokenCounter] 사용자 입력 감지 - 토큰 카운터 초기화")
    
    def add_tokens(self, input_tokens, output_tokens):
        """토큰 추가"""
        if self.user_input_detected:
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            logger.debug(f"GlobalTokenCounter] 토큰 추가: +{input_tokens}/{output_tokens} -> 누적: {self.input_tokens}/{self.output_tokens}")
    
    def get_conversation_summary(self):
        """대화 완료 시 토큰 요약"""
        total = self.input_tokens + self.output_tokens
        if total > 0 and self.user_input_detected:
            summary = f"이 대화 토큰: {total:,}개 (입력:{self.input_tokens:,} 출력:{self.output_tokens:,})"
            self.user_input_detected = False  # 표시 후 플래그 리셋
            return summary
        return ""
    
    def reset(self):
        """토큰 카운터 초기화"""
        self.input_tokens = 0
        self.output_tokens = 0

# 전역 인스턴스
global_token_counter = GlobalTokenCounter()