from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from .base_model_strategy import BaseModelStrategy
from ui.prompts import prompt_manager, ModelType
from core.token_logger import TokenLogger
import logging

logger = logging.getLogger(__name__)


class OpenAIStrategy(BaseModelStrategy):
    """OpenAI GPT 모델 전략"""
    
    def create_llm(self):
        """OpenAI LLM 생성"""
        return ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.api_key,
            temperature=0.1,
            max_tokens=4096,
        )
    
    def create_messages(self, user_input: str, system_prompt: str = None, conversation_history: List[Dict] = None) -> List[BaseMessage]:
        """OpenAI 메시지 형식 생성 - 대화 히스토리 포함"""
        messages = []
        
        # 사용자 입력에서 언어 감지 (원본 텍스트만 사용)
        user_language = self.detect_user_language(user_input)
        
        # 시스템 프롬프트 생성
        if system_prompt:
            enhanced_prompt = self.enhance_prompt_with_format(system_prompt)
        else:
            enhanced_prompt = self.get_default_system_prompt()
        
        # 언어별 응답 지침 추가
        if user_language == "ko":
            enhanced_prompt += "\n\n**중요**: 사용자가 한국어로 질문했으므로 반드시 한국어로 응답하세요."
        else:
            enhanced_prompt += "\n\n**Important**: The user asked in English, so please respond in English."
        
        messages.append(SystemMessage(content=enhanced_prompt))
        
        # 대화 히스토리를 실제 메시지로 변환 (시스템 프롬프트가 아닌 메시지로)
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
        """OpenAI 이미지 입력 처리"""
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
    
    def should_use_tools(self, user_input: str) -> bool:
        """OpenAI 모델의 도구 사용 여부 결정"""
        try:
            # 사용 가능한 도구 정보 수집
            available_tools = []
            if hasattr(self, 'tools') and self.tools:
                for tool in self.tools[:5]:  # 주요 도구 5개만
                    tool_desc = getattr(tool, 'description', tool.name)
                    available_tools.append(f"- {tool.name}: {tool_desc[:80]}")
            
            tools_info = "\n".join(available_tools) if available_tools else "사용 가능한 도구 없음"
            
            # 중앙관리 시스템에서 프롬프트 가져오기
            available_tools = getattr(self, 'tools', [])
            decision_prompt = prompt_manager.get_tool_decision_prompt(
                ModelType.OPENAI.value, user_input, available_tools
            )

            messages = [
                SystemMessage(content="You are an expert at analyzing user requests to determine if tools are needed."),
                HumanMessage(content=decision_prompt),
            ]

            response = self.llm.invoke(messages)
            decision = response.content.strip().upper()
            
            # 토큰 사용량 로깅
            TokenLogger.log_messages_token_usage(
                self.model_name, messages, decision, "tool_decision"
            )
            
            result = "YES" in decision
            logger.info(f"OpenAI AI 도구 사용 판단: '{user_input}' -> {decision} -> {result}")
            return result

        except Exception as e:
            logger.error(f"Tool usage decision error: {e}")
            return False
    
    def create_agent_executor(self, tools: List) -> Optional[AgentExecutor]:
        """OpenAI 도구 에이전트 생성"""
        if not tools:
            return None
        
        # 중앙관리 시스템에서 에이전트 시스템 프롬프트 가져오기
        system_message = prompt_manager.get_agent_system_prompt(ModelType.OPENAI.value)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_tools_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            max_execution_time=30,
            early_stopping_method="force",
            handle_parsing_errors="Check your output and make sure you are not providing both an Action and a Final Answer at the same time. Either provide an Action to use a tool, or provide a Final Answer to respond to the user.",
            return_intermediate_steps=True,
        )
    
    def _get_ocr_prompt(self) -> str:
        """OCR 전용 프롬프트"""
        return prompt_manager.get_ocr_prompt()