from typing import List, Dict, Tuple
from .base_chat_processor import BaseChatProcessor
import logging
import time

logger = logging.getLogger(__name__)


class ToolChatProcessor(BaseChatProcessor):
    """도구 사용 채팅 처리기"""
    
    def __init__(self, model_strategy, tools: List = None):
        super().__init__(model_strategy)
        self.tools = tools or []
        self._agent_executor = None
    
    def process_message(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """도구 사용 채팅 처리"""
        try:
            if not self.validate_input(user_input):
                return "유효하지 않은 입력입니다.", []
            
            if not self.tools:
                return "사용 가능한 도구가 없습니다.", []
            
            start_time = time.time()
            logger.info(f"도구 채팅 시작: {user_input[:50]}...")
            
            # 에이전트 실행기 생성 (지연 로딩)
            if not self._agent_executor:
                self._agent_executor = self.model_strategy.create_agent_executor(self.tools)
            
            if not self._agent_executor:
                return "에이전트 실행기를 생성할 수 없습니다.", []
            
            # 에이전트 실행 (파싱 오류 처리 강화)
            try:
                result = self._agent_executor.invoke({"input": user_input})
            except Exception as agent_error:
                # 파싱 오류 전용 처리
                if "parse" in str(agent_error).lower() or "format" in str(agent_error).lower():
                    logger.warning(f"에이전트 파싱 오류: {str(agent_error)[:200]}...")
                    
                    # 예외 객체에서 결과 추출 시도
                    if hasattr(agent_error, 'llm_output') and agent_error.llm_output:
                        logger.info("예외에서 LLM 출력 발견, 처리 중...")
                        return self._extract_response_from_error(agent_error.llm_output, user_input)
                    
                    # 단순 채팅으로 대체
                    logger.info("파싱 오류로 인해 단순 채팅으로 대체")
                    from .simple_chat_processor import SimpleChatProcessor
                    simple_processor = SimpleChatProcessor(self.model_strategy)
                    return simple_processor.process_message(user_input, conversation_history)
                else:
                    raise agent_error
            
            output = result.get("output", "")
            
            # 사용된 도구 정보 추출
            used_tools = self._extract_used_tools(result)
            
            # 결과 검증 및 처리
            if not output or not output.strip() or len(output.strip()) < 10:
                logger.warning("에이전트 결과 부족, 결과 확인 중...")
                return self._handle_agent_stopped(result, user_input)
            
            elapsed = time.time() - start_time
            logger.info(f"도구 채팅 완료: {elapsed:.2f}초")
            return self.format_response(output), used_tools
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"도구 채팅 오류: {e}")
            
            # 에이전트 실행 오류 시 결과 추출 시도
            if "parse" in error_msg.lower() or "format" in error_msg.lower() or "chain" in error_msg.lower():
                logger.warning(f"에이전트 실행 오류 발생: {error_msg[:100]}...")
                # 예외 객체에서 결과 추출 시도
                if hasattr(e, 'llm_output') and e.llm_output:
                    logger.info(f"예외에서 LLM 출력 발견: {e.llm_output[:200]}...")
                    return self.format_response(e.llm_output), []
                
                return f"도구 실행 중 형식 오류가 발생했습니다. 다시 시도해주세요.", []
            
            # 토큰 제한 오류 처리
            if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                logger.warning("토큰 제한 오류 발생, 단순 채팅으로 대체")
                from .simple_chat_processor import SimpleChatProcessor
                simple_processor = SimpleChatProcessor(self.model_strategy)
                return simple_processor.process_message(user_input, conversation_history)
            
            return f"도구 사용 중 오류가 발생했습니다: {str(e)[:100]}...", []
    
    def supports_tools(self) -> bool:
        """도구 지원함"""
        return True
    
    def set_tools(self, tools: List):
        """도구 설정"""
        self.tools = tools
        self._agent_executor = None  # 재생성 필요
    
    def _extract_used_tools(self, result: Dict) -> List:
        """사용된 도구 정보 추출"""
        used_tools = []
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if len(step) >= 2 and hasattr(step[0], "tool"):
                    used_tools.append(step[0].tool)
        return used_tools
    
    def _handle_agent_stopped(self, result: Dict, user_input: str) -> Tuple[str, List]:
        """에이전트 중단 처리 - 도구 사용 시 반드시 도구 결과 사용"""
        logger.info(f"=== 에이전트 결과 디버깅 ===")
        logger.info(f"result keys: {list(result.keys())}")
        logger.info(f"intermediate_steps 존재: {'intermediate_steps' in result}")
        if "intermediate_steps" in result:
            logger.info(f"intermediate_steps 길이: {len(result['intermediate_steps'])}")
            logger.info(f"intermediate_steps 내용: {result['intermediate_steps']}")
        
        # 1. intermediate_steps에서 도구 결과 확인
        if "intermediate_steps" in result and result["intermediate_steps"]:
            logger.info(f"도구 사용 감지: {len(result['intermediate_steps'])}개 단계")
            
            for i, step in enumerate(result["intermediate_steps"]):
                logger.info(f"단계 {i} 타입: {type(step)}, 길이: {len(step) if hasattr(step, '__len__') else 'N/A'}")
                
                if len(step) >= 2:
                    tool_action = step[0]
                    tool_result = step[1]
                    tool_name = getattr(tool_action, 'tool', 'unknown')
                    logger.info(f"단계 {i}: 도구={tool_name}, 결과 길이={len(str(tool_result))}")
                    
                    if tool_result is not None:
                        result_str = str(tool_result).strip()
                        if result_str:
                            logger.info(f"유효한 도구 결과 발견: {result_str[:200]}...")
                            
                            # 도구 결과를 AI가 정리하도록 요청
                            final_response = self._generate_final_response(user_input, result_str)
                            return final_response, [tool_name]
                        else:
                            logger.warning(f"단계 {i}: 도구 결과가 비어있음")
                    else:
                        logger.warning(f"단계 {i}: 도구 결과가 None")
        
        # 2. output에 결과가 있는지 확인 (Agent stopped 메시지 처리)
        output = result.get("output", "")
        logger.info(f"output 존재: {bool(output)}, 길이: {len(output) if output else 0}")
        if output:
            logger.info(f"output 내용: {output[:200]}...")
            
        # Agent stopped 메시지 감지 및 처리
        if output and "Agent stopped due to iteration limit or time limit" in output:
            logger.warning("Agent stopped 메시지 감지 - 도구 결과에서 응답 생성 시도")
            # intermediate_steps에서 모든 도구 결과 수집
            if "intermediate_steps" in result and result["intermediate_steps"]:
                all_tool_results = []
                used_tool_names = []
                
                for step in result["intermediate_steps"]:
                    if len(step) >= 2 and step[1]:
                        tool_result = str(step[1]).strip()
                        tool_name = getattr(step[0], 'tool', 'unknown')
                        if tool_result:
                            all_tool_results.append(f"[{tool_name}] {tool_result}")
                            used_tool_names.append(tool_name)
                
                if all_tool_results:
                    combined_results = "\n\n".join(all_tool_results)
                    logger.info(f"Agent stopped 상황에서 {len(all_tool_results)}개 도구 결과로 응답 생성")
                    return self._generate_final_response(user_input, combined_results), used_tool_names
        
        if output and output.strip() and "Agent stopped" not in output and len(output) > 50:
            logger.info(f"에이전트 출력에서 결과 발견")
            return self.format_response(output), self._extract_used_tools(result)
        
        # 3. 도구를 사용했지만 결과가 비어있는 경우
        if "intermediate_steps" in result and result["intermediate_steps"]:
            logger.warning("도구를 사용했지만 유효한 결과가 없음")
            return "도구를 사용했지만 예상한 결과를 얻지 못했습니다. 다시 시도해주세요.", []
        
        # 4. 도구를 사용하지 않은 경우 - 더 유용한 메시지 제공
        logger.warning("도구 사용 없이 에이전트 중단")
        return "요청을 처리하는 중에 시간이 초과되었습니다. 질문을 더 구체적으로 다시 해주시거나, 단순 채팅 모드를 사용해보세요.", []
    

    
    def _extract_response_from_error(self, llm_output: str, user_input: str) -> Tuple[str, List]:
        """파싱 오류에서 응답 추출"""
        try:
            # Final Answer 부분 추출 시도
            if "Final Answer:" in llm_output:
                final_answer = llm_output.split("Final Answer:")[-1].strip()
                if final_answer and len(final_answer) > 10:
                    logger.info(f"Final Answer에서 응답 추출: {final_answer[:100]}...")
                    return self.format_response(final_answer), []
            
            # 도구 결과가 있는지 확인
            if "Observation:" in llm_output:
                # 마지막 Observation 부분 추출
                observation_parts = llm_output.split("Observation:")
                if len(observation_parts) > 1:
                    tool_result = observation_parts[-1].strip()
                    if tool_result and len(tool_result) > 10:
                        logger.info(f"Observation에서 도구 결과 추출: {tool_result[:100]}...")
                        return self._generate_final_response(user_input, tool_result), []
            
            # 전체 출력에서 의미 있는 내용 추출
            if len(llm_output.strip()) > 50:
                logger.info(f"전체 LLM 출력 사용: {llm_output[:100]}...")
                return self.format_response(llm_output.strip()), []
            
            # 추출 실패 시 단순 채팅으로 대체
            logger.warning("파싱 오류에서 응답 추출 실패, 단순 채팅으로 대체")
            from .simple_chat_processor import SimpleChatProcessor
            simple_processor = SimpleChatProcessor(self.model_strategy)
            return simple_processor.process_message(user_input)
            
        except Exception as e:
            logger.error(f"오류 응답 추출 실패: {e}")
            return "도구 실행 중 오류가 발생했습니다. 다시 시도해주세요.", []
    
    def _generate_final_response(self, user_input: str, tool_result: str) -> str:
        """도구 결과를 바탕으로 최종 응답 생성"""
        try:
            # 도구 결과가 너무 길면 요약
            if len(tool_result) > 3000:
                tool_result = tool_result[:3000] + "\n\n...(결과가 길어서 일부만 표시)"
            
            # 도구 결과가 비어있거나 오류인 경우 처리
            if not tool_result or tool_result.strip() == "":
                return "도구를 실행했지만 결과를 가져올 수 없었습니다. 다시 시도해주세요."
            
            # 오류 메시지인 경우 처리
            if "error" in tool_result.lower() or "failed" in tool_result.lower():
                return f"도구 실행 중 문제가 발생했습니다: {tool_result[:200]}..."
            
            response_prompt = f"""사용자 질문: "{user_input}"

도구 실행 결과:
{tool_result}

위 도구 실행 결과를 바탕으로 사용자의 질문에 대한 답변을 작성해주세요.

답변 작성 지침:
1. 사용자가 실제로 알고 싶어하는 정보에 집중
2. 결과를 논리적이고 읽기 쉬운 구조로 정리
3. 자연스러운 한국어로 친근하게 설명
4. 표나 목록이 있다면 마크다운 형식으로 정리
5. 기술적 용어는 쉽게 풀어서 설명
6. 핵심 정보를 놓치지 않고 포함

사용자에게 도움이 되는 명확하고 유용한 한국어 답변을 제공해주세요."""

            messages = self.model_strategy.create_messages(response_prompt)
            response = self.model_strategy.llm.invoke(messages)
            
            final_response = response.content.strip()
            if not final_response or len(final_response) < 10:
                # 응답이 너무 짧거나 비어있으면 도구 결과를 직접 포맷팅
                return self.format_response(f"요청하신 정보입니다:\n\n{tool_result}")
            
            return self.format_response(final_response)
            
        except Exception as e:
            logger.error(f"최종 응답 생성 오류: {e}")
            # 오류 시 도구 결과를 직접 반환
            return self.format_response(f"도구 실행 결과:\n\n{tool_result[:1000]}{'...' if len(tool_result) > 1000 else ''}")