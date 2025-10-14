from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from .base_model_strategy import BaseModelStrategy
from ui.prompts import prompt_manager, ModelType
from core.token_logger import TokenLogger
from core.token_tracker import token_tracker, StepType
from core.logging import get_logger

logger = get_logger("openrouter_strategy")


class OpenRouterStrategy(BaseModelStrategy):
    """OpenRouter 모델 전략"""
    
    def create_llm(self):
        """OpenRouter LLM 생성"""
        params = self.get_model_parameters()
        
        llm = ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=params.get('temperature', 0.1),
            max_tokens=params.get('max_tokens', 4096),
            top_p=params.get('top_p', 0.9),
            frequency_penalty=params.get('frequency_penalty', 0.0),
            presence_penalty=params.get('presence_penalty', 0.0),
            stop=params.get('stop', None),
        )
        
        # 토큰 사용량 추적을 위한 콜백 설정
        self._setup_token_tracking_callbacks(llm)
        return llm
    
    def _setup_token_tracking_callbacks(self, llm):
        """토큰 사용량 추적을 위한 콜백 설정"""
        self._tracked_llm = llm
        pass
    
    def create_messages(self, user_input: str, system_prompt: str = None, conversation_history: List[Dict] = None) -> List[BaseMessage]:
        """OpenRouter 메시지 형식 생성 - 대화 히스토리 포함"""
        messages = []
        
        # 사용자 입력에서 언어 감지
        user_language = self.detect_user_language(user_input)
        
        # 시스템 프롬프트 생성 (언어 지침 포함)
        if system_prompt:
            enhanced_prompt = self.enhance_prompt_with_format(system_prompt)
        else:
            enhanced_prompt = self.get_default_system_prompt(user_language)
        
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
    
    def get_default_system_prompt(self, user_language: str = None) -> str:
        """기본 시스템 프롬프트 생성 (common + pollinations)"""
        # OpenRouter용 시스템 프롬프트 사용
        return prompt_manager.get_system_prompt(ModelType.OPENROUTER.value, use_tools=True, user_language=user_language)
    
    def should_use_tools(self, user_input: str) -> bool:
        """OpenRouter 모델의 도구 사용 여부 결정 - 토글 박스 값에 따라 결정"""
        return False
    
    def process_image_input(self, user_input: str) -> BaseMessage:
        """OpenRouter 이미지 입력 처리"""
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
    
    def _get_ocr_prompt(self) -> str:
        """OCR 전용 프롬프트"""
        return prompt_manager.get_ocr_prompt()
    
    def _test_function_calling_support(self) -> bool:
        """모델의 function calling 지원 여부 테스트"""
        # OpenRouter 모델에서는 일단 지원한다고 가정하고 시도
        # 실제 오류 발생 시에만 처리
        return True
    
    def create_agent_executor(self, tools: List) -> Optional[AgentExecutor]:
        """OpenRouter 도구 에이전트 생성 - function calling 지원 확인 후 생성"""
        if not tools:
            return None
        
        # function calling 지원 여부 사전 확인
        if not self._test_function_calling_support():
            logger.info(f"OpenRouter 모델 {self.model_name}는 도구 사용을 지원하지 않습니다. 일반 채팅 모드로 전환합니다.")
            return None
        
        try:
            # 중앙관리 시스템에서 에이전트 시스템 프롬프트 가져오기
            system_message = prompt_manager.get_agent_system_prompt(ModelType.OPENROUTER.value)
            
            if not system_message or system_message.strip() == "()":
                system_message = "You are a helpful AI assistant that can use various tools to help users. Always provide accurate and helpful responses."

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
        except Exception as e:
            logger.warning(f"OpenRouter 모델 {self.model_name}에서 도구 에이전트 생성 실패: {e}")
            return None