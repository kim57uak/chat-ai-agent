"""단순 채팅 처리를 담당하는 모듈"""
from typing import List, Dict, Any
from core.enhanced_system_prompts import SystemPrompts
from core.processors.message_converter import StandardMessageConverter
from core.processors.image_processor import StandardImageProcessor
from core.file_utils import load_config
import logging

logger = logging.getLogger(__name__)


class SimpleChatProcessor:
    """단순 채팅 처리기 - SRP 원칙 적용"""
    
    def __init__(self):
        self.message_converter = StandardMessageConverter()
        self.image_processor = StandardImageProcessor()
    
    def process_chat(self, user_input: str, llm: Any, conversation_history: List[Dict] = None) -> str:
        """일반 채팅 처리"""
        try:
            # 시스템 프롬프트 선택
            if self.image_processor.contains_image_data(user_input):
                system_content = SystemPrompts.get_image_analysis_prompt()
            else:
                system_content = SystemPrompts.get_general_chat_prompt()

            model_name = getattr(llm, 'model_name', str(llm))
            messages = [self.message_converter.create_system_message(system_content, model_name)]

            # 대화 히스토리 추가
            if conversation_history:
                history_messages = self.message_converter.convert_history_to_messages(conversation_history, model_name)
                messages.extend(history_messages)
                logger.info(f"대화 히스토리 사용: {len(history_messages)}개 메시지")
            else:
                logger.info("대화 히스토리 없음")

            # 사용자 입력 처리
            if self.image_processor.contains_image_data(user_input):
                processed_input = self.image_processor.process_image_input(user_input, model_name)
                messages.append(processed_input)
            else:
                from langchain.schema import HumanMessage
                messages.append(HumanMessage(content=user_input))

            logger.info(f"총 메시지 수: {len(messages)}개")
            response = llm.invoke(messages)
            
            return self._limit_response_length(response.content)

        except Exception as e:
            logger.error(f"일반 채팅 오류: {e}")
            return f"죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요."
    
    def _limit_response_length(self, response: str) -> str:
        """응답 길이 제한"""
        try:
            config = load_config()
            response_settings = config.get("response_settings", {})
            
            if not response_settings.get("enable_length_limit", True):
                return response
            
            max_length = response_settings.get("max_response_length", 8000)
            
            if len(response) <= max_length:
                return response
            
            logger.warning(f"응답 길이 제한 적용: {len(response)}자 -> {max_length}자")
            
            truncated = response[:max_length]
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            
            cut_point = max(last_period, last_newline)
            if cut_point > max_length * 0.8:
                truncated = response[:cut_point + 1]
            
            return truncated + "\n\n[응답이 너무 길어 일부만 표시됩니다. 더 자세한 내용이 필요하시면 구체적인 질문을 해주세요.]"
            
        except Exception as e:
            logger.error(f"응답 길이 제한 오류: {e}")
            return response