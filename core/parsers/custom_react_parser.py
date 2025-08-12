from typing import Union
from langchain.agents.agent import AgentAction, AgentFinish
from langchain.agents.react.output_parser import ReActOutputParser
from langchain.schema import OutputParserException
import re
import logging

logger = logging.getLogger(__name__)


class CustomReActParser(ReActOutputParser):
    """관대한 ReAct 파서 - OUTPUT_PARSING_FAILURE 방지"""
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """관대한 파싱 로직"""
        try:
            # 기본 ReAct 파서 시도
            return super().parse(text)
        except OutputParserException:
            logger.warning(f"기본 파싱 실패, 관대한 파싱 시도: {text[:100]}...")
            return self._lenient_parse(text)
    
    def _lenient_parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """관대한 파싱 로직 - Action 우선 처리"""
        # Action 패턴 먼저 찾기 (Final Answer보다 우선)
        action_match = re.search(r'Action:\s*([^\n]+)', text, re.IGNORECASE)
        input_match = re.search(r'Action Input:\s*```json\s*({.*?})\s*```|Action Input:\s*({.*?}|\[.*?\]|[^\n]+)', text, re.DOTALL | re.IGNORECASE)
        
        if action_match and input_match:
            action = action_match.group(1).strip()
            # 안전한 그룹 추출
            action_input = None
            for i in range(1, input_match.lastindex + 1 if input_match.lastindex else 1):
                if input_match.group(i):
                    action_input = input_match.group(i).strip()
                    break
            
            if not action_input:
                action_input = "{}"
            
            # 백틱 제거
            action = action.strip('`').strip('"').strip("'")
            
            # JSON 파싱 시도
            try:
                import json
                parsed_input = json.loads(action_input)
            except:
                parsed_input = action_input
            
            logger.info(f"Action 추출 성공 (우선 처리): {action}")
            return AgentAction(action, parsed_input, text)
        
        # Action이 없으면 Final Answer 찾기
        final_answer_match = re.search(r'Final Answer:\s*(.*)', text, re.DOTALL | re.IGNORECASE)
        if final_answer_match:
            answer = final_answer_match.group(1).strip()
            if answer:
                logger.info("Final Answer 추출 성공")
                return AgentFinish({"output": answer}, text)
        
        # 모든 파싱 실패 시 전체 텍스트를 Final Answer로 처리
        logger.warning("모든 파싱 실패, 전체 텍스트를 Final Answer로 처리")
        return AgentFinish({"output": text.strip()}, text)