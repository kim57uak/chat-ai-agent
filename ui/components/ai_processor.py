from PyQt6.QtCore import QObject, pyqtSignal
import threading
import logging
import time
from ui.components.status_display import status_display
from core.token_logger import TokenLogger
from core.ai_logger import ai_logger


class AIProcessor(QObject):
    """AI 요청 처리를 담당하는 클래스 (SRP)"""
    
    finished = pyqtSignal(str, str, list)  # sender, text, used_tools
    error = pyqtSignal(str)
    streaming = pyqtSignal(str, str)  # sender, partial_text
    streaming_complete = pyqtSignal(str, str, list)  # sender, full_text, used_tools
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancelled = False
        self._current_client = None
    
    def cancel(self):
        """요청 취소"""
        self._cancelled = True
        status_display.finish_processing(False)
        if self._current_client:
            self._current_client.cancel_streaming()
    
    def process_request(self, api_key, model, messages, user_text=None, agent_mode=False, file_prompt=None):
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
                
                # 모드별 프롬프트 구성 요소 로깅
                if agent_mode:
                    # Agent 모드 프롬프트 구성
                    prompt_components = [
                        ('system_base', prompt_manager.get_prompt('common', 'system_base')),
                        ('tone_guidelines', prompt_manager.get_prompt('common', 'tone_guidelines')),
                        ('tool_selection', prompt_manager.get_prompt('common', 'tool_selection')),
                        ('schema_compliance', prompt_manager.get_prompt('common', 'schema_compliance')),
                        ('table_formatting', prompt_manager.get_prompt('common', 'table_formatting')),
                        ('error_handling', prompt_manager.get_prompt('common', 'error_handling')),
                        ('response_format', prompt_manager.get_prompt('common', 'response_format')),
                        ('markdown_standard', prompt_manager.get_prompt('common', 'markdown_standard')),
                        ('readability_enhancement', prompt_manager.get_prompt('common', 'readability_enhancement')),
                        ('code_block_strict', prompt_manager.get_prompt('common', 'code_block_strict')),
                        ('mermaid_diagram_rule', prompt_manager.get_prompt('common', 'mermaid_diagram_rule')),
                        ('agent_base', prompt_manager.get_prompt('common', 'agent_base')),
                        ('react_format', prompt_manager.get_prompt('common', 'react_format')),
                        ('json_output_format', prompt_manager.get_prompt('common', 'json_output_format')),
                        ('common_agent_rules', prompt_manager.get_prompt('common', 'common_agent_rules')),
                        ('model_enhancement', prompt_manager.get_custom_prompt(provider, 'system_enhancement') or '')
                    ]
                else:
                    # Ask 모드 프롬프트 구성
                    prompt_components = [
                        ('system_base', prompt_manager.get_prompt('common', 'system_base')),
                        ('tone_guidelines', prompt_manager.get_prompt('common', 'tone_guidelines')),
                        ('table_formatting', prompt_manager.get_prompt('common', 'table_formatting')),
                        ('markdown_standard', prompt_manager.get_prompt('common', 'markdown_standard')),
                        ('readability_enhancement', prompt_manager.get_prompt('common', 'readability_enhancement')),
                        ('mermaid_diagram_rule', prompt_manager.get_prompt('common', 'mermaid_diagram_rule')),
                        ('model_enhancement', prompt_manager.get_custom_prompt(provider, 'system_enhancement') or '')
                    ]
                
                print(f"\n=== PROMPT COMPONENTS LOG ===\nModel: {model} | Mode: {'Agent' if agent_mode else 'Ask'}")
                for key, value in prompt_components:
                    if value:
                        print(f"\n--- {key.upper()} ---\n{value[:200]}{'...' if len(value) > 200 else ''}")
                
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
                    
                    print(f"\n=== LANGUAGE DETECTION ===\nKorean ratio: {korean_ratio:.3f} | Threshold: {korean_threshold}")
                    print(f"Language instruction: {'Korean' if korean_ratio >= korean_threshold else 'English'}")
                
                # 실제 사용자 입력 결정
                actual_user_input = processed_file_prompt or processed_user_text or ""
                
                request_id = ai_logger.log_request(
                    model=model,
                    system_prompt=system_prompt,
                    user_input=actual_user_input,
                    conversation_history=messages,
                    tools_available=available_tools if agent_mode else [],
                    agent_mode=agent_mode
                )
                
                from core.ai_client import AIClient
                client = AIClient(api_key, model)
                self._current_client = client
                self._current_model = model
                
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
                    if agent_mode:
                        # 에이전트 모드: 도구 사용 가능
                        if messages:
                            # 히스토리를 포함한 메시지 리스트 생성
                            full_messages = messages + [{'role': 'user', 'content': processed_user_text}]
                            # AIClient.chat() 메서드를 통해 force_agent=True 전달
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
                    # 실제 토큰 사용량 추출 먼저 수행
                    actual_input_tokens, actual_output_tokens = 0, 0
                    if hasattr(client, '_last_response'):
                        actual_input_tokens, actual_output_tokens = TokenLogger.extract_actual_tokens(client._last_response)
                    
                    # 실제 토큰이 없으면 추정치 사용
                    if actual_input_tokens == 0 and actual_output_tokens == 0:
                        # 입력 텍스트 구성
                        input_text = ""
                        if messages:
                            for msg in messages:
                                if isinstance(msg, dict) and msg.get('content'):
                                    input_text += str(msg['content']) + "\n"
                        if user_text:
                            input_text += user_text
                        if file_prompt:
                            input_text += file_prompt
                        
                        actual_input_tokens = TokenLogger.estimate_tokens(input_text, model)
                        actual_output_tokens = TokenLogger.estimate_tokens(response, model)
                    
                    # AI 응답 로깅 (정확한 토큰 정보 포함)
                    response_time = time.time() - request_start_time
                    token_usage = {
                        'input_tokens': actual_input_tokens,
                        'output_tokens': actual_output_tokens
                    }
                    
                    if request_id:
                        ai_logger.log_response(
                            request_id=request_id,
                            model=model,
                            response=str(response),
                            used_tools=[str(tool) for tool in used_tools],
                            token_usage=token_usage,
                            response_time=response_time
                        )
                        
                        # 추가 상세 로깅
                        print(f"\n=== AI THINKING PROCESS LOG ===\nRequest ID: {request_id}")
                        print(f"Model: {model} | Agent Mode: {agent_mode}")
                        print(f"Input Length: {len(actual_user_input)} chars")
                        print(f"Response Length: {len(str(response))} chars")
                        print(f"Tools Used: {used_tools}")
                        print(f"Response Time: {response_time:.2f}s")
                        print(f"Tokens: IN:{token_usage.get('input_tokens', 0)} OUT:{token_usage.get('output_tokens', 0)}")
                        if hasattr(client, '_last_response') and client._last_response:
                            print(f"\n--- RAW AI RESPONSE ---\n{str(client._last_response)[:500]}...")
                    
                    logging.info(f"AI Response Type: {type(response)}")
                    logging.info(f"AI Response: {str(response)}")
                    logging.info(f"Used Tools: {used_tools}")
                    
                    # 사용된 도구 업데이트
                    for tool in used_tools:
                        status_display.add_tool_used(str(tool))
                    

                    
                    # 상태 표시에 실제 토큰 정보 업데이트
                    status_display.update_tokens(actual_input_tokens, actual_output_tokens)
                    
                    # 로그에 실제 토큰 사용량 기록
                    if hasattr(client, '_last_response') and client._last_response:
                        TokenLogger.log_actual_token_usage(model, client._last_response, "agent_chat" if agent_mode else "simple_chat")
                    else:
                        TokenLogger.log_token_usage(model, input_text, response, "agent_chat" if agent_mode else "simple_chat")
                    
                    # 상태 표시 완료
                    status_display.finish_processing(True)
                    
                    # sender에 모델 정보와 토큰 정보 포함 - TokenLogger와 동일한 형식
                    total_tokens = actual_input_tokens + actual_output_tokens
                    token_info = f" | 📊 {total_tokens:,}토큰 (IN:{actual_input_tokens:,} OUT:{actual_output_tokens:,})"
                    model_sender = f"{sender}_{model}{token_info}"
                    self.finished.emit(model_sender, response, used_tools)
                elif not self._cancelled:
                    status_display.finish_processing(False)
                    self.error.emit("응답을 생성할 수 없습니다.")
                    
            except Exception as e:
                if not self._cancelled:
                    status_display.finish_processing(False)
                    error_msg = f'오류 발생: {str(e)}'
                    self.error.emit(error_msg)
                    
                    # 오류 상세 로깅
                    print(f"\n=== ERROR LOG ===\nRequest ID: {request_id}")
                    print(f"Model: {model} | Agent Mode: {agent_mode}")
                    print(f"Error: {str(e)}")
                    print(f"Error Type: {type(e).__name__}")
                    import traceback
                    print(f"Traceback:\n{traceback.format_exc()}")
                    
                    if request_id:
                        ai_logger.log_response(
                            request_id=request_id,
                            model=model,
                            response="",
                            used_tools=[],
                            token_usage={},
                            response_time=time.time() - request_start_time,
                            error=str(e)
                        )
        
        thread = threading.Thread(target=_process, daemon=True)
        thread.start()
    
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