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
            logger.debug(f"기본 파싱 실패, 관대한 파싱 시도: {text[:100]}...")
            return self._lenient_parse(text)
    
    def _lenient_parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """관대한 파싱 로직 - Claude 파서 참고"""
        print(f"\n=== LENIENT PARSING DEBUG ===\nFull AI Response:\n{text}\n=== END RESPONSE ===")
        
        # Action과 Action Input이 모두 있는 경우만 Action으로 처리
        action_match = re.search(r'Action:\s*([^\n\s]+)', text, re.IGNORECASE)
        input_match = re.search(r'Action Input:\s*({.*?})', text, re.DOTALL | re.IGNORECASE)
        
        if action_match and input_match:
            action = action_match.group(1).strip()
            action_input = input_match.group(1).strip()
            
            # 백틱과 따옴표 제거
            action = action.strip('`').strip('"').strip("'")
            
            # JSON 파싱 시도
            try:
                import json
                parsed_input = json.loads(action_input)
            except:
                parsed_input = action_input
            
            logger.debug(f"Action 추출 성공: {action}")
            return AgentAction(action, parsed_input, text)
        
        # Final Answer가 있으면 우선 처리
        final_answer_match = re.search(r'Final Answer[:\s]*(.*)', text, re.DOTALL | re.IGNORECASE)
        if final_answer_match:
            answer = final_answer_match.group(1).strip()
            if answer:
                logger.info("Final Answer 추출 성공")
                return AgentFinish({"output": answer}, text)
        
        # Action만 있고 Input이 없는 경우 - 계속 진행
        if action_match and not input_match:
            logger.warning("Action Input 대기 중 - 파싱 오류 발생")
            raise OutputParserException(
                "Action found but missing Action Input. Please provide Action Input.",
                observation="",
                llm_output=text,
                send_to_llm=True
            )
        
        # Thought만 있는 경우 파싱 오류로 처리
        thought_match = re.search(r'Thought:\s*(.*?)(?=\n\n|$)', text, re.DOTALL | re.IGNORECASE)
        if thought_match:
            thought_content = thought_match.group(1).strip()
            if thought_content and not re.search(r'(Action|Final Answer):', text, re.IGNORECASE):
                # 너무 긴 Thought는 잘리고 파싱 오류 발생
                if len(thought_content) > 200:
                    thought_content = thought_content[:200] + "..."
                logger.warning("Thought만 있는 불완전 응답 - 파싱 오류로 처리")
                print(f"\n=== INCOMPLETE AI RESPONSE DEBUG ===\nFull AI Response:\n{text}\n=== END RESPONSE ===")
                print(f"Thought Content: {thought_content}")
                print(f"Response Length: {len(text)} chars")
                raise OutputParserException(
                    f"Incomplete response - missing Action or Final Answer after Thought: {thought_content}",
                    observation="",
                    llm_output=text,
                    send_to_llm=True
                )
        
        # 긴 텍스트는 Final Answer로 처리
        if len(text.strip()) > 50:
            logger.info("긴 텍스트 - Final Answer로 처리")
            return AgentFinish({"output": text.strip()}, text)
        
        # 모든 파싱 실패 시 전체 텍스트를 Final Answer로 처리
        logger.debug("모든 파싱 실패, 전체 텍스트를 Final Answer로 처리")
        return AgentFinish({"output": text.strip()}, text)