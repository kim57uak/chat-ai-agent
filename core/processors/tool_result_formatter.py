"""도구 결과 포맷팅을 담당하는 모듈"""
from abc import ABC, abstractmethod
from typing import List, Any
from langchain.schema import HumanMessage
import logging

logger = logging.getLogger(__name__)


class ToolResultFormatter(ABC):
    """도구 결과 포맷팅을 위한 추상 클래스"""
    
    @abstractmethod
    def format_tool_results(self, used_tools: List, tool_results: List, user_input: str, llm: Any = None) -> str:
        """도구 실행 결과 포맷팅"""
        pass


class AIBasedToolResultFormatter(ToolResultFormatter):
    """AI 기반 도구 결과 포맷터"""
    
    def format_tool_results(self, used_tools: List, tool_results: List, user_input: str, llm: Any = None) -> str:
        """도구 실행 결과를 AI가 지능적으로 포맷팅"""
        try:
            if not tool_results:
                return None
            
            # 다중 페이지 데이터인지 확인하고 완전 출력 포맷터 사용
            if self._has_multi_part_data(tool_results):
                from .complete_output_formatter import CompleteOutputFormatter
                complete_formatter = CompleteOutputFormatter()
                return complete_formatter.format_tool_results(used_tools, tool_results, user_input, llm)
            
            tool_names = [getattr(tool, '__name__', str(tool)) for tool in used_tools]
            results_text = "\n\n".join([f"Tool {i+1} Result: {str(result)}" for i, result in enumerate(tool_results)])
            
            from ui.prompts import prompt_manager
            
            formatter_prompt = prompt_manager.get_prompt("tool_formatting", "result_formatter")
            format_prompt = f"""{formatter_prompt}

User Question: {user_input}
Used Tools: {', '.join(tool_names)}
Tool Results:
{results_text}"""
            
            if llm:
                messages = [HumanMessage(content=format_prompt)]
                response = llm.invoke(messages)
                return response.content
            
            return self._fallback_format(used_tools, tool_results)
            
        except Exception as e:
            logger.error(f"도구 결과 포맷팅 오류: {e}")
            return self._fallback_format(used_tools, tool_results)
    
    def _has_multi_part_data(self, tool_results: List) -> bool:
        """다중 파트 데이터인지 확인"""
        import re
        multi_part_indicators = [
            r'\d+/\d+',  # 페이지 표시
            r'페이지\s*\d+',  # 페이지 언급
            r'page\s*\d+',  # 영어 페이지
            r'섹션\s*\d+',  # 섹션 언급
        ]
        
        for result in tool_results:
            result_str = str(result).lower()
            if any(re.search(pattern, result_str) for pattern in multi_part_indicators):
                return True
        return False
    
    def _fallback_format(self, used_tools: List, tool_results: List) -> str:
        """폴백 포맷팅"""
        tool_names = [getattr(tool, '__name__', str(tool)) for tool in used_tools]
        return f"✅ 작업 완료 (사용된 도구: {', '.join(tool_names)})\n\n" + "\n\n".join([str(result) for result in tool_results])