from typing import List, Dict, Tuple
from .base_chat_processor import BaseChatProcessor
import logging

logger = logging.getLogger(__name__)


class SimpleChatProcessor(BaseChatProcessor):
    """단순 채팅 처리기 (도구 사용 없음)"""
    
    def process_message(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """단순 채팅 처리"""
        try:
            if not self.validate_input(user_input):
                return "유효하지 않은 입력입니다.", []
            
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
            
            # 대화 히스토리 포함 처리
            if conversation_history:
                messages = self._convert_history_to_messages(conversation_history)
                messages.extend(self.model_strategy.create_messages(user_input))
            else:
                messages = self.model_strategy.create_messages(user_input)
            
            response = self.model_strategy.llm.invoke(messages)
            
            # Perplexity 응답 처리 (문자열 또는 객체)
            if isinstance(response, str):
                response_content = response
            else:
                response_content = getattr(response, 'content', str(response))
            
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
    
    def _convert_history_to_messages(self, conversation_history: List[Dict]):
        """대화 히스토리를 메시지로 변환"""
        from langchain.schema import HumanMessage, AIMessage
        
        messages = []
        for msg in conversation_history[-10:]:  # 최근 10개만
            role = msg.get("role", "")
            content = msg.get("content", "")[:500]  # 내용 제한
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        
        return messages