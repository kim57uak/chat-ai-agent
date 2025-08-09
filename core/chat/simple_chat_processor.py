from typing import List, Dict, Tuple
from .base_chat_processor import BaseChatProcessor
from core.token_logger import TokenLogger
import logging

logger = logging.getLogger(__name__)


class SimpleChatProcessor(BaseChatProcessor):
    """단순 채팅 처리기 (도구 사용 없음)"""
    
    def process_message(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """단순 채팅 처리 - 대화 히스토리 포함"""
        try:
            if not self.validate_input(user_input):
                return "유효하지 않은 입력입니다.", []
            
            # 모델 전략에 도구 사용 안함을 명시
            if hasattr(self.model_strategy, '_use_tools_mode'):
                self.model_strategy._use_tools_mode = False
            
            # 이미지 데이터 처리
            if self._has_image_data(user_input):
                processed_message = self.model_strategy.process_image_input(user_input)
                response = self.model_strategy.llm.invoke([processed_message])
                
                # Perplexity 응답 처리 (문자열 또는 객체)
                if isinstance(response, str):
                    response_content = response
                else:
                    response_content = getattr(response, 'content', str(response))
                
                return self.format_response(response_content), []
            
            # 대화 히스토리 로깅
            if conversation_history:
                logger.info(f"Simple chat에 대화 히스토리 {len(conversation_history)}개 전달됨")
            else:
                logger.info("Simple chat에 대화 히스토리 없음")
            
            # 대화 히스토리를 포함한 메시지 생성
            messages = self.model_strategy.create_messages(
                user_input, 
                system_prompt=None,
                conversation_history=conversation_history
            )
            
            logger.info(f"생성된 메시지 수: {len(messages)}")
            
            response = self.model_strategy.llm.invoke(messages)
            
            # Perplexity 응답 처리 (문자열 또는 객체)
            if isinstance(response, str):
                response_content = response
            else:
                response_content = getattr(response, 'content', str(response))
            
            # 토큰 사용량 로깅
            TokenLogger.log_messages_token_usage(
                self.model_strategy.model_name, messages, response_content, "simple_chat"
            )
            
            return self.format_response(response_content), []
            
        except Exception as e:
            logger.error(f"Simple chat processing error: {e}")
            return f"채팅 처리 중 오류가 발생했습니다: {str(e)[:100]}...", []
    
    def supports_tools(self) -> bool:
        """도구 지원하지 않음"""
        return False
    
    def _has_image_data(self, user_input: str) -> bool:
        """이미지 데이터 포함 여부 확인"""
        cleaned_input = user_input.replace("\n", "")
        return "[IMAGE_BASE64]" in cleaned_input and "[/IMAGE_BASE64]" in cleaned_input