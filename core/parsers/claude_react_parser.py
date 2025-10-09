from typing import Union
from langchain.agents.agent import AgentAction, AgentFinish
from langchain.agents.react.output_parser import ReActOutputParser
from langchain.schema import OutputParserException
import re
from core.logging import get_logger

logger = get_logger("claude_react_parser")


class ClaudeReActParser(ReActOutputParser):
    """Claude 전용 ReAct 파서 - 마크다운 보존 우선"""
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Claude 전용 파싱 로직 - 마크다운 테이블 우선 감지"""
        # 마크다운 테이블 패턴 강화 감지
        table_patterns = [
            r'\|.*\|.*\|',  # 기본 테이블 패턴
            r'\|\s*---\s*\|',  # 헤더 구분자
            r'\|\s*코드\s*\|',  # 한글 테이블 헤더
            r'\|\s*Header\s*\|',  # 영문 테이블 헤더
        ]
        
        has_table = any(re.search(pattern, text) for pattern in table_patterns)
        if has_table or (text.count('|') > 3 and '\n' in text):
            logger.info("Claude 마크다운 테이블 감지 - 바로 Final Answer 처리")
            return AgentFinish({"output": text.strip()}, text)
        
        try:
            # 기본 ReAct 파서 시도
            return super().parse(text)
        except OutputParserException:
            logger.warning(f"기본 파싱 실패, Claude 전용 파싱 시도: {text[:100]}...")
            return self._claude_parse(text)
    
    def _claude_parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Claude 전용 파싱 로직 - 관대한 파싱으로 마크다운 보존"""
        
        # Action과 Action Input이 모두 있는 경우만 Action으로 처리
        action_match = re.search(r'Action:\s*([^\n\s]+)', text, re.IGNORECASE)
        input_match = re.search(r'Action Input:\s*({.*?})', text, re.DOTALL | re.IGNORECASE)
        
        if action_match and input_match:
            action = action_match.group(1).strip()
            action_input = input_match.group(1).strip()
            
            # 백틱과 따옴표 제거, Action Input 텍스트 제거
            action = action.strip('`').strip('"').strip("'")
            action = re.sub(r'\s+Action\s+Input.*$', '', action, flags=re.IGNORECASE)
            
            # JSON 파싱 시도
            try:
                import json
                parsed_input = json.loads(action_input)
            except:
                parsed_input = action_input
            
            logger.info(f"Claude Action 처리: {action}")
            return AgentAction(action, parsed_input, text)
        
        # Final Answer가 있으면 우선 처리 (마크다운 보존)
        final_answer_match = re.search(r'Final Answer[:\s]*(.*)', text, re.DOTALL | re.IGNORECASE)
        if final_answer_match:
            answer = final_answer_match.group(1).strip()
            if answer:
                logger.info("Claude Final Answer 처리 (마크다운 보존)")
                return AgentFinish({"output": answer}, text)
        
        # Action만 있고 Input이 없는 경우 - 계속 진행
        if action_match and not input_match:
            logger.info("Action Input 대기 중")
            return AgentFinish({"output": "도구 입력을 기다리는 중..."}, text)
        
        # 마크다운 테이블 강화 감지
        table_indicators = [
            '|' in text and '---' in text,  # 표준 마크다운 테이블
            text.count('|') > 6,  # 다중 열 테이블
            '|코드|' in text or '|Header|' in text,  # 테이블 헤더 감지
            re.search(r'\|[^|]*\|[^|]*\|[^|]*\|', text)  # 3열 이상 테이블
        ]
        
        if any(table_indicators):
            logger.info("Claude 마크다운 테이블 강화 감지 - Final Answer 처리")
            return AgentFinish({"output": text.strip()}, text)
        
        # 기타 마크다운 콘텐츠 감지
        markdown_patterns = [
            r'^#{1,6}\s',  # 헤더
            r'^[-*+]\s',  # 리스트
            r'^\d+\.\s',  # 숫자 리스트
            r'\*\*.*\*\*',  # 굵은 글씨
            r'```',  # 코드 블록
        ]
        
        has_markdown = any(re.search(pattern, text, re.MULTILINE) for pattern in markdown_patterns)
        
        if has_markdown:
            logger.info("Claude 마크다운 콘텐츠 감지 - Final Answer 처리")
            return AgentFinish({"output": text.strip()}, text)
        
        # 긴 텍스트는 Final Answer로 처리
        if len(text.strip()) > 50:
            logger.info("Claude 긴 텍스트 - Final Answer 처리")
            return AgentFinish({"output": text.strip()}, text)
        
        # 모든 파싱 실패 시 전체 텍스트를 Final Answer로 처리
        logger.warning("Claude 파싱 실패, 전체 텍스트를 Final Answer로 처리")
        return AgentFinish({"output": text.strip()}, text)