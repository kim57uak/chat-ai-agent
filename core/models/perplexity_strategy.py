from typing import List, Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from .base_model_strategy import BaseModelStrategy
from core.perplexity_llm import PerplexityLLM
from core.perplexity_wrapper import PerplexityWrapper
from core.perplexity_output_parser import PerplexityOutputParser
from core.enhanced_system_prompts import SystemPrompts
import logging

logger = logging.getLogger(__name__)


class PerplexityStrategy(BaseModelStrategy):
    """Perplexity 모델 전략 - 단순화된 구현"""
    
    def create_llm(self):
        """Perplexity LLM 생성"""
        return PerplexityWrapper(
            pplx_api_key=self.api_key,
            model=self.model_name
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
        """도구 사용 여부 결정 - AI가 컨텍스트를 이해하여 판단"""
        try:
            # 사용 가능한 도구 정보 수집
            available_tools = []
            if hasattr(self, 'tools') and self.tools:
                for tool in self.tools[:5]:  # 주요 도구 5개만
                    tool_desc = getattr(tool, 'description', tool.name)
                    available_tools.append(f"- {tool.name}: {tool_desc[:80]}")
            
            tools_info = "\n".join(available_tools) if available_tools else "사용 가능한 도구 없음"
            
            decision_prompt = f"""User request: "{user_input}"

Available tools:
{tools_info}

Analyze if this request requires using external tools to provide accurate information.

Use tools for:
- Real-time data queries (databases, web searches, file systems)
- Specific information lookups that I don't have in my knowledge
- External API calls or system operations
- Current/live information requests
- Data processing or calculations requiring external resources

Do NOT use tools for:
- General knowledge questions I can answer
- Simple conversations or greetings
- Creative writing or brainstorming
- Explanations of concepts I know
- Opinion-based discussions

Answer: YES or NO only."""
            
            # Perplexity LLM에 직접 요청
            response = self.llm._call(decision_prompt)
            decision = response.strip().upper()
            
            result = "YES" in decision
            logger.info(f"Perplexity AI 도구 사용 판단: '{user_input}' -> {decision} -> {result}")
            return result
            
        except Exception as e:
            logger.error(f"Perplexity 도구 사용 판단 오류: {e}")
            # 오류 시 기본적으로 도구 사용
            return True
    
    def create_agent_executor(self, tools: List) -> Optional[AgentExecutor]:
        """Perplexity ReAct 에이전트 생성 - 단순화된 구현"""
        if not tools:
            return None
        
        react_prompt = PromptTemplate.from_template(
            """You are a helpful assistant that uses tools to answer questions.

**CRITICAL: Follow EXACT format - ONE step at a time:**

Thought: [what you need to do]
Action: [tool_name]
Action Input: [input_for_tool]

(Wait for Observation)

Thought: [analyze result]
Final Answer: [response in Korean]

**RULES:**
1. Use ONE tool at a time
2. NEVER output Action and Final Answer together
3. Wait for Observation before Final Answer
4. Be precise and follow format exactly

Tools: {tools}
Tool names: {tool_names}

Question: {input}
Thought:{agent_scratchpad}"""
        )

        try:
            # 커스텀 파서 사용
            custom_parser = PerplexityOutputParser()
            
            # 에이전트 생성 시 커스텀 파서 사용
            agent = create_react_agent(self.llm, tools, react_prompt, output_parser=custom_parser)
            
            return AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=2,
                handle_parsing_errors=True,
                early_stopping_method="force",
                return_intermediate_steps=True,
            )
        except Exception as e:
            logger.error(f"Perplexity agent creation failed: {e}")
            return None
    
    def get_perplexity_system_prompt(self) -> str:
        """Perplexity 전용 시스템 프롬프트"""
        return SystemPrompts.get_perplexity_mcp_prompt()
    
    def supports_streaming(self) -> bool:
        """Perplexity는 스트리밍 미지원"""
        return False