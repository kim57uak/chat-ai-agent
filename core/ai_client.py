"""AI Client - refactored to follow SOLID principles."""

# Backward compatibility imports
from .client import ChatClient, ConversationManager, PromptManager
from .config import ConfigManager
from core.streaming_processor import StreamingChatProcessor, ChunkedResponseProcessor
from core.llm_factory import LLMFactoryProvider
from core.message_validator import MessageValidator
from core.token_accumulator import token_accumulator
import logging

try:
    from core.logging import get_logger
    _logger = get_logger("ai_client")
except:
    _logger = logging.getLogger("ai_client")


class AIClient:
    """AI 클라이언트 - 리팩토링된 버전 (하위 호환성 유지)"""
    
    logger = _logger

    def __init__(self, api_key, model_name="gpt-3.5-turbo"):
        self.api_key = api_key
        self.model_name = model_name
        
        # 리팩토링된 컴포넌트들 사용
        self._chat_client = ChatClient(api_key, model_name)
        self._config_manager = ConfigManager()
        self._conversation_manager = ConversationManager()
        self._prompt_manager = PromptManager(self._config_manager)
        
        # 스트리밍 처리기 (기존 호환성)
        self.streaming_processor = StreamingChatProcessor()
        self.chunked_processor = ChunkedResponseProcessor()
        self.streaming_llm = None
        
        # 토큰 사용량 추적을 위한 마지막 응답 저장
        self._last_response = None
        
        # 설정 로드
        conv_settings = self._config_manager.get("conversation_settings", {})
        self.max_history_pairs = conv_settings.get("max_history_pairs", 5)
        self.max_tokens_estimate = conv_settings.get("max_tokens_estimate", 2000)
        self.enable_history = conv_settings.get("enable_history", True)
        self.token_optimization = conv_settings.get("token_optimization", True)
        
        # 하위 호환성을 위한 속성들
        self.agent = self._chat_client.agent
        self.conversation_history = self._conversation_manager.conversation_history
        self.user_prompt = self._prompt_manager._prompts

    def chat(self, messages, force_agent=False):
        """토큰 최적화된 대화 기록 사용 (할당량 초과 시 청크 분할) - 안정성 개선"""
        try:
            # 입력 검증
            if not messages or not isinstance(messages, list):
                return "유효하지 않은 메시지 형식입니다."

            # 마지막 사용자 메시지 추출 (원본 텍스트 - 언어 판단용)
            original_user_message = ""
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get("role") == "user":
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        original_user_message = content.strip()
                        if original_user_message:
                            break
            
            # 프롬프트 추가 전 원본 메시지 저장 (언어 판단용)
            user_message = original_user_message

            # 이미지 데이터 감지 (줄바꿈 무시)
            cleaned_message = user_message.replace("\n", "")
            has_start_tag = "[IMAGE_BASE64]" in cleaned_message
            has_end_tag = "[/IMAGE_BASE64]" in cleaned_message
            has_image_data = has_start_tag and has_end_tag
            
            if has_image_data:
                # 중앙관리 시스템에서 OCR 프롬프트 가져오기
                from ui.prompts import prompt_manager
                ocr_prompt = prompt_manager.get_ocr_prompt()
                
                # 마지막 사용자 메시지에 OCR 프롬프트 추가
                for i in range(len(messages) - 1, -1, -1):
                    if messages[i].get("role") == "user":
                        content = messages[i]["content"]
                        cleaned_content = content.replace("\n", "")
                        has_image_in_content = "[IMAGE_BASE64]" in cleaned_content
                        if has_image_in_content:
                            messages[i]["content"] = f"{ocr_prompt}\n\n{content}"
                        break
            else:
                # 일반 텍스트의 경우 기존 유저 프롬프트 사용
                user_prompt = self.get_current_user_prompt()
                if user_prompt and user_message:
                    enhanced_message = f"{user_prompt}\n\n{user_message}"
                    for i in range(len(messages) - 1, -1, -1):
                        if messages[i].get("role") == "user":
                            messages[i]["content"] = enhanced_message
                            break

            if not user_message:
                return "처리할 메시지를 찾을 수 없습니다."
            self.logger.info(f"채팅 요청 처리 시작: {user_message[:50]}...")

            # 전달받은 메시지를 그대로 사용 (하이브리드 히스토리 적용)
            validated_messages = MessageValidator.validate_and_fix_messages(messages)
            
            # 대화 기록 사용 여부 확인
            if not self.enable_history:
                # 히스토리 없이 마지막 사용자 메시지만 처리
                last_user_msg = [msg for msg in validated_messages if msg.get('role') == 'user'][-1:]
                return self._process_with_quota_handling(user_message, last_user_msg, force_agent=force_agent)

            return self._process_with_quota_handling(user_message, validated_messages, force_agent=force_agent)

        except Exception as e:
            error_msg = str(e)
            _logger.error(f"AI 클라이언트 채팅 오류: {error_msg}")
            return f"채팅 처리 중 오류가 발생했습니다: {error_msg[:100]}..."

    def _process_with_quota_handling(
        self, user_message: str, history: list, force_agent: bool = False
    ):
        """할당량 초과 시 청크 분할 처리 - 단순화"""
        import time

        try:
            start_time = time.time()
            mode_info = " (Agent 모드)" if force_agent else " (Ask 모드)"
            
            self.logger.info(
                f"AI 요청 시작{mode_info}: {self.model_name} (히스토리: {len(history)}개)"
            )

            response, used_tools = self.agent.process_message_with_history(
                user_message, history, force_agent
            )
            
            # 마지막 응답 저장 및 토큰 정보 추출
            if hasattr(self.agent, '_last_response'):
                self._last_response = self.agent._last_response
                
                # 토큰 누적기에 응답 추가
                token_accumulator.add_response_tokens(self._last_response, self.model_name, "채팅")
                
                # 정확한 토큰 정보 추출 (기존 로깅용)
                from core.token_logger import TokenLogger
                input_tokens, output_tokens = TokenLogger.extract_actual_tokens(self._last_response)
                total_tokens = input_tokens + output_tokens if input_tokens > 0 or output_tokens > 0 else None
                
                # 토큰 정보 로깅
                if input_tokens > 0 or output_tokens > 0:
                    TokenLogger.log_actual_token_usage(self.model_name, self._last_response, "chat")
                
                # 대화 히스토리에 정확한 토큰 정보와 함께 저장
                if hasattr(self, 'conversation_history') and self.conversation_history:
                    self.conversation_history.add_message(
                        "assistant", 
                        response, 
                        model_name=self.model_name,
                        input_tokens=input_tokens if input_tokens > 0 else None,
                        output_tokens=output_tokens if output_tokens > 0 else None,
                        total_tokens=total_tokens
                    )

            elapsed_time = time.time() - start_time

            if used_tools:
                self.logger.debug(
                    f"도구 사용 응답 완료{mode_info}: {self.model_name} ({elapsed_time:.1f}초) - 도구: {used_tools}"
                )
            else:
                self.logger.debug(
                    f"일반 채팅 응답 완료{mode_info}: {self.model_name} ({elapsed_time:.1f}초)"
                )

            return response, used_tools

        except Exception as e:
            error_msg = str(e)

            # 할당량 초과 오류 감지
            if "429" in error_msg and "quota" in error_msg.lower():
                self.logger.warning(
                    f"할당량 초과 감지, 청크 분할 처리 시도: {self.model_name}"
                )
                return self._handle_quota_exceeded(user_message, history)

            # 연결 오류 감지
            elif any(
                keyword in error_msg.lower()
                for keyword in ["connection", "timeout", "network"]
            ):
                self.logger.error(f"네트워크 오류: {self.model_name} - {error_msg}")
                return "네트워크 연결에 문제가 있습니다. 잠시 후 다시 시도해주세요.", []

            else:
                self.logger.error(f"AI 클라이언트 오류: {self.model_name} - {error_msg}")
                raise e

    def _handle_quota_exceeded(self, user_message: str, history: list):
        """할당량 초과 시 청크 분할 처리"""
        # 긴 메시지를 청크로 분할
        if len(user_message) > 1000:
            chunks = self._split_message_into_chunks(user_message, 800)
            responses = []

            for i, chunk in enumerate(chunks):
                try:
                    # 각 청크를 간단한 히스토리로 처리
                    simple_history = history[-2:] if history else []  # 최근 2개만
                    chunk_response, _ = self.agent.process_message_with_history(
                        f"[{i+1}/{len(chunks)}] {chunk}",
                        simple_history,
                        force_agent=True,
                    )
                    responses.append(chunk_response)

                except Exception as chunk_error:
                    self.logger.error(f"청크 {i+1} 처리 오류: {chunk_error}")
                    responses.append(
                        f"[청크 {i+1} 처리 실패: {str(chunk_error)[:100]}...]"
                    )

            return "\n\n".join(responses), []

        else:
            # 짧은 메시지는 히스토리 없이 처리
            try:
                response, used_tools = self.agent.process_message(user_message)
                self.logger.info(f"할당량 초과로 히스토리 없이 처리: {self.model_name}")
                return response, used_tools
            except Exception as fallback_error:
                return (
                    f"할당량 초과 및 대체 처리 실패: {str(fallback_error)[:200]}...",
                    [],
                )

    def _split_message_into_chunks(self, message: str, chunk_size: int = 800):
        """메시지를 청크로 분할"""
        if len(message) <= chunk_size:
            return [message]

        chunks = []
        sentences = message.split(". ")
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk + sentence) <= chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def agent_chat(self, user_input: str):
        """에이전트 채팅 - 리팩토링된 버전"""
        try:
            if not user_input or not isinstance(user_input, str):
                return "유효하지 않은 입력입니다.", []
            
            user_input = user_input.strip()
            if not user_input:
                return "빈 메시지는 처리할 수 없습니다.", []
            
            # 리팩토링된 컴포넌트 사용
            return self._chat_client.agent_chat(user_input)
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"에이전트 채팅 오류: {error_msg}")
            return f"에이전트 채팅 오류: {error_msg[:100]}...", []

    def simple_chat(self, user_input: str):
        """단순 채팅 - 리팩토링된 버전"""
        try:
            # 기본 채팅 처리
            return self._chat_client.chat(user_input)
        except Exception as e:
            self.logger.error(f"단순 채팅 오류: {e}")
            return f"오류: {e}"

    def _optimize_conversation_history(self):
        """대화 기록 최적화 - 리팩토링된 버전"""
        return self._conversation_manager.get_optimized_history()

    def _estimate_tokens(self, text: str) -> int:
        """토큰 수 대략 추정 (한글 1자 = 1.5토큰, 영어 1단어 = 1.3토큰)"""
        if not text:
            return 0

        # 한글과 영어 분리 계산
        korean_chars = sum(1 for c in text if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3)
        english_words = len([w for w in text.split() if w.isascii()])
        other_chars = len(text) - korean_chars

        estimated_tokens = int(
            korean_chars * 1.5 + english_words * 1.3 + other_chars * 0.8
        )
        return max(estimated_tokens, len(text) // 4)  # 최소값 보장

    def _limit_by_tokens(self, history: list) -> list:
        """토큰 수 기반으로 대화 기록 제한"""
        if not history:
            return []

        total_tokens = 0
        limited_history = []

        # 마지막부터 역순으로 처리
        for msg in reversed(history):
            content = msg.get("content", "")
            msg_tokens = self._estimate_tokens(content)

            if total_tokens + msg_tokens > self.max_tokens_estimate:
                break

            limited_history.insert(0, msg)
            total_tokens += msg_tokens

        self.logger.info(
            f"대화 기록 최적화: {len(history)}개 -> {len(limited_history)}개 (예상 토큰: {total_tokens})"
        )
        return limited_history

    def _load_user_prompt(self):
        """유저 프롬프트 로드 - 중앙관리 시스템 사용"""
        try:
            from core.file_utils import load_config
            from ui.prompts import prompt_manager, ModelType

            config = load_config()
            # 설정 파일에서 커스텀 프롬프트가 있으면 사용, 없으면 중앙관리 시스템 사용
            user_prompts = config.get(
                "user_prompt",
                {
                    "gpt": prompt_manager.get_system_prompt(ModelType.OPENAI.value),
                    "gemini": prompt_manager.get_system_prompt(ModelType.GOOGLE.value),
                    "perplexity": prompt_manager.get_system_prompt(ModelType.PERPLEXITY.value),
                },
            )
            self.logger.info(f"유저 프롬프트 로드 완료: {len(user_prompts)}개 모델")
            return user_prompts
        except Exception as e:
            self.logger.error(f"유저 프롬프트 로드 오류: {e}")
            # 오류 시 중앙관리 시스템에서 기본 프롬프트 사용
            from ui.prompts import prompt_manager, ModelType
            return {
                "gpt": prompt_manager.get_system_prompt(ModelType.OPENAI.value),
                "gemini": prompt_manager.get_system_prompt(ModelType.GOOGLE.value),
                "perplexity": prompt_manager.get_system_prompt(ModelType.PERPLEXITY.value),
            }

    def get_current_user_prompt(self):
        """현재 모델에 맞는 유저 프롬프트 반환 - 리팩토링된 버전"""
        return self._prompt_manager.get_prompt_for_model(self.model_name)

    def update_user_prompt(self, prompt_text, model_type="both"):
        """유저 프롬프트 업데이트 - 리팩토링된 버전"""
        if model_type == "both":
            for mt in ["gpt", "gemini", "perplexity"]:
                self._prompt_manager.update_prompt(mt, prompt_text)
        else:
            self._prompt_manager.update_prompt(model_type, prompt_text)

    def _save_user_prompt(self):
        """유저 프롬프트 저장"""
        try:
            from core.file_utils import load_config, save_config

            config = load_config()
            config["user_prompt"] = self.user_prompt
            save_config(config)
            self.logger.info(f"유저 프롬프트 저장 완료: {self.user_prompt}")
        except Exception as e:
            self.logger.error(f"유저 프롬프트 저장 오류: {e}", exc_info=True)
    
    def streaming_chat(
        self, 
        user_input: str, 
        on_token=None, 
        on_complete=None, 
        on_error=None
    ):
        """스트리밍 채팅 - 대용량 응답 지원"""
        try:
            # 스트리밍용 LLM 생성 (한 번만)
            if not self.streaming_llm:
                self.streaming_llm = LLMFactoryProvider.create_llm(
                    self.api_key, self.model_name, streaming=True
                )
                self.logger.info(f"스트리밍 LLM 생성: {self.model_name}")
            
            # 대화 기록 최적화
            optimized_history = self._optimize_conversation_history()
            
            # 스트리밍 처리 시작
            self.streaming_processor.process_streaming_chat(
                user_input=user_input,
                llm=self.streaming_llm,
                conversation_history=optimized_history,
                on_token=on_token,
                on_complete=on_complete,
                on_error=on_error
            )
            
        except Exception as e:
            error_msg = f"스트리밍 채팅 오류: {str(e)}"
            self.logger.error(error_msg)
            if on_error:
                on_error(error_msg)
    
    def cancel_streaming(self):
        """스트리밍 취소"""
        self.streaming_processor.cancel_current_stream()
        self.chunked_processor.cancel()
        self.logger.info("스트리밍 취소 요청")
    
    def process_large_response(
        self, 
        response: str, 
        on_chunk=None, 
        on_complete=None
    ):
        """대용량 응답 처리 - 청크 단위 전송"""
        self.chunked_processor.process_large_response(
            response=response,
            on_chunk=on_chunk,
            on_complete=on_complete
        )


# 기존 호환성을 위한 전역 클라이언트
mcp_client = None


def get_mcp_client():
    global mcp_client
    return mcp_client


def set_mcp_client(client):
    global mcp_client
    mcp_client = client
