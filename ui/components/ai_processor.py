from PyQt6.QtCore import QObject, pyqtSignal
import threading


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
        if self._current_client:
            self._current_client.cancel_streaming()
    
    def process_request(self, api_key, model, messages, user_text=None, agent_mode=False, file_prompt=None):
        """AI 요청 처리"""
        def _process():
            try:
                if self._cancelled:
                    return
                
                from core.ai_client import AIClient
                client = AIClient(api_key, model)
                
                if messages:
                    client.conversation_history = messages
                    client._conversation_manager.conversation_history = messages
                
                response = None
                sender = 'AI'
                used_tools = []
                
                if file_prompt:
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
                    if agent_mode:
                        if messages:
                            result = client.agent.process_message_with_history(user_text, messages, force_agent=True)
                        else:
                            result = client.agent_chat(user_text)
                        if isinstance(result, tuple):
                            response, used_tools = result
                        else:
                            response = result
                            used_tools = []
                        sender = '에이전트'
                    else:
                        if messages:
                            response = client.agent.simple_chat_with_history(user_text, messages)
                        else:
                            response = client.simple_chat(user_text)
                        sender = 'AI'
                        used_tools = []
                
                if not self._cancelled and response:
                    self.finished.emit(sender, response, used_tools)
                elif not self._cancelled:
                    self.error.emit("응답을 생성할 수 없습니다.")
                    
            except Exception as e:
                if not self._cancelled:
                    self.error.emit(f'오류 발생: {str(e)}')
        
        thread = threading.Thread(target=_process, daemon=True)
        thread.start()