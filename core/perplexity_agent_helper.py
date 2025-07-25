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
        logger.info(f"[PerplexityOutputParser] 원본 응답(앞 200자): {text[:200]}")

        # 1. Final Answer 뒤에 Action/Action Input이 붙어 있는 경우 우선 파싱
        # 예: Final Answer: ... Action: tool_name Action Input: {...}
        final_answer_action_block = re.search(
            r"Final Answer:.*?(Action:\s*.*?Action Input:\s*.*?)(?:\n|$)", text, re.DOTALL
        )
        if final_answer_action_block:
            logger.info("[PerplexityOutputParser] Final Answer 뒤에 Action/Action Input 블록 감지, 도구 실행 우선 트리거")
            # Action/Action Input 블록만 파싱 재귀 호출
            action_block_text = final_answer_action_block.group(1)
            # Action/Action Input만 남기고 parse 재귀 호출
            return self.parse(action_block_text)

        # 2. Action/Action Input이 Observation 없이 단독으로 있는 경우도 도구 실행 트리거
        action_match = re.search(r"Action:\s*(.*?)(?:\n|$)", text)
        action_input_match = re.search(r"Action Input:\s*(.*?)(?:\n|$)", text, re.DOTALL)
        if action_match and action_input_match:
            action = action_match.group(1).strip()
            action_input = action_input_match.group(1).strip()
            logger.info(f"[PerplexityOutputParser] Observation 없이 Action/Action Input만 감지: {action}, {action_input[:50]}...")
            # 이하 기존 Action/Action Input 파싱 로직 복사
            if action.lower() == "final answer":
                final_answer_match = re.search(r"Final Answer:\s*(.*?)(?:$|Thought:)", text, re.DOTALL)
                if final_answer_match:
                    final_answer = final_answer_match.group(1).strip()
                    logger.info(f"[PerplexityOutputParser] Action이 Final Answer, Final Answer 섹션 사용: {final_answer[:50]}...")
                    return AgentFinish(
                        return_values={"output": final_answer},
                        log=text
                    )
                else:
                    logger.info(f"[PerplexityOutputParser] Action이 Final Answer, Action Input 사용: {action_input[:50]}...")
                    return AgentFinish(
                        return_values={"output": action_input},
                        log=text
                    )
            try:
                action_input = action_input.strip()
                if "Observation:" in action_input:
                    action_input = action_input.split("Observation:")[0].strip()
                    logger.debug(f"[PerplexityOutputParser] Observation 태그 제거: {action_input[:50]}...")
                if action_input.count('"') % 2 != 0:
                    logger.debug(f"[PerplexityOutputParser] 따옴표 불일치 감지, 모두 제거: {action_input[:50]}...")
                    action_input = action_input.replace('"', '')
                action_input_dict = None
                try:
                    if action_input.startswith("{") and action_input.endswith("}"):
                        action_input_dict = json.loads(action_input)
                    elif action_input.startswith("{") and not action_input.endswith("}"):
                        action_input_dict = json.loads(action_input + "}")
                    elif not action_input.startswith("{") and action_input.endswith("}"):
                        action_input_dict = json.loads("{" + action_input)
                    elif re.search(r'[=:]', action_input):
                        pairs = re.findall(r'"?([\w_]+)"?\s*[:=]\s*"?([^,\"\n}}]*)"?', action_input)
                        if pairs:
                            action_input_dict = {k.strip(): v.strip() for k, v in pairs}
                    if action_input_dict is None:
                        action_input_dict = {"input": action_input}
                except Exception as e:
                    logger.warning(f"[PerplexityOutputParser] JSON 파싱 실패(1차): {action_input}, 오류: {str(e)}")
                    action_input_dict = {"input": action_input}
            except Exception as e:
                logger.error(f"[PerplexityOutputParser] Action Input 파싱 예외: {str(e)} | 원본: {action_input}")
                action_input_dict = {"input": action_input}
            logger.debug(f"[PerplexityOutputParser] 최종 Action Input 파싱 결과: {action_input_dict}")
            return AgentAction(
                tool=action,
                tool_input=action_input_dict,
                log=text
            )

        # 이하 기존 로직 유지
        # Final Answer 확인
        if "Final Answer:" in text:
            match = re.search(r"Final Answer:\s*(.*?)(?:$|Thought:)", text, re.DOTALL)
            if match:
                final_answer = match.group(1).strip()
                logger.info(f"[PerplexityOutputParser] Final Answer 추출 성공: {final_answer[:50]}...")
                return AgentFinish(
                    return_values={"output": final_answer},
                    log=text
                )
            else:
                logger.warning("[PerplexityOutputParser] Final Answer 태그는 있으나 추출 실패")
        
        # Action과 Action Input 추출
        action_match = re.search(r"Action:\s*(.*?)(?:\n|$)", text)
        action_input_match = re.search(r"Action Input:\s*(.*?)(?:\n\s*Observation:|\n\s*Thought:|\n\s*Final Answer:|$)", text, re.DOTALL)
        
        if action_match and action_input_match:
            action = action_match.group(1).strip()
            action_input = action_input_match.group(1).strip()
            logger.info(f"[PerplexityOutputParser] Action/Action Input 추출 성공: {action}, {action_input[:50]}...")
            # Action이 "Final Answer"인 경우 처리
            if action.lower() == "final answer":
                final_answer_match = re.search(r"Final Answer:\s*(.*?)(?:$|Thought:)", text, re.DOTALL)
                if final_answer_match:
                    final_answer = final_answer_match.group(1).strip()
                    logger.info(f"[PerplexityOutputParser] Action이 Final Answer, Final Answer 섹션 사용: {final_answer[:50]}...")
                    return AgentFinish(
                        return_values={"output": final_answer},
                        log=text
                    )
                else:
                    logger.info(f"[PerplexityOutputParser] Action이 Final Answer, Action Input 사용: {action_input[:50]}...")
                    return AgentFinish(
                        return_values={"output": action_input},
                        log=text
                    )
            # Action Input이 JSON 형식인지 확인하고 파싱
            try:
                action_input = action_input.strip()
                if "Observation:" in action_input:
                    action_input = action_input.split("Observation:")[0].strip()
                    logger.debug(f"[PerplexityOutputParser] Observation 태그 제거: {action_input[:50]}...")
                if action_input.count('"') % 2 != 0:
                    logger.debug(f"[PerplexityOutputParser] 따옴표 불일치 감지, 모두 제거: {action_input[:50]}...")
                    action_input = action_input.replace('"', '')
                # JSON 파싱 시도 (더 유연하게)
                action_input_dict = None
                try:
                    if action_input.startswith("{") and action_input.endswith("}"):
                        action_input_dict = json.loads(action_input)
                    elif action_input.startswith("{") and not action_input.endswith("}"):
                        action_input_dict = json.loads(action_input + "}")
                    elif not action_input.startswith("{") and action_input.endswith("}"):
                        action_input_dict = json.loads("{" + action_input)
                    elif re.search(r'[=:]', action_input):
                        # 키-값 쌍 패턴
                        pairs = re.findall(r'"?([\w_]+)"?\s*[:=]\s*"?([^,\"\n}}]*)"?', action_input)
                        if pairs:
                            action_input_dict = {k.strip(): v.strip() for k, v in pairs}
                    if action_input_dict is None:
                        # 중괄호 없는 경우, 키-값 쌍이 아니면 일반 문자열 처리
                        action_input_dict = {"input": action_input}
                except Exception as e:
                    logger.warning(f"[PerplexityOutputParser] JSON 파싱 실패(1차): {action_input}, 오류: {str(e)}")
                    action_input_dict = {"input": action_input}
            except Exception as e:
                logger.error(f"[PerplexityOutputParser] Action Input 파싱 예외: {str(e)} | 원본: {action_input}")
                action_input_dict = {"input": action_input}
            logger.debug(f"[PerplexityOutputParser] 최종 Action Input 파싱 결과: {action_input_dict}")
            return AgentAction(
                tool=action,
                tool_input=action_input_dict,
                log=text
            )
        # 추가 파싱 시도: 일반적인 패턴이 아닌 경우
        action_blocks = re.findall(r"Action:\s*(.*?)\s*Action Input:\s*(.*?)(?:\n\s*Observation:|\n\s*Thought:|\n\s*Final Answer:|$)", text, re.DOTALL)
        if not action_blocks and "Action:" in text and "Action Input:" in text:
            logger.debug("[PerplexityOutputParser] 유연한 패턴으로 Action/Action Input 재탐색")
            action_match = re.search(r"Action:\s*(.*?)(?:\n|$)", text)
            if action_match:
                action = action_match.group(1).strip()
                action_input_match = re.search(r"Action Input:\s*(.*?)(?:\n\s*Observation:|\n\s*Thought:|\n\s*Final Answer:|$)", text[text.find("Action Input:"):], re.DOTALL)
                if action_input_match:
                    action_input = action_input_match.group(1).strip()
                    action_blocks = [(action, action_input)]
        if action_blocks:
            action, action_input = action_blocks[-1]
            action = action.strip()
            action_input = action_input.strip()
            logger.info(f"[PerplexityOutputParser] 대체 패턴 Action/Action Input 추출: {action}, {action_input[:50]}...")
            if action.lower() == "final answer":
                final_answer_match = re.search(r"Final Answer:\s*(.*?)(?:$|Thought:)", text, re.DOTALL)
                if final_answer_match:
                    final_answer = final_answer_match.group(1).strip()
                    logger.info(f"[PerplexityOutputParser] 대체 패턴 Final Answer 섹션 사용: {final_answer[:50]}...")
                    return AgentFinish(
                        return_values={"output": final_answer},
                        log=text
                    )
                else:
                    logger.info(f"[PerplexityOutputParser] 대체 패턴 Action Input 사용: {action_input[:50]}...")
                    return AgentFinish(
                        return_values={"output": action_input},
                        log=text
                    )
            # Action Input JSON 파싱 시도 (유연하게)
            try:
                action_input_dict = None
                try:
                    if action_input.startswith("{") and action_input.endswith("}"):
                        action_input_dict = json.loads(action_input)
                    elif re.search(r'[=:]', action_input):
                        pairs = re.findall(r'"?([\w_]+)"?\s*[:=]\s*"?([^,\"\n}}]*)"?', action_input)
                        if pairs:
                            action_input_dict = {k.strip(): v.strip() for k, v in pairs}
                    if action_input_dict is None:
                        action_input_dict = {"input": action_input}
                except Exception as e:
                    logger.warning(f"[PerplexityOutputParser] 대체 패턴 JSON 파싱 실패: {action_input}, 오류: {str(e)}")
                    action_input_dict = {"input": action_input}
            except Exception as e:
                logger.error(f"[PerplexityOutputParser] 대체 패턴 Action Input 파싱 예외: {str(e)} | 원본: {action_input}")
                action_input_dict = {"input": action_input}
            logger.debug(f"[PerplexityOutputParser] 대체 패턴 최종 Action Input 파싱 결과: {action_input_dict}")
            return AgentAction(
                tool=action,
                tool_input=action_input_dict,
                log=text
            )
        # Final Answer만 있는 경우 추가 처리
        final_answer_match = re.search(r"Final Answer:\s*(.*?)(?:$|Thought:)", text, re.DOTALL)
        if final_answer_match:
            final_answer = final_answer_match.group(1).strip()
            logger.info(f"[PerplexityOutputParser] Final Answer만 추출: {final_answer[:50]}...")
            return AgentFinish(
                return_values={"output": final_answer},
                log=text
            )
        # 어떠한 패턴도 찾을 수 없는 경우 마지막 수단으로 전체 텍스트를 최종 응답으로 처리
        logger.error(f"[PerplexityOutputParser] 표준 포맷 파싱 실패, 전체 응답을 Final Answer로 처리. 원본(앞 200자): {text[:200]}")
        cleaned_text = re.sub(r'(Thought:|Action:|Action Input:|Observation:|Final Answer:)\s*', '', text)
        return AgentFinish(
            return_values={"output": cleaned_text.strip()},
            log=text
        )
        
    
    def get_format_instructions(self) -> str:
        """
        Perplexity 모델에게 제공할 형식 지침 반환
        """
        return """
When using tools, you MUST follow this exact format:

Thought: [your reasoning about what to do]
Action: [tool name]
Action Input: [tool input as valid JSON with proper quotes and braces]

After receiving the Observation, continue with:

Thought: [your reasoning about the result]
Action: [next tool name or "Final Answer" if done]
...

When you have all the information needed:

Thought: [final reasoning]
Final Answer: [your complete response to the user]

CRITICAL REQUIREMENTS:
1. NEVER deviate from this format when using tools.
2. ALWAYS include "Action:" immediately after "Thought:".
3. ALWAYS format Action Input as valid JSON with proper quotes and braces.
4. ALWAYS include a "Final Answer:" when you have the final response.
5. Make sure all JSON is properly formatted with quotes around keys and string values.
6. NEVER skip any of the required sections (Thought, Action, Action Input).

Example of correct JSON format for Action Input:
Action Input: {"query": "search term", "filter": "recent"}

Incorrect format (avoid):
Action Input: query: search term, filter: recent
"""

