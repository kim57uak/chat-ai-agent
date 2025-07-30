from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from .base_model_strategy import BaseModelStrategy
from ui.prompts import prompt_manager, ModelType
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
    
    def create_messages(self, user_input: str, system_prompt: str = None, conversation_history: List[Dict] = None) -> List[BaseMessage]:
        """Gemini 메시지 형식 생성 - 대화 히스토리 포함"""
        messages = []
        
        # 시스템 프롬프트 추가
        if system_prompt:
            enhanced_prompt = self.enhance_prompt_with_format(system_prompt)
        else:
            enhanced_prompt = self.get_default_system_prompt()
        
        # 대화 히스토리가 있으면 시스템 프롬프트에 컨텍스트 추가
        if conversation_history:
            history_context = self._format_conversation_history(conversation_history)
            enhanced_prompt += f"\n\n**Previous Conversation Context:**\n{history_context}\n\nPlease consider this conversation history when responding."
        
        messages.append(HumanMessage(content=enhanced_prompt))
        
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
    
    def _format_conversation_history(self, conversation_history: List[Dict]) -> str:
        """대화 히스토리를 텍스트로 포맷팅"""
        formatted_history = []
        for msg in conversation_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                formatted_history.append(f"User: {content}")
            elif role in ["assistant", "agent"]:
                formatted_history.append(f"Assistant: {content}")
        
        return "\n".join(formatted_history)
    
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
                decision_prompt += "\n\nIMPORTANT: The user has specifically selected Agent mode, indicating they want to use available tools when possible. Be more inclined to use tools for information gathering, searches, or data processing tasks."
            
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
        
        # 중앙관리 시스템에서 에이전트 시스템 프롬프트 가져오기
        agent_system_prompt = prompt_manager.get_agent_system_prompt(ModelType.GOOGLE.value)
        
        # Gemini는 ReAct 에이전트만 지원
        react_prompt = PromptTemplate.from_template(
            f"""{agent_system_prompt}

Available tools:
{{tools}}

Tool names: {{tool_names}}

Question: {{input}}
{{agent_scratchpad}}
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
            early_stopping_method="force",
            return_intermediate_steps=True,
        )
    
    def _get_ocr_prompt(self) -> str:
        """OCR 전용 프롬프트"""
        return prompt_manager.get_ocr_prompt()