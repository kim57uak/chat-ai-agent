from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from ui.components.status_display import status_display
from core.token_logger import TokenLogger
from core.simple_token_accumulator import token_accumulator
from core.logging import get_logger

logger = get_logger('ui.ai_processor')


class AIProcessor(QObject):
    """AI 요청 처리를 담당하는 클래스 (스레드 풀 최적화)"""
    
    finished = pyqtSignal(str, str, list)  # sender, text, used_tools
    error = pyqtSignal(str)
    streaming = pyqtSignal(str, str)  # sender, partial_text
    streaming_complete = pyqtSignal(str, str, list)  # sender, full_text, used_tools
    conversation_completed = pyqtSignal(object)  # ConversationTokens 객체
    
    def __init__(self, parent=None, max_workers=3):
        super().__init__(parent)
        self._cancelled = False
        self._current_client = None
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AIProcessor")
        self._current_future = None
        self._lock = threading.Lock()
    
    def cancel(self):
        """요청 취소 (스레드 안전)"""
        with self._lock:
            self._cancelled = True
            if self._current_future and not self._current_future.done():
                self._current_future.cancel()
            if self._current_client:
                self._current_client.cancel_streaming()
        status_display.finish_processing(False)
    
    def shutdown(self):
        """스레드 풀 종료 (리소스 정리)"""
        self._executor.shutdown(wait=False)
        logger.info("AIProcessor 스레드 풀 종료")
    
    def process_request(self, api_key, model, messages, user_text=None, agent_mode=False, file_prompt=None, chat_mode="simple", session_id=None):
        """AI 요청 처리 - 대화 히스토리 포함"""
        def _process():
            request_start_time = time.time()
            request_id = None
            try:
                if self._cancelled:
                    return
                
                # 상태 표시 시작
                mode = 'agent' if agent_mode else 'ask'
                status_display.start_processing(model, mode)
                
                # AI 요청 로깅
                available_tools = []
                try:
                    from mcp.client.mcp_client import mcp_manager
                    all_tools = mcp_manager.get_all_tools()
                    available_tools = [f"{server}.{tool['name']}" for server, tools in all_tools.items() for tool in tools]
                except:
                    pass
                
                # 시스템 프롬프트 가져오기 (모드별 차등 적용)
                from ui.prompts import prompt_manager
                provider = prompt_manager.get_provider_from_model(model)
                
                # 모드에 따른 시스템 프롬프트 선택
                system_prompt = prompt_manager.get_system_prompt(provider, use_tools=agent_mode)
                
                # 모드별 프롬프트 구성 요소 로깅 (실제 존재하는 키만)
                if agent_mode:
                    # Agent 모드 프롬프트 구성
                    prompt_components = [
                        ('system_base', prompt_manager.get_prompt('common', 'system_base')),
                        ('context_awareness', prompt_manager.get_prompt('common', 'context_awareness')),
                        ('response_tone', prompt_manager.get_prompt('common', 'response_tone')),
                        ('emoji_usage', prompt_manager.get_prompt('common', 'emoji_usage')),
                        ('tool_usage', prompt_manager.get_prompt('common', 'tool_usage')),
                        ('formatting', prompt_manager.get_prompt('common', 'formatting')),
                        ('code_rules', prompt_manager.get_prompt('common', 'code_rules')),
                        ('mermaid_rules', prompt_manager.get_prompt('common', 'mermaid_rules')),
                        ('agent_base', prompt_manager.get_prompt('common', 'agent_base')),
                        ('react_format', prompt_manager.get_prompt('common', 'react_format')),
                        ('json_format', prompt_manager.get_prompt('common', 'json_format')),
                        ('execution_rules', prompt_manager.get_prompt('common', 'execution_rules')),
                        # 모델별 특수 프롬프트
                        ('model_enhancement', prompt_manager.get_custom_prompt(provider, 'system_enhancement') or ''),
                        ('agent_system', prompt_manager.get_custom_prompt(provider, 'agent_system') or ''),
                        ('react_template', prompt_manager.get_custom_prompt(provider, 'react_template') or ''),
                        ('tool_decision', prompt_manager.get_custom_prompt(provider, 'tool_decision') or ''),
                        ('image_generation', prompt_manager.get_custom_prompt(provider, 'image_generation') or '')
                    ]
                else:
                    # Ask 모드 프롬프트 구성
                    prompt_components = [
                        ('system_base', prompt_manager.get_prompt('common', 'system_base')),
                        ('context_awareness', prompt_manager.get_prompt('common', 'context_awareness')),
                        ('response_tone', prompt_manager.get_prompt('common', 'response_tone')),
                        ('emoji_usage', prompt_manager.get_prompt('common', 'emoji_usage')),
                        ('formatting', prompt_manager.get_prompt('common', 'formatting')),
                        ('mermaid_rules', prompt_manager.get_prompt('common', 'mermaid_rules')),
                        ('ask_mode', prompt_manager.get_prompt('common', 'ask_mode')),
                        # 모델별 특수 프롬프트
                        ('model_enhancement', prompt_manager.get_custom_prompt(provider, 'system_enhancement') or '')
                    ]
                
                logger.debug(f"Prompt components - Model: {model}, Mode: {'Agent' if agent_mode else 'Ask'}")
                for key, value in prompt_components:
                    if value:
                        logger.debug(f"{key}: {value[:100]}...")
                
                # 언어 감지를 위한 입력 결정
                input_for_detection = (file_prompt or "") + (user_text or "")
                
                # 언어 감지 및 강제 언어 지시 추가
                processed_file_prompt = file_prompt
                processed_user_text = user_text
                
                if input_for_detection.strip():
                    korean_ratio = self._detect_korean_ratio(input_for_detection)
                    korean_threshold = self._get_korean_threshold()
                    
                    if korean_ratio >= korean_threshold:
                        language_instruction = "\n\n[CRITICAL: 반드시 한글로만 답변해주세요. Answer only in Korean.]"
                    else:
                        language_instruction = "\n\n[CRITICAL: Please answer only in English. 영어로만 답변해주세요.]"
                    
                    # 사용자 입력에 언어 지시 추가
                    if processed_file_prompt:
                        processed_file_prompt = processed_file_prompt + language_instruction
                    if processed_user_text:
                        processed_user_text = processed_user_text + language_instruction
                    
                    logger.debug(f"Language detection - Korean ratio: {korean_ratio:.3f}, Threshold: {korean_threshold}, Language: {'Korean' if korean_ratio >= korean_threshold else 'English'}")
                
                # 실제 사용자 입력 결정
                actual_user_input = processed_file_prompt or processed_user_text or ""
                
                # request_id = ai_logger.log_request(
                #     model=model,
                #     system_prompt=system_prompt,
                #     user_input=actual_user_input,
                #     conversation_history=messages,
                #     tools_available=available_tools if agent_mode else [],
                #     agent_mode=agent_mode
                # )
                request_id = None
                
                from core.ai_client import AIClient
                client = AIClient(api_key, model)
                
                # session_id 설정
                if session_id is not None:
                    client.set_session_id(session_id)
                
                self._current_client = client
                self._current_model = model
                
                # RAG 모드일 경우 RAG Manager 초기화 및 Agent 모드 설정
                if chat_mode == "rag":
                    from core.rag.rag_manager import RAGManager
                    if not hasattr(client, 'rag_manager'):
                        client.rag_manager = RAGManager()
                    
                    # Agent에 RAG 모드 설정
                    if hasattr(client, 'agent') and hasattr(client.agent, 'set_chat_mode'):
                        client.agent.set_chat_mode("rag")
                        client.agent.set_vectorstore(client.rag_manager.vectorstore)
                        logger.info("RAG mode activated and configured")
                    else:
                        logger.warning("Agent does not support RAG mode configuration")
                
                # 대화 히스토리 설정
                if messages:
                    client.conversation_history = messages
                    if hasattr(client, '_conversation_manager'):
                        client._conversation_manager.conversation_history = messages
                
                response = None
                sender = 'AI'
                used_tools = []
                
                if processed_file_prompt:
                    # 파일 프롬프트 처리
                    if agent_mode:
                        result = client.agent_chat(processed_file_prompt)
                        if isinstance(result, tuple):
                            response, used_tools = result
                        else:
                            response = result
                            used_tools = []
                        sender = '에이전트'
                    else:
                        response = client.simple_chat(processed_file_prompt)
                        sender = 'AI'
                        used_tools = []
                else:
                    # 일반 텍스트 처리
                    if chat_mode == "rag":
                        # RAG 모드: RAG + Multi-Agent
                        logger.info(f"RAG mode processing: {processed_user_text[:50]}")
                        
                        # RAG Manager 가져오기
                        from core.rag.rag_manager import RAGManager
                        if not hasattr(client, 'rag_manager'):
                            client.rag_manager = RAGManager()
                        
                        # RAG 검색 먼저 수행
                        # 설정에서 top_k 가져오기
                        try:
                            from utils.config_path import config_path_manager
                            import json
                            config_path = config_path_manager.get_config_path('rag_config.json')
                            if config_path.exists():
                                with open(config_path, 'r', encoding='utf-8') as f:
                                    rag_config = json.load(f)
                                    top_k = rag_config.get('top_k', 5)
                            else:
                                top_k = 5
                        except:
                            top_k = 5
                        
                        rag_results = client.rag_manager.search(processed_user_text, k=top_k)
                        
                        if rag_results:
                            # RAG 결과를 컨텍스트로 추가
                            context = "\n\n[관련 문서]\n"
                            for i, doc in enumerate(rag_results, 1):
                                context += f"{i}. {doc.page_content[:200]}...\n\n"
                            
                            enhanced_text = f"{context}\n[사용자 질문]\n{processed_user_text}"
                            logger.info(f"RAG: Found {len(rag_results)} documents")
                        else:
                            enhanced_text = processed_user_text
                            logger.info("RAG: No documents found")
                        
                        # RAG 모드: 문서 검색 + 도구 사용 가능
                        if messages:
                            full_messages = messages + [{'role': 'user', 'content': enhanced_text}]
                            result = client.chat(full_messages, force_agent=True)
                            if isinstance(result, tuple):
                                response, used_tools = result
                            else:
                                response = result
                                used_tools = []
                        else:
                            result = client.agent_chat(enhanced_text)
                            if isinstance(result, tuple):
                                response, used_tools = result
                            else:
                                response = result
                                used_tools = []
                        sender = 'RAG+Agent'
                    elif agent_mode:
                        # 에이전트 모드: 도구 사용 가능
                        if messages:
                            full_messages = messages + [{'role': 'user', 'content': processed_user_text}]
                            result = client.chat(full_messages, force_agent=True)
                            if isinstance(result, tuple):
                                response, used_tools = result
                            else:
                                response = result
                                used_tools = []
                        else:
                            result = client.agent_chat(processed_user_text)
                            if isinstance(result, tuple):
                                response, used_tools = result
                            else:
                                response = result
                                used_tools = []
                        sender = '에이전트'
                    else:
                        # Ask 모드: 도구 사용 없이 단순 채팅만
                        if messages:
                            # Ask 모드: force_agent=False로 명시적 전달
                            full_messages = messages + [{'role': 'user', 'content': processed_user_text}]
                            result = client.chat(full_messages, force_agent=False)
                            if isinstance(result, tuple):
                                response, used_tools = result
                            else:
                                response = result
                                used_tools = []
                        else:
                            response = client.simple_chat(processed_user_text)
                            used_tools = []
                        sender = 'AI'
                        
                        # Ask 모드에서는 도구 사용 불가 메시지 제거 (AI가 컨텍스트 파악해서 판단)
                
                if not self._cancelled and response:
                    # 토큰 추적은 chat_processor에서 이미 완료됨 (중복 방지)
                    # 여기서는 UI 업데이트만 수행
                    from core.token_tracker import token_tracker
                    
                    # AI 응답 로깅
                    response_time = time.time() - request_start_time
                    
                    # 토큰 정보는 tracker에서 가져오기
                    tracker_stats = token_tracker.get_conversation_stats()
                    if tracker_stats:
                        actual_input_tokens = tracker_stats.get('total_actual_input', 0) or tracker_stats.get('total_estimated_input', 0)
                        actual_output_tokens = tracker_stats.get('total_actual_output', 0) or tracker_stats.get('total_estimated_output', 0)
                    else:
                        actual_input_tokens = 0
                        actual_output_tokens = 0
                    
                    # token_accumulator에 토큰 추가 (채팅 하단 표시용)
                    if actual_input_tokens > 0 or actual_output_tokens > 0:
                        token_accumulator.add(actual_input_tokens, actual_output_tokens)
                        logger.debug(f"Token accumulator updated: {token_accumulator.get_total()}")
                    
                    token_usage = {
                        'input_tokens': actual_input_tokens,
                        'output_tokens': actual_output_tokens,
                        'total_tokens': actual_input_tokens + actual_output_tokens
                    }
                    
                    # if request_id:
                    #     ai_logger.log_response(
                    #         request_id=request_id,
                    #         model=model,
                    #         response=str(response),
                    #         used_tools=[str(tool) for tool in used_tools],
                    #         token_usage=token_usage,
                    #         response_time=response_time
                    #     )
                    
                    # AI 사고 프로세스 로깅
                    logger.info(f"AI Response - Model: {model}, Agent: {agent_mode}, Time: {response_time:.2f}s, Tokens: IN:{token_usage.get('input_tokens', 0)} OUT:{token_usage.get('output_tokens', 0)}, Tools: {len(used_tools)}")
                    logger.debug(f"Response type: {type(response)}, Length: {len(str(response))} chars")
                    
                    # 응답이 문자열이 아닌 경우 문자열로 변환
                    if not isinstance(response, str):
                        response = str(response)
                    
                    # 사용된 도구 업데이트
                    for tool in used_tools:
                        status_display.add_tool_used(str(tool))
                    

                    
                    # 상태 표시에 토큰 정보 업데이트
                    status_display.update_tokens(actual_input_tokens, actual_output_tokens)
                    
                    # 상태 표시 완료
                    status_display.finish_processing(True)
                    
                    # sender에 모델 정보와 토큰 정보 포함
                    total_tokens = actual_input_tokens + actual_output_tokens
                    if total_tokens > 0:
                        token_info = f" | 📊 {total_tokens:,}토큰"
                    else:
                        token_info = ""
                    
                    model_sender = f"{sender}_{model}{token_info}"
                    
                    # 응답 전송
                    self.finished.emit(model_sender, response, used_tools)
                    
                    # 대화 완료 시그널 발송 (응답 전송 후)
                    self.conversation_completed.emit(None)
                elif not self._cancelled:
                    status_display.finish_processing(False)
                    logger.warning("Failed to generate response")
                    self.error.emit("응답을 생성할 수 없습니다.")
                    
            except Exception as e:
                if not self._cancelled:
                    status_display.finish_processing(False)
                    error_msg = f'오류 발생: {str(e)}'
                    logger.error(f"AI processing error - Model: {model}, Agent: {agent_mode}", exc_info=True)
                    self.error.emit(error_msg)
                    
                    # if request_id:
                    #     ai_logger.log_response(
                    #         request_id=request_id,
                    #         model=model,
                    #         response="",
                    #         used_tools=[],
                    #         token_usage={},
                    #         response_time=time.time() - request_start_time,
                    #         error=str(e)
                    #     )
        
        # 스레드 풀에 작업 제출
        with self._lock:
            self._cancelled = False
            self._current_future = self._executor.submit(_process)
        
        # 에러 핸들링
        def _handle_future_exception(future: Future):
            try:
                future.result()
            except Exception as e:
                if not self._cancelled:
                    logger.error(f"Future 실행 오류: {e}", exc_info=True)
        
        self._current_future.add_done_callback(_handle_future_exception)
    
    def _detect_korean_ratio(self, text: str) -> float:
        """텍스트에서 한글 문자 비율 계산"""
        if not text:
            return 0.0
        
        korean_chars = 0
        total_chars = 0
        
        for char in text:
            if char.strip():  # 공백 제외
                total_chars += 1
                # 한글 유니코드 범위: 가(0xAC00) ~ 힣(0xD7A3)
                if 0xAC00 <= ord(char) <= 0xD7A3:
                    korean_chars += 1
        
        return korean_chars / total_chars if total_chars > 0 else 0.0
    
    def _get_korean_threshold(self) -> float:
        """config.json에서 한글 임계값 읽기"""
        try:
            import json
            import os
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('language_detection', {}).get('korean_threshold', 0.1)
        except Exception:
            return 0.1  # 기본값