"""
Perplexity LLM을 위한 LangChain 호환 래퍼
단순하고 확장 가능한 구현
"""

from core.logging import get_logger
from typing import Any, Dict, List, Optional, Iterator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from core.perplexity_llm import PerplexityLLM

logger = get_logger("perplexity_wrapper")


class PerplexityWrapper(BaseChatModel):
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
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """메시지를 처리하여 ChatResult 생성"""
        try:
            # BaseMessage를 dict로 변환
            api_messages = []
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    api_messages.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    api_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    api_messages.append({"role": "assistant", "content": msg.content})
            
            # Perplexity API 호출
            response_text = self.perplexity_llm.generate(api_messages, **kwargs)
            
            # ChatGeneration 생성
            message = AIMessage(content=response_text)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
        except Exception as e:
            logger.error(f"Perplexity API call failed: {e}")
            raise
    

    

    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """모델 식별 파라미터"""
        return {
            "model_name": self.perplexity_llm.get_model_name(),
            "llm_type": self._llm_type,
        }