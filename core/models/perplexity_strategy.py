from typing import List, Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from .base_model_strategy import BaseModelStrategy
from core.perplexity_wrapper import PerplexityWrapper
from core.enhanced_system_prompts import SystemPrompts
import logging

logger = logging.getLogger(__name__)


class PerplexityStrategy(BaseModelStrategy):
    """Perplexity 모델 전략"""
    
    def create_llm(self):
        """Perplexity LLM 생성"""
        return PerplexityWrapper(
            model=self.model_name,
            pplx_api_key=self.api_key,
            temperature=0.1,
            max_tokens=4096,
            request_timeout=120,
        )
    
    def create_messages(self, user_input: str, system_prompt: str = None) -> List[BaseMessage]:
        """Perplexity 메시지 형식 생성"""
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        else:
            messages.append(SystemMessage(content=self.get_perplexity_system_prompt()))
        
        messages.append(HumanMessage(content=user_input))
        return messages
    
    def process_image_input(self, user_input: str) -> BaseMessage:
        """Perplexity는 이미지 처리 미지원"""
        # 이미지 태그 제거하고 텍스트만 처리
        import re
        cleaned_input = re.sub(r'\[IMAGE_BASE64\].*?\[/IMAGE_BASE64\]', '', user_input, flags=re.DOTALL)
        return HumanMessage(content=cleaned_input.strip() or "이미지 처리는 지원되지 않습니다.")
    
    def should_use_tools(self, user_input: str) -> bool:
        """Perplexity 모델은 항상 도구 사용"""
        logger.info("Perplexity 모델은 항상 도구를 사용하도록 강제합니다")
        return True
    
    def create_agent_executor(self, tools: List) -> Optional[AgentExecutor]:
        """Perplexity ReAct 에이전트 생성"""
        if not tools:
            return None
        
        perplexity_react_prompt = PromptTemplate.from_template(
            """You are an AI assistant that uses various tools to provide accurate information.

**Instructions:**
- Carefully analyze user requests to select the most appropriate tools
- Use tools to gather current, accurate information when needed
- Organize information in a clear, logical structure
- Respond in natural, conversational Korean
- Be friendly and helpful while maintaining accuracy
- If multiple tools are needed, use them systematically
- Focus on providing exactly what the user asked for
- Always parse MCP tool results accurately and present them to the user

Available tools:
{tools}

Tool names: {tool_names}

**IMPORTANT: YOU MUST FOLLOW THIS FORMAT EXACTLY**

Question: {input}. You must end with "Action" or "Final Answer."
Thought: I need to analyze this request and determine which tool(s) would be most helpful.
Action: tool_name
Action Input: {{"param1": "value1", "param2": "value2"}}
Observation: tool_execution_result
Thought: Based on the result, I will decide whether to use another tool.
Action: another_tool_name
Action Input: {{"param1": "value1"}}
Observation: another_tool_execution_result
Thought: Now I have enough information to provide a comprehensive answer.
Final Answer: My comprehensive response in Korean

**CRITICAL FORMAT RULES - FOLLOW THESE EXACTLY**:
- After EVERY "Thought:" line, you MUST IMMEDIATELY include either "Action:" or "Final Answer:"
- NEVER skip the "Action:" line after a "Thought:" line
- NEVER include any other text between "Thought:" and "Action:" lines
- ALWAYS follow "Action:" with "Action Input:" on the next line
- ALWAYS use valid JSON format for "Action Input:" parameters
- When finished, ALWAYS end with "Thought:" followed by "Final Answer:"

**REMEMBER**: The format must be EXACTLY as shown above. This is CRITICAL for the system to work properly.

{agent_scratchpad}
            """
        )

        try:
            from core.perplexity_agent_helper import create_perplexity_agent
            agent = create_perplexity_agent(self.llm, tools, perplexity_react_prompt)
        except ImportError as e:
            logger.error(f"perplexity_agent_helper module import failed: {e}")
            agent = create_react_agent(self.llm, tools, perplexity_react_prompt)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True,
            early_stopping_method="force",
            return_intermediate_steps=True,
        )
    
    def get_perplexity_system_prompt(self) -> str:
        """Perplexity 전용 시스템 프롬프트"""
        return SystemPrompts.get_perplexity_mcp_prompt()
    
    def supports_streaming(self) -> bool:
        """Perplexity는 스트리밍 제한적 지원"""
        return False