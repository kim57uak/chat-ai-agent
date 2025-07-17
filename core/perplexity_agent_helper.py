"""
Perplexity 모델을 위한 커스텀 에이전트 헬퍼 함수
"""

import logging
import copy
from typing import Any, List, Optional
from langchain.agents import Agent
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from core.perplexity_wrapper import PerplexityWrapper

logger = logging.getLogger(__name__)

def create_perplexity_agent(
    llm: Any,
    tools: List[BaseTool],
    prompt: PromptTemplate,
) -> Agent:
    """
    Perplexity 모델을 위한 커스텀 ReAct 에이전트 생성
    stop_sequences 파라미터 문제를 해결하기 위한 특별 처리
    """
    try:
        # 기본 ReAct 에이전트 생성 시도
        from langchain.agents import create_react_agent
        
        # LLM이 PerplexityWrapper가 아니면 래핑
        if not isinstance(llm, PerplexityWrapper):
            logger.info("LLM을 PerplexityWrapper로 래핑합니다")
            # LLM 객체의 속성 추출
            kwargs = {}
            for key, value in llm.__dict__.items():
                if not key.startswith('_') and key != 'client':
                    kwargs[key] = value
            
            # PerplexityWrapper 생성
            modified_llm = PerplexityWrapper(**kwargs)
        else:
            modified_llm = llm
        
        logger.info("Perplexity 모델용 커스텀 에이전트 생성 시작")
        agent = create_react_agent(modified_llm, tools, prompt)
        logger.info("Perplexity 모델용 커스텀 에이전트 생성 완료")
        return agent
        
    except Exception as e:
        logger.error(f"Perplexity 에이전트 생성 오류: {e}")
        
        # 폴백: 간단한 에이전트 생성 시도
        try:
            from langchain.agents.react.base import ReActDocstoreAgent
            
            # 간단한 ReAct 에이전트 생성
            agent = ReActDocstoreAgent.from_llm_and_tools(
                llm=llm,
                tools=tools,
                prompt=prompt,
                handle_parsing_errors=True
            )
            logger.info("Perplexity 모델용 폴백 에이전트 생성 완료")
            return agent
            
        except Exception as fallback_error:
            logger.error(f"폴백 에이전트 생성 오류: {fallback_error}")
            
            # 최종 폴백: 기본 ReAct 에이전트 생성 시도
            from langchain.agents import create_react_agent
            return create_react_agent(llm, tools, prompt)