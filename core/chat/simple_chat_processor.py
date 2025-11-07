from typing import List, Dict, Tuple
from .base_chat_processor import BaseChatProcessor
from core.token_logger import TokenLogger
from core.token_tracker import token_tracker, StepType
from core.token_tracking import get_unified_tracker, ChatModeType
from core.logging import get_logger
import time

logger = get_logger('chat.simple')


class SimpleChatProcessor(BaseChatProcessor):
    """단순 채팅 처리기 (도구 사용 없음)"""
    
    def process_message(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """단순 채팅 처리 - 대화 히스토리 포함"""
        try:
            # Unified tracker 시작
            start_time = time.time()
            unified_tracker = None
            try:
                from core.security.secure_path_manager import secure_path_manager
                db_path = secure_path_manager.get_database_path()
                unified_tracker = get_unified_tracker(db_path)
                
                unified_tracker.start_conversation(
                    mode=ChatModeType.SIMPLE,
                    model=self.model_strategy.model_name,
                    session_id=self.session_id
                )
            except Exception as e:
                logger.debug(f"Unified tracker start failed: {e}")
                unified_tracker = None
            
            # 토큰 트래킹 시작 (기존 호환성)
            token_tracker.start_step(StepType.INITIAL_PROMPT, "Simple Chat Processing")
            
            # user_input 타입 검증 및 변환
            if isinstance(user_input, list):
                user_input = str(user_input)
            elif not isinstance(user_input, str):
                user_input = str(user_input) if user_input else ""
            
            if not self.validate_input(user_input):
                return "유효하지 않은 입력입니다.", []
            
            # Pollinations 모델인 경우 이미지 생성 처리
            if hasattr(self.model_strategy, 'generate_image_response'):
                if self.model_strategy.should_use_tools(user_input):
                    response = self.model_strategy.generate_image_response(user_input)
                    return self.format_response(response), []
            
            # 모델 전략에 도구 사용 안함을 명시
            if hasattr(self.model_strategy, '_use_tools_mode'):
                self.model_strategy._use_tools_mode = False
            
            # 이미지 데이터 처리
            if self._has_image_data(user_input):
                processed_message = self.model_strategy.process_image_input(user_input)
                response = self.model_strategy.llm.invoke([processed_message])
                
                # Perplexity 응답 처리 (문자열 또는 객체)
                if isinstance(response, str):
                    response_content = response
                else:
                    response_content = getattr(response, 'content', str(response))
                
                return self.format_response(response_content), []
            
            # 대화 히스토리 로깅
            if conversation_history:
                logger.info(f"Simple chat에 대화 히스토리 {len(conversation_history)}개 전달됨")
            else:
                logger.info("Simple chat에 대화 히스토리 없음")
            
            # ASK 모드 전용 시스템 프롬프트 생성 (도구 사용 금지)
            from ui.prompts import prompt_manager
            provider = prompt_manager.get_provider_from_model(self.model_strategy.model_name)
            ask_mode_prompt = prompt_manager.get_system_prompt(provider, use_tools=False)
            
            # ASK 모드에서 도구 사용 금지 명시
            ask_mode_prompt += "\n\nIMPORTANT: You are in ASK mode. Do NOT use any tools or external functions. Provide answers based only on your knowledge."
            
            # Pollinations 전략인 경우 전용 메서드 사용
            if 'pollinations' in self.model_strategy.model_name.lower():
                response_content = self.model_strategy.generate_response(user_input, conversation_history)
                logger.info(f"Pollinations 전용 응답 생성 완료")
            else:
                # Google Gemini 경고 억제
                import warnings
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message="Convert_system_message_to_human will be deprecated!")
                    
                    # 대화 히스토리를 포함한 메시지 생성 (도구 사용 금지)
                    messages = self.model_strategy.create_messages(
                        user_input, 
                        system_prompt=ask_mode_prompt,
                        conversation_history=conversation_history
                    )
                    
                    # 도구 사용 방지를 위한 추가 처리
                    if hasattr(self.model_strategy.llm, 'bind'):
                        # LangChain 모델인 경우 도구 바인딩 제거
                        bound_llm = self.model_strategy.llm.bind(tools=[])
                        response = bound_llm.invoke(messages)
                    else:
                        response = self.model_strategy.llm.invoke(messages)
                
                logger.info(f"생성된 메시지 수: {len(messages)}")
                
                # 응답 처리 (모든 모델 대응)
                if isinstance(response, str):
                    response_content = response
                else:
                    # 다양한 속성에서 응답 추출 시도
                    response_content = None
                    
                    # 1. content 속성 확인
                    if hasattr(response, 'content') and response.content:
                        response_content = response.content
                    # 2. choices 구조 확인 (OpenAI 호환)
                    elif hasattr(response, 'choices') and response.choices and len(response.choices) > 0:
                        choice = response.choices[0]
                        if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                            response_content = choice.message.content
                    # 3. text 속성 확인
                    elif hasattr(response, 'text') and response.text:
                        response_content = response.text
                    # 4. 기본 문자열 변환
                    else:
                        response_content = str(response)
                
                # tool_calls가 있으면 도구 사용 시도로 간주하고 거부
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    logger.warning(f"Tool calls detected in ASK mode: {response.tool_calls}")
                    response_content = "죄송합니다. Ask 모드에서는 도구를 사용할 수 없습니다. 제가 알고 있는 지식으로 답변드리겠습니다.\n\n" + self._get_fallback_response(user_input)
                
                # 응답 디버깅
                logger.debug(f"AI Response - Type: {type(response)}, Has tool_calls: {hasattr(response, 'tool_calls') and bool(response.tool_calls)}, Content length: {len(response_content) if response_content else 0}")
            
            # 응답 내용 검증 및 디버깅
            if not response_content or response_content.strip() == "":
                logger.warning(f"Empty response detected - Type: {type(response)}")
                logger.debug(f"Response attributes: {response.__dict__ if hasattr(response, '__dict__') else 'N/A'}")
                
                # OpenRouter 모델의 경우 다른 속성 확인
                if 'openrouter' in self.model_strategy.model_name.lower() or any(prefix in self.model_strategy.model_name for prefix in ['deepseek/', 'qwen/', 'meta-llama/', 'nvidia/']):
                    logger.debug(f"OpenRouter model detected: {self.model_strategy.model_name}")
                    for attr in ['message', 'choices', 'data', 'result']:
                        if hasattr(response, attr):
                            attr_value = getattr(response, attr)
                            logger.debug(f"Response.{attr}: {attr_value}")
                            if attr == 'choices' and attr_value and len(attr_value) > 0:
                                choice = attr_value[0]
                                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                                    response_content = choice.message.content
                                    logger.debug(f"Found content in choices[0].message.content")
                                    break
                
                # 여전히 비어있으면 기본 메시지
                if not response_content or response_content.strip() == "":
                    response_content = "죄송합니다. 현재 응답을 생성할 수 없습니다. 잠시 후 다시 시도해 주세요."
            
            # 토큰 사용량 로깅 및 트래킹
            if 'pollinations' not in self.model_strategy.model_name.lower():
                # 실제 토큰 정보 추출
                actual_input, actual_output = TokenLogger.extract_actual_tokens(response)
                
                # 추정치 사용 (실제 토큰이 없는 경우)
                if actual_input == 0 and actual_output == 0:
                    input_text = "\n".join([str(msg.content) if hasattr(msg, 'content') else str(msg) for msg in messages])
                    actual_input = TokenLogger.estimate_tokens(input_text, self.model_strategy.model_name)
                    actual_output = TokenLogger.estimate_tokens(response_content, self.model_strategy.model_name)
                    logger.warning(f"ASK 모드 추정 토큰 사용: IN:{actual_input}, OUT:{actual_output}")
                else:
                    logger.info(f"ASK 모드 실제 토큰: IN:{actual_input}, OUT:{actual_output}")
                
                # Unified tracker 기록 (1회만)
                if unified_tracker and actual_input > 0:
                    duration_ms = (time.time() - start_time) * 1000
                    unified_tracker.track_agent(
                        agent_name="SimpleLLM",
                        model=self.model_strategy.model_name,
                        input_tokens=actual_input,
                        output_tokens=actual_output,
                        duration_ms=duration_ms
                    )
                
                # 기존 토큰 트래커 (호환성)
                input_text = "\n".join([str(msg.content) if hasattr(msg, 'content') else str(msg) for msg in messages])
                token_tracker.end_step(
                    StepType.FINAL_RESPONSE,
                    "Simple Chat Response",
                    input_text=input_text,
                    output_text=response_content,
                    response_obj=response,
                    additional_info={
                        "input_tokens": actual_input,
                        "output_tokens": actual_output,
                        "total_tokens": actual_input + actual_output
                    }
                )
            else:
                # Pollinations의 경우 추정치만 사용
                input_text = user_input
                token_tracker.end_step(
                    StepType.FINAL_RESPONSE,
                    "Pollinations Response",
                    input_text=input_text,
                    output_text=response_content
                )
            
            # Unified tracker 종료 (session_id가 있을 때만 DB 저장)
            if unified_tracker:
                unified_tracker.end_conversation()
            
            return self.format_response(response_content), []
            
        except Exception as e:
            logger.error(f"Simple chat processing error: {e}")
            return f"채팅 처리 중 오류가 발생했습니다: {str(e)[:100]}...", []
    
    def supports_tools(self) -> bool:
        """도구 지원하지 않음"""
        return False
    
    def _has_image_data(self, user_input: str) -> bool:
        """이미지 데이터 포함 여부 확인"""
        if not isinstance(user_input, str):
            return False
        cleaned_input = user_input.replace("\n", "")
        return "[IMAGE_BASE64]" in cleaned_input and "[/IMAGE_BASE64]" in cleaned_input
    
    def _get_fallback_response(self, user_input: str) -> str:
        """도구 없이 기본 지식으로 응답 생성"""
        try:
            # AI가 도구 없이 직접 응답 생성
            from ui.prompts import prompt_manager
            provider = prompt_manager.get_provider_from_model(self.model_strategy.model_name)
            
            fallback_prompt = (
                "You are a helpful AI assistant. Answer the user's question using only your knowledge. "
                "Do not use any tools or external functions. Provide a helpful and informative response."
            )
            
            messages = self.model_strategy.create_messages(
                user_input,
                system_prompt=fallback_prompt
            )
            
            # 도구 바인딩 제거하고 응답 생성
            if hasattr(self.model_strategy.llm, 'bind'):
                bound_llm = self.model_strategy.llm.bind(tools=[])
                response = bound_llm.invoke(messages)
            else:
                response = self.model_strategy.llm.invoke(messages)
            
            # 응답 내용 추출
            if isinstance(response, str):
                return response
            else:
                content = getattr(response, 'content', str(response))
                return content if content else "죄송합니다. 답변을 생성할 수 없습니다."
                
        except Exception as e:
            logger.error(f"Fallback response generation error: {e}")
            return "죄송합니다. 현재 답변을 제공할 수 없습니다. 잠시 후 다시 시도해 주세요."