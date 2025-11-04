"""
Multi-Agent Orchestrator
여러 Agent를 조율하고 실행
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from langchain.schema import HumanMessage
from langchain.prompts import ChatPromptTemplate
from core.logging import get_logger
from .base_agent import BaseAgent, AgentResult

logger = get_logger("multi_agent_orchestrator")


class ExecutionStrategy(Enum):
    """Agent 실행 전략"""
    SEQUENTIAL = "sequential"      # 순차 실행
    PARALLEL = "parallel"          # 병렬 실행
    CONDITIONAL = "conditional"    # 조건부 분기
    HYBRID = "hybrid"              # 혼합


class MultiAgentOrchestrator:
    """Multi-Agent 오케스트레이터"""
    
    def __init__(self, llm, agents: List[BaseAgent]):
        """
        Initialize orchestrator
        
        Args:
            llm: LangChain LLM for agent selection
            agents: List of agents
        """
        self.llm = llm
        self.agents = agents
        
        logger.info(f"Orchestrator initialized with {len(agents)} agents")
    
    def run(self, query: str, context: Optional[Dict] = None) -> str:
        """
        Run orchestrator with LLM-based agent selection
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Final response
        """
        # LLM 기반 Agent 선택 (우선)
        selected_agent = self._select_agent_with_llm(query, context)
        
        # Fallback: 규칙 기반
        if not selected_agent:
            logger.warning("LLM selection failed, using rule-based fallback")
            selected_agent = self._select_agent_fallback(query, context)
        
        if not selected_agent:
            return "No suitable agent found for this query."
        
        # Agent 실행
        result = selected_agent.execute(query, context)
        
        return result.output
    
    def _select_agent_fallback(self, query: str, context: Optional[Dict] = None) -> Optional[BaseAgent]:
        """
        Fallback: Rule-based agent selection
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Selected agent or None
        """
        # Agent의 can_handle 메서드 활용
        for agent in self.agents:
            if agent.can_handle(query, context):
                logger.info(f"Fallback selected agent: {agent.get_name()}")
                return agent
        
        # 기본 Agent (첫 번째)
        if self.agents:
            logger.info(f"Using default agent: {self.agents[0].get_name()}")
            return self.agents[0]
        
        return None
    
    def _select_agent_with_llm(self, query: str, context: Optional[Dict] = None) -> Optional[BaseAgent]:
        """
        Select agent using LLM based on context analysis
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Selected agent
        """
        # Agent 정보 수집
        agent_info = []
        for agent in self.agents:
            agent_info.append(f"- {agent.get_name()}: {agent.get_description()}")
        
        agents_text = "\n".join(agent_info)
        
        # Context 정보 추가
        context_info = ""
        if context:
            context_info = f"\nContext: {context}"
        
        # LLM에게 Agent 선택 요청
        prompt = f"""Analyze the query and context, then select the MOST appropriate agent.

Query: {query}{context_info}

Available Agents:
{agents_text}

Consider:
1. Query intent and requirements
2. Agent capabilities and strengths
3. Context information if provided

Return ONLY the exact agent name (e.g., "RAGAgent" or "MCPAgent"):"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            selected_name = response.content.strip()
            
            # Agent 찾기 (부분 매칭 포함)
            for agent in self.agents:
                if agent.get_name() in selected_name or selected_name in agent.get_name():
                    logger.info(f"LLM selected agent: {agent.get_name()}")
                    return agent
            
            logger.warning(f"LLM returned unknown agent: {selected_name}")
        
        except Exception as e:
            logger.error(f"LLM agent selection failed: {e}")
        
        return None
    
    def execute_sequential(self, query: str, agent_names: List[str]) -> List[AgentResult]:
        """
        Execute agents sequentially
        
        Args:
            query: User query
            agent_names: List of agent names to execute
            
        Returns:
            List of results
        """
        results = []
        
        for name in agent_names:
            agent = self._get_agent_by_name(name)
            if agent:
                result = agent.execute(query)
                results.append(result)
        
        return results
    
    def execute_parallel(self, query: str, agent_names: List[str]) -> List[AgentResult]:
        """
        Execute agents in parallel
        
        Args:
            query: User query
            agent_names: List of agent names to execute
            
        Returns:
            List of results
        """
        from concurrent.futures import ThreadPoolExecutor
        
        agents = [self._get_agent_by_name(name) for name in agent_names]
        agents = [a for a in agents if a]  # Filter None
        
        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = [executor.submit(agent.execute, query) for agent in agents]
            results = [future.result() for future in futures]
        
        return results
    
    def _get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        for agent in self.agents:
            if agent.get_name() == name:
                return agent
        return None
