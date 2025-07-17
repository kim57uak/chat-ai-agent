"""
Perplexity API 호환성 문제를 해결하기 위한 래퍼 클래스
"""

import logging
import inspect
from typing import Any, Dict, List, Optional, Union, Iterator, Mapping
from langchain_perplexity import ChatPerplexity
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatGenerationChunk, ChatResult

logger = logging.getLogger(__name__)

class PerplexityWrapper(ChatPerplexity):
    """
    Perplexity API 호환성 문제를 해결하기 위한 강화된 래퍼 클래스
    stop_sequences 파라미터 문제를 완전히 해결합니다.
    """
    
    def __init__(self, **kwargs):
        # stop_sequences 파라미터 제거
        kwargs.pop('stop_sequences', None)
        kwargs.pop('stop', None)
        
        # 부모 클래스 초기화
        super().__init__(**kwargs)
        
        # 모델 설정에서 stop_sequences 관련 설정 제거
        if hasattr(self, 'model_kwargs'):
            self.model_kwargs.pop('stop_sequences', None)
            self.model_kwargs.pop('stop', None)
        
        logger.info("PerplexityWrapper 초기화 완료 (stop_sequences 파라미터 제거)")
    
    def invoke(self, *args, **kwargs):
        """
        invoke 메서드 오버라이드하여 stop_sequences 파라미터 제거
        """
        # stop_sequences 파라미터 제거
        kwargs.pop('stop_sequences', None)
        kwargs.pop('stop', None)
        
        # 부모 클래스의 invoke 메서드 호출
        return super().invoke(*args, **kwargs)
    
    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """
        _stream 메서드 오버라이드하여 stop_sequences 파라미터 제거
        """
        # stop_sequences 파라미터 제거
        kwargs.pop('stop_sequences', None)
        kwargs.pop('stop', None)
        
        # stop 파라미터를 None으로 설정 (Perplexity API에서 지원하지 않음)
        stop = None
        
        # 부모 클래스의 _stream 메서드 호출
        return super()._stream(messages, stop=stop, run_manager=run_manager, **kwargs)
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        _generate 메서드 오버라이드하여 stop_sequences 파라미터 제거
        """
        # stop_sequences 파라미터 제거
        kwargs.pop('stop_sequences', None)
        kwargs.pop('stop', None)
        
        # stop 파라미터를 None으로 설정 (Perplexity API에서 지원하지 않음)
        stop = None
        
        # 부모 클래스의 _generate 메서드 호출
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
    
    def _create_message_dicts(
        self, messages: List[BaseMessage], stop: Optional[List[str]]
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        _create_message_dicts 메서드 오버라이드하여 stop_sequences 파라미터 제거
        """
        # 부모 클래스의 _create_message_dicts 메서드 호출
        message_dicts, params = super()._create_message_dicts(messages, None)  # stop을 None으로 설정
        
        # stop 파라미터 제거
        params.pop('stop', None)
        params.pop('stop_sequences', None)
        
        return message_dicts, params
    
    def _call(self, *args, **kwargs):
        """
        _call 메서드 오버라이드하여 stop_sequences 파라미터 제거
        """
        # stop_sequences 파라미터 제거
        kwargs.pop('stop_sequences', None)
        kwargs.pop('stop', None)
        
        # 부모 클래스의 _call 메서드 호출
        return super()._call(*args, **kwargs)
    
    @property
    def _invocation_params(self) -> Mapping[str, Any]:
        """
        _invocation_params 프로퍼티 오버라이드하여 stop_sequences 파라미터 제거
        """
        params = super()._invocation_params
        
        # dict 복사 후 stop_sequences 파라미터 제거
        params_copy = dict(params)
        params_copy.pop('stop_sequences', None)
        params_copy.pop('stop', None)
        
        return params_copy