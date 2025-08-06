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
        """관대한 파싱 로직"""
        # Final Answer 찾기
        final_answer_match = re.search(r'Final Answer:\s*(.*)', text, re.DOTALL | re.IGNORECASE)
        if final_answer_match:
            answer = final_answer_match.group(1).strip()
            if answer:
                logger.info("Final Answer 추출 성공")
                return AgentFinish({"output": answer}, text)
        
        # Action 패턴 찾기
        action_match = re.search(r'Action:\s*([^\n]+)', text, re.IGNORECASE)
        input_match = re.search(r'Action Input:\s*```json\s*({.*?})\s*```|Action Input:\s*({.*?}|\[.*?\]|[^\n]+)', text, re.DOTALL | re.IGNORECASE)
        
        if action_match:
            action = action_match.group(1).strip()
            # 백틱 제거
            action = action.strip('`').strip('"').strip("'")
            # JSON 마크다운 블록 처리
            if input_match:
                action_input = input_match.group(1) or input_match.group(2) or "{}"
                action_input = action_input.strip()
            else:
                action_input = "{}"
            
            # JSON 파싱 시도
            try:
                import json
                if not action_input.startswith(('{', '[')):
                    action_input = f'"{action_input}"'
                parsed_input = json.loads(action_input)
            except:
                parsed_input = action_input
            
            logger.info(f"Action 추출 성공: {action}")
            return AgentAction(action, parsed_input, text)
        
        # 모든 파싱 실패 시 전체 텍스트를 Final Answer로 처리
        logger.warning("모든 파싱 실패, 전체 텍스트를 Final Answer로 처리")
        return AgentFinish({"output": text.strip()}, text)