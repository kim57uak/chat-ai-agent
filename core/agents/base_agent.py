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
            context: Additional context
            
        Returns:
            AgentResult
        """
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
                inputs = {"question": query, "chat_history": []}
                logger.info(f"[LLM REQ] {self.get_name()} invoking Chain")
            else:
                # 다른 Agent: AgentExecutor 사용
                inputs = {"input": query}
                logger.info(f"[LLM REQ] {self.get_name()} invoking AgentExecutor")
            
            result = executor.invoke(inputs)
            logger.info(f"[LLM RES] {self.get_name()} completed")
            
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
