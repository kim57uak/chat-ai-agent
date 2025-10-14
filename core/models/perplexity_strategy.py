from typing import List, Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from .base_model_strategy import BaseModelStrategy
from core.perplexity_llm import PerplexityLLM
from core.perplexity_wrapper import PerplexityWrapper
from core.perplexity_output_parser import PerplexityOutputParser
from ui.prompts import prompt_manager, ModelType
from core.token_logger import TokenLogger
from core.logging import get_logger

logger = get_logger("perplexity_strategy")


class PerplexityStrategy(BaseModelStrategy):
    """Perplexity 모델 전략 - 단순화된 구현"""
    
    def create_llm(self):
        """Perplexity LLM 생성"""
        params = self.get_model_parameters()
        wrapper = PerplexityWrapper(
            pplx_api_key=self.api_key,
            model=self.model_name
        )
        # 파라미터를 wrapper에 저장하여 generate 호출 시 사용
        wrapper._model_params = params
        return wrapper
    
    def create_messages(self, user_input: str, system_prompt: str = None, conversation_history: List[Dict] = None) -> List[BaseMessage]:
        """Perplexity 메시지 형식 생성 - 대화 히스토리 포함"""
        messages = []
        
        # 사용자 입력에서 언어 감지
        user_language = self.detect_user_language(user_input)
        
        # 시스템 프롬프트 생성 (언어 지침 포함)
        if system_prompt:
            enhanced_prompt = self.enhance_prompt_with_format(system_prompt)
        else:
            enhanced_prompt = self.get_perplexity_system_prompt(user_language)
        
        # 대화 히스토리가 있으면 시스템 프롬프트에 컨텍스트 강조 추가
        if conversation_history:
            history_context = self._format_conversation_history(conversation_history)
            enhanced_prompt += f"\n\n=== CONVERSATION HISTORY (HIGHEST PRIORITY) ===\n{history_context}\n\n**ABSOLUTE PRIORITY RULE**: \n1. ALWAYS check this conversation history FIRST before searching\n2. If the answer exists in this history, use it directly\n3. Only search for NEW information not in this conversation\n4. When referencing history, say \"Based on our conversation...\"\n5. Remember names, preferences, and context from above messages\n==========================================="
            
            logger.info(f"Perplexity에 대화 히스토리 {len(conversation_history)}개 메시지 컨텍스트 추가")
        
        # Perplexity는 시스템 메시지를 첫 번째 메시지로 처리
        messages.append(SystemMessage(content=enhanced_prompt))
        
        # 대화 히스토리를 실제 메시지로 변환 - 교대 패턴 보장
        if conversation_history:
            last_role = None
            for i, msg in enumerate(conversation_history):
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if not content.strip():
                    continue
                
                # 연속된 같은 role 방지
                if role == "user" and last_role != "user":
                    messages.append(HumanMessage(content=content))
                    logger.debug(f"  히스토리 메시지 {i+1}: user - {content[:50]}...")
                    last_role = "user"
                elif role in ["assistant", "agent"] and last_role != "assistant":
                    messages.append(AIMessage(content=content))
                    logger.debug(f"  히스토리 메시지 {i+1}: assistant - {content[:50]}...")
                    last_role = "assistant"
                elif role == "user" and last_role == "user":
                    # 연속된 user 메시지는 마지막 메시지에 병합
                    if messages and isinstance(messages[-1], HumanMessage):
                        messages[-1].content += f"\n\n{content}"
                        logger.debug(f"  연속 user 메시지 병합: {content[:30]}...")
        
        # 현재 사용자 입력 추가 - 마지막이 user면 병합
        if messages and isinstance(messages[-1], HumanMessage):
            messages[-1].content += f"\n\n{user_input}"
            logger.info(f"  현재 입력을 마지막 user 메시지에 병합")
        else:
            messages.append(HumanMessage(content=user_input))
        
        logger.info(f"Perplexity에 최종 전달되는 메시지 수: {len(messages)}")
        return messages
    
    def _format_conversation_history(self, conversation_history: List[Dict]) -> str:
        """대화 히스토리를 텍스트로 포맷팅 - 강화된 버전"""
        if not conversation_history:
            return "No previous conversation."
        
        formatted_history = []
        formatted_history.append("💬 **CONVERSATION CONTEXT (Remember this!):**")
        formatted_history.append("=" * 50)
        
        for i, msg in enumerate(conversation_history, 1):
            role = msg.get("role", "")
            content = msg.get("content", "").strip()
            
            if not content:
                continue
                
            if role == "user":
                formatted_history.append(f"[{i}] 👤 **User said**: {content}")
            elif role in ["assistant", "agent"]:
                formatted_history.append(f"[{i}] 🤖 **I replied**: {content}")
        
        formatted_history.append("=" * 50)
        formatted_history.append("📝 **IMPORTANT**: This conversation history contains personal context, names, preferences, and previous discussions. Use this information to provide contextual responses.")
        
        return "\n".join(formatted_history)
    
    def process_image_input(self, user_input: str) -> BaseMessage:
        """Perplexity는 이미지 처리 미지원"""
        # 이미지 태그 제거하고 텍스트만 처리
        import re
        cleaned_input = re.sub(r'\[IMAGE_BASE64\].*?\[/IMAGE_BASE64\]', '', user_input, flags=re.DOTALL)
        return HumanMessage(content=cleaned_input.strip() or "이미지 처리는 지원되지 않습니다.")
    
    def should_use_tools(self, user_input: str) -> bool:
        """도구 사용 여부 결정 - AI 컨텍스트 기반"""
        try:
            available_tools = getattr(self, 'tools', [])
            if not available_tools:
                return False
            
            # 중앙관리 시스템에서 프롬프트 가져오기
            decision_prompt = prompt_manager.get_tool_decision_prompt(
                ModelType.PERPLEXITY.value, user_input, available_tools
            )
            
            response = self.llm._call(decision_prompt)
            decision = response.strip().upper()
            
            TokenLogger.log_token_usage(
                self.model_name, decision_prompt, decision, "tool_decision"
            )
            
            result = "YES" in decision
            logger.info(f"🤔 Perplexity 도구 사용 판단: '{user_input}' -> {decision} -> {result}")
            return result
            
        except Exception as e:
            logger.error(f"Perplexity 도구 사용 판단 오류: {e}")
            return True
    
    def create_agent_executor(self, tools: List) -> Optional[AgentExecutor]:
        """Perplexity ReAct 에이전트 생성 - 단순화된 구현"""
        if not tools:
            return None
        
        # Common 프롬프트에서 도구 사용 규칙 가져오기
        tool_usage_rules = prompt_manager.get_tool_prompt(ModelType.PERPLEXITY.value)
        execution_rules = prompt_manager.get_custom_prompt(ModelType.COMMON.value, "execution_rules")
        
        react_prompt = PromptTemplate.from_template(
            f"""You are an expert data analyst that uses tools to gather information and provides comprehensive analysis.

**CRITICAL: THOROUGH OBSERVATION ANALYSIS REQUIRED**

{tool_usage_rules}

{execution_rules}

**EXACT FORMAT (MANDATORY):**

Thought: [Analyze what information is needed for the user's question]
Action: [exact_tool_name]
Action Input: {{{{"exact_parameter_name_from_schema": "value"}}}}

(System provides Observation with tool results)

Thought: [CRITICAL ANALYSIS STEP: Read the ENTIRE Observation carefully. Extract ALL key information including names, numbers, dates, details. Identify patterns and relationships. Organize findings logically. This analysis determines the quality of your Final Answer.]
Final Answer: [Comprehensive Korean response based EXCLUSIVELY on Observation data. Include specific details, exact numbers, names, and all relevant information from the tool results. Structure the response clearly with proper formatting. Do NOT add external knowledge - use ONLY the data provided in the Observation.]

**ANALYSIS REQUIREMENTS:**
1. **COMPLETE DATA PROCESSING**: Read every part of the Observation
2. **EXTRACT SPECIFICS**: Include exact names, numbers, dates from results
3. **LOGICAL ORGANIZATION**: Structure information clearly
4. **COMPREHENSIVE COVERAGE**: Address all aspects relevant to user's question
5. **DATA-ONLY RESPONSES**: Base answer EXCLUSIVELY on Observation data

**PARSING RULES:**
- Use EXACT keywords: "Thought:", "Action:", "Action Input:", "Final Answer:"
- Action Input MUST be valid JSON with EXACT parameter names from inputSchema
- NEVER use generic names like "param", "value" - check the tool's inputSchema
- NEVER mix Action and Final Answer
- Analyze Observation thoroughly before Final Answer

Tools: {{tools}}
Tool names: {{tool_names}}

Question: {{input}}
Thought:{{agent_scratchpad}}"""
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
                max_iterations=5,
                max_execution_time=60,
                handle_parsing_errors="CRITICAL: Follow the exact format. After receiving Observation, analyze ALL the data thoroughly in your Thought, then provide a comprehensive Final Answer based ONLY on the Observation data. Include specific details from the results.",
                early_stopping_method="force",
                return_intermediate_steps=True,
            )
        except Exception as e:
            logger.error(f"Perplexity agent creation failed: {e}")
            return None
    
    def get_perplexity_system_prompt(self, user_language: str = None) -> str:
        """Perplexity 전용 시스템 프롬프트 - 도구 인식 강화"""
        base_prompt = prompt_manager.get_system_prompt(ModelType.PERPLEXITY.value, use_tools=True, user_language=user_language)
        
        # 도구가 있을 때 도구 인식 강화 프롬프트 추가
        if hasattr(self, 'tools') and self.tools:
            tool_awareness = prompt_manager.get_custom_prompt(ModelType.PERPLEXITY.value, "tool_awareness")
            agent_system = prompt_manager.get_agent_system_prompt(ModelType.PERPLEXITY.value)
            
            # 사용 가능한 도구 목록 생성
            tool_list = []
            for tool in self.tools[:10]:
                tool_desc = getattr(tool, 'description', tool.name)
                tool_list.append(f"- {tool.name}: {tool_desc[:80]}")
            
            tools_summary = "\n".join(tool_list) if tool_list else "No tools available"
            
            enhanced_prompt = f"""{base_prompt}

{tool_awareness}

**AVAILABLE MCP TOOLS:**
{tools_summary}

{agent_system}

**CRITICAL REMINDER**: When user asks for data, search, current information, or external resources, IMMEDIATELY use the appropriate MCP tool. These tools provide real-time, accurate data that surpasses your training knowledge."""
            
            return enhanced_prompt
        else:
            return base_prompt
    
    def supports_streaming(self) -> bool:
        """Perplexity는 스트리밍 미지원"""
        return False