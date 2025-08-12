import requests
import json
import logging
from typing import List, Dict, Any, Optional, Iterator
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM

logger = logging.getLogger(__name__)


class ClaudeWrapper(LLM):
    """AWS Bedrock API Key Claude 모델 래퍼"""
    
    model: str = "us.anthropic.claude-3-haiku-20240307-v1:0"
    api_key: Optional[str] = None
    region_name: str = "us-east-1"
    temperature: float = 0.1
    max_tokens: int = 4096
    streaming: bool = False
    request_timeout: int = 120
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # API 키를 aws_access_key_id에서 가져오기
        if 'aws_access_key_id' in kwargs:
            self.api_key = kwargs['aws_access_key_id']
    
    @property
    def _llm_type(self) -> str:
        return "claude_bedrock_api"
    
    def _get_bedrock_url(self) -> str:
        """Bedrock API URL 생성"""
        return f"https://bedrock-runtime.{self.region_name}.amazonaws.com/model/{self.model}/invoke"
    
    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Claude 모델 호출"""
        try:
            if not self.api_key:
                return "안녕하세요! Claude 모델입니다. BEDROCK_API_KEY 설정이 필요합니다."
            
            data = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                self._get_bedrock_url(),
                headers=self._get_headers(),
                json=data,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                logger.error(f"Bedrock API 오류: {response.status_code} - {response.text}")
                return "안녕하세요! Claude 모델입니다. 현재 연결에 문제가 있어 모킹 응답을 드립니다."
            
        except Exception as e:
            logger.error(f"Claude 모델 호출 오류: {e}")
            return "안녕하세요! Claude 모델입니다. 현재 연결에 문제가 있어 모킹 응답을 드립니다."
    
    def invoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """LangChain 호환 invoke 메서드"""
        try:
            if not self.api_key:
                return AIMessage(content="안녕하세요! Claude 모델입니다. BEDROCK_API_KEY 설정이 필요합니다.")
            
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
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": claude_messages
            }
            
            if system_message:
                data["system"] = system_message
            
            response = requests.post(
                self._get_bedrock_url(),
                headers=self._get_headers(),
                json=data,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                return AIMessage(content=content)
            else:
                logger.error(f"Bedrock API 오류: {response.status_code} - {response.text}")
                return AIMessage(content="안녕하세요! Claude 모델입니다. 현재 연결에 문제가 있어 모킹 응답을 드립니다.")
            
        except Exception as e:
            logger.error(f"Claude invoke 오류: {e}")
            return AIMessage(content="안녕하세요! Claude 모델입니다. 현재 연결에 문제가 있어 모킹 응답을 드립니다.")
    
    def _stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Claude 스트리밍 응답"""
        try:
            from langchain_core.outputs import GenerationChunk
            
            response = self._call(prompt, stop, run_manager, **kwargs)
            words = response.split()
            for word in words:
                chunk_text = word + " "
                if run_manager:
                    run_manager.on_llm_new_token(chunk_text)
                yield GenerationChunk(text=chunk_text)
                        
        except Exception as e:
            logger.error(f"Claude 스트리밍 오류: {e}")
            from langchain_core.outputs import GenerationChunk
            yield GenerationChunk(text=f"스트리밍 중 오류가 발생했습니다: {str(e)}")
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """모델 식별 파라미터"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "region_name": self.region_name
        }