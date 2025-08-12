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
    
    def supports_tools(self) -> bool:
        """도구 지원 여부"""
        return True
    
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
                
                # 토큰 제한 오류 처리 (에이전트 실행 중)
                if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                    logger.warning(f"에이전트 실행 중 토큰 제한 오류 발생, 단순 채팅으로 대체: {error_msg[:100]}")
                    from .simple_chat_processor import SimpleChatProcessor
                    simple_processor = SimpleChatProcessor(self.model_strategy)
                    return simple_processor.process_message(user_input, conversation_history)
                
                # 시간 초과 및 Agent stopped 오류 처리
                if (self._is_agent_stopped_error(error_msg)):
                    logger.warning(f"에이전트 실행 시간/반복 제한 도달: {error_msg[:100]}")
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
            logger.info(f"도구 채팅 완료: {elapsed:.2f}초")
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
            
            return f"도구 사용 중 오류가 발생했습니다: {str(e)[:100]}...", []
    
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
                
                # JSON 파싱 실패 시 원본 결과 반환
                return f"검색 결과:\n\n{final_result[:1000]}...", used_tools
        
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