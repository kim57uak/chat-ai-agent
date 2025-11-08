from typing import List, Dict, Tuple
from .base_chat_processor import BaseChatProcessor
from core.token_logger import TokenLogger
from core.token_tracker import token_tracker, StepType
from core.token_tracking import get_unified_tracker, ChatModeType
from core.logging import get_logger
import time

logger = get_logger("tool_chat_processor")


class ToolChatProcessor(BaseChatProcessor):
    """도구 사용 채팅 처리기"""
    
    def __init__(self, model_strategy, tools: List = None):
        super().__init__(model_strategy)
        self.tools = tools or []
        self._agent_executor = None
    
    def supports_tools(self) -> bool:
        """도구 지원 여부"""
        return True
    
    def process_message(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """도구 사용 채팅 처리 - 시간 제한 및 반복 제한 적용"""
        try:
            # Unified tracker 시작
            start_time = time.time()
            unified_tracker = None
            try:
                from core.security.secure_path_manager import secure_path_manager
                db_path = secure_path_manager.get_database_path()
                unified_tracker = get_unified_tracker(db_path)
                unified_tracker.start_conversation(
                    mode=ChatModeType.TOOL,
                    model=self.model_strategy.model_name,
                    session_id=self.session_id
                )
            except Exception as e:
                logger.debug(f"Unified tracker not initialized: {e}")
                unified_tracker = None
            
            # 대화 트래킹 시작 (현재 대화가 없는 경우)
            if not token_tracker.current_conversation:
                token_tracker.start_conversation(user_input, self.model_strategy.model_name)
            
            # 토큰 트래킹 시작
            token_tracker.start_step(StepType.TOOL_DECISION, "Tool Usage Decision")
            
            if not self.validate_input(user_input):
                return "유효하지 않은 입력입니다.", []
            
            if not self.tools:
                return "사용 가능한 도구가 없습니다.", []
            
            start_time = time.time()
            logger.info(f"도구 채팅 시작: {user_input[:50]}...")
            
            # 도구 결정 단계 종료
            token_tracker.end_step(
                StepType.TOOL_DECISION,
                "Tool Usage Decision",
                input_text=user_input,
                output_text=f"Using {len(self.tools)} available tools"
            )
            
            # 에이전트 실행기 생성 (지연 로딩)
            if not self._agent_executor:
                self._agent_executor = self.model_strategy.create_agent_executor(self.tools)
            
            if not self._agent_executor:
                return "에이전트 실행기를 생성할 수 없습니다.", []
            
            # 모델별 시간 제한 설정 (더 여유롭게)
            if 'gemini' in self.model_strategy.model_name.lower():
                timeout = 240  # Gemini는 240초
            elif 'gpt-4' in self.model_strategy.model_name.lower():
                timeout = 180  # GPT-4는 180초
            else:
                timeout = 120  # 다른 모델은 120초
            
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
                
                # 도구 실행 단계 시작
                token_tracker.start_step(StepType.TOOL_EXECUTION, "Agent Tool Execution")
                
                result = self._agent_executor.invoke(agent_input)
                
                # 에이전트 실행 결과 토큰 로깅 및 히스토리 저장
                output_text = result.get("output", "")
                if output_text:
                    # MCP 도구 결과를 포함한 전체 입력 토큰 계산
                    total_input_text = input_text
                    
                    # 중간 단계에서 도구 결과 추출하여 입력 토큰에 포함
                    intermediate_steps = result.get("intermediate_steps", [])
                    tool_results_text = ""
                    used_tools = []
                    
                    for step in intermediate_steps:
                        if len(step) >= 2:
                            action, observation = step[0], step[1]
                            # 도구명 추출
                            tool_name = getattr(action, 'tool', 'unknown_tool')
                            used_tools.append(tool_name)
                            
                            if observation and str(observation).strip():
                                tool_results_text += f"\nTool Result: {str(observation)}"
                    
                    # 도구 결과가 있으면 입력 토큰에 추가
                    if tool_results_text:
                        total_input_text += tool_results_text
                        logger.info(f"MCP 도구 결과 {len(tool_results_text)} 문자를 입력 토큰에 추가")
                    
                    # 실제 토큰 정보 추출
                    actual_input, actual_output = 0, 0
                    if hasattr(self.model_strategy, '_last_response') and self.model_strategy._last_response:
                        actual_input, actual_output = TokenLogger.extract_actual_tokens(self.model_strategy._last_response)
                        logger.info(f"실제 토큰 추출: IN:{actual_input}, OUT:{actual_output}")
                    else:
                        logger.warning("_last_response 없음 - 실제 토큰 추출 불가")
                    
                    # 도구 실행 단계 종료
                    token_tracker.end_step(
                        StepType.TOOL_EXECUTION,
                        "Agent Tool Execution",
                        input_text=total_input_text,
                        output_text=output_text,
                        response_obj=getattr(self.model_strategy, '_last_response', None),
                        tool_name=",".join(used_tools) if used_tools else None,
                        additional_info={
                            "intermediate_steps_count": len(intermediate_steps),
                            "input_tokens": actual_input,
                            "output_tokens": actual_output,
                            "total_tokens": actual_input + actual_output
                        }
                    )
                    
                    # 실제 토큰 정보 추출
                    input_tokens, output_tokens = 0, 0
                    if hasattr(self.model_strategy, '_last_response') and self.model_strategy._last_response:
                        input_tokens, output_tokens = TokenLogger.extract_actual_tokens(self.model_strategy._last_response)
                        logger.info(f"TOOL 모드 실제 토큰: IN:{input_tokens}, OUT:{output_tokens}")
                    
                    # 실제 토큰이 없으면 추정치 사용 (도구 결과 포함)
                    if input_tokens == 0 and output_tokens == 0:
                        input_tokens = TokenLogger.estimate_tokens(total_input_text, self.model_strategy.model_name)
                        output_tokens = TokenLogger.estimate_tokens(output_text, self.model_strategy.model_name)
                        logger.warning(f"TOOL 모드 추정 토큰 사용: IN:{input_tokens}, OUT:{output_tokens}")
                    
                    # 대화 히스토리에 토큰 정보와 함께 저장
                    if hasattr(self, 'conversation_history') and self.conversation_history:
                        total_tokens = input_tokens + output_tokens if input_tokens > 0 or output_tokens > 0 else None
                        self.conversation_history.add_message(
                            "assistant", 
                            output_text, 
                            model_name=self.model_strategy.model_name,
                            input_tokens=input_tokens if input_tokens > 0 else None,
                            output_tokens=output_tokens if output_tokens > 0 else None,
                            total_tokens=total_tokens
                        )
                    
            except Exception as agent_error:
                error_msg = str(agent_error)
                
                # No generation chunks 오류 처리
                if "No generation chunks were returned" in error_msg:
                    logger.warning(f"Generation chunks 오류 발생, 단순 채팅으로 대체: {error_msg[:100]}")
                    from .simple_chat_processor import SimpleChatProcessor
                    simple_processor = SimpleChatProcessor(self.model_strategy)
                    return simple_processor.process_message(user_input, conversation_history)
                
                # 토큰 제한 오류 처리 (에이전트 실행 중)
                if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                    logger.warning(f"에이전트 실행 중 토큰 제한 오류 발생, 단순 채팅으로 대체: {error_msg[:100]}")
                    from .simple_chat_processor import SimpleChatProcessor
                    simple_processor = SimpleChatProcessor(self.model_strategy)
                    return simple_processor.process_message(user_input, conversation_history)
                
                # 시간 초과 및 Agent stopped 오류 처리 - Gemini 특별 처리
                if (self._is_agent_stopped_error(error_msg)):
                    logger.warning(f"에이전트 실행 시간/반복 제한 도달: {error_msg[:100]}")
                    # Gemini의 경우 부분 결과라도 활용 시도
                    if 'gemini' in self.model_strategy.model_name.lower():
                        try:
                            # 에이전트 실행기에서 부분 결과 추출 시도
                            partial_result = getattr(self._agent_executor, '_last_result', None)
                            if partial_result and isinstance(partial_result, dict):
                                return self._handle_agent_stopped(partial_result, user_input)
                        except:
                            pass
                    return "요청이 복잡하여 처리 시간이 초과되었습니다. 더 구체적이고 간단한 질문으로 다시 시도해주세요.", []
                
                # 파싱 오류 또는 형식 오류 처리
                if any(keyword in error_msg.lower() for keyword in ["parse", "format", "invalid format", "exact format"]):
                    logger.warning(f"에이전트 형식 오류 감지, 단순 채팅으로 전환: {error_msg[:100]}")
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
            logger.debug(f"도구 채팅 완료: {elapsed:.2f}초")
            
            # Unified tracker 기록
            if unified_tracker:
                # 실제 토큰 추출
                actual_input, actual_output = 0, 0
                if hasattr(self.model_strategy, '_last_response') and self.model_strategy._last_response:
                    actual_input, actual_output = TokenLogger.extract_actual_tokens(self.model_strategy._last_response)
                    logger.info(f"TOOL 모드 실제 토큰: IN:{actual_input}, OUT:{actual_output}")
                
                # 실제 토큰이 없으면 추정치 사용 (도구 결과 포함)
                if actual_input == 0 and actual_output == 0:
                    input_text = user_input
                    intermediate_steps = result.get("intermediate_steps", [])
                    if intermediate_steps:
                        for step in intermediate_steps:
                            if len(step) >= 2:
                                observation = str(step[1])
                                input_text += "\n" + observation
                    
                    actual_input = TokenLogger.estimate_tokens(input_text, self.model_strategy.model_name)
                    actual_output = TokenLogger.estimate_tokens(output, self.model_strategy.model_name)
                    logger.warning(f"TOOL 모드 추정 토큰 사용: IN:{actual_input}, OUT:{actual_output}")
                
                if actual_input > 0:
                    duration_ms = (time.time() - start_time) * 1000
                    unified_tracker.track_agent(
                        agent_name="MCPAgent",
                        model=self.model_strategy.model_name,
                        input_tokens=actual_input,
                        output_tokens=actual_output,
                        tool_calls=used_tools,
                        duration_ms=duration_ms
                    )
                unified_tracker.end_conversation()
            
            # 대화 종료
            if token_tracker.current_conversation:
                token_tracker.end_conversation(output)
            
            return self.format_response(output), used_tools
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"도구 채팅 오류: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # 'str' object has no attribute 'text' 오류 특별 처리
            if "'str' object has no attribute 'text'" in error_msg:
                logger.error("Claude 모델에서 text 속성 오류 발생 - 단순 채팅으로 대체")
                from .simple_chat_processor import SimpleChatProcessor
                simple_processor = SimpleChatProcessor(self.model_strategy)
                return simple_processor.process_message(user_input, conversation_history)
            
            # Agent stopped 오류 처리
            if self._is_agent_stopped_error(error_msg):
                return "요청 처리가 복잡하여 시간이 초과되었습니다. 더 간단한 질문으로 다시 시도해주세요.", []
            
            # 토큰 제한 오류 처리
            if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                logger.warning("토큰 제한 오류 발생, 단순 채팅으로 대체")
                from .simple_chat_processor import SimpleChatProcessor
                simple_processor = SimpleChatProcessor(self.model_strategy)
                return simple_processor.process_message(user_input, conversation_history)
            
            # 사용자 친화적 메시지
            return "요청을 처리하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.", []
    
    def _is_agent_stopped_error(self, error_msg: str) -> bool:
        """에이전트 중단 오류 메시지 감지"""
        agent_stopped_patterns = [
            "Agent stopped due to iteration limit or time limit",
            "Agent stopped due to max iterations",
            "Agent stopped due to time limit",
            "max_execution_time",
            "max_iterations",
            "timeout",
            "time limit exceeded",
            "iteration limit exceeded"
        ]
        
        error_lower = error_msg.lower()
        return any(pattern.lower() in error_lower for pattern in agent_stopped_patterns)
    
    def _is_agent_stopped_message(self, output: str) -> bool:
        """에이전트 중단 메시지 감지"""
        if not output:
            return False
            
        stopped_patterns = [
            "Agent stopped due to iteration limit or time limit",
            "Agent stopped due to max iterations", 
            "Agent stopped due to time limit",
            "I need to stop here",
            "I'll stop here",
            "I cannot continue",
            "시간이 초과",
            "반복 제한",
            "처리 시간 초과"
        ]
        
        output_lower = output.lower()
        return any(pattern.lower() in output_lower for pattern in stopped_patterns)
    
    def _handle_agent_stopped(self, result: Dict, user_input: str) -> Tuple[str, List]:
        """에이전트 중단 상황 처리 - 도구 결과 활용"""
        intermediate_steps = result.get("intermediate_steps", [])
        
        if intermediate_steps:
            logger.info(f"중간 단계 {len(intermediate_steps)}개 발견, 부분 결과 활용")
            
            # 모든 도구 실행 결과 수집
            tool_results = []
            used_tools = []
            
            for step in intermediate_steps:
                if len(step) >= 2:
                    action, observation = step[0], step[1]
                    
                    # 도구명 추출
                    tool_name = getattr(action, 'tool', 'unknown_tool')
                    used_tools.append(tool_name)
                    
                    # 결과 데이터 추출
                    if observation and str(observation).strip():
                        tool_results.append(str(observation))
            
            # 도구 결과가 있으면 포맷팅하여 반환
            if tool_results:
                # 마지막 도구 결과 사용 (가장 최신)
                final_result = tool_results[-1]
                
                # JSON 데이터인지 확인하고 파싱 시도
                try:
                    import json
                    if '{' in final_result and '}' in final_result:
                        # JSON 부분 추출
                        start = final_result.find('{')
                        end = final_result.rfind('}') + 1
                        json_str = final_result[start:end]
                        data = json.loads(json_str)
                        
                        # 여행 상품 데이터 포맷팅
                        if 'data' in data and 'saleProductList' in data['data']:
                            products = data['data']['saleProductList']
                            if products:
                                response = "검색된 여행 상품 정보:\n\n"
                                for i, product in enumerate(products[:5], 1):
                                    response += f"{i}. **{product.get('saleProductName', 'N/A')}**\n"
                                    response += f"   - 상품코드: {product.get('saleProductCode', 'N/A')}\n"
                                    response += f"   - 가격: {product.get('allProductPrice', 'N/A'):,}원\n"
                                    response += f"   - 출발일: {product.get('departureDay', 'N/A')}\n"
                                    response += f"   - 도착일: {product.get('arrivalDay', 'N/A')}\n\n"
                                
                                total_count = data['data'].get('resultCount', len(products))
                                response += f"총 {total_count}개 상품이 검색되었습니다."
                                return response, used_tools
                except:
                    pass
                
                # 도구 실행 결과를 사용자 친화적으로 처리
                formatted_result, tools = self._format_tool_result(final_result, used_tools)
                
                # MCP 도구 사용 시 토큰 로깅 (부분 결과)
                self._log_mcp_token_usage(user_input, tool_results, formatted_result)
                
                return formatted_result, tools
        
        return "요청이 복잡하여 처리 시간이 초과되었습니다. 더 구체적이고 간단한 질문으로 다시 시도해주세요.", []
    
    def _extract_used_tools(self, result: Dict) -> List:
        """사용된 도구 정보 추출"""
        used_tools = []
        intermediate_steps = result.get("intermediate_steps", [])
        
        for step in intermediate_steps:
            if len(step) >= 2:
                action = step[0]
                if hasattr(action, 'tool'):
                    used_tools.append(action.tool)
                elif isinstance(action, dict) and 'tool' in action:
                    used_tools.append(action['tool'])
        
        return list(set(used_tools))  # 중복 제거
    
    def _format_conversation_history(self, conversation_history: List[Dict]) -> str:
        """대화 히스토리를 문자열로 포맷팅"""
        if not conversation_history:
            return ""
        
        formatted_history = []
        for msg in conversation_history[-5:]:  # 최근 5개만 사용
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if content and len(content.strip()) > 0:
                formatted_history.append(f"{role}: {content[:200]}...")
        
        return "\n".join(formatted_history)
    
    def _format_tool_result(self, result: str, used_tools: List) -> Tuple[str, List]:
        """도구 실행 결과를 사용자 친화적으로 포맷팅"""
        try:
            import json
            # JSON 형태의 결과인지 확인
            if result.strip().startswith('{') and result.strip().endswith('}'):
                data = json.loads(result)
                
                # 성공적인 작업 완료 메시지 처리
                if 'content' in data and isinstance(data['content'], list):
                    for content_item in data['content']:
                        if isinstance(content_item, dict) and content_item.get('type') == 'text':
                            text_content = content_item.get('text', '')
                            if 'written' in text_content.lower() or 'created' in text_content.lower():
                                # 파일 작업 완료 메시지
                                if 'excel' in used_tools[0].lower() if used_tools else False:
                                    return "✅ **엑셀 파일이 성공적으로 생성되었습니다!**\n\n📊 요청하신 데이터가 엑셀 파일로 저장되었습니다.", used_tools
                                else:
                                    return f"✅ **작업이 성공적으로 완료되었습니다!**\n\n{text_content}", used_tools
                
                # 구조화된 결과가 있는 경우
                if 'structuredContent' in data:
                    structured = data['structuredContent']
                    if isinstance(structured, dict) and 'result' in structured:
                        result_text = structured['result']
                        if 'written' in result_text.lower():
                            return "✅ **파일이 성공적으로 생성되었습니다!**\n\n📄 요청하신 데이터가 파일로 저장되었습니다.", used_tools
                        return f"✅ **작업 완료:** {result_text}", used_tools
                
                # 일반적인 성공 응답
                if data.get('isError') == False:
                    return "✅ **요청하신 작업이 성공적으로 완료되었습니다!**", used_tools
            
            # JSON이 아닌 일반 텍스트 결과
            if 'success' in result.lower() or 'completed' in result.lower():
                return f"✅ **작업 완료:** {result[:200]}", used_tools
            
            return f"📋 **결과:** {result[:500]}{'...' if len(result) > 500 else ''}", used_tools
            
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 일반 텍스트로 처리
            return f"📋 **결과:** {result[:500]}{'...' if len(result) > 500 else ''}", used_tools
        except Exception:
            return "✅ **작업이 완료되었습니다.**", used_tools
    
    def _log_mcp_token_usage(self, user_input: str, tool_results: List[str], ai_response: str):
        """MCP 도구 사용 시 토큰 사용량 로깅"""
        try:
            # 전체 입력 토큰 계산 (사용자 입력 + 도구 결과)
            total_input = user_input
            if tool_results:
                tool_text = "\n".join(tool_results)
                total_input += f"\n\nMCP Tool Results:\n{tool_text}"
            
            # 토큰 추정
            input_tokens = TokenLogger.estimate_tokens(total_input, self.model_strategy.model_name)
            output_tokens = TokenLogger.estimate_tokens(ai_response, self.model_strategy.model_name)
            
            # 로깅
            TokenLogger.log_token_usage(
                self.model_strategy.model_name, 
                total_input, 
                ai_response, 
                "mcp_partial_result"
            )
            
        except Exception as e:
            logger.warning(f"MCP 토큰 로깅 실패: {e}")