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
    
    def invoke(self, input, config=None, **kwargs):
        """LangChain invoke 메서드 오버라이드 - 메시지 리스트 처리"""
        # 저장된 파라미터 병합
        if hasattr(self, '_model_params'):
            kwargs.update(self._model_params)
        
        try:
            # BaseMessage 리스트인 경우 직접 처리
            if isinstance(input, list):
                messages = []
                logger.info(f"Perplexity 입력 메시지 수: {len(input)}")
                
                for i, msg in enumerate(input):
                    if hasattr(msg, 'type') and hasattr(msg, 'content'):
                        if msg.type == 'system':
                            role = 'system'
                        elif msg.type == 'human':
                            role = 'user'
                        elif msg.type == 'ai':
                            role = 'assistant'
                        else:
                            role = 'user'
                        
                        content = msg.content
                        messages.append({"role": role, "content": content})
                        
                        # 대화 히스토리 로깅
                        content_preview = content[:50] + '...' if len(content) > 50 else content
                        logger.info(f"  변환된 메시지 {i+1}: {role} - {content_preview}")
                        
                    elif isinstance(msg, dict):
                        messages.append(msg)
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        content_preview = content[:50] + '...' if len(content) > 50 else content
                        logger.info(f"  딕셔너리 메시지 {i+1}: {role} - {content_preview}")
                
                # Perplexity API 형식에 맞게 메시지 정리
                cleaned_messages = self._fix_message_alternation(messages)
                
                logger.info(f"Perplexity에 최종 전달되는 메시지 수: {len(cleaned_messages)}")
                response = self.perplexity_llm.generate(cleaned_messages, **kwargs)
                return response
            else:
                # 문자열인 경우 기존 방식 사용
                logger.info(f"Perplexity 단일 문자열 입력: {str(input)[:50]}...")
                return self._call(str(input), **kwargs)
                
        except Exception as e:
            logger.error(f"Perplexity invoke failed: {e}")
            # 실패 시 기존 방식으로 대체
            return self._call(str(input), **kwargs)
    
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
    
    def _fix_message_alternation(self, messages: List[Dict]) -> List[Dict]:
        """Perplexity API 형식에 맞게 메시지 교대 패턴 수정"""
        if not messages:
            return messages
        
        fixed_messages = []
        last_role = None
        
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')
            
            if role == last_role and role == 'user':
                # 연속된 user 메시지는 병합
                if fixed_messages and fixed_messages[-1]['role'] == 'user':
                    fixed_messages[-1]['content'] += f"\n\n{content}"
                    logger.info(f"연속된 user 메시지 병합: {content[:30]}...")
                else:
                    fixed_messages.append(msg)
            else:
                fixed_messages.append(msg)
            
            last_role = role
        
        return fixed_messages
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """모델 식별 파라미터"""
        return {
            "model_name": self.perplexity_llm.get_model_name(),
            "llm_type": self._llm_type,
        }