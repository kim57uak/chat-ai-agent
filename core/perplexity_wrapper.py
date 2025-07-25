"""
Perplexity LLM을 위한 LangChain 호환 래퍼
단순하고 확장 가능한 구현
"""

import logging
from typing import Any, Dict, List, Optional, Iterator
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import GenerationChunk
from core.perplexity_llm import PerplexityLLM

logger = logging.getLogger(__name__)


class PerplexityWrapper(LLM):
    """
    Perplexity LLM을 LangChain과 호환되도록 하는 단순한 래퍼
    복잡한 기능 대신 핵심 기능에 집중
    """
    
    # Pydantic 모델 필드 선언
    perplexity_llm: Any = None
    
    def __init__(self, pplx_api_key: str, model: str = None, **kwargs):
        super().__init__(**kwargs)
        self.perplexity_llm = PerplexityLLM(
            api_key=pplx_api_key,
            model_name=model
        )
    
    @property
    def _llm_type(self) -> str:
        """LLM 타입 식별자"""
        return "perplexity"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """프롬프트를 처리하여 응답 생성"""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.perplexity_llm.generate(messages, **kwargs)
            
            if run_manager:
                run_manager.on_llm_new_token(response)
            
            return response
        except Exception as e:
            logger.error(f"Perplexity API call failed: {e}")
            raise
    
    def _stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        """스트리밍은 현재 미지원"""
        # Perplexity는 스트리밍을 제한적으로 지원하므로 일반 호출로 대체
        response = self._call(prompt, stop, run_manager, **kwargs)
        yield GenerationChunk(text=response)
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """모델 식별 파라미터"""
        return {
            "model_name": self.perplexity_llm.get_model_name(),
            "llm_type": self._llm_type,
        }