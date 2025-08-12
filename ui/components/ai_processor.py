from PyQt6.QtCore import QObject, pyqtSignal
import threading
from ui.components.status_display import status_display
from core.token_logger import TokenLogger


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
            try:
                if self._cancelled:
                    return
                
                # 상태 표시 시작
                mode = 'agent' if agent_mode else 'ask'
                status_display.start_processing(model, mode)
                
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
                
                if file_prompt:
                    # 파일 프롬프트 처리
                    if agent_mode:
                        result = client.agent_chat(file_prompt)
                        if isinstance(result, tuple):
                            response, used_tools = result
                        else:
                            response = result
                            used_tools = []
                        sender = '에이전트'
                    else:
                        response = client.simple_chat(file_prompt)
                        sender = 'AI'
                        used_tools = []
                else:
                    # 일반 텍스트 처리
                    if agent_mode:
                        # 에이전트 모드: 도구 사용 가능
                        if messages:
                            # 히스토리를 포함한 메시지 리스트 생성
                            full_messages = messages + [{'role': 'user', 'content': user_text}]
                            # AIClient.chat() 메서드를 통해 force_agent=True 전달
                            result = client.chat(full_messages, force_agent=True)
                            if isinstance(result, tuple):
                                response, used_tools = result
                            else:
                                response = result
                                used_tools = []
                        else:
                            result = client.agent_chat(user_text)
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
                            full_messages = messages + [{'role': 'user', 'content': user_text}]
                            result = client.chat(full_messages, force_agent=False)
                            if isinstance(result, tuple):
                                response, used_tools = result
                            else:
                                response = result
                                used_tools = []
                        else:
                            response = client.simple_chat(user_text)
                            used_tools = []
                        sender = 'AI'
                
                if not self._cancelled and response:
                    # 사용된 도구 업데이트
                    for tool in used_tools:
                        status_display.add_tool_used(str(tool))
                    
                    # 토큰 사용량 계산 및 업데이트
                    input_text = ""
                    if messages:
                        for msg in messages:
                            if isinstance(msg, dict) and msg.get('content'):
                                input_text += str(msg['content']) + "\n"
                    if user_text:
                        input_text += user_text
                    if file_prompt:
                        input_text += file_prompt
                    
                    input_tokens = TokenLogger.estimate_tokens(input_text, model)
                    output_tokens = TokenLogger.estimate_tokens(response, model)
                    
                    # 상태 표시에 토큰 정보 업데이트
                    status_display.update_tokens(input_tokens, output_tokens)
                    
                    # 상태 표시 완료
                    status_display.finish_processing(True)
                    
                    # sender에 모델 정보 포함
                    model_sender = f"{sender}_{model}"
                    self.finished.emit(model_sender, response, used_tools)
                elif not self._cancelled:
                    status_display.finish_processing(False)
                    self.error.emit("응답을 생성할 수 없습니다.")
                    
            except Exception as e:
                if not self._cancelled:
                    status_display.finish_processing(False)
                    self.error.emit(f'오류 발생: {str(e)}')
        
        thread = threading.Thread(target=_process, daemon=True)
        thread.start()