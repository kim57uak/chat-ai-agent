"""
세션 토큰 관리 시스템 - 대화별 토큰 누적 및 표시
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
import time
from collections import defaultdict
from core.logging import get_logger

logger = get_logger('token.session')


@dataclass
class ConversationTokens:
    """대화별 토큰 정보"""
    conversation_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class SessionTokenManager:
    """세션 토큰 관리자 - 대화별 토큰 누적 및 표시"""
    
    def __init__(self):
        # 현재 진행 중인 대화의 토큰 누적 저장소
        self.current_conversation_input: int = 0
        self.current_conversation_output: int = 0
        self.current_conversation_id: Optional[str] = None
        
        # 완료된 대화들의 토큰 정보
        self.completed_conversations: Dict[str, ConversationTokens] = {}
        
        # 세션 전체 누적 토큰
        self.session_total_input: int = 0
        self.session_total_output: int = 0
    
    def start_conversation(self, conversation_id: str):
        """새로운 대화 시작"""
        # 이전 대화가 있다면 완료 처리
        if self.current_conversation_id and (self.current_conversation_input > 0 or self.current_conversation_output > 0):
            self._complete_current_conversation()
        
        self.current_conversation_id = conversation_id
        self.current_conversation_input = 0
        self.current_conversation_output = 0
        logger.debug(f"New conversation started: {conversation_id}")
    
    def add_tokens(self, input_tokens: int, output_tokens: int):
        """현재 대화에 토큰 추가 (임시 저장소에 누적)"""
        if input_tokens > 0 or output_tokens > 0:
            self.current_conversation_input += input_tokens
            self.current_conversation_output += output_tokens
            logger.debug(f"Tokens added: IN+{input_tokens}, OUT+{output_tokens} -> Total: IN{self.current_conversation_input}, OUT{self.current_conversation_output}")
    
    def complete_conversation(self) -> Optional[ConversationTokens]:
        """현재 대화 완료 및 토큰 정보 반환"""
        if not self.current_conversation_id:
            return None
        
        return self._complete_current_conversation()
    
    def _complete_current_conversation(self) -> Optional[ConversationTokens]:
        """현재 대화 완료 처리"""
        if not self.current_conversation_id:
            return None
        
        # 누적된 토큰 사용
        total_input = self.current_conversation_input
        total_output = self.current_conversation_output
        
        # 대화 토큰 정보 생성
        conversation_tokens = ConversationTokens(
            conversation_id=self.current_conversation_id,
            input_tokens=total_input,
            output_tokens=total_output,
            end_time=time.time()
        )
        
        # 완료된 대화에 추가
        self.completed_conversations[self.current_conversation_id] = conversation_tokens
        
        # 세션 전체 토큰에 누적
        self.session_total_input += total_input
        self.session_total_output += total_output
        
        logger.info(f"Conversation completed: {self.current_conversation_id}, Tokens: IN{total_input}, OUT{total_output}, TOTAL{total_input + total_output}")
        
        # 현재 대화 정보 초기화
        self.current_conversation_input = 0
        self.current_conversation_output = 0
        self.current_conversation_id = None
        
        return conversation_tokens
    
    def get_current_conversation_tokens(self) -> Tuple[int, int, int]:
        """현재 진행 중인 대화의 토큰 정보 반환 (input, output, total)"""
        return self.current_conversation_input, self.current_conversation_output, self.current_conversation_input + self.current_conversation_output
    
    def get_session_total_tokens(self) -> Tuple[int, int, int]:
        """세션 전체 토큰 정보 반환 (input, output, total)"""
        # 완료된 대화들의 토큰 + 현재 진행 중인 대화의 토큰
        current_input, current_output, _ = self.get_current_conversation_tokens()
        
        total_input = self.session_total_input + current_input
        total_output = self.session_total_output + current_output
        
        return total_input, total_output, total_input + total_output
    
    def get_conversation_token_display(self, conversation_tokens: ConversationTokens) -> str:
        """대화 완료 시 표시할 토큰 정보 HTML 생성"""
        duration = ""
        if conversation_tokens.end_time:
            duration_sec = conversation_tokens.end_time - conversation_tokens.start_time
            if duration_sec < 60:
                duration = f" | ⏱️ {duration_sec:.1f}초"
            else:
                duration = f" | ⏱️ {duration_sec//60:.0f}분 {duration_sec%60:.1f}초"
        
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
            📊 <strong>대화 토큰 사용량</strong><br>
            <div style="margin-top: 8px; font-size: 14px; font-weight: 600;">
                🔹 입력: <span style="color: #90EE90;">{conversation_tokens.input_tokens:,}개</span> | 
                출력: <span style="color: #FFB6C1;">{conversation_tokens.output_tokens:,}개</span> | 
                총합: <span style="color: #87CEEB; font-weight: 700;">{conversation_tokens.total_tokens:,}개</span>{duration}
            </div>
        </div>
        """
    
    def get_session_token_display(self) -> str:
        """세션 전체 토큰 정보 HTML 생성"""
        total_input, total_output, total_tokens = self.get_session_total_tokens()
        
        if total_tokens == 0:
            return ""
        
        return f"""
        <div style="
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.15), rgba(76, 175, 80, 0.05));
            border: 2px solid rgba(76, 175, 80, 0.4);
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            font-size: 13px;
            color: #90EE90;
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.1);
        ">
            🏆 <strong>세션 누적 토큰</strong><br>
            <div style="margin-top: 8px; font-size: 14px; font-weight: 600;">
                🔸 입력: <span style="color: #98FB98;">{total_input:,}개</span> | 
                출력: <span style="color: #FFB6C1;">{total_output:,}개</span> | 
                총합: <span style="color: #90EE90; font-weight: 700;">{total_tokens:,}개</span>
            </div>
        </div>
        """
    
    def reset_session(self):
        """세션 초기화"""
        self.current_conversation_input = 0
        self.current_conversation_output = 0
        self.current_conversation_id = None
        self.completed_conversations.clear()
        self.session_total_input = 0
        self.session_total_output = 0


# 전역 세션 토큰 매니저 인스턴스
session_token_manager = SessionTokenManager()