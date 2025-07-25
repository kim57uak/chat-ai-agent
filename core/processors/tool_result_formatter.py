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
            
            tool_names = [getattr(tool, '__name__', str(tool)) for tool in used_tools]
            results_text = "\n\n".join([f"Tool {i+1} Result: {str(result)}" for i, result in enumerate(tool_results)])
            
            format_prompt = f"""Please format the following tool execution results in a user-friendly way in Korean:

User Question: {user_input}
Used Tools: {', '.join(tool_names)}
Tool Results:
{results_text}

Please:
1. Analyze the results and provide a clear summary
2. Use appropriate emojis and formatting
3. Structure the information logically
4. Keep it concise but informative
5. Respond in Korean

Format the response as if you're directly answering the user's question based on these tool results."""
            
            if llm:
                messages = [HumanMessage(content=format_prompt)]
                response = llm.invoke(messages)
                return response.content
            
            return self._fallback_format(used_tools, tool_results)
            
        except Exception as e:
            logger.error(f"도구 결과 포맷팅 오류: {e}")
            return self._fallback_format(used_tools, tool_results)
    
    def _fallback_format(self, used_tools: List, tool_results: List) -> str:
        """폴백 포맷팅"""
        tool_names = [getattr(tool, '__name__', str(tool)) for tool in used_tools]
        return f"✅ 작업 완료 (사용된 도구: {', '.join(tool_names)})\n\n" + "\n\n".join([str(result) for result in tool_results])