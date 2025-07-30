from typing import List, Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from .base_model_strategy import BaseModelStrategy
from ui.prompts import prompt_manager, ModelType
import logging

logger = logging.getLogger(__name__)


class ClaudeStrategy(BaseModelStrategy):
    """Claude 모델 전략 (예시 구현)"""
    
    def create_llm(self):
        """Claude LLM 생성 (예시)"""
        # 실제 구현 시 langchain-anthropic 사용
        # from langchain_anthropic import ChatAnthropic
        # return ChatAnthropic(
        #     model=self.model_name,
        #     anthropic_api_key=self.api_key,
        #     temperature=0.1,
        #     max_tokens=4096,
        # )
        
        # 현재는 예시로 None 반환
        logger.warning("Claude LLM은 아직 구현되지 않았습니다.")
        return None
    
    def create_messages(self, user_input: str, system_prompt: str = None) -> List[BaseMessage]:
        """Claude 메시지 형식 생성"""
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        else:
            messages.append(SystemMessage(content=self.get_claude_system_prompt()))
        
        messages.append(HumanMessage(content=user_input))
        return messages
    
    def process_image_input(self, user_input: str) -> BaseMessage:
        """Claude 이미지 입력 처리"""
        import re
        import base64
        
        image_match = re.search(
            r"\[IMAGE_BASE64\](.*?)\[/IMAGE_BASE64\]", user_input, re.DOTALL
        )
        if not image_match:
            return HumanMessage(content=user_input)
        
        image_data = image_match.group(1).strip()
        text_content = user_input.replace(image_match.group(0), "").strip()
        
        try:
            base64.b64decode(image_data)
        except Exception as e:
            logger.error(f"Invalid Base64 image data: {e}")
            return HumanMessage(content="Invalid image data.")
        
        if not text_content:
            text_content = self._get_ocr_prompt()
        
        # Claude 이미지 형식 (실제 구현 시 수정 필요)
        return HumanMessage(
            content=[
                {"type": "text", "text": text_content},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_data
                    }
                },
            ]
        )
    
    def should_use_tools(self, user_input: str) -> bool:
        """Claude 모델의 도구 사용 여부 결정"""
        try:
            decision_prompt = f"""User request: "{user_input}". You must end with "Action" or "Final Answer."

Determine if this request requires using tools to provide accurate information.

Requires tools:
- Real-time information search
- Database queries
- External API calls
- File processing
- Current information lookups
- Location-based queries

Does not require tools:
- General conversation
- Explanations or opinions
- Creative writing
- General knowledge

Answer: YES or NO only."""

            messages = [
                SystemMessage(content="You are an expert at analyzing user requests to determine if tools are needed."),
                HumanMessage(content=decision_prompt),
            ]

            if self.llm:
                response = self.llm.invoke(messages)
                decision = response.content.strip().upper()
                
                result = "YES" in decision
                logger.info(f"Claude tool usage decision: {decision} -> {result}")
                return result
            else:
                # LLM이 없으면 기본적으로 도구 사용 안함
                return False

        except Exception as e:
            logger.error(f"Claude tool usage decision error: {e}")
            return False
    
    def create_agent_executor(self, tools: List) -> Optional:
        """Claude 에이전트 생성 (예시)"""
        if not tools or not self.llm:
            return None
        
        # 실제 구현 시 Claude에 맞는 에이전트 생성
        logger.warning("Claude 에이전트는 아직 구현되지 않았습니다.")
        return None
    
    def get_claude_system_prompt(self) -> str:
        """Claude 전용 시스템 프롬프트"""
        # Claude는 아직 구현되지 않았으므로 공통 프롬프트 사용
        return prompt_manager.get_system_prompt(ModelType.COMMON.value)
    
    def supports_streaming(self) -> bool:
        """Claude 스트리밍 지원"""
        return True
    
    def _get_ocr_prompt(self) -> str:
        """OCR 전용 프롬프트"""
        return prompt_manager.get_prompt("ocr", "image_text_extraction")


# 새로운 전략을 팩토리에 등록하는 방법 (필요시 사용)
def register_claude_strategy():
    """Claude 전략을 팩토리에 등록"""
    from .model_strategy_factory import ModelStrategyFactory
    ModelStrategyFactory.register_strategy('claude', ClaudeStrategy)
    logger.info("Claude 전략이 등록되었습니다.")