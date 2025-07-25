import re
import json
import logging
from typing import Union
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.output_parsers import BaseOutputParser

logger = logging.getLogger(__name__)


class PerplexityOutputParser(BaseOutputParser):
    """Perplexity 모델을 위한 단순하고 관대한 출력 파서"""
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """텍스트를 파싱하여 AgentAction 또는 AgentFinish 반환"""
        logger.debug(f"Perplexity 파싱 시작: {text[:200]}...")
        
        try:
            # 텍스트 정리
            cleaned_text = text.strip()
            
            # Final Answer 우선 확인 (가장 마지막 것 사용)
            final_answer_matches = list(re.finditer(r'Final Answer:\s*(.*?)(?=\n(?:Thought|Action)|$)', cleaned_text, re.DOTALL | re.IGNORECASE))
            if final_answer_matches:
                final_answer = final_answer_matches[-1].group(1).strip()
                # 불필요한 내용 제거
                final_answer = re.sub(r'For troubleshooting.*$', '', final_answer, flags=re.DOTALL).strip()
                if final_answer and len(final_answer) > 5:
                    logger.info(f"Final Answer 발견: {final_answer[:100]}...")
                    return AgentFinish(
                        return_values={"output": final_answer},
                        log=cleaned_text
                    )
            
            # Action 찾기 (가장 마지막 것 사용)
            action_matches = list(re.finditer(r'Action:\s*([^\n]+)', cleaned_text, re.IGNORECASE))
            if action_matches:
                action_match = action_matches[-1]
                action = action_match.group(1).strip()
                
                # Action Input 찾기
                remaining_text = cleaned_text[action_match.end():]
                action_input_match = re.search(r'Action Input:\s*([^\n]+)', remaining_text, re.IGNORECASE)
                
                if action_input_match:
                    action_input_str = action_input_match.group(1).strip()
                    action_input = self._parse_action_input(action_input_str)
                    
                    logger.info(f"Action 발견: {action}, Input: {action_input_str[:50]}...")
                    return AgentAction(
                        tool=action,
                        tool_input=action_input,
                        log=cleaned_text
                    )
                else:
                    # Action Input이 없으면 빈 입력으로 처리
                    logger.info(f"Action 발견 (빈 입력): {action}")
                    return AgentAction(
                        tool=action,
                        tool_input={},
                        log=cleaned_text
                    )
            
            # Thought만 있는 경우 - 계속 진행
            if re.search(r'Thought:\s*', cleaned_text, re.IGNORECASE):
                logger.warning("Thought만 발견됨, 빈 Action 반환")
                return AgentAction(
                    tool="",
                    tool_input={},
                    log=cleaned_text
                )
            
            # 아무것도 찾지 못한 경우 - 전체 텍스트를 Final Answer로 처리
            logger.warning(f"파싱 실패, 전체 텍스트를 Final Answer로 처리: {cleaned_text[:100]}...")
            return AgentFinish(
                return_values={"output": cleaned_text},
                log=cleaned_text
            )
            
        except Exception as e:
            logger.error(f"Perplexity 파싱 오류: {e}")
            return AgentFinish(
                return_values={"output": text.strip()},
                log=text
            )
    
    def _extract_final_answer(self, text: str) -> str:
        """Final Answer 추출 - Action이 있으면 무시"""
        # Action이 있으면 Final Answer 무시
        if "Action:" in text and "Action Input:" in text:
            return ""
        
        match = re.search(r"Final Answer:\s*(.*?)(?:\n|$)", text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_action(self, text: str) -> dict:
        """Action과 Action Input 추출"""
        action_match = re.search(r"Action:\s*([^\n]+)", text)
        if not action_match:
            return None
        
        action = action_match.group(1).strip()
        action_input = self._extract_action_input(text)
        
        return {
            "tool": action,
            "input": action_input
        }
    
    def _parse_action_input(self, action_input: str) -> dict:
        """Action Input 파싱"""
        if not action_input or action_input.lower() == "none":
            return {}
        
        # JSON 파싱 시도
        try:
            if action_input.startswith('{') and action_input.endswith('}'):
                return json.loads(action_input)
        except json.JSONDecodeError:
            pass
        
        # 경로나 단순 문자열인 경우 path로 처리
        if action_input.startswith('/') or action_input.startswith('~'):
            return {"path": action_input}
        
        return {"query": action_input}