"""
Perplexity 모델을 위한 커스텀 에이전트 헬퍼 모듈

이 모듈은 Perplexity 모델의 응답을 LangChain이 이해할 수 있는 형식으로 변환하는
커스텀 출력 파서와 관련 유틸리티 함수를 제공합니다.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import BasePromptTemplate
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

class PerplexityOutputParser:
    """
    Perplexity 모델의 응답을 파싱하기 위한 커스텀 출력 파서
    
    LangChain의 ReAct 형식을 준수하도록 응답을 변환합니다.
    """
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """
        Perplexity 모델의 응답을 파싱하여 AgentAction 또는 AgentFinish로 변환
        
        Args:
            text: Perplexity 모델의 응답 텍스트
            
        Returns:
            AgentAction 또는 AgentFinish 객체
        """
        # Final Answer 확인
        if "Final Answer:" in text:
            # Final Answer 추출
            match = re.search(r"Final Answer:\s*(.*?)(?:$|Thought:)", text, re.DOTALL)
            if match:
                return AgentFinish(
                    return_values={"output": match.group(1).strip()},
                    log=text
                )
        
        # Action과 Action Input 추출
        action_match = re.search(r"Action:\s*(.*?)(?:\n|$)", text)
        action_input_match = re.search(r"Action Input:\s*(.*?)(?:\n|$|Observation:)", text, re.DOTALL)
        
        if action_match and action_input_match:
            action = action_match.group(1).strip()
            action_input = action_input_match.group(1).strip()
            
            # Action이 "Final Answer"인 경우 처리
            if action.lower() == "final answer":
                return AgentFinish(
                    return_values={"output": action_input},
                    log=text
                )
            
            # Action Input이 JSON 형식인지 확인하고 파싱
            try:
                if action_input.startswith("{") and action_input.endswith("}"):
                    action_input_dict = json.loads(action_input)
                else:
                    # 중괄호가 없는 경우 추가
                    action_input_dict = json.loads("{" + action_input + "}")
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 문자열 그대로 사용
                action_input_dict = {"input": action_input}
                logger.warning(f"JSON 파싱 실패: {action_input}")
            
            return AgentAction(
                tool=action,
                tool_input=action_input_dict,
                log=text
            )
        
        # 파싱 실패 시 예외 발생
        raise OutputParserException(f"Perplexity 응답 파싱 실패: {text}")
    
    def get_format_instructions(self) -> str:
        """
        Perplexity 모델에게 제공할 형식 지침 반환
        """
        return """
When using tools, you MUST follow this exact format:

Thought: [your reasoning about what to do]
Action: [tool name]
Action Input: [tool input as JSON]

After receiving the Observation, continue with:

Thought: [your reasoning about the result]
Action: [next tool name or "Final Answer" if done]
...

When you have all the information needed:

Thought: [final reasoning]
Final Answer: [your complete response to the user]

NEVER deviate from this format when using tools. ALWAYS include "Action:" immediately after "Thought:".
"""

def create_perplexity_agent(
    llm: BaseLanguageModel,
    tools: List[BaseTool],
    prompt: BasePromptTemplate
) -> Any:
    """
    Perplexity 모델을 위한 커스텀 에이전트 생성
    
    Args:
        llm: 언어 모델
        tools: 사용할 도구 목록
        prompt: 에이전트 프롬프트 템플릿
        
    Returns:
        Perplexity 모델용 커스텀 에이전트
    """
    from langchain.agents import Agent
    from langchain_core.runnables import RunnablePassthrough
    
    # 커스텀 출력 파서 생성
    output_parser = PerplexityOutputParser()
    
    # 도구 이름 목록 생성
    tool_names = [tool.name for tool in tools]
    
    # 도구 설명 생성
    tool_strings = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
    
    # 프롬프트에 도구 정보 추가
    prompt = prompt.partial(
        tools=tool_strings,
        tool_names=", ".join(tool_names),
    )
    
    # 에이전트 체인 생성
    agent = (
        RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_function_messages(
                x["intermediate_steps"]
            )
        )
        | prompt
        | llm
        | output_parser
    )
    
    # 에이전트 객체 생성
    return Agent(
        agent=agent,
        tools=tools,
        output_parser=output_parser,
        allowed_tools=tool_names,
    )

def format_to_openai_function_messages(intermediate_steps):
    """
    중간 단계 결과를 Perplexity 모델이 이해할 수 있는 형식으로 변환
    
    Args:
        intermediate_steps: 중간 단계 결과 목록
        
    Returns:
        형식화된 중간 단계 결과 문자열
    """
    if not intermediate_steps:
        return ""
    
    messages = []
    for action, observation in intermediate_steps:
        messages.append(f"Action: {action.tool}\nAction Input: {json.dumps(action.tool_input)}")
        messages.append(f"Observation: {observation}")
    
    return "\n".join(messages)