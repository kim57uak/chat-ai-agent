"""토큰 사용량 누적 관리자"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal
from .token_extractor import TokenUsage, TokenExtractor

logger = logging.getLogger(__name__)


class TokenAccumulator(QObject):
    """토큰 사용량 누적 및 관리"""
    
    # 토큰 사용량 업데이트 신호
    token_updated = pyqtSignal(dict)  # {model: str, usage: TokenUsage, session_total: TokenUsage}
    
    def __init__(self):
        super().__init__()
        self.session_tokens: Dict[str, TokenUsage] = {}  # 모델별 세션 누적
        self.conversation_tokens: List[Dict] = []  # 대화별 토큰 기록
        self.current_session_id: Optional[int] = None
        self.conversation_active: bool = False
        self.current_conversation_tokens: TokenUsage = TokenUsage()  # 현재 대화 누적
    
    def set_session(self, session_id: int):
        """현재 세션 설정"""
        if self.current_session_id != session_id:
            self.current_session_id = session_id
            self.session_tokens.clear()
            self.conversation_tokens.clear()
            logger.info(f"토큰 누적기 세션 변경: {session_id}")
    
    def add_response_tokens(self, response: any, model_name: str, context: str = "") -> Optional[TokenUsage]:
        """AI 응답에서 토큰 추출 및 누적"""
        try:
            # 응답에서 토큰 추출
            usage = TokenExtractor.extract_from_response(response, model_name)
            
            if usage:
                # 모델별 누적
                if model_name not in self.session_tokens:
                    self.session_tokens[model_name] = TokenUsage(model=model_name)
                
                self.session_tokens[model_name] += usage
                
                # 대화 기록 추가
                self.conversation_tokens.append({
                    'timestamp': datetime.now(),
                    'model': model_name,
                    'context': context,
                    'usage': usage
                })
                
                logger.info(f"토큰 누적 ({model_name}): +{usage.total_tokens} = 세션:{self.session_tokens[model_name].total_tokens}, 대화:{self.current_conversation_tokens.total_tokens}")
                
                # UI 업데이트 신호 발송 (현재 대화 토큰 포함)
                self.token_updated.emit({
                    'model': model_name,
                    'usage': usage,
                    'session_total': self.session_tokens[model_name],
                    'conversation_total': self.current_conversation_tokens
                })
                
                return usage
            else:
                logger.debug(f"토큰 정보 없음 ({model_name}): {context}")
                return None
                
        except Exception as e:
            logger.error(f"토큰 누적 오류 ({model_name}): {e}")
            return None
    
    def add_estimated_tokens(self, text: str, model_name: str, context: str = "") -> TokenUsage:
        """텍스트에서 토큰 추정 및 누적 (실제 사용량이 없을 때)"""
        try:
            usage = TokenExtractor.estimate_tokens(text, model_name)
            
            # 모델별 누적
            if model_name not in self.session_tokens:
                self.session_tokens[model_name] = TokenUsage(model=model_name)
            
            self.session_tokens[model_name] += usage
            
            # 대화 기록 추가
            self.conversation_tokens.append({
                'timestamp': datetime.now(),
                'model': model_name,
                'context': f"{context} (추정)",
                'usage': usage
            })
            
            logger.debug(f"토큰 추정 누적 ({model_name}): +{usage.total_tokens} = {self.session_tokens[model_name].total_tokens}")
            
            # UI 업데이트 신호 발송
            self.token_updated.emit({
                'model': model_name,
                'usage': usage,
                'session_total': self.session_tokens[model_name]
            })
            
            return usage
            
        except Exception as e:
            logger.error(f"토큰 추정 누적 오류 ({model_name}): {e}")
            return TokenUsage(model=model_name)
    
    def get_session_total(self, model_name: str = None) -> TokenUsage:
        """세션 총 토큰 사용량 반환"""
        if model_name:
            return self.session_tokens.get(model_name, TokenUsage(model=model_name))
        
        # 모든 모델 합계
        total = TokenUsage()
        for usage in self.session_tokens.values():
            total += usage
        return total
    
    def get_model_list(self) -> List[str]:
        """사용된 모델 목록 반환"""
        return list(self.session_tokens.keys())
    
    def get_conversation_history(self) -> List[Dict]:
        """대화별 토큰 사용 기록 반환"""
        return self.conversation_tokens.copy()
    
    def clear_session(self):
        """현재 세션 토큰 정보 초기화"""
        self.session_tokens.clear()
        self.conversation_tokens.clear()
        logger.info("세션 토큰 정보 초기화")
    
    def start_conversation(self):
        """대화 시작"""
        self.conversation_active = True
        self.current_conversation_tokens = TokenUsage()  # 대화 시작 시 초기화
        logger.debug("대화 시작 - 토큰 누적 초기화")
    
    def end_conversation(self) -> bool:
        """대화 종료"""
        if hasattr(self, 'conversation_active') and self.conversation_active:
            self.conversation_active = False
            logger.info(f"대화 종료 - 총 사용 토큰: {self.current_conversation_tokens.total_tokens}")
            return True
        return False
    
    def reset(self):
        """전체 초기화"""
        self.session_tokens.clear()
        self.conversation_tokens.clear()
        self.current_session_id = None
        self.conversation_active = False
        logger.info("토큰 누적기 전체 초기화")
    
    def get_total(self) -> tuple:
        """현재 대화 토큰 사용량 반환 (input, output, total)"""
        return (self.current_conversation_tokens.prompt_tokens, self.current_conversation_tokens.completion_tokens, self.current_conversation_tokens.total_tokens)
    
    def get_summary(self) -> Dict:
        """토큰 사용량 요약 정보"""
        total_usage = self.get_session_total()
        
        return {
            'session_id': self.current_session_id,
            'total_tokens': total_usage.total_tokens,
            'total_prompt_tokens': total_usage.prompt_tokens,
            'total_completion_tokens': total_usage.completion_tokens,
            'models_used': len(self.session_tokens),
            'model_breakdown': {
                model: {
                    'total': usage.total_tokens,
                    'prompt': usage.prompt_tokens,
                    'completion': usage.completion_tokens
                }
                for model, usage in self.session_tokens.items()
            },
            'conversation_count': len(self.conversation_tokens)
        }


# 전역 토큰 누적기 인스턴스
token_accumulator = TokenAccumulator()