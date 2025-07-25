from typing import List, Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from .base_model_strategy import BaseModelStrategy
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
        return """You are Claude, a helpful AI assistant created by Anthropic.

**Response Guidelines:**
- Always respond in natural, conversational Korean
- Organize information clearly with headings and bullet points
- Highlight important information using **bold** formatting
- Be friendly, helpful, and accurate
- Use proper markdown table format when creating tables

**TABLE FORMAT RULES**: When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row. Format: |Header1|Header2|Header3|\\n|---|---|---|\\n|Data1|Data2|Data3|. Never use tabs or spaces for table alignment."""
    
    def supports_streaming(self) -> bool:
        """Claude 스트리밍 지원"""
        return True
    
    def _get_ocr_prompt(self) -> str:
        """OCR 전용 프롬프트"""
        return """이 이미지에서 **모든 텍스트를 정확히 추출(OCR)**해주세요.

**필수 작업:**
1. **완전한 텍스트 추출**: 이미지 내 모든 한글, 영어, 숫자, 기호를 빠짐없이 추출
2. **구조 분석**: 표, 목록, 제목, 단락 등의 문서 구조 파악
3. **레이아웃 정보**: 텍스트의 위치, 크기, 배치 관계 설명
4. **정확한 전사**: 오타 없이 정확하게 모든 문자 기록

**응답 형식:**
## 📄 추출된 텍스트
[모든 텍스트를 정확히 나열]

## 📋 문서 구조
[표, 목록, 제목 등의 구조 설명]

**중요**: 이미지에서 읽을 수 있는 모든 텍스트를 절대 누락하지 말고 완전히 추출해주세요."""


# 새로운 전략을 팩토리에 등록하는 방법 (필요시 사용)
def register_claude_strategy():
    """Claude 전략을 팩토리에 등록"""
    from .model_strategy_factory import ModelStrategyFactory
    ModelStrategyFactory.register_strategy('claude', ClaudeStrategy)
    logger.info("Claude 전략이 등록되었습니다.")