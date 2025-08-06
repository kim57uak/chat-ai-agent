from typing import List, Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from .base_model_strategy import BaseModelStrategy
from ui.prompts import prompt_manager, ModelType
from core.llm_factory import LLMFactoryProvider
import logging

logger = logging.getLogger(__name__)


class ClaudeStrategy(BaseModelStrategy):
    """Claude 모델 전략 (예시 구현)"""
    
    def create_llm(self):
        """Claude LLM 생성"""
        try:
            factory = LLMFactoryProvider.get_factory(self.model_name)
            self.llm = factory.create_llm(self.api_key, self.model_name, streaming=False)
            logger.info(f"Claude LLM 생성 성공: {self.model_name}")
            return self.llm
        except Exception as e:
            logger.error(f"Claude LLM 생성 실패: {e}")
            return None
    
    def create_messages(self, user_input: str, system_prompt: str = None, conversation_history: List[Dict] = None) -> List[BaseMessage]:
        """Claude 메시지 형식 생성 - 대화 히스토리 포함"""
        messages = []
        
        # 시스템 프롬프트 생성
        if system_prompt:
            enhanced_prompt = self.enhance_prompt_with_format(system_prompt)
        else:
            enhanced_prompt = self.get_claude_system_prompt()
        
        messages.append(SystemMessage(content=enhanced_prompt))
        
        # 대화 히스토리를 실제 메시지로 변환
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user" and content.strip():
                    messages.append(HumanMessage(content=content))
                elif role in ["assistant", "agent"] and content.strip():
                    messages.append(AIMessage(content=content))
        
        # 현재 사용자 입력 추가
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
        """Claude 에이전트 생성"""
        if not tools or not self.llm:
            return None
        
        try:
            from langchain.agents import create_react_agent, AgentExecutor
            from langchain.prompts import PromptTemplate
            
            # Claude용 ReAct 프롬프트 사용
            react_template = """
You are a helpful assistant that uses tools to answer questions.

**TOOL CALLING APPROACH**:
- Follow tool schemas exactly with all required parameters
- Use EXACT parameter names from schema (verify spelling)
- Include ALL required parameters in tool calls
- Use clear structured thinking and standard agent format
- Be proactive: prefer autonomous tool use when solution is evident
- Maintain helpful approach while considering safety implications
- Format responses clearly using markdown for maximum readability

**FORMAT**:
Thought: [your reasoning]
Action: [exact_tool_name]
Action Input: {{"param": "value"}}

Observation: [tool result will appear here]

Thought: [analyze the observation]
Final Answer: [Korean response based on observation]

Tools: {tools}
Tool names: {tool_names}

Question: {input}
Thought:{agent_scratchpad}"""
            
            prompt = PromptTemplate.from_template(react_template)
            
            agent = create_react_agent(self.llm, tools, prompt)
            return AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5
            )
        except Exception as e:
            logger.error(f"Claude 에이전트 생성 실패: {e}")
            return None
    
    def get_claude_system_prompt(self) -> str:
        """Claude 전용 시스템 프롬프트"""
        return prompt_manager.get_system_prompt(ModelType.CLAUDE.value)
    
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