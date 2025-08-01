from typing import List, Dict, Any, Callable, Optional
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema.output import LLMResult
from ui.prompts import prompt_manager, ModelType
from core.token_logger import TokenLogger
import logging
import threading
import time

logger = logging.getLogger(__name__)


class StreamingCallbackHandler(BaseCallbackHandler):
    """스트리밍 응답을 처리하는 콜백 핸들러"""
    
    def __init__(self, on_token: Callable[[str], None]):
        self.on_token = on_token
        self.tokens = []
        self._cancelled = False
    
    def cancel(self):
        """스트리밍 취소"""
        self._cancelled = True
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """새 토큰이 생성될 때 호출"""
        if not self._cancelled:
            self.tokens.append(token)
            self.on_token(token)
    
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """LLM 응답 완료 시 호출"""
        if not self._cancelled:
            logger.info(f"스트리밍 완료 - 총 토큰 수: {len(self.tokens)}")


class StreamingChatProcessor:
    """스트리밍 채팅 처리기"""
    
    def __init__(self):
        self.current_handler: Optional[StreamingCallbackHandler] = None
    
    def cancel_current_stream(self):
        """현재 스트리밍 취소"""
        if self.current_handler:
            self.current_handler.cancel()
    
    def process_streaming_chat(
        self,
        user_input: str,
        llm: Any,
        conversation_history: List[Dict] = None,
        on_token: Callable[[str], None] = None,
        on_complete: Callable[[str], None] = None,
        on_error: Callable[[str], None] = None
    ) -> None:
        """스트리밍 채팅 처리 (비동기)"""
        
        def _process():
            try:
                # 스트리밍 콜백 핸들러 생성
                accumulated_response = []
                
                def handle_token(token: str):
                    accumulated_response.append(token)
                    if on_token:
                        on_token(token)
                
                self.current_handler = StreamingCallbackHandler(handle_token)
                
                # 메시지 구성
                messages = self._build_messages(user_input, conversation_history)
                
                # 스트리밍 LLM 호출
                logger.info(f"스트리밍 채팅 시작 - 메시지 수: {len(messages)}")
                
                # LangChain의 스트리밍 기능 사용
                llm.callbacks = [self.current_handler]
                response = llm.invoke(messages)
                
                # 완료된 응답 처리
                if not self.current_handler._cancelled:
                    full_response = ''.join(accumulated_response)
                    if not full_response and hasattr(response, 'content'):
                        full_response = response.content
                    
                    logger.info(f"스트리밍 응답 완료 - 길이: {len(full_response)}자")
                    
                    # 토큰 사용량 로깅
                    model_name = getattr(llm, 'model_name', getattr(llm, 'model', 'unknown'))
                    TokenLogger.log_messages_token_usage(
                        model_name, messages, full_response, "streaming_chat"
                    )
                    
                    if on_complete:
                        on_complete(full_response)
                
            except Exception as e:
                error_msg = f"스트리밍 처리 오류: {str(e)}"
                logger.error(error_msg)
                if on_error:
                    on_error(error_msg)
            finally:
                self.current_handler = None
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=_process, daemon=True)
        thread.start()
    
    def _build_messages(self, user_input: str, conversation_history: List[Dict] = None) -> List:
        """메시지 구성"""
        messages = []
        
        # 시스템 메시지 추가 (공통 프롬프트 사용)
        system_prompt = prompt_manager.get_system_prompt(ModelType.COMMON.value)
        messages.append(SystemMessage(content=system_prompt))
        
        # 대화 히스토리 추가
        if conversation_history:
            for msg in conversation_history[-10:]:  # 최근 10개만
                role = msg.get('role', '')
                content = msg.get('content', '')
                
                if role == 'user':
                    messages.append(HumanMessage(content=content))
                elif role == 'assistant':
                    messages.append(AIMessage(content=content))
        
        # 현재 사용자 메시지 추가
        messages.append(HumanMessage(content=user_input))
        
        return messages


class ChunkedResponseProcessor:
    """대용량 응답을 청크 단위로 처리하는 프로세서"""
    
    def __init__(self, chunk_size: int = 100):
        self.chunk_size = chunk_size
        self._cancelled = False
    
    def cancel(self):
        """처리 취소"""
        self._cancelled = True
    
    def process_large_response(
        self,
        response: str,
        on_chunk: Callable[[str], None] = None,
        on_complete: Callable[[str], None] = None,
        chunk_delay: float = 0.05
    ) -> None:
        """대용량 응답을 청크 단위로 처리"""
        
        def _process():
            try:
                if len(response) <= self.chunk_size:
                    # 작은 응답은 즉시 전송
                    if on_chunk:
                        on_chunk(response)
                    if on_complete:
                        on_complete(response)
                    return
                
                # 의미 단위로 청크 분할
                chunks = self._split_into_meaningful_chunks(response)
                
                logger.info(f"대용량 응답 처리 시작 - 총 {len(chunks)}개 청크")
                
                for i, chunk in enumerate(chunks):
                    if self._cancelled:
                        break
                    
                    if on_chunk:
                        on_chunk(chunk)
                    
                    # 마지막 청크가 아니면 지연
                    if i < len(chunks) - 1:
                        time.sleep(chunk_delay)
                
                if not self._cancelled and on_complete:
                    on_complete(response)
                    
            except Exception as e:
                logger.error(f"청크 처리 오류: {e}")
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=_process, daemon=True)
        thread.start()
    
    def _split_into_meaningful_chunks(self, text: str) -> List[str]:
        """의미 단위로 텍스트 분할"""
        import re
        
        # 문장 단위로 분할
        sentences = re.split(r'([.!?]\s+)', text)
        chunks = []
        current_chunk = ""
        
        for i, part in enumerate(sentences):
            current_chunk += part
            
            # 청크 크기 확인
            if len(current_chunk) >= self.chunk_size:
                # 문장 끝에서 분할
                if part.strip().endswith(('.', '!', '?')) or i == len(sentences) - 1:
                    chunks.append(current_chunk)
                    current_chunk = ""
        
        # 남은 내용 추가
        if current_chunk.strip():
            chunks.append(current_chunk)
        
        return chunks if chunks else [text]