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
import logging

logger = logging.getLogger(__name__)


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
        
        # 사용자 입력에서 언어 감지 (원본 텍스트만 사용)
        user_language = self.detect_user_language(user_input)
        
        # 시스템 프롬프트 생성
        if system_prompt:
            enhanced_prompt = self.enhance_prompt_with_format(system_prompt)
        else:
            enhanced_prompt = self.get_perplexity_system_prompt()
        
        # 언어별 응답 지침 추가
        if user_language == "ko":
            enhanced_prompt += "\n\n**중요**: 사용자가 한국어로 질문했으므로 반드시 한국어로 응답하세요."
        else:
            enhanced_prompt += "\n\n**Important**: The user asked in English, so please respond in English."
        
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
        """도구 사용 여부 결정 - 강화된 컨텍스트 이해"""
        try:
            # 키워드 기반 1차 필터링
            tool_keywords = [
                '검색', 'search', '찾아', '조회', '확인', 'check', '가져와', 'get',
                '데이터베이스', 'database', 'mysql', 'sql', '쿼리', 'query',
                '이메일', 'email', 'gmail', '메일', 'mail',
                '파일', 'file', '엑셀', 'excel', '문서', 'document',
                '지라', 'jira', '이슈', 'issue', '티켓', 'ticket',
                '컨플루언스', 'confluence', '위키', 'wiki',
                '여행', 'travel', '하나투어', 'hanatour', '상품', 'product',
                '지도', 'map', '위치', 'location', '주소', 'address',
                '날씨', 'weather', '뉴스', 'news', '최신', 'latest', '현재', 'current',
                '오늘', 'today', '어제', 'yesterday', '최근', 'recent',
                '생성', 'create', '만들어', 'make', '작성', 'write',
                '업데이트', 'update', '수정', 'modify', '변경', 'change',
                '삭제', 'delete', '제거', 'remove',
                '다운로드', 'download', '업로드', 'upload',
                '실행', 'execute', '실시간', 'realtime', 'real-time'
            ]
            
            user_lower = user_input.lower()
            has_tool_keywords = any(keyword in user_lower for keyword in tool_keywords)
            
            if not has_tool_keywords:
                logger.info(f"🚫 키워드 기반 필터링: 도구 사용 불필요 - '{user_input}'")
                return False
            
            # 사용 가능한 도구 정보 수집
            available_tools = []
            if hasattr(self, 'tools') and self.tools:
                for tool in self.tools[:15]:  # 더 많은 도구 표시
                    tool_desc = getattr(tool, 'description', tool.name)
                    available_tools.append(f"- {tool.name}: {tool_desc[:120]}")
            
            if not available_tools:
                logger.info(f"🚫 사용 가능한 도구 없음")
                return False
            
            tools_info = "\n".join(available_tools)
            
            # 강화된 도구 판단 프롬프트
            decision_prompt = f"""TASK: Determine if the user request requires external tools or data.

USER REQUEST: "{user_input}"

AVAILABLE TOOLS:
{tools_info}

**DECISION CRITERIA:**

USE TOOLS (Answer YES) when request involves:
✅ External data retrieval (search, database queries, file access)
✅ Real-time information (current news, weather, stock prices)
✅ Specific system operations (Jira issues, email management)
✅ File operations (Excel, documents, downloads)
✅ API calls to external services
✅ Time-sensitive data (today's data, recent updates)
✅ User's personal/work data (my files, assigned issues)

NO TOOLS (Answer NO) when request is:
❌ General knowledge questions I can answer directly
❌ Explanations, concepts, tutorials
❌ Creative writing, brainstorming
❌ Code examples without external data
❌ Mathematical calculations
❌ Theoretical discussions

**CRITICAL**: If the request mentions specific external systems, data sources, or requires current information, ALWAYS use tools.

Answer with ONLY: YES or NO"""
            
            # Perplexity LLM에 직접 요청
            response = self.llm._call(decision_prompt)
            decision = response.strip().upper()
            
            # 토큰 사용량 로깅
            TokenLogger.log_token_usage(
                self.model_name, decision_prompt, decision, "tool_decision"
            )
            
            result = "YES" in decision
            logger.info(f"🤔 Perplexity 도구 사용 판단: '{user_input}' -> {decision} -> {result}")
            return result
            
        except Exception as e:
            logger.error(f"Perplexity 도구 사용 판단 오류: {e}")
            # 오류 시 키워드 기반으로 판단
            tool_keywords = ['검색', 'search', '찾아', '조회', '확인', 'check', '가져와', 'get', '데이터베이스', 'mysql', 'jira', 'email']
            return any(keyword in user_input.lower() for keyword in tool_keywords)
    
    def create_agent_executor(self, tools: List) -> Optional[AgentExecutor]:
        """Perplexity ReAct 에이전트 생성 - 단순화된 구현"""
        if not tools:
            return None
        
        react_prompt = PromptTemplate.from_template(
            """You are an expert data analyst that uses tools to gather information and provides comprehensive analysis.

**CRITICAL: THOROUGH OBSERVATION ANALYSIS REQUIRED**

**EXACT FORMAT (MANDATORY):**

Thought: [Analyze what information is needed for the user's question]
Action: [exact_tool_name]
Action Input: {{"param": "value"}}

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
- Action Input MUST be valid JSON
- NEVER mix Action and Final Answer
- Analyze Observation thoroughly before Final Answer

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
                max_iterations=5,
                max_execution_time=60,
                handle_parsing_errors="CRITICAL: Follow the exact format. After receiving Observation, analyze ALL the data thoroughly in your Thought, then provide a comprehensive Final Answer based ONLY on the Observation data. Include specific details from the results.",
                early_stopping_method="force",
                return_intermediate_steps=True,
            )
        except Exception as e:
            logger.error(f"Perplexity agent creation failed: {e}")
            return None
    
    def get_perplexity_system_prompt(self) -> str:
        """Perplexity 전용 시스템 프롬프트 - 도구 인식 강화"""
        base_prompt = prompt_manager.get_system_prompt(ModelType.PERPLEXITY.value)
        
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