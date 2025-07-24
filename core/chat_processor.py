from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from core.enhanced_system_prompts import SystemPrompts
from core.file_utils import load_config
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
            # AI-driven system prompt selection based on content type
            if self._contains_image_data(user_input):
                system_content = SystemPrompts.get_image_analysis_prompt()
            else:
                system_content = SystemPrompts.get_general_chat_prompt()

            # Gemini 모델의 경우 시스템 메시지를 인간 메시지로 변환
            model_name = getattr(llm, 'model_name', str(llm))
            if 'gemini' in model_name.lower():
                messages = [HumanMessage(content=system_content)]
            else:
                messages = [SystemMessage(content=system_content)]

            # 대화 히스토리 추가 (순서 중요)
            if conversation_history:
                history_messages = self._convert_history_to_messages(conversation_history, model_name)
                messages.extend(history_messages)
                logger.info(f"대화 히스토리 사용: {len(history_messages)}개 메시지")
            else:
                logger.info("대화 히스토리 없음")

            # 이미지 데이터 처리
            if self._contains_image_data(user_input):
                processed_input = self._process_image_input(user_input, model_name)
                messages.append(processed_input)
            else:
                messages.append(HumanMessage(content=user_input))

            logger.info(f"총 메시지 수: {len(messages)}개")
            response = llm.invoke(messages)
            response_content = response.content
            
            return response_content

        except Exception as e:
            logger.error(f"일반 채팅 오류: {e}")
            return f"죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요."
    
    def _convert_history_to_messages(self, conversation_history: List[Dict], model_name: str):
        """대화 기록을 LangChain 메시지로 변환"""
        messages = []
        
        # 대화 기록이 비어있으면 빈 리스트 반환
        if not conversation_history:
            return messages
        
        # 최근 대화 기록 사용 (더 많이 포함)
        recent_history = (
            conversation_history[-10:]
            if len(conversation_history) > 10
            else conversation_history
        )

        for msg in recent_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # 내용이 비어있으면 건너뛰기
            if not content or not content.strip():
                continue
                
            # 내용 제한을 더 늘리고 중요한 내용은 유지
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        logger.info(f"대화 기록 변환 완료: {len(recent_history)}개 -> {len(messages)}개 메시지")
        return messages
    
    def _contains_image_data(self, user_input: str) -> bool:
        """Check if input contains image data"""
        return "[IMAGE_BASE64]" in user_input and "[/IMAGE_BASE64]" in user_input
    
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

        # AI-driven image analysis prompt
        if not text_content:
            text_content = """Analyze this image comprehensively and extract all information.

**Analysis Tasks:**
1. **Complete Text Extraction**: Extract all visible text with perfect accuracy
2. **Content Understanding**: Identify the type and purpose of the document/image
3. **Structure Analysis**: Describe layout, organization, and visual hierarchy
4. **Context Interpretation**: Explain what the image represents and its significance

**Response Requirements:**
- Extract ALL text without any omissions
- Organize information logically and clearly
- Use appropriate formatting (tables, lists, headings) based on content
- Provide context and interpretation where helpful
- Respond in Korean unless the content suggests otherwise

**Quality Standards:**
- Accuracy: 100% faithful text extraction
- Completeness: Cover all visible information
- Clarity: Well-organized, easy to understand presentation
- Intelligence: Apply appropriate formatting based on content type"""

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
    
    def _limit_response_length(self, response: str) -> str:
        """응답 길이 제한"""
        try:
            config = load_config()
            response_settings = config.get("response_settings", {})
            
            if not response_settings.get("enable_length_limit", True):
                return response
            
            max_length = response_settings.get("max_response_length", 8000)
            
            if len(response) <= max_length:
                return response
            
            logger.warning(f"응답 길이 제한 적용: {len(response)}자 -> {max_length}자")
            
            # 마지막 완전한 문장에서 자르기
            truncated = response[:max_length]
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            
            # 마지막 마침표나 줄바꿈 위치에서 자르기
            cut_point = max(last_period, last_newline)
            if cut_point > max_length * 0.8:  # 80% 이상에서 찾은 경우만 사용
                truncated = response[:cut_point + 1]
            
            return truncated + "\n\n[응답이 너무 길어 일부만 표시됩니다. 더 자세한 내용이 필요하시면 구체적인 질문을 해주세요.]"
            
        except Exception as e:
            logger.error(f"응답 길이 제한 오류: {e}")
            return response


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
        """Gemini 모델용 도구 채팅 - 실제 도구 사용"""
        try:
            # 에이전트 실행기가 없으면 생성
            if not self.agent_executor:
                logger.info("🔧 Gemini용 에이전트 실행기 생성")
                self.agent_executor = self.agent_executor_factory.create_agent_executor(llm, self.tools)
            
            if not self.agent_executor:
                logger.warning("에이전트 실행기 생성 실패")
                return "사용 가능한 도구가 없습니다.", []
            
            # 에이전트 실행
            logger.info(f"🔧 Gemini 에이전트 실행: {user_input[:50]}...")
            result = self.agent_executor.invoke({"input": user_input})
            output = result.get("output", "")
            
            # 사용된 도구 정보 추출
            used_tools = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) >= 2 and hasattr(step[0], "tool"):
                        used_tools.append(step[0].tool)
            
            # 도구가 사용된 경우 결과 처리
            if len(used_tools) > 0:
                # 도구 실행 결과 수집
                tool_results = []
                if "intermediate_steps" in result:
                    for step in result["intermediate_steps"]:
                        if len(step) >= 2:
                            tool_results.append(step[1])
                
                # 에이전트 응답이 부적절한 경우 도구 결과를 직접 정리
                if not output.strip() or "Agent stopped" in output or "도구 실행이 완료되었습니다" in output:
                    logger.info(f"Gemini 에이전트 응답 부적절, 도구 결과 직접 정리: {len(used_tools)}개 도구")
                    
                    # 도구 결과를 기반으로 새로운 응답 생성
                    if tool_results:
                        self.llm = llm  # AI 포맷팅을 위해 LLM 저장
                        formatted_results = self._format_tool_results(used_tools, tool_results, user_input)
                        if formatted_results:
                            return formatted_results, used_tools
                    
                    # 도구 결과가 없으면 기본 메시지
                    tool_names = [getattr(tool, '__name__', str(tool)) for tool in used_tools]
                    output = f"요청하신 작업을 완료했습니다. 사용된 도구: {', '.join(tool_names)}"
            # 도구가 사용되지 않았고 응답이 비어있거나 에이전트가 중단된 경우
            elif not output.strip() or "Agent stopped" in output:
                logger.warning("Gemini 에이전트 응답이 비어있거나 중단됨, 일반 채팅으로 대체")
                simple_processor = SimpleChatProcessor()
                return simple_processor.process_chat(user_input, llm), []
            
            logger.info(f"✅ Gemini 도구 채팅 성공: {len(used_tools)}개 도구 사용")
            return output, used_tools
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Gemini 도구 채팅 오류: {e}")
            
            # ReAct 형식 오류 처리
            if "Invalid Format" in error_msg and len(self.tools) > 0:
                # 형식 오류지만 도구가 있는 경우, 다른 프롬프트로 재시도
                logger.info("ReAct 형식 오류 발생, 단순화된 프롬프트로 재시도")
                try:
                    # 단순화된 프롬프트 사용
                    simple_prompt = f"""Please use the following tools to answer the user's question:

{[str(tool) for tool in self.tools]}

Question: {user_input}

Please respond in the following format:
1. Select the appropriate tool to use
2. Explain the parameters to pass to the tool
3. Interpret the results and provide a final answer in Korean"""
                    messages = [HumanMessage(content=simple_prompt)]
                    response = llm.invoke(messages)
                    return response.content, []
                except Exception as inner_e:
                    logger.error(f"❌ 단순화된 프롬프트 실패: {inner_e}")
            
            # 오류 시 일반 채팅으로 폴백
            simple_processor = SimpleChatProcessor()
            return simple_processor.process_chat(user_input, llm), []
    
    def _format_tool_results(self, used_tools: List, tool_results: List, user_input: str) -> str:
        """도구 실행 결과를 AI가 지능적으로 포맷팅"""
        try:
            if not tool_results:
                return None
            
            # AI에게 결과 포맷팅 요청
            tool_names = [getattr(tool, '__name__', str(tool)) for tool in used_tools]
            results_text = "\n\n".join([f"Tool {i+1} Result: {str(result)}" for i, result in enumerate(tool_results)])
            
            format_prompt = f"""Please format the following tool execution results in a user-friendly way in Korean:

User Question: {user_input}
Used Tools: {', '.join(tool_names)}
Tool Results:
{results_text}

Please:
1. Analyze the results and provide a clear summary
2. Use appropriate emojis and formatting
3. Structure the information logically
4. Keep it concise but informative
5. Respond in Korean

Format the response as if you're directly answering the user's question based on these tool results."""
            
            # SimpleChatProcessor를 사용하여 AI가 결과 포맷팅
            from core.llm_factory import LLMFactoryProvider
            formatting_llm = LLMFactoryProvider.create_llm("dummy", "gpt-3.5-turbo")
            
            if hasattr(self, 'llm') and self.llm:
                formatting_llm = self.llm
            
            messages = [HumanMessage(content=format_prompt)]
            response = formatting_llm.invoke(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"도구 결과 포맷팅 오류: {e}")
            # 폴백: 기본 포맷팅
            tool_names = [getattr(tool, '__name__', str(tool)) for tool in used_tools]
            return f"✅ 작업 완료 (사용된 도구: {', '.join(tool_names)})\n\n" + "\n\n".join([str(result) for result in tool_results])
    
    def _limit_response_length(self, response: str) -> str:
        """응답 길이 제한"""
        try:
            config = load_config()
            response_settings = config.get("response_settings", {})
            
            if not response_settings.get("enable_length_limit", True):
                return response
            
            max_length = response_settings.get("max_response_length", 8000)
            
            if len(response) <= max_length:
                return response
            
            logger.warning(f"도구 응답 길이 제한 적용: {len(response)}자 -> {max_length}자")
            
            # 마지막 완전한 문장에서 자르기
            truncated = response[:max_length]
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            
            # 마지막 마침표나 줄바꿈 위치에서 자르기
            cut_point = max(last_period, last_newline)
            if cut_point > max_length * 0.8:  # 80% 이상에서 찾은 경우만 사용
                truncated = response[:cut_point + 1]
            
            return truncated + "\n\n[도구 사용 응답이 너무 길어 일부만 표시됩니다. 더 자세한 내용이 필요하시면 구체적인 질문을 해주세요.]"
            
        except Exception as e:
            logger.error(f"도구 응답 길이 제한 오류: {e}")
            return response