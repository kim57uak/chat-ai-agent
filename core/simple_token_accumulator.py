"""
간단한 토큰 누적기 - 하나의 대화에서 사용한 모든 토큰을 누적
"""
from core.logging import get_logger

logger = get_logger('token.accumulator')

class SimpleTokenAccumulator:
    """대화 단위 토큰 누적기"""
    
    def __init__(self):
        self.reset()
        self.conversation_active = False
    
    def start_conversation(self):
        """대화 시작 (사용자 입력 시에만 초기화)"""
        logger.debug(f"start_conversation called: active={self.conversation_active}")
        if not self.conversation_active:
            self.input_tokens = 0
            self.output_tokens = 0
            self.conversation_active = True
            logger.debug("Conversation started - accumulator initialized")
        else:
            logger.debug("Conversation already active - continuing accumulation")
    
    def reset(self):
        """토큰 누적기 초기화"""
        self.input_tokens = 0
        self.output_tokens = 0
        self.conversation_active = False
        logger.debug("Token accumulator reset")
    
    def add(self, input_tokens: int, output_tokens: int):
        """토큰 추가 (대화 중에만)"""
        logger.debug(f"add called: active={self.conversation_active}, +{input_tokens}/{output_tokens}")
        if self.conversation_active:
            old_total = self.input_tokens + self.output_tokens
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            new_total = self.input_tokens + self.output_tokens
            logger.debug(f"Tokens accumulated: {old_total} -> {new_total} (+{input_tokens + output_tokens})")
        else:
            logger.debug("Conversation inactive - token addition ignored")
    
    def get_total(self):
        """누적된 토큰 반환"""
        return self.input_tokens, self.output_tokens, self.input_tokens + self.output_tokens
    
    def get_display_html(self):
        """표시용 HTML 반환"""
        total = self.input_tokens + self.output_tokens
        if total == 0:
            return ""
        
        return f"""
        <div style="
            background: linear-gradient(135deg, rgba(25, 118, 210, 0.15), rgba(25, 118, 210, 0.05));
            border: 2px solid rgba(25, 118, 210, 0.4);
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            font-size: 13px;
            color: #87CEEB;
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            box-shadow: 0 2px 8px rgba(25, 118, 210, 0.1);
        ">
            📊 <strong>이 대화에서 사용한 토큰</strong><br>
            <div style="margin-top: 8px; font-size: 14px; font-weight: 600;">
                🔹 입력: <span style="color: #90EE90;">{self.input_tokens:,}개</span> | 
                출력: <span style="color: #FFB6C1;">{self.output_tokens:,}개</span> | 
                총합: <span style="color: #87CEEB; font-weight: 700;">{total:,}개</span>
            </div>
        </div>
        """
    
    def end_conversation(self):
        """대화 종료 (초기화하지 않음)"""
        logger.debug(f"end_conversation called: active={self.conversation_active}, tokens={self.get_total()}")
        if self.conversation_active:
            self.conversation_active = False
            total = self.get_total()
            logger.debug(f"Conversation ended - final tokens: {total}")
            return True
        logger.debug("Conversation inactive - end ignored")
        return False
    
    def should_display(self):
        """토큰 정보를 표시할지 여부 결정"""
        return (self.input_tokens + self.output_tokens) > 0 and not self.conversation_active

# 전역 인스턴스
token_accumulator = SimpleTokenAccumulator()