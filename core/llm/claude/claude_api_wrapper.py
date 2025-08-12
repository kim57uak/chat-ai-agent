import requests
import json
import logging
from typing import List, Dict, Any, Optional, Iterator
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM

logger = logging.getLogger(__name__)


class ClaudeAPIWrapper(LLM):
    """실제 Anthropic Claude API 래퍼"""
    
    model: str = "claude-3-sonnet-20240229"
    api_key: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4096
    streaming: bool = False
    request_timeout: int = 120
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'anthropic_api_key' in kwargs:
            self.api_key = kwargs['anthropic_api_key']
    
    @property
    def _llm_type(self) -> str:
        return "claude_api"
    
    def _get_api_url(self) -> str:
        """Anthropic API URL"""
        return "https://api.anthropic.com/v1/messages"
    
    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더"""
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Claude API 호출"""
        try:
            if not self.api_key:
                return "Claude API 키가 설정되지 않았습니다. 환경설정에서 Anthropic API 키를 입력해주세요."
            
            data = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                self._get_api_url(),
                headers=self._get_headers(),
                json=data,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                logger.error(f"Claude API 오류: {response.status_code} - {response.text}")
                return f"Claude API 오류가 발생했습니다. 상태 코드: {response.status_code}"
            
        except Exception as e:
            logger.error(f"Claude API 호출 오류: {e}")
            return f"Claude API 연결 오류: {str(e)}"
    
    def invoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """LangChain 호환 invoke 메서드"""
        try:
            if not self.api_key:
                return AIMessage(content="Claude API 키가 설정되지 않았습니다.")
            
            # 메시지를 Claude 형식으로 변환
            claude_messages = []
            system_message = ""
            
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    system_message = msg.content
                elif isinstance(msg, HumanMessage):
                    claude_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    claude_messages.append({"role": "assistant", "content": msg.content})
            
            data = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": claude_messages
            }
            
            if system_message:
                data["system"] = system_message
            
            response = requests.post(
                self._get_api_url(),
                headers=self._get_headers(),
                json=data,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                return AIMessage(content=content)
            else:
                logger.error(f"Claude API 오류: {response.status_code} - {response.text}")
                return AIMessage(content=f"Claude API 오류: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Claude invoke 오류: {e}")
            return AIMessage(content=f"Claude API 연결 오류: {str(e)}")
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """모델 식별 파라미터"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }