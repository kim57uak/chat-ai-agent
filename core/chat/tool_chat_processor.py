from typing import List, Dict, Tuple
from .base_chat_processor import BaseChatProcessor
from core.token_logger import TokenLogger
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
        """도구 사용 채팅 처리 - 시간 제한 및 반복 제한 적용"""
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
            
            # 시간 제한 설정 (30초)
            timeout = 30
            
            # 에이전트 실행 - 대화 히스토리 포함
            try:
                # 대화 히스토리를 포함한 입력 구성
                agent_input = {"input": user_input}
                
                # 대화 히스토리가 있으면 컨텍스트에 추가
                if conversation_history:
                    history_context = self._format_conversation_history(conversation_history)
                    enhanced_input = f"Previous conversation context:\n{history_context}\n\nCurrent question: {user_input}"
                    agent_input["input"] = enhanced_input
                    logger.info(f"Agent 모드에 대화 히스토리 {len(conversation_history)}개 전달")
                
                # 에이전트 실행 전 입력 토큰 로깅을 위한 준비
                input_text = agent_input["input"]
                
                result = self._agent_executor.invoke(agent_input)
                
                # 에이전트 실행 결과 토큰 로깅
                output_text = result.get("output", "")
                if output_text:
                    TokenLogger.log_token_usage(
                        self.model_strategy.model_name, input_text, output_text, "agent_execution"
                    )
                    
            except Exception as agent_error:
                error_msg = str(agent_error)
                
                # 시간 초과 및 Agent stopped 오류 처리
                if (self._is_agent_stopped_error(error_msg)):
                    logger.warning(f"에이전트 실행 시간/반복 제한 도달: {error_msg[:100]}")
                    return "요청이 복잡하여 처리 시간이 초과되었습니다. 더 구체적이고 간단한 질문으로 다시 시도해주세요.", []
                
                # 파싱 오류 처리
                if "parse" in error_msg.lower() or "format" in error_msg.lower():
                    logger.warning(f"에이전트 파싱 오류: {error_msg[:200]}...")
                    
                    # 단순 채팅으로 대체
                    logger.info("파싱 오류로 인해 단순 채팅으로 대체")
                    from .simple_chat_processor import SimpleChatProcessor
                    simple_processor = SimpleChatProcessor(self.model_strategy)
                    return simple_processor.process_message(user_input, conversation_history)
                else:
                    raise agent_error
            
            output = result.get("output", "")
            
            # Agent stopped 메시지 확인 - 다양한 형태 감지
            if self._is_agent_stopped_message(output):
                logger.warning(f"에이전트 중단 메시지 감지: {output[:100]}")
                return self._handle_agent_stopped(result, user_input)
            
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
            
            # Agent stopped 오류 처리
            if self._is_agent_stopped_error(error_msg):
                return "요청 처리가 복잡하여 시간이 초과되었습니다. 더 간단한 질문으로 다시 시도해주세요.", []
            
            # 토큰 제한 오류 처리
            if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                logger.warning("토큰 제한 오류 발생, 단순 채팅으로 대체")
                from .simple_chat_processor import SimpleChatProcessor
                simple_processor = SimpleChatProcessor(self.model_strategy)
                return simple_processor.process_message(user_input, conversation_history)
            
            return f"도구 사용 중 오류가 발생했습니다: {str(e)[:100]}...", []
    
    def _is_agent_stopped_error(self, error_msg: str) -> bool:
        """에이전트 중단 오류 메시지 감지"""
        agent_stopped_patterns = [
            "Agent stopped due to iteration limit or time limit",
            "Agent stopped due to max iterations",
            "timeout",
            "time limit",
            "iteration limit",
            "max iterations"
        ]
        
        error_lower = error_msg.lower()
        return any(pattern.lower() in error_lower for pattern in agent_stopped_patterns)
    
    def _is_agent_stopped_message(self, output: str) -> bool:
        """에이전트 중단 메시지 감지"""
        if not output:
            return False
            
        agent_stopped_patterns = [
            "Agent stopped due to iteration limit or time limit",
            "Agent stopped due to max iterations",
            "Agent stopped",
            "max iterations",
            "iteration limit",
            "time limit"
        ]
        
        output_lower = output.lower()
        return any(pattern.lower() in output_lower for pattern in agent_stopped_patterns)
    
    def supports_tools(self) -> bool:
        """도구 지원함"""
        return True
    
    def _format_conversation_history(self, conversation_history: List[Dict]) -> str:
        """대화 히스토리를 텍스트로 포맷팅"""
        formatted_history = []
        for msg in conversation_history[-6:]:  # 최근 6개만
            role = msg.get("role", "")
            content = msg.get("content", "")[:300]  # 내용 제한
            
            if role == "user":
                formatted_history.append(f"User: {content}")
            elif role == "assistant":
                formatted_history.append(f"Assistant: {content}")
        
        return "\n".join(formatted_history)
    
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
                            
                            # 도구 결과를 AI가 정리하도록 요청 (대용량 처리 적용)
                            final_response = self._process_large_result(user_input, result_str)
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
        if output and self._is_agent_stopped_message(output):
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
                    return self._process_large_result(user_input, combined_results), used_tool_names
        
        if output and output.strip() and not self._is_agent_stopped_message(output) and len(output) > 50:
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
    
    def _process_large_result(self, user_input: str, tool_result: str) -> str:
        """대용량 도구 결과 처리"""
        try:
            # 1. 결과 크기 확인
            result_size = len(tool_result)
            logger.info(f"도구 결과 크기: {result_size} 문자")
            
            # 2. 크기별 처리 전략
            if result_size < 2000:
                # 작은 결과: 그대로 처리
                return self._generate_final_response(user_input, tool_result)
            
            elif result_size < 10000:
                # 중간 크기: 요약 처리
                return self._summarize_result(user_input, tool_result)
            
            else:
                # 대용량: 청크 단위 처리
                return self._chunk_process_result(user_input, tool_result)
                
        except Exception as e:
            logger.error(f"대용량 결과 처리 오류: {e}")
            return f"결과가 너무 커서 처리하지 못했습니다. 더 구체적인 질문으로 다시 시도해주세요."
    
    def _summarize_result(self, user_input: str, tool_result: str) -> str:
        """중간 크기 결과 요약"""
        summary_prompt = f"""다음 도구 실행 결과를 사용자 질문에 맞게 요약해주세요:

사용자 질문: "{user_input}"

도구 결과:
{tool_result[:5000]}

요약 지침:
- 사용자 질문과 관련된 핵심 정보만 추출
- 중요한 수치나 데이터는 유지
- 불필요한 세부사항은 제거
- 최대 1000자 이내로 요약"""

        try:
            messages = self.model_strategy.create_messages(summary_prompt)
            response = self.model_strategy.llm.invoke(messages)
            
            # 모델별 응답 추출
            response_text = self._extract_response_text(response)
            return self.format_response(response_text)
        except Exception as e:
            logger.error(f"요약 처리 오류: {e}")
            return self.format_response(f"요약 처리 중 오류가 발생했습니다:\n\n{tool_result[:1000]}...")
    
    def _chunk_process_result(self, user_input: str, tool_result: str) -> str:
        """대용량 결과 청크 단위 처리"""
        chunk_size = 3000
        chunks = [tool_result[i:i+chunk_size] for i in range(0, len(tool_result), chunk_size)]
        
        # 첫 번째 청크로 초기 응답 생성
        first_chunk = chunks[0]
        
        summary_prompt = f"""대용량 데이터의 첫 번째 부분입니다. 사용자 질문에 대한 답변을 시작해주세요:

사용자 질문: "{user_input}"

데이터 (1/{len(chunks)} 부분):
{first_chunk}

지침:
- 이것은 전체 데이터의 일부임을 명시
- 현재 부분에서 확인할 수 있는 정보 제공
- 전체 데이터가 크다는 것을 사용자에게 알림"""

        try:
            messages = self.model_strategy.create_messages(summary_prompt)
            response = self.model_strategy.llm.invoke(messages)
            
            # 모델별 응답 추출
            response_text = self._extract_response_text(response)
            result = response_text + f"\n\n📊 **데이터 정보**: 총 {len(chunks)}개 섹션 중 첫 번째 부분을 표시했습니다. 더 자세한 정보가 필요하시면 구체적인 질문을 해주세요."
            
            return self.format_response(result)
        except Exception as e:
            logger.error(f"대용량 데이터 처리 오류: {e}")
            return self.format_response(f"대용량 데이터 처리 중 오류가 발생했습니다:\n\n{first_chunk[:1000]}...")

    def _generate_final_response(self, user_input: str, tool_result: str) -> str:
        """도구 결과를 바탕으로 최종 응답 생성 - 크기 제한 적용"""
        try:
            # 결과 크기 확인 및 처리 방식 결정
            if len(tool_result) > 8000:
                return self._process_large_result(user_input, tool_result)
            
            # 도구 결과가 비어있거나 오류인 경우 처리
            if not tool_result or tool_result.strip() == "":
                return "도구를 실행했지만 결과를 가져올 수 없었습니다. 다시 시도해주세요."
            
            # 오류 메시지인 경우 처리
            if "error" in tool_result.lower() or "failed" in tool_result.lower():
                return f"도구 실행 중 문제가 발생했습니다: {tool_result[:200]}..."
            
            # 적절한 크기로 제한
            limited_result = tool_result[:6000] if len(tool_result) > 6000 else tool_result
            
            response_prompt = f"""사용자 질문: "{user_input}"

도구 실행 결과:
{limited_result}

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
            
            # 모델별 응답 추출
            final_response = self._extract_response_text(response)
            
            # 토큰 사용량 로깅
            TokenLogger.log_messages_token_usage(
                self.model_strategy.model_name, messages, final_response, "tool_response_generation"
            )
            if not final_response or len(final_response) < 10:
                # 응답이 너무 짧거나 비어있으면 도구 결과를 직접 포맷팅
                return self.format_response(f"요청하신 정보입니다:\n\n{limited_result}")
            
            # 원본 결과가 잘렸다면 알림 추가
            if len(tool_result) > 6000:
                final_response += f"\n\n💡 **참고**: 결과가 길어서 일부만 처리했습니다. 더 구체적인 질문을 하시면 정확한 정보를 제공할 수 있습니다."
            
            return self.format_response(final_response)
            
        except Exception as e:
            logger.error(f"최종 응답 생성 오류: {e}")
            # 오류 시 도구 결과를 직접 반환
            return self.format_response(f"도구 실행 결과:\n\n{tool_result[:1000]}{'...' if len(tool_result) > 1000 else ''}")
    
    def _extract_response_text(self, response) -> str:
        """모델별 응답 구조 차이를 처리하여 텍스트 추출"""
        try:
            # OpenAI/Gemini 스타일: response.content
            if hasattr(response, 'content'):
                return response.content.strip()
            
            # Perplexity 스타일: 직접 문자열이거나 다른 구조
            if isinstance(response, str):
                return response.strip()
            
            # 딕셔너리 형태의 응답
            if isinstance(response, dict):
                # 일반적인 키들 시도
                for key in ['content', 'text', 'message', 'response', 'output']:
                    if key in response and response[key]:
                        return str(response[key]).strip()
            
            # 기타 객체에서 텍스트 추출 시도
            if hasattr(response, 'text'):
                return response.text.strip()
            
            if hasattr(response, 'message'):
                return response.message.strip()
            
            # 마지막 수단: 문자열 변환
            response_str = str(response).strip()
            if response_str and response_str != 'None':
                return response_str
            
            return "응답을 추출할 수 없습니다."
            
        except Exception as e:
            logger.error(f"응답 텍스트 추출 오류: {e}")
            return f"응답 처리 중 오류가 발생했습니다: {str(e)[:100]}"