class PerplexityAgent:
    """
    Perplexity 모델을 위한 독립적인 에이전트 클래스
    """
    
    def __init__(self, llm: BaseLanguageModel, tools: List[BaseTool], prompt: BasePromptTemplate):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.prompt = prompt
        self.parser = PerplexityOutputParser()
        
    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 실행"""
        user_input = inputs.get("input", "")
        max_iterations = 10
        intermediate_steps = []
        
        for i in range(max_iterations):
            # 프롬프트 준비
            tool_strings = "\n".join([f"{name}: {tool.description}" for name, tool in self.tools.items()])
            tool_names = ", ".join(self.tools.keys())
            
            # 중간 단계 포맷팅
            scratchpad = "\n".join([
                f"Action: {action.tool}\nAction Input: {json.dumps(action.tool_input)}\nObservation: {observation}"
                for action, observation in intermediate_steps
            ])
            
            # 프롬프트 포맷팅
            formatted_prompt = self.prompt.format(
                input=user_input,
                tools=tool_strings,
                tool_names=tool_names,
                agent_scratchpad=scratchpad
            )
            
            # LLM 호출
            response = self.llm.invoke(formatted_prompt)
            text = response.content if hasattr(response, 'content') else str(response)
            
            # 파싱
            try:
                result = self.parser.parse(text)
                
                if isinstance(result, AgentFinish):
                    return {"output": result.return_values["output"]}
                    
                elif isinstance(result, AgentAction):
                    # 도구 실행
                    tool_name = result.tool
                    if tool_name in self.tools:
                        try:
                            observation = self.tools[tool_name].invoke(result.tool_input)
                            intermediate_steps.append((result, str(observation)))
                        except Exception as e:
                            observation = f"Error: {str(e)}"
                            intermediate_steps.append((result, observation))
                    else:
                        observation = f"Tool '{tool_name}' not found"
                        intermediate_steps.append((result, observation))
                        
            except Exception as e:
                return {"output": f"Parsing error: {str(e)}"}
                
        return {"output": "Maximum iterations reached"}

def create_perplexity_agent(
    llm: BaseLanguageModel,
    tools: List[BaseTool],
    prompt: BasePromptTemplate
) -> PerplexityAgent:
    """
    Perplexity 모델을 위한 커스텀 에이전트 생성
    
    Args:
        llm: 언어 모델
        tools: 사용할 도구 목록
        prompt: 에이전트 프롬프트 템플릿
        
    Returns:
        Perplexity 모델용 커스텀 에이전트
    """
    return PerplexityAgent(llm, tools, prompt)

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