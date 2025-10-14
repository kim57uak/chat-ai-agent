from typing import List, Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from .base_model_strategy import BaseModelStrategy
from ui.prompts import prompt_manager, ModelType
from core.llm_factory import LLMFactoryProvider
from core.logging import get_logger

logger = get_logger("claude_strategy")


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
        
        # 사용자 입력에서 언어 감지
        user_language = self.detect_user_language(user_input)
        
        # 시스템 프롬프트 생성 (언어 지침 포함)
        if system_prompt:
            enhanced_prompt = self.enhance_prompt_with_format(system_prompt)
        else:
            enhanced_prompt = self.get_claude_system_prompt(user_language)
        
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
        """Claude 모델의 도구 사용 여부 결정 - AI 컴텍스트 기반"""
        try:
            available_tools = getattr(self, 'tools', [])
            if not available_tools:
                return False
            
            # 중앙관리 시스템에서 프롬프트 가져오기
            decision_prompt = prompt_manager.get_tool_decision_prompt(
                ModelType.CLAUDE.value, user_input, available_tools
            )

            messages = [
                SystemMessage(content="You are an expert at analyzing user requests to determine optimal tool usage."),
                HumanMessage(content=decision_prompt)
            ]

            if self.llm:
                response = self.llm.invoke(messages)
                decision = response.content.strip().upper()
                
                result = "YES" in decision
                logger.info(f"Claude AI tool decision: {decision} -> {result}")
                return result
            else:
                return True

        except Exception as e:
            logger.error(f"Claude tool usage decision error: {e}")
            return True
    
    def create_agent_executor(self, tools: List) -> Optional:
        """Claude 에이전트 생성"""
        if not tools or not self.llm:
            return None
        
        try:
            from langchain.agents import create_react_agent, AgentExecutor
            from langchain.prompts import PromptTemplate
            from core.parsers.claude_react_parser import ClaudeReActParser
            
            # 공통 프롬프트 시스템 사용
            system_prompt = prompt_manager.get_agent_system_prompt(ModelType.CLAUDE.value)
            response_format = prompt_manager.get_response_format_prompt()
            
            react_template = f"""You are a helpful assistant that provides well-formatted responses in Korean.

{system_prompt}

{response_format}

## 🚨 CRITICAL: NEVER OUTPUT ACTION AND FINAL ANSWER TOGETHER!

**STEP 1 - Tool Use (if needed):**
```
Thought: [your reasoning]
Action: [exact_tool_name_from_list]
Action Input: {{{{"param": "value"}}}}
```
**STOP HERE! Wait for Observation!**

**STEP 2 - After receiving Observation:**
```
Thought: [analyze the observation]
Final Answer: [Korean response with markdown]
```

## 📊 DATA ANALYSIS RULES:
- ALWAYS analyze ALL data in API responses
- If API returns products, ALWAYS show them in table format
- Don't ignore data just because it doesn't match search keywords
- Present actual results, then explain any mismatches
- Use markdown tables for structured data

## 🛑 FORBIDDEN:
- Never output Action and Final Answer in same response
- Never skip waiting for Observation
- Never make up data without tool results
- Never ignore API response data

## Available Tools:
{{tools}}

## Tool Names:
{{tool_names}}

---
**Question:** {{input}}
{{agent_scratchpad}}"""
            
            prompt = PromptTemplate(
                input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
                template=react_template
            )
            
            # 도구 목록 디버깅
            logger.info(f"Claude 에이전트에 전달되는 도구 목록:")
            for tool in tools:
                logger.info(f"  - {tool.name}: {getattr(tool, 'description', 'No description')[:100]}")
            
            custom_parser = ClaudeReActParser()
            agent = create_react_agent(self.llm, tools, prompt, output_parser=custom_parser)
            return AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=15,
                max_execution_time=120,
                handle_parsing_errors=True,
                early_stopping_method="force",
                return_intermediate_steps=True
            )
        except Exception as e:
            logger.error(f"Claude 에이전트 생성 실패: {e}")
            return None
    
    def get_claude_system_prompt(self, user_language: str = None) -> str:
        """Claude 전용 시스템 프롬프트"""
        return prompt_manager.get_system_prompt(ModelType.CLAUDE.value, use_tools=True, user_language=user_language)
    
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