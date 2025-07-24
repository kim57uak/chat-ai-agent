from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.agents import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_perplexity import ChatPerplexity
from core.perplexity_wrapper import PerplexityWrapper
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.tools import BaseTool
from tools.langchain.langchain_tools import MCPTool, MCPToolRegistry
from core.mcp_interface import MCPToolCaller
from mcp.servers.mcp import get_all_mcp_tools
from mcp.tools.tool_manager import tool_manager, ToolCategory
from core.conversation_history import ConversationHistory
from core.message_validator import MessageValidator
from core.enhanced_system_prompts import SystemPrompts
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AIAgent:
    """AI 에이전트 - 도구 사용 여부를 결정하고 실행"""

    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model_name = model_name
        self.llm = self._create_llm()
        self.tools: List[MCPTool] = []
        self.agent_executor: Optional[AgentExecutor] = None
        self.conversation_history = ConversationHistory()

        # MCP 도구 로드 및 등록
        self._load_mcp_tools()
        # 기존 히스토리 로드
        self.conversation_history.load_from_file()

    def _create_llm(self):
        """LLM 인스턴스 생성"""
        if self.model_name.startswith("gemini"):
            # Gemini 모델에 멀티모달 지원 활성화 및 이미지 처리 최적화
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=0.1,  # 정확한 텍스트 추출을 위해 낮은 온도
                convert_system_message_to_human=True,  # 시스템 메시지를 인간 메시지로 변환
                max_tokens=4096,  # 충분한 토큰 할당
            )
        elif (
            "sonar" in self.model_name
            or "r1-" in self.model_name
            or "perplexity" in self.model_name
        ):
            # Perplexity 모델에 특별한 래퍼 클래스 사용
            logger.info(f"Perplexity 모델 사용: {self.model_name}")
            return PerplexityWrapper(
                model=self.model_name,
                pplx_api_key=self.api_key,
                temperature=0.1,
                max_tokens=4096,
                request_timeout=120,
            )
        else:
            return ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                temperature=0.1,
                max_tokens=4096,
            )

    def _load_mcp_tools(self):
        """MCP 도구 로드 및 LangChain 도구로 등록"""
        try:
            # 실제 MCP 도구 호출자 사용
            from core.mcp_implementation import mcp_tool_caller

            tool_registry = MCPToolRegistry(mcp_tool_caller)

            all_mcp_tools = get_all_mcp_tools()
            if all_mcp_tools:
                # 모든 도구 등록
                self.tools = tool_registry.register_mcp_tools(all_mcp_tools)
                tool_manager.register_tools(all_mcp_tools)
                logger.info(f"AI 에이전트에 {len(self.tools)}개 도구 로드됨")
            else:
                logger.warning("사용 가능한 MCP 도구가 없습니다")
        except Exception as e:
            logger.error(f"MCP 도구 로드 실패: {e}")
            # 폴백: 실제 도구 호출 기능이 있는 MCP 도구 호출자 생성
            try:
                class SimpleMCPToolCaller(MCPToolCaller):
                    def call_tool(self, server_name, tool_name, arguments=None):
                        from mcp.servers.mcp import call_mcp_tool
                        return call_mcp_tool(server_name, tool_name, arguments)
                    
                    def get_all_tools(self):
                        return get_all_mcp_tools()
                
                # 도구 레지스트리 생성
                mcp_caller = SimpleMCPToolCaller()
                tool_registry = MCPToolRegistry(mcp_caller)
                
                all_mcp_tools = get_all_mcp_tools()
                if all_mcp_tools:
                    # 모든 도구 등록
                    self.tools = tool_registry.register_mcp_tools(all_mcp_tools)
                    tool_manager.register_tools(all_mcp_tools)
                    logger.info(f"폴백 방식으로 AI 에이전트에 {len(self.tools)}개 도구 로드됨")
                else:
                    logger.warning("사용 가능한 MCP 도구가 없습니다")
            except Exception as fallback_error:
                logger.error(f"폴백 MCP 도구 로드 실패: {fallback_error}")
                self.tools = []

    def _should_use_tools(self, user_input: str, force_agent: bool = False) -> bool:
        """AI가 자연어를 이해하여 도구 사용 여부를 지능적으로 결정"""
        import time

        start_time = time.time()
        logger.info(f"🤔 도구 사용 판단 시작: {user_input[:30]}...")

        # Perplexity 모델의 경우 항상 도구를 사용하도록 강제
        if (
            "sonar" in self.model_name
            or "r1-" in self.model_name
            or "perplexity" in self.model_name
        ):
            logger.info("🔧 Perplexity 모델은 항상 도구를 사용하도록 강제합니다")
            return True

        # Agent 모드가 강제된 경우 항상 도구 사용
        if force_agent:
            logger.info("🔧 Agent 모드가 강제되어 도구를 사용합니다")
            return True

        try:
            # 도구 설명 수집
            tool_descriptions = []
            for tool in self.tools[:8]:  # 주요 도구들만
                desc = getattr(tool, "description", tool.name)
                tool_descriptions.append(f"- {tool.name}: {desc[:100]}")

            tools_info = (
                "\n".join(tool_descriptions)
                if tool_descriptions
                else "사용 가능한 도구 없음"
            )

            # Agent 모드 선택 시 더 적극적인 판단 기준 적용
            agent_context = ""
            if force_agent:
                agent_context = "\n\nIMPORTANT: The user has specifically selected Agent mode, indicating they want to use available tools when possible. Be more inclined to use tools for information gathering, searches, or data processing tasks."

            decision_prompt = f"""User request: "{user_input}". You must end with "Action" or "Final Answer."

Available tools:
{tools_info}

Determine if this request requires using tools to provide accurate information.

Requires tools:
- Real-time information search (web search, news, weather, etc.)
- Database queries (travel products, flights, etc.)
- External API calls (maps, translation, etc.)
- File processing or calculations
- Current time or date-related information
- Specific data lookups or searches
- Location-based queries
- If you request something You don't know, utilize appropriate tools.

Does not require tools:
- A question about knowledge you already know.
- General conversation or questions
- Explanations or opinions
- Creative writing or idea suggestions
- General knowledge already known{agent_context}

Answer: YES or NO only."""

            messages = [
                SystemMessage(
                    content="You are an expert at analyzing user requests to determine if tools are needed. When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row."
                ),
                HumanMessage(content=decision_prompt),
            ]

            llm_start = time.time()
            response = self.llm.invoke(messages)
            llm_elapsed = time.time() - llm_start
            decision = response.content.strip().upper()

            result = "YES" in decision
            mode_info = " (Agent 모드)" if force_agent else " (Ask 모드)"
            total_elapsed = time.time() - start_time
            logger.info(
                f"🤔 도구 사용 판단{mode_info}: {decision} -> {result} (LLM: {llm_elapsed:.2f}초, 총: {total_elapsed:.2f}초)"
            )
            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ 도구 사용 판단 오류: {elapsed:.2f}초, 오류: {e}")
            return False

    def _create_agent_executor(self) -> AgentExecutor:
        """에이전트 실행기 생성"""
        if not self.tools:
            return None

        # OpenAI 도구 에이전트 생성 (GPT 모델용)
        if not self.model_name.startswith("gemini") and not (
            "sonar" in self.model_name
            or "r1-" in self.model_name
            or "perplexity" in self.model_name
        ):
            from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

            system_message = """You are a helpful AI assistant that can use various tools to provide accurate information.

**Instructions:**
- Analyze user requests carefully to select the most appropriate tools
- Use tools to gather current, accurate information when needed
- Organize information in a clear, logical structure
- Respond in natural, conversational Korean
- Be friendly and helpful while maintaining accuracy
- If multiple tools are needed, use them systematically
- Focus on providing exactly what the user asked for

**TABLE FORMAT RULES**: When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row. Format: |Header1|Header2|Header3|\n|---|---|---|\n|Data1|Data2|Data3|. Never use tabs or spaces for table alignment.

**Response Format:**
- Use clear headings and bullet points when appropriate
- Format information in a structured, readable way
- Always end your response with either an Action or Final Answer
- ONLY SHOW THE FINAL ANSWER TO THE USER - HIDE ALL THOUGHT PROCESSES

**IMPORTANT**: 
- Always end your response with either an Action or Final Answer
- ONLY SHOW THE FINAL ANSWER TO THE USER - DO NOT SHOW ANY THOUGHT PROCESSES, ACTIONS, OR OBSERVATIONSghlight important information
- Keep responses well-organized and easy to read"""

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_message),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )

            agent = create_openai_tools_agent(self.llm, self.tools, prompt)
            return AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=2,
                handle_parsing_errors=True,
            )

        # Perplexity 모델용 ReAct 에이전트 생성
        elif (
            "sonar" in self.model_name
            or "r1-" in self.model_name
            or "perplexity" in self.model_name
        ):
            logger.info("Perplexity 모델용 ReAct 에이전트 생성")

            # Perplexity 모델을 위한 특별한 프롬프트 (영어로 작성)
            perplexity_react_prompt = PromptTemplate.from_template(
                """
 You are an AI assistant that uses various tools to provide accurate information.

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
Action Input: {"param1": "value1", "param2": "value2"}
Observation: tool_execution_result
Thought: Based on the result, I will decide whether to use another tool.
Action: another_tool_name
Action Input: {"param1": "value1"}
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

{agent_scratchpad}
                """
            )

            # 특별한 시스템 프롬프트 추가
            try:
                from core.perplexity_agent_helper import create_perplexity_agent
                
                agent = create_perplexity_agent(
                    self.llm, self.tools, perplexity_react_prompt
                )
            except ImportError as e:
                logger.error(f"perplexity_agent_helper 모듈 가져오기 실패: {e}")
                # 폴백: 기본 ReAct 에이전트 생성
                agent = create_react_agent(self.llm, self.tools, perplexity_react_prompt)

            # AgentExecutor 생성 시 파싱 오류 처리 강화
            executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,  # 디버깅을 위해 verbose 활성화
                max_iterations=3,  # 반복 횟수 증가
                handle_parsing_errors=True,
                early_stopping_method="force",
                return_intermediate_steps=True,
            )

            # 추가 설정
            if hasattr(executor, "handle_parsing_errors"):
                executor.handle_parsing_errors = True

            return executor

        # ReAct 에이전트 생성 (Gemini 등 다른 모델용)
        else:
            react_prompt = PromptTemplate.from_template(
                """
You are a helpful AI assistant that can use various tools to provide accurate information.

**Instructions:**
- Analyze user requests carefully to select the most appropriate tools
- Use tools to gather current, accurate information when needed
- Organize information in a clear, logical structure
- Respond in natural, conversational Korean
- Be friendly and helpful while maintaining accuracy
- If multiple tools are needed, use them systematically
- Focus on providing exactly what the user asked for

Available tools:
{tools}

Tool names: {tool_names}

Follow this format exactly:

Question: {input}.You must end with "Action" or "Final Answer."
Thought: I need to analyze this request and determine which tool(s) would be most helpful.
Action: tool_name
Action Input: input_for_tool
Observation: tool_execution_result
Thought: Based on the result, I will provide a comprehensive answer in Korean with clear formatting.
Final Answer: [Provide a well-organized response in Korean with clear headings, bullet points, and highlighted important information]

{agent_scratchpad}
                """
            )

            agent = create_react_agent(self.llm, self.tools, react_prompt)
            return AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=False,
                max_iterations=2,
                handle_parsing_errors=True,
                early_stopping_method="force",
                return_intermediate_steps=False,
            )

    def chat_with_tools(self, user_input: str) -> tuple[str, list]:
        """도구를 사용한 채팅"""
        import time

        start_time = time.time()
        logger.info(f"🚀 도구 채팅 시작: {user_input[:50]}...")

        try:
            # 토큰 제한 오류 방지를 위해 대화 히스토리 제한
            if "context_length_exceeded" in str(getattr(self, "_last_error", "")):
                logger.warning("토큰 제한 오류로 인해 일반 채팅으로 대체")
                return self.simple_chat(user_input), []

            # Gemini 모델은 직접 도구 호출 방식 사용
            if self.model_name.startswith("gemini"):
                logger.info("🔧 Gemini 도구 채팅 시작")
                gemini_start = time.time()
                result = self._gemini_tool_chat(user_input)
                logger.info(
                    f"🔧 Gemini 도구 채팅 완료: {time.time() - gemini_start:.2f}초"
                )
                return result

            # Perplexity 모델은 직접 도구 호출 방식 사용
            elif (
                "sonar" in self.model_name
                or "r1-" in self.model_name
                or "perplexity" in self.model_name
            ):
                logger.info("🔧 Perplexity 도구 채팅 시작")
                perplexity_start = time.time()
                result = self._perplexity_tool_chat(user_input)
                logger.info(
                    f"🔧 Perplexity 도구 채팅 완료: {time.time() - perplexity_start:.2f}초"
                )
                return result

            # GPT 모델은 기존 에이전트 방식 사용
            if not self.agent_executor:
                logger.info("🔧 에이전트 실행기 생성 시작")
                agent_create_start = time.time()
                self.agent_executor = self._create_agent_executor()
                logger.info(
                    f"🔧 에이전트 실행기 생성 완료: {time.time() - agent_create_start:.2f}초"
                )

            if not self.agent_executor:
                return "사용 가능한 도구가 없습니다.", []

            logger.info("🔧 에이전트 실행 시작")
            agent_invoke_start = time.time()
            result = self.agent_executor.invoke({"input": user_input})
            logger.info(
                f"🔧 에이전트 실행 완료: {time.time() - agent_invoke_start:.2f}초"
            )
            output = result.get("output", "")

            # 사용된 도구 정보 추출
            used_tools = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) >= 2 and hasattr(step[0], "tool"):
                        used_tools.append(step[0].tool)

            if "Agent stopped" in output or not output.strip():
                logger.warning("에이전트 중단 감지, 결과 확인 중...")
                
                # 중간 단계에서 도구가 사용되었는지 확인
                if "intermediate_steps" in result and result["intermediate_steps"]:
                    # 도구가 사용되었으면 마지막 도구 결과 확인
                    last_step = result["intermediate_steps"][-1]
                    if len(last_step) >= 2:
                        tool_result = last_step[1]
                        logger.info(f"도구 결과 발견: {str(tool_result)[:100]}...")
                        
                        # 도구 결과를 바탕으로 최종 응답 생성
                        final_response = self._generate_final_response(user_input, str(tool_result))
                        return final_response, [last_step[0].tool]
                
                # 도구 결과가 없으면 일반 채팅으로 대체
                logger.warning("유효한 도구 결과 없음, 일반 채팅으로 대체")
                return self.simple_chat(user_input), []

            elapsed = time.time() - start_time
            logger.info(f"✅ 도구 채팅 완료: {elapsed:.2f}초")
            return output, used_tools

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            self._last_error = error_msg
            logger.error(f"❌ 도구 사용 채팅 오류: {elapsed:.2f}초, 오류: {e}")

            # 토큰 제한 오류 처리
            if (
                "context_length_exceeded" in error_msg
                or "maximum context length" in error_msg
            ):
                logger.warning("토큰 제한 오류 발생, 일반 채팅으로 대체")
                return self.simple_chat(user_input), []

            return self.simple_chat(user_input), []

    def simple_chat(self, user_input: str) -> str:
        """일반 채팅 (도구 사용 없음)"""
        try:
            # 통일된 시스템 메시지 - 이미지 텍스트 추출에 특화
            system_content = """You are an expert AI assistant specialized in image analysis and text extraction (OCR).

**Primary Mission for Images:**
- **COMPLETE TEXT EXTRACTION**: Extract every single character, number, and symbol from images with 100% accuracy
- **ZERO OMISSIONS**: Never skip or miss any text, no matter how small or unclear
- **PERFECT TRANSCRIPTION**: Reproduce all text exactly as it appears, including spacing and formatting
- **STRUCTURAL ANALYSIS**: Identify tables, lists, headers, paragraphs, and document layout
- **MULTILINGUAL SUPPORT**: Handle Korean, English, numbers, and special characters flawlessly

**TABLE FORMAT RULES**: When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row. Format: |Header1|Header2|Header3|\n|---|---|---|\n|Data1|Data2|Data3|. Never use tabs or spaces for table alignment.

**Response Format for Images:**
## 📄 추출된 텍스트
[모든 텍스트를 정확히 나열 - 절대 누락 금지]

## 📋 문서 구조
[표, 목록, 제목 등의 구조 설명]

## 📍 레이아웃 정보
[텍스트 배치와 위치 관계]

**Critical Rules:**
- NEVER say "텍스트가 없습니다" or "추출할 텍스트가 없습니다"
- ALWAYS extract something, even if text is small or unclear
- If text is unclear, provide your best interpretation with [불명확] notation
- Focus on TEXT EXTRACTION as the absolute priority

**For General Questions:**
- Always respond in natural, conversational Korean
- Organize information clearly with headings and bullet points
- Highlight important information using **bold** formatting
- Be friendly, helpful, and accurate"""

            # Gemini 모델의 경우 시스템 메시지를 인간 메시지로 변환
            if self.model_name.startswith("gemini"):
                messages = [HumanMessage(content=system_content)]
            else:
                messages = [SystemMessage(content=system_content)]

            # 이미지 데이터 처리
            if "[IMAGE_BASE64]" in user_input and "[/IMAGE_BASE64]" in user_input:
                processed_input = self._process_image_input(user_input)
                messages.append(processed_input)
            else:
                messages.append(HumanMessage(content=user_input))

            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"일반 채팅 오류: {e}")
            return f"죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요."

    def simple_chat_with_history(
        self, user_input: str, conversation_history: List[Dict]
    ) -> str:
        """대화 기록을 포함한 일반 채팅"""
        try:
            logger.info(
                f"히스토리와 함께 채팅 시작: {len(conversation_history)}개 메시지"
            )

            messages = self._convert_history_to_messages(conversation_history)

            # 이미지 데이터 처리
            if "[IMAGE_BASE64]" in user_input and "[/IMAGE_BASE64]" in user_input:
                processed_input = self._process_image_input(user_input)
                messages.append(processed_input)
            else:
                messages.append(HumanMessage(content=user_input))

            logger.info(f"최종 메시지 수: {len(messages)}개")

            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"대화 기록 채팅 오류: {e}")
            return self.simple_chat(user_input)

    def _process_image_input(self, user_input: str):
        """이미지 데이터를 처리하여 LangChain 메시지로 변환"""
        import re
        import base64

        # 이미지 데이터 추출
        image_match = re.search(
            r"\[IMAGE_BASE64\](.*?)\[/IMAGE_BASE64\]", user_input, re.DOTALL
        )
        if not image_match:
            return HumanMessage(content=user_input)

        image_data = image_match.group(1).strip()
        text_content = user_input.replace(image_match.group(0), "").strip()

        # Base64 데이터 검증
        try:
            base64.b64decode(image_data)
        except Exception as e:
            logger.error(f"잘못된 Base64 이미지 데이터: {e}")
            return HumanMessage(content="잘못된 이미지 데이터입니다.")

        # 텍스트 추출에 특화된 프롬프트
        if not text_content:
            text_content = """이 이미지에서 **모든 텍스트를 정확히 추출(OCR)**해주세요.

**필수 작업:**
1. **완전한 텍스트 추출**: 이미지 내 모든 한글, 영어, 숫자, 기호를 빠짐없이 추출
2. **구조 분석**: 표, 목록, 제목, 단락 등의 문서 구조 파악
3. **레이아웃 정보**: 텍스트의 위치, 크기, 배치 관계 설명
4. **정확한 전사**: 오타 없이 정확하게 모든 문자 기록
5. **맥락 설명**: 문서의 종류와 목적 파악
6. **테이블 포맷**: 표를 만들 때는 마크다운 형식 사용: |Header1|Header2|\n|---|---|\n|Data1|Data2|

**응답 형식:**
## 📄 추출된 텍스트
[모든 텍스트를 정확히 나열]

## 📋 문서 구조
[표, 목록, 제목 등의 구조 설명]

## 📍 레이아웃 정보
[텍스트 배치와 위치 관계]

**중요**: 이미지에서 읽을 수 있는 모든 텍스트를 절대 누락하지 말고 완전히 추출해주세요."""

        try:
            # Gemini 모델의 경우 특별한 형식 사용
            if self.model_name.startswith("gemini"):
                # Gemini 2.0 Flash에 최적화된 형식
                return HumanMessage(
                    content=[
                        {"type": "text", "text": text_content},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{image_data}",
                        },
                    ]
                )
            else:
                # OpenAI GPT-4V 형식
                return HumanMessage(
                    content=[
                        {"type": "text", "text": text_content},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            },
                        },
                    ]
                )
        except Exception as e:
            logger.error(f"이미지 처리 오류: {e}")
            return HumanMessage(
                content=f"{text_content}\n\n[이미지 처리 오류: {str(e)}]"
            )

    def process_message(self, user_input: str) -> tuple[str, list]:
        """메시지 처리 - AI가 도구 사용 여부 결정"""
        # 사용자 메시지를 히스토리에 추가
        self.conversation_history.add_message("user", user_input)

        if not self.tools:
            response = self.simple_chat_with_history(
                user_input, self.conversation_history.get_recent_messages(10)  # 5개 대화
            )
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            return response, []

        # Perplexity 모델의 경우 항상 도구 사용
        if (
            "sonar" in self.model_name
            or "r1-" in self.model_name
            or "perplexity" in self.model_name
        ):
            logger.info("🔧 Perplexity 모델은 항상 도구를 사용합니다")
            response, used_tools = self.chat_with_tools(user_input)
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            return response, used_tools

        # AI가 컨텍스트를 분석하여 도구 사용 여부 결정
        use_tools = self._should_use_tools(user_input)

        if use_tools:
            response, used_tools = self.chat_with_tools(user_input)
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            return response, used_tools
        else:
            response = self.simple_chat_with_history(
                user_input, self.conversation_history.get_recent_messages(10)  # 5개 대화
            )
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            return response, []

    def process_message_with_history(
        self,
        user_input: str,
        conversation_history: List[Dict],
        force_agent: bool = False,
    ) -> tuple[str, list]:
        """대화 기록을 포함한 메시지 처리"""
        if not self.tools:
            response = self.simple_chat_with_history(user_input, conversation_history)
            return response, []

        # force_agent가 True면 더 적극적으로 도구 사용 판단
        use_tools = self._should_use_tools(user_input, force_agent)

        if use_tools:
            response, used_tools = self.chat_with_tools(user_input)
            return response, used_tools
        else:
            response = self.simple_chat_with_history(user_input, conversation_history)
            return response, []

    def _convert_history_to_messages(self, conversation_history: List[Dict]):
        """대화 기록을 LangChain 메시지로 변환 - 토큰 제한 고려"""
        # Perplexity API 메시지 형식 검증
        validated_history = MessageValidator.validate_and_fix_messages(
            conversation_history
        )

        messages = []

        # 통일된 시스템 메시지 - 히스토리 활용 강조
        unified_system_content = """You are a helpful AI assistant that provides contextual responses based on conversation history.

**Response Guidelines:**
- Always respond in natural, conversational Korean
- Use conversation history to provide relevant, contextual answers
- Organize information clearly with headings and bullet points when appropriate
- Highlight important information using **bold** formatting
- Be friendly, helpful, and maintain conversation flow
- Reference previous context when relevant
- Provide comprehensive, well-structured responses

**TABLE FORMAT RULES**: When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row. Format: |Header1|Header2|Header3|\n|---|---|---|\n|Data1|Data2|Data3|. Never use tabs or spaces for table alignment."""

        if self.model_name.startswith("gemini"):
            messages.append(HumanMessage(content=unified_system_content))
        else:
            messages.append(SystemMessage(content=unified_system_content))

        # 최근 5개 대화 기록 사용 (10개 메시지 = 5개 대화)
        recent_history = (
            validated_history[-10:] if len(validated_history) > 10 else validated_history
        )

        for msg in recent_history:
            role = msg.get("role", "")
            content = msg.get("content", "")[:500]  # 내용 제한 증가
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                from langchain.schema import AIMessage

                messages.append(AIMessage(content=content))

        logger.info(
            f"히스토리 변환 완료: {len(recent_history)}개 메시지 -> {len(messages)}개 LangChain 메시지"
        )
        return messages

    def _gemini_tool_chat(self, user_input: str) -> tuple[str, list]:
        """게미니 모델용 AI 기반 도구 선택 및 실행 - 연쇄적 도구 사용 지원"""
        try:
            if self._is_tool_list_request(user_input):
                return self._show_tool_list(), []

            # 연쇄적 도구 사용 시작
            return self._execute_tool_chain(user_input)

        except Exception as e:
            logger.error(f"게미니 도구 채팅 오류: {e}")
            return self.simple_chat(user_input), []

    def _get_realistic_date_range(self, user_input: str) -> tuple[str, str]:
        """사용자 입력에서 현실적인 날짜 범위 생성 - 범용적 접근"""
        # 특정 API 형식에 의존하지 않고 AI가 적절한 형식을 결정하도록 함
        # 날짜 파싱은 각 도구의 스키마에 따라 AI가 처리
        return None, None  # AI가 적절한 도구를 선택하여 처리하도록 함

    def _get_area_code(self, user_input: str) -> str:
        """사용자 입력에서 지역 코드 추출 - AI가 동적으로 결정"""
        # AI가 사용 가능한 도구를 통해 지역 코드를 동적으로 조회하도록 변경
        # 하드코딩된 매핑 제거하고 범용적 접근 방식 사용
        return None  # AI가 적절한 도구를 선택하여 처리하도록 함

    def _ai_select_tool(self, user_input: str):
        """초기 도구 선택 (호환성을 위해 유지)"""
        return self._ai_select_next_tool(user_input, [], 0)

    def _legacy_ai_select_tool(self, user_input: str):
        """AI가 사용자 요청을 분석하여 최적의 도구와 파라미터를 지능적으로 결정"""
        try:
            if not self.tools:
                logger.warning("사용 가능한 도구가 없습니다")
                return None

            # 도구 설명 수집 (상세 정보 포함)
            tools_info = []
            for tool in self.tools:
                desc = getattr(tool, "description", tool.name)
                # 도구 스키마 정보도 포함
                schema_info = ""
                if hasattr(tool, "args_schema") and tool.args_schema:
                    try:
                        schema = tool.args_schema.schema()
                        if "properties" in schema:
                            params = list(schema["properties"].keys())[
                                :3
                            ]  # 주요 파라미터만
                            schema_info = f" (파라미터: {', '.join(params)})"
                    except:
                        pass
                tools_info.append(f"- {tool.name}: {desc}{schema_info}")

            tools_list = "\n".join(tools_info)

            selection_prompt = f"""User request: "{user_input}"

Available tools:
{tools_list}

Analyze the user's request and select the most appropriate tool with necessary parameters.

Response format:
- Use tool: TOOL: tool_name | PARAMS: {{"key": "value"}}
- No tool needed: TOOL: none

Examples:
- Web search: TOOL: search | PARAMS: {{"query": "search_term"}}
- Travel products: TOOL: retrieveSaleProductInformation | PARAMS: {{"startDate": "20240301", "endDate": "20240310", "productAreaCode": "A0"}}

Extract parameter values from user request or use reasonable defaults."""

            messages = [
                SystemMessage(
                    content="You are an expert at analyzing user requests to select the optimal tool. When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row."
                ),
                HumanMessage(content=selection_prompt),
            ]

            response = self.llm.invoke(messages)
            return self._parse_tool_decision(response.content)

        except Exception as e:
            logger.error(f"AI 도구 선택 오류: {e}")
            return None

    def _parse_tool_decision(self, response: str):
        """도구 선택 응답 파싱"""
        try:
            import re
            import json

            logger.info(f"파싱할 응답: {response}")

            # "TOOL: toolname | PARAMS: {...}" 형식 파싱
            match = re.search(
                r"TOOL:\s*([^|\n]+)(?:\s*\|\s*PARAMS:\s*([^\n]+))?",
                response,
                re.IGNORECASE,
            )
            if not match:
                logger.warning(f"도구 형식 매칭 실패: {response}")
                return None

            tool_name = match.group(1).strip()
            params_str = match.group(2).strip() if match.group(2) else "{}"

            logger.info(f"파싱된 도구명: '{tool_name}', 파라미터: '{params_str}'")

            if tool_name.lower() == "none":
                return {"tool": "none"}

            try:
                params = json.loads(params_str)
            except json.JSONDecodeError as je:
                logger.warning(f"JSON 파싱 실패: {params_str}, 오류: {je}")
                params = {}

            return {"tool": tool_name, "params": params}

        except Exception as e:
            logger.error(f"도구 결정 파싱 오류: {e}")
            return None

    def _split_large_response(
        self, response_text: str, max_chunk_size: int = 3000
    ) -> List[str]:
        """큰 응답을 청크로 분할"""
        if len(response_text) <= max_chunk_size:
            return [response_text]

        chunks = []
        current_pos = 0

        while current_pos < len(response_text):
            # JSON 구조를 고려한 분할 지점 찾기
            end_pos = min(current_pos + max_chunk_size, len(response_text))

            # JSON 객체나 배열 끝에서 분할
            if end_pos < len(response_text):
                # 뒤에서 가장 가까운 }, ] 찾기
                for i in range(end_pos, current_pos, -1):
                    if response_text[i] in ["}", "]", ","]:
                        end_pos = i + 1
                        break

            chunk = response_text[current_pos:end_pos]
            chunks.append(chunk)
            current_pos = end_pos

        return chunks

    def _process_chunked_response(self, large_response: str, user_query: str) -> str:
        """대용량 응답을 전체 분석하여 결과만 보여주기"""
        logger.info(f"대용량 응답 분석 시작: {len(large_response)}자")

        # 전체 데이터를 한 번에 분석
        analysis_prompt = f"""User query: {user_query}
                            Data:
                            {large_response}
                            Analyze the above data and provide useful information to the user in Korean. Don't mention chunk numbers or analysis progress, just show the results."""

        messages = [
            SystemMessage(
                content="You are an expert who analyzes data and provides useful information to users in Korean. Don't mention the analysis process, just show the results."
            ),
            HumanMessage(content=analysis_prompt),
        ]

        analysis_response = self.llm.invoke(messages)
        return analysis_response.content

    def _execute_selected_tool(self, tool_decision):
        """선택된 도구 실행"""
        try:
            tool_name = tool_decision["tool"]
            params = tool_decision.get("params", {})

            # 도구 스키마에 따라 파라미터 자동 변환
            selected_tool = None
            for tool in self.tools:
                if tool.name.lower() == tool_name.lower():
                    selected_tool = tool
                    break

            if (
                selected_tool
                and hasattr(selected_tool, "args_schema")
                and selected_tool.args_schema
            ):
                try:
                    schema = selected_tool.args_schema.schema()
                    if "properties" in schema:
                        for param_name, param_value in params.items():
                            if param_name in schema["properties"]:
                                param_schema = schema["properties"][param_name]
                                if param_schema.get("type") == "array" and isinstance(
                                    param_value, str
                                ):
                                    params[param_name] = [param_value]
                except:
                    pass

            logger.info(f"도구 찾기: '{tool_name}'")

            # 도구 찾기 (더 유연한 매칭)
            selected_tool = None
            for tool in self.tools:
                tool_name_lower = tool_name.lower()
                actual_name_lower = tool.name.lower()

                # 정확한 이름 매칭 또는 부분 매칭
                if (
                    tool_name_lower == actual_name_lower
                    or tool_name_lower in actual_name_lower
                    or actual_name_lower in tool_name_lower
                    or tool_name_lower.replace("_", "-")
                    == actual_name_lower.replace("_", "-")
                ):
                    selected_tool = tool
                    logger.info(f"도구 매칭 성공: '{tool_name}' -> '{tool.name}'")
                    break

            if not selected_tool:
                available_tools = [t.name for t in self.tools]
                logger.error(
                    f"도구 '{tool_name}'을 찾을 수 없습니다. 사용 가능한 도구: {available_tools}"
                )
                return f"도구 '{tool_name}'을 찾을 수 없습니다. 사용 가능한 도구: {available_tools}"

            # 검색 도구의 경우 더 많은 결과 요청
            if "search" in selected_tool.name.lower():
                if "limit" not in params and "maxResults" not in params:
                    params["maxResults"] = 10  # 기본 10개 결과
                if "includeHtml" not in params:
                    params["includeHtml"] = False

            # 도구 실행 (GPT 스타일 로깅)
            print(f"\n> Invoking: `{selected_tool.name}` with `{params}`\n")

            result = selected_tool.invoke(params)

            # 결과 출력
            print(result)
            print("\n")

            # 결과가 비어있는 경우 대안 제시
            if isinstance(result, str) and (
                '"resultCount": 0' in result
                or '"saleProductItemResponseList": []' in result
            ):
                logger.warning(f"도구 실행 결과가 비어있음: {selected_tool.name}")
                return f"검색 결과가 없습니다. 다른 날짜나 지역으로 다시 시도해보세요.\n\n원본 결과: {result}"

            logger.info(f"도구 실행 결과: {str(result)[:200]}...")

            # 대용량 응답 처리
            if isinstance(result, str) and len(result) > 5000:
                logger.info(f"대용량 응답 감지: {len(result)}자")
                original_query = (
                    tool_decision.get("original_query", "")
                    if isinstance(tool_decision, dict)
                    else ""
                )
                return self._process_chunked_response(result, original_query)

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"도구 실행 오류: {e}")

            # 타임아웃 오류 처리
            if "timeout" in error_msg.lower() or "MCP 응답 타임아웃" in error_msg:
                return f"도구 호출 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."

            return f"도구 실행 중 오류가 발생했습니다: {e}"

    def _is_tool_list_request(self, user_input: str) -> bool:
        """도구 목록 요청인지 AI가 판단"""
        try:
            # 도구 목록이 비어있으면 항상 False 반환
            if not self.tools:
                return False

            # 간단한 프롬프트로 AI에게 판단 요청
            prompt = f"""User input: "{user_input}"

Determine if this user input is asking to see a list of available tools.
Examples of tool list requests:
- "What tools can I use?"
- "Show me the available tools"
- "List MCP tools"
- "What active tools are there?"

If this input is asking for a tool list, answer ONLY 'YES'. Otherwise, answer ONLY 'NO'."""

            messages = [
                SystemMessage(
                    content="You are a helpful assistant that determines if a user is asking to see a list of available tools."
                ),
                HumanMessage(content=prompt),
            ]

            # 간단한 응답만 필요하므로 토큰 제한
            response = self.llm.invoke(messages)
            result = response.content.strip().upper()

            logger.info(f"도구 목록 요청 판단: {result}")
            return "YES" in result

        except Exception as e:
            logger.error(f"도구 목록 요청 판단 오류: {e}")
            # 오류 발생 시 안전하게 False 반환
            return False

    def _show_tool_list(self) -> str:
        """사용 가능한 도구 목록을 동적으로 생성하여 반환"""
        if not self.tools:
            return "현재 사용 가능한 도구가 없습니다."

        # 서버별로 도구 분류
        tools_by_server = {}
        for tool in self.tools:
            server_name = getattr(tool, "server_name", "Unknown")
            if server_name not in tools_by_server:
                tools_by_server[server_name] = []
            tools_by_server[server_name].append(tool)

        # 도구 목록 생성
        result = ["🔧 **사용 가능한 도구 목록**\n"]

        for server_name, server_tools in tools_by_server.items():
            result.append(f"📦 **{server_name}** ({len(server_tools)}개 도구):")
            for tool in server_tools:
                desc = getattr(tool, "description", tool.name)
                # 전체 설명 표시
                result.append(f"  • {tool.name}: {desc}")
            result.append("")  # 빈 줄 추가

        result.append(f"총 {len(self.tools)}개의 도구를 사용할 수 있습니다.")
        return "\n".join(result)

    def _format_response(self, text: str) -> str:
        """응답 텍스트를 자연스럽게 정리"""
        if not text:
            return text

        import re

        # 과도한 줄바꿈 정리
        formatted = re.sub(r"\n{3,}", "\n\n", text)

        # 불규칙한 들여쓰기 정리 - 5개 이상의 공백을 4개로 통일
        formatted = re.sub(r"\n\s{5,}", "\n    ", formatted)

        formatted = formatted.strip()
        return formatted

    def _generate_final_response(self, user_input: str, tool_result: str):
        """도구 결과를 바탕으로 최종 응답 생성 - 토큰 제한 고려"""
        try:
            # 도구 결과가 너무 길면 요약
            if len(tool_result) > 2000:
                tool_result = tool_result[:2000] + "...(생략)"

            response_prompt = f"""User asked: "{user_input}"

Data from tools:
{tool_result}

Your task:
1. Extract the most relevant information that directly answers the user's question
2. Organize the information in a logical, easy-to-follow structure
3. Write in conversational Korean as if explaining to a friend
4. Focus on what the user actually needs to know
5. Use simple, clear sentences without technical jargon
6. If there are multiple pieces of information, prioritize the most important ones first
7. Format your response using simple markdown (## for headings, **bold** for emphasis, - for bullet points)
8. Keep formatting minimal and clean
9. Use consistent indentation for lists and structured data

Provide a helpful, natural Korean response in markdown format that directly addresses what the user wanted to know."""

            unified_system_message = """You are a helpful AI assistant that analyzes tool results and provides comprehensive responses.

**Response Guidelines:**
- Always respond in natural, conversational Korean
- Organize information clearly with headings and bullet points
- Highlight important information using **bold** formatting
- Extract and present the most relevant information
- Use simple, clear sentences without technical jargon
- Structure responses logically and systematically
- Focus on what the user actually needs to know

**TABLE FORMAT RULES**: When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row. Format: |Header1|Header2|Header3|\n|---|---|---|\n|Data1|Data2|Data3|. Never use tabs or spaces for table alignment."""

            messages = [
                SystemMessage(content=unified_system_message),
                HumanMessage(content=response_prompt),
            ]

            response = self.llm.invoke(messages)
            return self._format_response(response.content)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"최종 응답 생성 오류: {e}")

            # 토큰 제한 오류 처리
            if (
                "context_length_exceeded" in error_msg
                or "maximum context length" in error_msg
            ):
                return self._format_response(
                    "검색 결과를 찾았지만 내용이 너무 길어 요약할 수 없습니다. 더 구체적인 질문으로 다시 시도해주세요."
                )

            return self._format_response(
                "도구 실행은 성공했지만 응답 생성 중 오류가 발생했습니다."
            )

    def _execute_tool_chain(
        self, user_input: str, max_iterations: int = 3
    ) -> tuple[str, list]:
        """연쇄적 도구 사용 실행"""
        all_used_tools = []
        accumulated_results = []
        current_query = user_input

        for iteration in range(max_iterations):
            logger.info(f"도구 체인 {iteration + 1}단계 시작: {current_query[:50]}...")

            # AI가 다음 도구 결정
            tool_decision = self._ai_select_next_tool(
                current_query, accumulated_results, iteration
            )

            if not tool_decision or tool_decision.get("tool") == "none":
                logger.info(f"도구 체인 {iteration + 1}단계에서 종료")
                break

            # 도구 실행
            tool_result = self._execute_selected_tool(tool_decision)
            used_tool_name = tool_decision.get("tool", "")

            if used_tool_name:
                all_used_tools.append(used_tool_name)

            accumulated_results.append(
                {
                    "step": iteration + 1,
                    "tool": used_tool_name,
                    "query": current_query,
                    "result": tool_result,
                }
            )

            # 다음 단계 질의 생성
            next_query = self._generate_next_query(user_input, accumulated_results)
            if not next_query or next_query == current_query:
                logger.info(f"다음 단계 질의가 없어 종료")
                break

            current_query = next_query

        # 최종 응답 생성
        final_response = self._generate_chain_response(user_input, accumulated_results)
        return final_response, all_used_tools

    def _ai_select_next_tool(
        self, current_query: str, previous_results: list, step: int
    ):
        """다음 단계에서 사용할 도구를 AI가 지능적으로 결정"""
        try:
            # 도구 설명 수집
            tools_info = []
            for tool in self.tools:
                desc = getattr(tool, "description", tool.name)
                tools_info.append(f"- {tool.name}: {desc}")

            tools_list = "\n".join(tools_info)

            # 이전 결과 요약
            previous_summary = ""
            if previous_results:
                previous_summary = "\n\nPrevious steps:\n"
                for result in previous_results:
                    result_preview = (
                        str(result["result"])[:200] + "..."
                        if len(str(result["result"])) > 200
                        else str(result["result"])
                    )
                    previous_summary += f"Step {result['step']}: Used {result['tool']} -> {result_preview}\n"

            selection_prompt = f"""Current query: "{current_query}"
Step: {step + 1}

{previous_summary}

Available tools:
{tools_list}

Analyze the current query and previous results. Determine if additional information is needed to fully answer the user's request.

Think about:
- What information does the user ultimately want?
- What gaps exist in the current results?
- Which tool could provide the missing information?
- Are the results sufficient to answer the original question?

Response format:
- Use tool: TOOL: tool_name | PARAMS: {{"key": "value"}}
- No more tools needed: TOOL: none

Use your judgment to select the most appropriate tool and extract relevant parameters from the available information."""

            messages = [
                SystemMessage(
                    content="You are an intelligent assistant that can analyze information gaps and select appropriate tools to gather missing data. Use your reasoning to determine what additional information would be valuable to complete the user's request. When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row."
                ),
                HumanMessage(content=selection_prompt),
            ]

            response = self.llm.invoke(messages)
            return self._parse_tool_decision(response.content)

        except Exception as e:
            logger.error(f"AI 다음 도구 선택 오류: {e}")
            return None

    def _generate_next_query(
        self, original_query: str, accumulated_results: list
    ) -> str:
        """다음 단계 질의 생성"""
        try:
            results_summary = "\n".join(
                [
                    f"Step {r['step']}: {r['tool']} -> {str(r['result'])[:300]}..."
                    for r in accumulated_results
                ]
            )

            prompt = f"""Original user query: "{original_query}"

Results so far:
{results_summary}

Analyze what information is still missing to fully satisfy the user's request. 

If additional specific information is needed, generate a focused query for the next step.
If the current results are sufficient to answer the original query, respond with "COMPLETE".

Next query:"""

            messages = [
                SystemMessage(
                    content="You are an intelligent assistant that can identify information gaps and determine what additional data is needed to complete a user's request. When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row."
                ),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            next_query = response.content.strip()

            if "COMPLETE" in next_query.upper():
                return None

            return next_query

        except Exception as e:
            logger.error(f"다음 질의 생성 오류: {e}")
            return None

    def _generate_chain_response(
        self, original_query: str, accumulated_results: list
    ) -> str:
        """연쇄적 도구 사용 결과를 바탕으로 최종 응답 생성"""
        try:
            if not accumulated_results:
                return self.simple_chat(original_query)

            # 모든 결과 합치기
            all_results = "\n\n".join(
                [
                    f"Step {r['step']} ({r['tool']}):\n{r['result']}"
                    for r in accumulated_results
                ]
            )

            response_prompt = f"""User's original request: "{original_query}"

Information gathered through multiple tools:
{all_results}

Your task:
1. Synthesize all the information to provide a comprehensive answer
2. Organize the information logically and clearly
3. Focus on what the user actually wanted to know
4. Present the information in a natural, conversational Korean format
5. If location information is available, include addresses and coordinates
6. If business information is available, include names, addresses, and contact details

Provide a helpful, well-organized response in Korean that directly addresses the user's original request."""

            messages = [
                SystemMessage(
                    content="You are an expert at synthesizing information from multiple sources to provide comprehensive answers in Korean. When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row."
                ),
                HumanMessage(content=response_prompt),
            ]

            response = self.llm.invoke(messages)
            return self._format_response(response.content)

        except Exception as e:
            logger.error(f"체인 응답 생성 오류: {e}")
            return self._format_response(
                "여러 도구를 사용하여 정보를 수집했지만 최종 응답 생성 중 오류가 발생했습니다."
            )

    def _perplexity_tool_chat(self, user_input: str) -> tuple[str, list]:
        """퍼플렉시티 모델용 AI 기반 도구 선택 및 실행 - 연쇄적 도구 사용 지원"""
        try:
            if self._is_tool_list_request(user_input):
                return self._show_tool_list(), []

            # 직접 에이전트 실행기 생성 및 실행 시도
            try:
                logger.info("🔧 퍼플렉시티 에이전트 실행기 생성 시작")
                agent_create_start = time.time()
                agent_executor = self._create_agent_executor()
                logger.info(
                    f"🔧 퍼플렉시티 에이전트 실행기 생성 완료: {time.time() - agent_create_start:.2f}초"
                )
                
                if not agent_executor:
                    return "사용 가능한 도구가 없습니다.", []
                
                logger.info("🔧 퍼플렉시티 에이전트 실행 시작")
                agent_invoke_start = time.time()
                result = agent_executor.invoke({"input": user_input})
                logger.info(
                    f"🔧 퍼플렉시티 에이전트 실행 완료: {time.time() - agent_invoke_start:.2f}초"
                )
                
                output = result.get("output", "")
                
                # 사용된 도구 정보 추출
                used_tools = []
                if "intermediate_steps" in result:
                    for step in result["intermediate_steps"]:
                        if len(step) >= 2 and hasattr(step[0], "tool"):
                            used_tools.append(step[0].tool)
                
                if "Agent stopped" in output or not output.strip():
                    logger.warning("퍼플렉시티 에이전트 중단 감지, 결과 확인 중...")
                    
                    # 중간 단계에서 도구가 사용되었는지 확인
                    if "intermediate_steps" in result and result["intermediate_steps"]:
                        # 도구가 사용되었으면 마지막 도구 결과 확인
                        last_step = result["intermediate_steps"][-1]
                        if len(last_step) >= 2:
                            tool_result = last_step[1]
                            logger.info(f"도구 결과 발견: {str(tool_result)[:100]}...")
                            
                            # 도구 결과를 바탕으로 최종 응답 생성
                            final_response = self._generate_perplexity_final_response(user_input, str(tool_result))
                            return final_response, [last_step[0].tool]
                
                # 정상 출력이 있으면 그대로 반환
                if output.strip():
                    return output, used_tools
                
                # 출력이 없으면 연쇄적 도구 사용 시도
                logger.warning("퍼플렉시티 에이전트 출력 없음, 연쇄적 도구 사용 시도")
                return self._execute_perplexity_tool_chain(user_input)
                
            except Exception as agent_error:
                logger.error(f"퍼플렉시티 에이전트 실행 오류: {agent_error}, 연쇄적 도구 사용 시도")
                # 에이전트 실행 실패 시 연쇄적 도구 사용 시도
                return self._execute_perplexity_tool_chain(user_input)

        except Exception as e:
            logger.error(f"퍼플렉시티 도구 채팅 오류: {e}")
            return self.simple_chat(user_input), []

    def _execute_perplexity_tool_chain(
        self, user_input: str, max_iterations: int = 3
    ) -> tuple[str, list]:
        """퍼플렉시티 모델을 위한 연쇄적 도구 사용 실행"""
        all_used_tools = []
        accumulated_results = []
        current_query = user_input

        for iteration in range(max_iterations):
            logger.info(f"도구 체인 {iteration + 1}단계 시작: {current_query[:50]}...")

            # AI가 다음 도구 결정
            tool_decision = self._ai_select_perplexity_tool(
                current_query, accumulated_results, iteration
            )

            if not tool_decision or tool_decision.get("tool") == "none":
                logger.info(f"도구 체인 {iteration + 1}단계에서 종료")
                break

            # 도구 실행
            tool_result = self._execute_selected_tool(tool_decision)
            used_tool_name = tool_decision.get("tool", "")

            if used_tool_name:
                all_used_tools.append(used_tool_name)

            accumulated_results.append(
                {
                    "step": iteration + 1,
                    "tool": used_tool_name,
                    "query": current_query,
                    "result": tool_result,
                }
            )

            # 다음 단계 질의 생성
            next_query = self._generate_perplexity_next_query(
                user_input, accumulated_results
            )
            if not next_query or next_query == current_query:
                logger.info(f"다음 단계 질의가 없어 종료")
                break

            current_query = next_query

        # 최종 응답 생성
        final_response = self._generate_perplexity_chain_response(
            user_input, accumulated_results
        )
        return final_response, all_used_tools

    def _ai_select_perplexity_tool(
        self, current_query: str, previous_results: list, step: int
    ):
        """퍼플렉시티 모델을 위한 도구 선택"""
        try:
            # 도구 설명 수집
            tools_info = []
            for tool in self.tools:
                desc = getattr(tool, "description", tool.name)
                tools_info.append(f"- {tool.name}: {desc}")

            tools_list = "\n".join(tools_info)

            # 이전 결과 요약
            previous_summary = ""
            if previous_results:
                previous_summary = "\n\n이전 단계:\n"
                for result in previous_results:
                    result_preview = (
                        str(result["result"])[:200] + "..."
                        if len(str(result["result"])) > 200
                        else str(result["result"])
                    )
                    previous_summary += f"단계 {result['step']}: {result['tool']} 사용 -> {result_preview}\n"

            selection_prompt = f"""현재 질의: "{current_query}"
단계: {step + 1}

{previous_summary}

사용 가능한 도구:
{tools_list}

현재 질의와 이전 결과를 분석하여 사용자의 요청에 완전히 답변하는 데 필요한 추가 정보가 있는지 확인하세요.

고려할 사항:
- 사용자가 최종적으로 원하는 정보는 무엇인가?
- 현재 결과에서 어떤 정보가 부족한가?
- 어떤 도구가 부족한 정보를 제공할 수 있는가?
- 원래 질문에 답변하기에 결과가 충분한가?

응답 형식:
- 도구 사용: TOOL: tool_name | PARAMS: {{"key": "value"}}
- 더 이상 도구가 필요하지 않음: TOOL: none

가장 적절한 도구를 선택하고 사용 가능한 정보에서 관련 파라미터를 추출하세요."""

            # Perplexity 모델을 위한 특별한 시스템 프롬프트 추가
            mcp_system_prompt = SystemPrompts.get_perplexity_mcp_prompt()
            messages = [
                SystemMessage(content=mcp_system_prompt),
                HumanMessage(content=selection_prompt),
            ]

            response = self.llm.invoke(messages)
            return self._parse_tool_decision(response.content)

        except Exception as e:
            logger.error(f"Perplexity 도구 선택 오류: {e}")
            return None

    def _generate_perplexity_next_query(
        self, original_query: str, accumulated_results: list
    ) -> str:
        """퍼플렉시티 모델을 위한 다음 단계 질의 생성"""
        try:
            results_summary = "\n".join(
                [
                    f"단계 {r['step']}: {r['tool']} -> {str(r['result'])[:300]}..."
                    for r in accumulated_results
                ]
            )

            prompt = f"""원래 사용자 질의: "{original_query}"

지금까지의 결과:
{results_summary}

사용자의 요청을 완전히 충족시키기 위해 어떤 정보가 여전히 부족한지 분석하세요.

추가적인 구체적 정보가 필요하다면, 다음 단계를 위한 집중적인 질의를 생성하세요.
현재 결과가 원래 질의에 답변하기에 충분하다면, "COMPLETE"로 응답하세요.

다음 질의:"""

            # Perplexity 모델을 위한 특별한 시스템 프롬프트 추가
            mcp_system_prompt = SystemPrompts.get_perplexity_mcp_prompt()
            messages = [
                SystemMessage(content=mcp_system_prompt),
                HumanMessage(content=prompt),
            ]

            response = self.llm.invoke(messages)
            next_query = response.content.strip()

            if "COMPLETE" in next_query.upper():
                return None

            return next_query

        except Exception as e:
            logger.error(f"Perplexity 다음 질의 생성 오류: {e}")
            return None

    def _generate_perplexity_final_response(self, user_input: str, tool_result: str) -> str:
        """도구 결과를 바탕으로 퍼플렉시티 모델을 위한 최종 응답 생성"""
        try:
            # 도구 결과가 너무 길면 요약
            if len(tool_result) > 3000:
                tool_result = tool_result[:3000] + "...(생략)"

            response_prompt = f"""사용자 질문: "{user_input}"

도구에서 가져온 데이터:
{tool_result}

수행할 작업:
1. 사용자의 질문에 직접적으로 답변하는 가장 관련성 높은 정보 추출
2. 정보를 논리적이고 이해하기 쉽게 구성
3. 자연스러운 한국어로 친구에게 설명하듯 작성
4. 사용자가 실제로 알고 싶어하는 내용에 집중
5. 기술적 용어 없이 간결하고 명확한 문장 사용
6. 여러 정보가 있는 경우 가장 중요한 정보를 우선순위로 배치
7. 간단한 마크다운(## 제목, **강조**, - 글머리 기호)를 사용하여 응답 형식화
8. 형식을 최소화하고 깔끔하게 유지
9. 목록과 구조화된 데이터에 일관된 들여쓰기 사용

사용자가 알고 싶어했던 내용에 직접적으로 대응하는 마크다운 형식의 도움되고 자연스러운 한국어 응답을 제공하세요."""

            # Perplexity 모델을 위한 특별한 시스템 프롬프트 추가
            mcp_system_prompt = SystemPrompts.get_perplexity_mcp_prompt()
            messages = [
                SystemMessage(content=mcp_system_prompt),
                HumanMessage(content=response_prompt),
            ]

            response = self.llm.invoke(messages)
            return self._format_response(response.content)

        except Exception as e:
            logger.error(f"Perplexity 최종 응답 생성 오류: {e}")
            # 오류 발생 시 원본 도구 결과 반환
            return self._format_response(
                f"""도구 결과를 처리하는 중 오류가 발생했습니다. 원본 결과를 표시합니다:

{tool_result}"""
            )

    def _generate_perplexity_chain_response(
        self, original_query: str, accumulated_results: list
    ) -> str:
        """퍼플렉시티 모델을 위한 연쇄적 도구 사용 결과를 바탕으로 최종 응답 생성"""
        try:
            if not accumulated_results:
                return self.simple_chat(original_query)

            # 모든 결과 합치기
            all_results = "\n\n".join(
                [
                    f"단계 {r['step']} ({r['tool']}):\n{r['result']}"
                    for r in accumulated_results
                ]
            )

            # 결과가 너무 길면 요약
            if len(all_results) > 3000:
                all_results = all_results[:3000] + "...(생략)"

            response_prompt = f"""사용자의 원래 요청: "{original_query}"

여러 도구를 통해 수집한 정보:
{all_results}

수행할 작업:
1. 모든 정보를 종합하여 포괄적인 답변 제공
2. 정보를 논리적이고 명확하게 구성
3. 사용자가 실제로 알고 싶어했던 내용에 집중
4. 자연스러운 한국어 형식으로 정보 제공
5. 위치 정보가 있는 경우 주소와 좌표 포함
6. 비즈니스 정보가 있는 경우 이름, 주소, 연락처 포함

사용자의 원래 요청에 직접적으로 대응하는 도움이 되고 잘 구성된 한국어 응답을 제공하세요."""

            # Perplexity 모델을 위한 특별한 시스템 프롬프트 추가
            mcp_system_prompt = SystemPrompts.get_perplexity_mcp_prompt()
            messages = [
                SystemMessage(content=mcp_system_prompt),
                HumanMessage(content=response_prompt),
            ]

            response = self.llm.invoke(messages)
            return self._format_response(response.content)

        except Exception as e:
            logger.error(f"Perplexity 체인 응답 생성 오류: {e}")
            # 오류 발생 시 마지막 도구 결과 반환
            if accumulated_results:
                last_result = accumulated_results[-1]['result']
                return self._format_response(
                    f"""여러 도구를 사용하여 정보를 수집했지만 최종 응답 생성 중 오류가 발생했습니다. 마지막 도구 결과를 표시합니다:

{last_result}"""
                )
            else:
                return self._format_response(
                    "여러 도구를 사용하여 정보를 수집했지만 최종 응답 생성 중 오류가 발생했습니다."
                )
