from typing import Union
from langchain.agents.agent import AgentOutputParser
from langchain.agents.conversational.output_parser import ConvoOutputParser
from langchain.schema import AgentAction, AgentFinish
import re
import logging

logger = logging.getLogger(__name__)


class ClaudeOutputParser(AgentOutputParser):
    """Claude 전용 출력 파서 - Final Answer와 Action이 동시에 나오는 경우 처리"""
    
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        """Claude 출력을 파싱하여 AgentAction 또는 AgentFinish 반환"""
        try:
            # 한 줄에 Thought와 Final Answer가 같이 있는 경우 처리
            if "Thought:" in llm_output and "Final Answer:" in llm_output:
                # Final Answer 부분만 추출
                final_answer_match = re.search(r"Final Answer:\s*(.*?)$", 
                                             llm_output, re.DOTALL | re.MULTILINE)
                if final_answer_match:
                    answer = final_answer_match.group(1).strip()
                    # 테이블 마지막에 설명 텍스트가 혼재된 경우 처리
                    answer = self._clean_table_description(answer)
                    logger.info(f"Claude Final Answer 감지 (혼합): {answer[:100]}...")
                    return AgentFinish(
                        return_values={"output": answer},
                        log=answer
                    )
            
            # 일반적인 Final Answer 처리
            if "Final Answer:" in llm_output:
                final_answer_match = re.search(r"Final Answer:\s*(.*?)(?=\n\n|\nThought:|\nAction:|$)", 
                                             llm_output, re.DOTALL)
                if final_answer_match:
                    answer = final_answer_match.group(1).strip()
                    # 테이블 마지막에 설명 텍스트가 혼재된 경우 처리
                    answer = self._clean_table_description(answer)
                    logger.info(f"Claude Final Answer 감지: {answer[:100]}...")
                    return AgentFinish(
                        return_values={"output": answer},
                        log=answer
                    )
            
            # Action이 있으면 처리
            action_match = re.search(r"Action:\s*(.*?)\nAction Input:\s*(.*?)(?=\n\n|\nObservation:|\nThought:|$)", 
                                   llm_output, re.DOTALL)
            if action_match:
                action = action_match.group(1).strip()
                action_input = action_match.group(2).strip()
                
                # JSON 형태가 아니면 문자열로 처리
                try:
                    import json
                    parsed_input = json.loads(action_input)
                except:
                    parsed_input = action_input
                
                logger.info(f"Claude Action 감지: {action}")
                return AgentAction(
                    tool=action,
                    tool_input=parsed_input,
                    log=llm_output
                )
            
            # 둘 다 없으면 기본 파서 사용
            fallback_parser = ConvoOutputParser()
            return fallback_parser.parse(llm_output)
            
        except Exception as e:
            logger.error(f"Claude 파싱 오류: {e}")
            # 파싱 실패 시 출력을 Final Answer로 처리
            return AgentFinish(
                return_values={"output": llm_output},
                log=llm_output
            )
    
    @property
    def _type(self) -> str:
        return "claude_output_parser"