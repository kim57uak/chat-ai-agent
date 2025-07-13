from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import logging
import re
import base64

logger = logging.getLogger(__name__)


class ChatProcessor(ABC):
    """채팅 처리를 위한 추상 클래스"""
    
    @abstractmethod
    def process_chat(self, user_input: str, llm: Any, conversation_history: List[Dict] = None) -> str:
        pass


class SimpleChatProcessor(ChatProcessor):
    """단순 채팅 처리기"""
    
    def process_chat(self, user_input: str, llm: Any, conversation_history: List[Dict] = None) -> str:
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
            model_name = getattr(llm, 'model_name', str(llm))
            if 'gemini' in model_name.lower():
                messages = [HumanMessage(content=system_content)]
            else:
                messages = [SystemMessage(content=system_content)]

            # 대화 히스토리 추가
            if conversation_history:
                messages.extend(self._convert_history_to_messages(conversation_history, model_name))

            # 이미지 데이터 처리
            if "[IMAGE_BASE64]" in user_input and "[/IMAGE_BASE64]" in user_input:
                processed_input = self._process_image_input(user_input, model_name)
                messages.append(processed_input)
            else:
                messages.append(HumanMessage(content=user_input))

            response = llm.invoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"일반 채팅 오류: {e}")
            return f"죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요."
    
    def _convert_history_to_messages(self, conversation_history: List[Dict], model_name: str):
        """대화 기록을 LangChain 메시지로 변환"""
        messages = []
        
        # 최근 대화 기록 사용
        recent_history = (
            conversation_history[-6:]
            if len(conversation_history) > 6
            else conversation_history
        )

        for msg in recent_history:
            role = msg.get("role", "")
            content = msg.get("content", "")[:500]  # 내용 제한
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        return messages
    
    def _process_image_input(self, user_input: str, model_name: str):
        """이미지 데이터를 처리하여 LangChain 메시지로 변환"""
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
            text_content = """Please **extract all text accurately (OCR)** from this image.

**Required Tasks:**
1. **Complete Text Extraction**: Extract all Korean, English, numbers, and symbols without omission
2. **Structure Analysis**: Identify document structures like tables, lists, headings, paragraphs
3. **Layout Information**: Describe text position, size, and arrangement relationships
4. **Accurate Transcription**: Record all characters precisely without typos
5. **Context Description**: Identify document type and purpose

**Response Format:**
## 📄 Extracted Text
[List all text accurately]

## 📋 Document Structure
[Describe structure of tables, lists, headings, etc.]

## 📍 Layout Information
[Text arrangement and positional relationships]

**Important**: Please extract all readable text from the image completely without any omissions."""

        try:
            # Gemini 모델의 경우 특별한 형식 사용
            if 'gemini' in model_name.lower():
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


class ToolChatProcessor(ChatProcessor):
    """도구 사용 채팅 처리기"""
    
    def __init__(self, tools: List[Any], agent_executor_factory):
        self.tools = tools
        self.agent_executor_factory = agent_executor_factory
        self.agent_executor = None
    
    def process_chat(self, user_input: str, llm: Any, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """도구를 사용한 채팅"""
        import time
        start_time = time.time()
        logger.info(f"🚀 도구 채팅 시작: {user_input[:50]}...")
        
        try:
            # 토큰 제한 오류 방지를 위해 대화 히스토리 제한
            if "context_length_exceeded" in str(getattr(self, "_last_error", "")):
                logger.warning("토큰 제한 오류로 인해 일반 채팅으로 대체")
                simple_processor = SimpleChatProcessor()
                return simple_processor.process_chat(user_input, llm), []

            # Gemini 모델은 직접 도구 호출 방식 사용
            model_name = getattr(llm, 'model_name', str(llm))
            if 'gemini' in model_name.lower():
                logger.info("🔧 Gemini 도구 채팅 시작")
                gemini_start = time.time()
                result = self._gemini_tool_chat(user_input, llm)
                logger.info(f"🔧 Gemini 도구 채팅 완료: {time.time() - gemini_start:.2f}초")
                return result

            # GPT 모델은 기존 에이전트 방식 사용
            if not self.agent_executor:
                logger.info("🔧 에이전트 실행기 생성 시작")
                agent_create_start = time.time()
                self.agent_executor = self.agent_executor_factory.create_agent_executor(llm, self.tools)
                logger.info(f"🔧 에이전트 실행기 생성 완료: {time.time() - agent_create_start:.2f}초")

            if not self.agent_executor:
                return "사용 가능한 도구가 없습니다.", []

            logger.info("🔧 에이전트 실행 시작")
            agent_invoke_start = time.time()
            result = self.agent_executor.invoke({"input": user_input})
            logger.info(f"🔧 에이전트 실행 완료: {time.time() - agent_invoke_start:.2f}초")
            output = result.get("output", "")

            # 사용된 도구 정보 추출
            used_tools = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) >= 2 and hasattr(step[0], "tool"):
                        used_tools.append(step[0].tool)

            if "Agent stopped" in output or not output.strip():
                logger.warning("에이전트 중단로 인해 일반 채팅으로 대체")
                simple_processor = SimpleChatProcessor()
                return simple_processor.process_chat(user_input, llm), []

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
                simple_processor = SimpleChatProcessor()
                return simple_processor.process_chat(user_input, llm), []

            simple_processor = SimpleChatProcessor()
            return simple_processor.process_chat(user_input, llm), []
    
    def _gemini_tool_chat(self, user_input: str, llm: Any) -> Tuple[str, List]:
        """Gemini 모델용 도구 채팅 (간단한 구현)"""
        # 실제 구현은 기존 로직을 참조하여 작성
        return f"Gemini 도구 채팅 결과: {user_input}", []