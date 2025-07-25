from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from .base_model_strategy import BaseModelStrategy
import logging

logger = logging.getLogger(__name__)


class GeminiStrategy(BaseModelStrategy):
    """Google Gemini 모델 전략"""
    
    def create_llm(self):
        """Gemini LLM 생성"""
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.1,
            convert_system_message_to_human=True,
            max_tokens=4096,
        )
    
    def create_messages(self, user_input: str, system_prompt: str = None) -> List[BaseMessage]:
        """Gemini 메시지 형식 생성 (시스템 메시지를 인간 메시지로 변환)"""
        messages = []
        
        if system_prompt:
            messages.append(HumanMessage(content=system_prompt))
        else:
            messages.append(HumanMessage(content=self.get_default_system_prompt()))
        
        messages.append(HumanMessage(content=user_input))
        return messages
    
    def process_image_input(self, user_input: str) -> BaseMessage:
        """Gemini 이미지 입력 처리"""
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
    
    def should_use_tools(self, user_input: str, force_agent: bool = False) -> bool:
        """Gemini가 자연어를 이해하여 도구 사용 여부를 지능적으로 결정"""
        import time
        
        start_time = time.time()
        logger.info(f"🤔 Gemini 도구 사용 판단 시작: {user_input[:30]}...")
        
        # Agent 모드가 강제된 경우 항상 도구 사용
        if force_agent:
            logger.info("🔧 Agent 모드가 강제되어 도구를 사용합니다")
            return True
        
        try:
            # 사용 가능한 도구 정보 수집
            available_tools = []
            if hasattr(self, 'tools') and self.tools:
                for tool in self.tools[:5]:  # 주요 도구 5개만
                    tool_desc = getattr(tool, 'description', tool.name)
                    available_tools.append(f"- {tool.name}: {tool_desc[:80]}")
            
            tools_info = "\n".join(available_tools) if available_tools else "사용 가능한 도구 없음"
            
            # Agent 모드 선택 시 더 적극적인 판단 기준 적용
            agent_context = ""
            if force_agent:
                agent_context = "\n\nIMPORTANT: The user has specifically selected Agent mode, indicating they want to use available tools when possible. Be more inclined to use tools for information gathering, searches, or data processing tasks."
            
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
- Opinion-based discussions{agent_context}

Answer: YES or NO only."""
            
            # Gemini는 시스템 메시지를 인간 메시지로 변환
            messages = [
                HumanMessage(content="You are an expert at analyzing user requests to determine if tools are needed. When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row."),
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
                f"🤔 Gemini 도구 사용 판단{mode_info}: {decision} -> {result} (LLM: {llm_elapsed:.2f}초, 총: {total_elapsed:.2f}초)"
            )
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ Gemini 도구 사용 판단 오류: {elapsed:.2f}초, 오류: {e}")
            return False
    
    def create_agent_executor(self, tools: List) -> Optional[AgentExecutor]:
        """Gemini ReAct 에이전트 생성 (도구 호환성 개선)"""
        if not tools:
            return None
        
        # Gemini는 ReAct 에이전트만 지원
        react_prompt = PromptTemplate.from_template(
            """You are a helpful AI assistant that can use various tools to provide accurate information.

**CRITICAL PARSING RULES:**
1. NEVER output both Action and Final Answer in the same response
2. Follow EXACT format: Thought -> Action -> Action Input -> (wait for Observation) -> Thought -> Final Answer
3. Each step must be on a separate line
4. Use EXACT keywords: "Thought:", "Action:", "Action Input:", "Final Answer:"
5. Do NOT include "Observation:" - it will be added automatically

Available tools:
{tools}

Tool names: {tool_names}

**STRICT FORMAT:**
Thought: [your reasoning]
Action: [exact_tool_name]
Action Input: [input_for_tool]

(System will add Observation automatically)

Thought: [analyze the observation]
Final Answer: [your response in Korean]

**EXAMPLE:**
Question: Show me files in /home
Thought: I need to list directory contents to show the user what files are in /home.
Action: filesystem_list_directory
Action Input: /home

(After receiving observation:)
Thought: Now I have the directory listing and can provide a formatted response to the user.
Final Answer: /home 디렉토리에는 다음 파일들이 있습니다: [formatted list]

Question: {input}
{agent_scratchpad}
            """
        )

        agent = create_react_agent(self.llm, tools, react_prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            max_execution_time=30,
            handle_parsing_errors="Invalid format! You must follow the exact format: Thought -> Action -> Action Input. Do NOT include both Action and Final Answer in the same response.",
            early_stopping_method="generate",
            return_intermediate_steps=True,
        )
    
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