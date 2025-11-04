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
        if not self.executor:
            self.executor = self._create_executor()
        
        try:
            result = self.executor.invoke({"input": query})
            
            return AgentResult(
                output=result.get("output", ""),
                intermediate_steps=result.get("intermediate_steps", []),
                metadata={"agent": self.__class__.__name__}
            )
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return AgentResult(
                output=f"Error: {str(e)}",
                metadata={"error": True}
            )
    
    def get_name(self) -> str:
        """Get agent name"""
        return self.__class__.__name__
    
    def get_description(self) -> str:
        """Get agent description"""
        return self.__doc__ or "No description"
