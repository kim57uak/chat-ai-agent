"""
Base Agent Interface
LangChain AgentExecutor를 래핑한 추상 클래스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain.agents import AgentExecutor
from langchain.tools import BaseTool
from core.logging import get_logger
import time

logger = get_logger("base_agent")


@dataclass
class AgentResult:
    """Agent 실행 결과"""
    output: str
    intermediate_steps: List[Any] = None
    metadata: Dict[str, Any] = None


class BaseAgent(ABC):
    """LangChain AgentExecutor를 래핑한 추상 클래스"""
    
    # 서브클래스에서 오버라이드: True면 Chain, False면 AgentExecutor
    is_chain_based = False
    
    def __init__(self, llm, tools: Optional[List[BaseTool]] = None):
        """
        Initialize base agent
        
        Args:
            llm: LangChain LLM instance
            tools: List of LangChain tools
        """
        self.llm = llm
        self.tools = tools or []
        self.executor = None
        self._can_handle_cache = {}  # 캠싱: {query_hash: result}
        
        logger.info(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    def _create_executor(self) -> AgentExecutor:
        """
        Create LangChain AgentExecutor
        
        Returns:
            AgentExecutor instance
        """
        pass
    
    @abstractmethod
    def can_handle(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Check if agent can handle the query
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if agent can handle
        """
        pass
    
    def execute(self, query: str, context: Optional[Dict] = None) -> AgentResult:
        """
        Execute agent
        
        Args:
            query: User query
            context: Additional context (includes conversation_history, unified_tracker)
            
        Returns:
            AgentResult
        """
        start_time = time.time()
        
        try:
            executor = self._create_executor()
            
            if not executor:
                return AgentResult(
                    output="Agent executor not available",
                    metadata={"error": True}
                )
            
            # 클래스 속성으로 타입 구분 (isinstance 대신)
            if self.is_chain_based:
                # RAGAgent: Chain 사용 (대화 맥락 유지)
                chat_history = self._extract_chat_history(context)
                inputs = {"question": query, "chat_history": chat_history}
                logger.info(f"[LLM REQ] {self.get_name()} invoking Chain with {len(chat_history)} history messages")
            else:
                # 다른 Agent: AgentExecutor 사용
                inputs = {"input": query}
                logger.info(f"[LLM REQ] {self.get_name()} invoking AgentExecutor")
            
            result = executor.invoke(inputs)
            logger.info(f"[LLM RES] {self.get_name()} completed")
            
            # Unified tracker 기록
            self._track_execution(context, start_time, result)
            
            # 결과 추출 (Chain은 answer/result, AgentExecutor는 output)
            output = result.get("answer") or result.get("result") or result.get("output") or str(result)
            
            # 도구 호출 여부 확인
            intermediate_steps = result.get("intermediate_steps", [])
            logger.info(f"{self.get_name()} executed {len(intermediate_steps)} tool calls")
            
            # 도구 호출 내역 로깅
            for i, step in enumerate(intermediate_steps, 1):
                if len(step) >= 2:
                    action = step[0]
                    tool_name = getattr(action, 'tool', 'unknown')
                    logger.info(f"  Tool {i}: {tool_name}")
            
            # 결과 검증 및 처리 (Tool 모드 방식)
            if not output or not output.strip() or len(output.strip()) < 10:
                logger.warning(f"{self.get_name()} returned insufficient output, extracting from intermediate_steps")
                if intermediate_steps:
                    extracted = self._extract_tool_results(intermediate_steps)
                    if extracted and extracted != "Tool executed but no clear result":
                        output = extracted
                        logger.info(f"Extracted {len(output)} chars from tool results")
            elif intermediate_steps:
                logger.info(f"{self.get_name()} executed {len(intermediate_steps)} tool calls successfully")
            
            return AgentResult(
                output=output,
                intermediate_steps=result.get("intermediate_steps", []),
                metadata={"agent": self.__class__.__name__}
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Agent execution failed: {error_msg}")
            

            
            # 사용자 친화적 메시지
            user_message = "요청을 처리하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
            
            return AgentResult(
                output=user_message,
                metadata={"error": True, "error_detail": error_msg}
            )
    
    def get_name(self) -> str:
        """Get agent name"""
        return self.__class__.__name__
    
    def get_description(self) -> str:
        """Get agent description"""
        return self.__doc__ or "No description"
    
    def _extract_tool_results(self, intermediate_steps: List) -> str:
        """
        Extract and format tool results (Tool mode style)
        
        Args:
            intermediate_steps: List of (action, observation) tuples
            
        Returns:
            Formatted tool results
        """
        if not intermediate_steps:
            return "Tool executed but no clear result"
        
        # 마지막 도구 결과 사용 (가장 최신)
        tool_results = []
        for step in intermediate_steps:
            if len(step) >= 2:
                action, observation = step[0], step[1]
                if observation and str(observation).strip():
                    tool_results.append(str(observation).strip())
        
        if not tool_results:
            return "Tool executed but no clear result"
        
        # 가장 최신 결과 반환
        final_result = tool_results[-1]
        
        # JSON 데이터 파싱 시도
        try:
            import json
            if '{' in final_result and '}' in final_result:
                start = final_result.find('{')
                end = final_result.rfind('}') + 1
                json_str = final_result[start:end]
                data = json.loads(json_str)
                
                # 성공적인 작업 메시지
                if data.get('isError') == False:
                    return "✅ 요청하신 작업이 성공적으로 완료되었습니다!"
        except:
            pass
        
        # 일반 텍스트 결과
        return final_result[:1000] if len(final_result) > 1000 else final_result
    
    def _extract_chat_history(self, context: Optional[Dict]) -> List:
        """
        Extract chat history from context and convert to LangChain format
        
        Args:
            context: Context dict with conversation_history
            
        Returns:
            List of (question, answer) tuples for ConversationalRetrievalChain
        """
        if not context or 'conversation_history' not in context:
            return []
        
        history = context.get('conversation_history', [])
        if not history:
            return []
        
        # ConversationalRetrievalChain expects [(question, answer), ...]
        chat_history = []
        for i in range(0, len(history) - 1, 2):
            if i + 1 < len(history):
                user_msg = history[i]
                ai_msg = history[i + 1]
                
                if user_msg.get('role') == 'user' and ai_msg.get('role') == 'assistant':
                    question = user_msg.get('content', '')
                    answer = ai_msg.get('content', '')
                    chat_history.append((question, answer))
        
        # prompt_config.json의 max_history_pairs 설정 적용
        max_pairs = self._get_max_history_pairs()
        if max_pairs and len(chat_history) > max_pairs:
            chat_history = chat_history[-max_pairs:]
            logger.debug(f"Limited to {max_pairs} pairs (from prompt_config.json)")
        
        logger.debug(f"Extracted {len(chat_history)} conversation pairs from history")
        return chat_history
    
    def _get_max_history_pairs(self) -> int:
        """
        Get max_history_pairs from prompt_config.json
        
        Returns:
            Max history pairs (default: 4)
        """
        try:
            from core.config.config_manager import ConfigManager
            config_manager = ConfigManager('prompt_config.json')
            config = config_manager.load()
            return config.get('conversation_settings', {}).get('max_history_pairs', 4)
        except Exception as e:
            logger.warning(f"Failed to load max_history_pairs: {e}, using default 4")
            return 4
    
    def _track_execution(self, context: Optional[Dict], start_time: float, result: Dict):
        """
        Track agent execution with unified tracker
        
        Args:
            context: Context dict with unified_tracker
            start_time: Execution start time
            result: Agent execution result
        """
        if not context or 'unified_tracker' not in context:
            return
        
        unified_tracker = context.get('unified_tracker')
        if not unified_tracker:
            return
        
        try:
            # Extract token counts from result
            input_tokens, output_tokens = self._extract_token_counts(result)
            
            # Extract tool calls
            tool_calls = []
            intermediate_steps = result.get("intermediate_steps", [])
            for step in intermediate_steps:
                if len(step) >= 2:
                    action = step[0]
                    tool_name = getattr(action, 'tool', None)
                    if tool_name:
                        tool_calls.append(tool_name)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # 모델명 추출 (context 또는 llm에서)
            model_name = 'unknown'
            if context and 'model_name' in context:
                model_name = context['model_name']
            elif hasattr(self.llm, 'model_name'):
                model_name = self.llm.model_name
            elif hasattr(self.llm, 'model'):
                model_name = self.llm.model
            
            logger.debug(f"{self.get_name()} using model: {model_name}")
            
            # Track with unified tracker
            unified_tracker.track_agent(
                agent_name=self.get_name(),
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                tool_calls=tool_calls,
                duration_ms=duration_ms
            )
            
            logger.debug(f"Tracked {self.get_name()}: {input_tokens}+{output_tokens} tokens, {len(tool_calls)} tools")
            
        except Exception as e:
            logger.warning(f"Failed to track agent execution: {e}")
    
    def _extract_token_counts(self, result: Dict) -> tuple:
        """
        Extract token counts from agent result
        
        Args:
            result: Agent execution result
            
        Returns:
            (input_tokens, output_tokens)
        """
        from core.token_logger import TokenLogger
        
        try:
            # 1. LLM의 _last_response에서 추출 (가장 정확)
            if hasattr(self.llm, '_last_response') and self.llm._last_response:
                input_t, output_t = TokenLogger.extract_actual_tokens(self.llm._last_response)
                if input_t > 0 or output_t > 0:
                    logger.info(f"{self.get_name()} extracted tokens from LLM: {input_t}/{output_t}")
                    return input_t, output_t
                else:
                    logger.warning(f"{self.get_name()} _last_response exists but no tokens extracted")
            
            # 2. intermediate_steps에서 추출
            intermediate_steps = result.get('intermediate_steps', [])
            if intermediate_steps:
                for step in intermediate_steps:
                    if len(step) >= 2:
                        action, observation = step[0], step[1]
                        if hasattr(observation, 'response_metadata'):
                            input_t, output_t = TokenLogger.extract_actual_tokens(observation)
                            if input_t > 0 or output_t > 0:
                                return input_t, output_t
            
            # 3. result metadata에서 추출
            if 'usage_metadata' in result:
                metadata = result['usage_metadata']
                input_tokens = metadata.get('input_tokens', 0)
                output_tokens = metadata.get('output_tokens', 0)
                if input_tokens > 0 or output_tokens > 0:
                    return input_tokens, output_tokens
            
            # Fallback: 텍스트 길이로 추정
            input_text = result.get('input', '') or result.get('question', '')
            output_text = result.get('output', '') or result.get('answer', '') or result.get('result', '')
            
            user_input_size = len(str(input_text))
            
            # RAG: 검색된 문서를 입력 토큰에 포함 (CRITICAL)
            rag_docs_size = 0
            source_documents = result.get('source_documents', [])
            if source_documents:
                rag_docs_text = ""
                for doc in source_documents:
                    if hasattr(doc, 'page_content'):
                        rag_docs_text += "\n" + doc.page_content
                    else:
                        rag_docs_text += "\n" + str(doc)
                
                if rag_docs_text:
                    rag_docs_size = len(rag_docs_text)
                    input_text = str(input_text) + rag_docs_text
                    logger.debug(f"Added {len(source_documents)} RAG documents ({rag_docs_size} chars) to input")
            
            # 도구 결과를 입력 토큰에 포함
            intermediate_steps = result.get('intermediate_steps', [])
            tool_results_size = 0
            if intermediate_steps:
                tool_results_text = ""
                for step in intermediate_steps:
                    if len(step) >= 2:
                        observation = str(step[1])
                        tool_results_text += "\n" + observation
                
                if tool_results_text:
                    tool_results_size = len(tool_results_text)
                    input_text = str(input_text) + tool_results_text
            
            # 시스템 프롬프트 추가 (약 500-1000 tokens)
            system_prompt_tokens = 800
            
            model_name = getattr(self.llm, 'model_name', 'gpt-3.5-turbo')
            input_tokens = TokenLogger.estimate_tokens(str(input_text), model_name) + system_prompt_tokens
            output_tokens = TokenLogger.estimate_tokens(str(output_text), model_name)
            
            logger.info(f"{self.get_name()} estimated: IN:{input_tokens} (user:{user_input_size}, rag:{rag_docs_size}, tool:{tool_results_size}, system:~800), OUT:{output_tokens}")
            return input_tokens, output_tokens
            
        except Exception as e:
            logger.warning(f"Failed to extract token counts: {e}")
            return 0, 0
