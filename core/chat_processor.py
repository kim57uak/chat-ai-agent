# 하위 호환성을 위한 레거시 임포트
from abc import ABC, abstractmethod
from core.chat_processor_refactored import (
    ChatProcessor as BaseChatProcessor, 
    RefactoredSimpleChatProcessor, 
    RefactoredToolChatProcessor
)
from langchain.schema import HumanMessage
from core.file_utils import load_config
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ChatProcessor(BaseChatProcessor):
    """채팅 처리를 위한 추상 클래스 - 하위 호환성 유지"""
    pass


class SimpleChatProcessor(RefactoredSimpleChatProcessor):
    """단순 채팅 처리기 - 하위 호환성 유지"""
    pass
    
    pass


class ToolChatProcessor(RefactoredToolChatProcessor):
    """도구 사용 채팅 처리기 - 하위 호환성 유지"""
    
    def __init__(self, tools: List[Any], agent_executor_factory):
        super().__init__(tools, agent_executor_factory)
        # 하위 호환성을 위한 속성 유지
        self.tools = tools
        self.agent_executor_factory = agent_executor_factory
        self.agent_executor = None
    
    # 하위 호환성을 위해 기존 메서드 유지
    def process_chat(self, user_input: str, llm: Any, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        return super().process_chat(user_input, llm, conversation_history)
    
    def _gemini_tool_chat(self, user_input: str, llm: Any) -> Tuple[str, List]:
        """Gemini 모델용 도구 채팅 - 실제 도구 사용"""
        try:
            # 에이전트 실행기가 없으면 생성
            if not self.agent_executor:
                logger.info("🔧 Gemini용 에이전트 실행기 생성")
                self.agent_executor = self.agent_executor_factory.create_agent_executor(llm, self.tools)
            
            if not self.agent_executor:
                logger.warning("에이전트 실행기 생성 실패")
                return "사용 가능한 도구가 없습니다.", []
            
            # 에이전트 실행
            logger.info(f"🔧 Gemini 에이전트 실행: {user_input[:50]}...")
            result = self.agent_executor.invoke({"input": user_input})
            output = result.get("output", "")
            
            # 사용된 도구 정보 추출
            used_tools = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) >= 2 and hasattr(step[0], "tool"):
                        used_tools.append(step[0].tool)
            
            # 도구가 사용된 경우 결과 처리
            if len(used_tools) > 0:
                # 도구 실행 결과 수집
                tool_results = []
                if "intermediate_steps" in result:
                    for step in result["intermediate_steps"]:
                        if len(step) >= 2:
                            tool_results.append(step[1])
                
                # 에이전트 응답이 부적절한 경우 도구 결과를 직접 정리
                if not output.strip() or "Agent stopped" in output or "도구 실행이 완료되었습니다" in output:
                    logger.info(f"Gemini 에이전트 응답 부적절, 도구 결과 직접 정리: {len(used_tools)}개 도구")
                    
                    # 도구 결과를 기반으로 새로운 응답 생성
                    if tool_results:
                        self.llm = llm  # AI 포맷팅을 위해 LLM 저장
                        formatted_results = self._format_tool_results(used_tools, tool_results, user_input)
                        if formatted_results:
                            return formatted_results, used_tools
                    
                    # 도구 결과가 없으면 기본 메시지
                    tool_names = [getattr(tool, '__name__', str(tool)) for tool in used_tools]
                    output = f"요청하신 작업을 완료했습니다. 사용된 도구: {', '.join(tool_names)}"
            # 도구가 사용되지 않았고 응답이 비어있거나 에이전트가 중단된 경우
            elif not output.strip() or "Agent stopped" in output:
                logger.warning("Gemini 에이전트 응답이 비어있거나 중단됨, 일반 채팅으로 대체")
                simple_processor = SimpleChatProcessor()
                return simple_processor.process_chat(user_input, llm), []
            
            logger.info(f"✅ Gemini 도구 채팅 성공: {len(used_tools)}개 도구 사용")
            return output, used_tools
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Gemini 도구 채팅 오류: {e}")
            
            # ReAct 형식 오류 처리
            if "Invalid Format" in error_msg and len(self.tools) > 0:
                # 형식 오류지만 도구가 있는 경우, 다른 프롬프트로 재시도
                logger.info("ReAct 형식 오류 발생, 단순화된 프롬프트로 재시도")
                try:
                    # 단순화된 프롬프트 사용
                    simple_prompt = f"""Please use the following tools to answer the user's question:

{[str(tool) for tool in self.tools]}

Question: {user_input}

Please respond in the following format:
1. Select the appropriate tool to use
2. Explain the parameters to pass to the tool
3. Interpret the results and provide a final answer in Korean"""
                    messages = [HumanMessage(content=simple_prompt)]
                    response = llm.invoke(messages)
                    return response.content, []
                except Exception as inner_e:
                    logger.error(f"❌ 단순화된 프롬프트 실패: {inner_e}")
            
            # 오류 시 일반 채팅으로 폴백
            simple_processor = SimpleChatProcessor()
            return simple_processor.process_chat(user_input, llm), []
    
    def _format_tool_results(self, used_tools: List, tool_results: List, user_input: str) -> str:
        """도구 실행 결과를 AI가 지능적으로 포맷팅"""
        try:
            if not tool_results:
                return None
            
            # AI에게 결과 포맷팅 요청
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
            
            # SimpleChatProcessor를 사용하여 AI가 결과 포맷팅
            from core.llm_factory import LLMFactoryProvider
            formatting_llm = LLMFactoryProvider.create_llm("dummy", "gpt-3.5-turbo")
            
            if hasattr(self, 'llm') and self.llm:
                formatting_llm = self.llm
            
            messages = [HumanMessage(content=format_prompt)]
            response = formatting_llm.invoke(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"도구 결과 포맷팅 오류: {e}")
            # 폴백: 기본 포맷팅
            tool_names = [getattr(tool, '__name__', str(tool)) for tool in used_tools]
            return f"✅ 작업 완료 (사용된 도구: {', '.join(tool_names)})\n\n" + "\n\n".join([str(result) for result in tool_results])
    
    def _limit_response_length(self, response: str) -> str:
        """응답 길이 제한"""
        try:
            config = load_config()
            response_settings = config.get("response_settings", {})
            
            if not response_settings.get("enable_length_limit", True):
                return response
            
            max_length = response_settings.get("max_response_length", 8000)
            
            if len(response) <= max_length:
                return response
            
            logger.warning(f"도구 응답 길이 제한 적용: {len(response)}자 -> {max_length}자")
            
            # 마지막 완전한 문장에서 자르기
            truncated = response[:max_length]
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            
            # 마지막 마침표나 줄바꿈 위치에서 자르기
            cut_point = max(last_period, last_newline)
            if cut_point > max_length * 0.8:  # 80% 이상에서 찾은 경우만 사용
                truncated = response[:cut_point + 1]
            
            return truncated + "\n\n[도구 사용 응답이 너무 길어 일부만 표시됩니다. 더 자세한 내용이 필요하시면 구체적인 질문을 해주세요.]"
            
        except Exception as e:
            logger.error(f"도구 응답 길이 제한 오류: {e}")
            return response