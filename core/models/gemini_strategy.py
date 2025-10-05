from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from .base_model_strategy import BaseModelStrategy
from ui.prompts import prompt_manager, ModelType
from core.token_logger import TokenLogger
from core.token_tracker import token_tracker, StepType
from core.parsers.custom_react_parser import CustomReActParser
import logging

logger = logging.getLogger(__name__)


class GeminiStrategy(BaseModelStrategy):
    """Google Gemini 모델 전략"""
    
    def create_llm(self):
        """Gemini LLM 생성"""
        # Pro 모델의 경우 더 긴 타임아웃과 더 많은 재시도
        if "pro" in self.model_name.lower():
            max_tokens = 32768
            max_retries = 5
            request_timeout = 60
        else:
            max_tokens = 16384
            max_retries = 3
            request_timeout = 30
        
        llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.1,
            convert_system_message_to_human=True,
            max_tokens=max_tokens,
            max_retries=max_retries,
            request_timeout=request_timeout,
        )
        
        # 토큰 사용량 추적을 위한 콜백 설정
        self._setup_token_tracking_callbacks(llm)
        return llm
    
    def _setup_token_tracking_callbacks(self, llm):
        """토큰 사용량 추적을 위한 콜백 설정 - 단순화"""
        # Pydantic 모델의 제약사항으로 인해 단순히 전략 객체에 참조만 저장
        self._tracked_llm = llm
        pass
    
    def create_messages(self, user_input: str, system_prompt: str = None, conversation_history: List[Dict] = None) -> List[BaseMessage]:
        """Gemini 메시지 형식 생성 - 대화 히스토리 포함"""
        messages = []
        
        # 사용자 입력에서 언어 감지 (원본 텍스트만 사용)
        user_language = self.detect_user_language(user_input)
        
        # 시스템 프롬프트 추가
        if system_prompt:
            enhanced_prompt = self.enhance_prompt_with_format(system_prompt)
        else:
            enhanced_prompt = self.get_default_system_prompt()
        
        # 언어별 응답 지침 추가
        if user_language == "ko":
            enhanced_prompt += "\n\n**중요**: 사용자가 한국어로 질문했으므로 반드시 한국어로 응답하세요."
        else:
            enhanced_prompt += "\n\n**Important**: The user asked in English, so please respond in English."
        
        # 대화 히스토리 컨텍스트 추가
        if conversation_history:
            history_context = self._format_conversation_history(conversation_history)
            if user_language == "ko":
                enhanced_prompt += (
                    f"\n\n## 💬 이전 대화:\n"
                    f"{history_context}\n\n"
                    f"ℹ️ 이 대화 내역을 고려하여 응답해주세요."
                )
            else:
                enhanced_prompt += (
                    f"\n\n## 💬 Previous Conversation:\n"
                    f"{history_context}\n\n"
                    f"ℹ️ Please consider this conversation history when responding."
                )
        
        messages.append(HumanMessage(content=enhanced_prompt))
        
        # 대화 히스토리를 실제 메시지로 변환
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user" and isinstance(content, str) and content.strip():
                    messages.append(HumanMessage(content=content))
                elif role in ["assistant", "agent"] and isinstance(content, str) and content.strip():
                    messages.append(AIMessage(content=content))
        
        # 현재 사용자 입력 추가
        messages.append(HumanMessage(content=user_input))
        return messages
    
    def _format_conversation_history(self, conversation_history: List[Dict]) -> str:
        """대화 히스토리를 가독성 좋게 포맷팅"""
        formatted_history = []
        for i, msg in enumerate(conversation_history, 1):
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                formatted_history.append(f"**[{i}] 👤 User:** {content}")
            elif role in ["assistant", "agent"]:
                formatted_history.append(f"**[{i}] 🤖 Assistant:** {content}")
        
        return "\n\n".join(formatted_history)
    
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
            
            # 중앙관리 시스템에서 프롬프트 가져오기
            available_tools = getattr(self, 'tools', [])
            decision_prompt = prompt_manager.get_tool_decision_prompt(
                ModelType.GOOGLE.value, user_input, available_tools
            )
            
            # Agent 모드 컨텍스트 추가
            if force_agent:
                decision_prompt += (
                    "\n\n## 🔧 Agent Mode Active\n"
                    "User selected Agent mode - be more inclined to use tools for:\n"
                    "- Information gathering\n"
                    "- Searches and data processing\n"
                    "- External API calls"
                )
            
            # Gemini 메시지 구성
            messages = [
                HumanMessage(content=(
                    "# Tool Decision Expert\n\n"
                    "You analyze user requests to determine if tools are needed.\n\n"
                    "ℹ️ **Important:** When creating tables, use proper markdown format with pipe separators."
                )),
                HumanMessage(content=decision_prompt),
            ]
            
            # 도구 결정 단계 시작
            token_tracker.start_step(StepType.TOOL_DECISION, "Gemini Tool Decision")
            
            llm_start = time.time()
            response = self.llm.invoke(messages)
            llm_elapsed = time.time() - llm_start
            decision = response.content.strip().upper()
            
            # 응답 객체 저장 (토큰 추출용)
            self._last_response = response
            
            # 도구 결정 단계 종료
            input_text = "\n".join([str(msg.content) for msg in messages])
            token_tracker.end_step(
                StepType.TOOL_DECISION,
                "Gemini Tool Decision",
                input_text=input_text,
                output_text=decision,
                response_obj=response,
                additional_info={"force_agent": force_agent}
            )
            
            # 기존 로깅
            TokenLogger.log_messages_token_usage(
                self.model_name, messages, decision, "tool_decision"
            )
            
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
        """Gemini ReAct 에이전트 생성 (모델별 프롬프트 분기)"""
        if not tools:
            return None
        
        # 중앙 관리 시스템에서 시스템 프롬프트 가져오기 (날짜 정보 포함)
        base_system_prompt = prompt_manager.get_system_prompt(ModelType.GOOGLE.value, use_tools=True)
        
        # 모델별 ReAct 형식 가이드 추가
        if "pro" in self.model_name.lower():
            react_guide = (
                "\n\n## 🚨 CRITICAL: Every response MUST start with a keyword\n\n"
                "### Required Keywords:\n"
                "- `Thought:` [your reasoning]\n"
                "- `Action:` [exact_tool_name]\n"
                "- `Action Input:` [json_parameters]\n"
                "- `Final Answer:` [complete response with tables/content]\n\n"
                "### ✅ Correct Examples:\n"
                "```\n"
                "Final Answer: Here are the search results.\n"
                "| Product | Price |\n"
                "```\n\n"
                "### 📏 Response Length Control:\n"
                "- Keep Final Answer under 16384 tokens to prevent parsing errors\n"
                "- If data is large, provide summary with key statistics\n"
                "- Always prioritize essential information over details\n\n"
                "**Rule: Follow ReAct format - Thought → Action → Action Input → Final Answer**"
            )
        else:
            react_guide = (
                "\n\n## Google Gemini ReAct Format\n\n"
                "### Step 1 - Tool Use:\n"
                "`Thought:` [your reasoning]\n"
                "`Action:` [exact_tool_name]\n"
                "`Action Input:` [json_params]\n\n"
                "### Step 2 - After Observation:\n"
                "`Thought:` [analyze the observation result]\n"
                "`Final Answer:` [response based on observation]\n\n"
                "### 🚨 Critical Rules:\n"
                "- Never skip Observation\n"
                "- Never mix steps\n"
                "- Use exact tool names from schema\n"
                "- Wait for system Observation before Final Answer\n"
                "- Keep Final Answer under 16384 tokens (summarize if needed)"
            )
        
        agent_system_prompt = base_system_prompt + react_guide
        
        # Gemini는 ReAct 에이전트만 지원
        if "pro" in self.model_name.lower():
            # Pro 모델용 강력한 파싱 템플릿
            react_prompt = PromptTemplate.from_template(
                f"""# 🚨 Parsing Rule: Start every response with a keyword

{agent_system_prompt}

## Available Tools:
{{tools}}

## Tool Names:
{{tool_names}}

## Process:
1. **First**: `Thought:` → `Action:` → `Action Input:`
2. **Wait for Observation**
3. **Then**: `Thought:` → `Final Answer:`

---
**Question:** {{input}}
{{agent_scratchpad}}"""
            )
        else:
            # Flash 및 기타 모델용 기존 템플릿 (가독성 개선)
            react_prompt = PromptTemplate.from_template(
                f"""# Google Gemini ReAct Agent

{agent_system_prompt}

## Available Tools:
{{tools}}

## Tool Names:
{{tool_names}}

## Example Process:
**Step 1:**
```
Thought: I need to use a tool
Action: [exact_tool_name_from_list]
Action Input: {{{{"param": "value"}}}}
```

**Step 2 (After Observation):**
```
Thought: [analyze the observation result]
Final Answer: [response based on observation]
```

⚠️ **Important:** Never output content directly! Always use Final Answer format!

---
**Question:** {{input}}
{{agent_scratchpad}}"""
            )

        # 커스텀 파서 사용
        custom_parser = CustomReActParser()
        agent = create_react_agent(self.llm, tools, react_prompt, output_parser=custom_parser)
        
        # Pro 모델의 경우 더 긴 시간과 더 많은 반복 허용
        if "pro" in self.model_name.lower():
            max_iterations = 8
            max_execution_time = 60
        else:
            max_iterations = 5
            max_execution_time = 30
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=max_iterations,
            max_execution_time=max_execution_time,
            handle_parsing_errors=True,  # 커스텀 파서가 처리
            early_stopping_method="force",
            return_intermediate_steps=True,
        )
    
    def _get_ocr_prompt(self) -> str:
        """OCR 전용 프롬프트"""
        return prompt_manager.get_ocr_prompt()