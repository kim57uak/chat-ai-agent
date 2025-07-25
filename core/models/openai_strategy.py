from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from .base_model_strategy import BaseModelStrategy
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
    
    def create_messages(self, user_input: str, system_prompt: str = None) -> List[BaseMessage]:
        """OpenAI 메시지 형식 생성"""
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        else:
            messages.append(SystemMessage(content=self.get_default_system_prompt()))
        
        messages.append(HumanMessage(content=user_input))
        return messages
    
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
            decision_prompt = f"""User request: "{user_input}". You must end with "Action" or "Final Answer."

Determine if this request requires using tools to provide accurate information.

Requires tools:
- Real-time information search (web search, news, weather, etc.)
- Database queries (travel products, flights, etc.)
- External API calls (maps, translation, etc.)
- File processing or calculations
- Current time or date-related information
- Specific data lookups or searches
- Location-based queries

Does not require tools:
- General conversation or questions
- Explanations or opinions
- Creative writing or idea suggestions
- General knowledge already known

Answer: YES or NO only."""

            messages = [
                SystemMessage(content="You are an expert at analyzing user requests to determine if tools are needed."),
                HumanMessage(content=decision_prompt),
            ]

            response = self.llm.invoke(messages)
            decision = response.content.strip().upper()
            
            result = "YES" in decision
            logger.info(f"Tool usage decision: {decision} -> {result}")
            return result

        except Exception as e:
            logger.error(f"Tool usage decision error: {e}")
            return False
    
    def create_agent_executor(self, tools: List) -> Optional[AgentExecutor]:
        """OpenAI 도구 에이전트 생성"""
        if not tools:
            return None
        
        system_message = """You are a helpful AI assistant that can use various tools to provide accurate information.

**Instructions:**
- Analyze user requests carefully to select the most appropriate tools
- Use tools to gather current, accurate information when needed
- Organize information in a clear, logical structure
- Respond in natural, conversational Korean
- Be friendly and helpful while maintaining accuracy
- If multiple tools are needed, use them systematically
- Focus on providing exactly what the user asked for

**TABLE FORMAT RULES**: When creating tables, ALWAYS use proper markdown table format with pipe separators and header separator row.

**Response Format:**
- Use clear headings and bullet points when appropriate
- Format information in a structured, readable way
- Always end your response with either an Action or Final Answer
- ONLY SHOW THE FINAL ANSWER TO THE USER - HIDE ALL THOUGHT PROCESSES"""

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
            max_iterations=2,
            handle_parsing_errors=True,
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