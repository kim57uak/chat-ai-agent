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
            agents: List of agents (RAGAgent, MCPAgent, PandasAgent, SQLAgent, etc.)
        """
        self.llm = llm
        self.agents = agents
        
        logger.info(f"Orchestrator initialized with {len(agents)} agents")
        for agent in agents:
            logger.info(f"  - {agent.get_name()}: {agent.get_description()}")
    
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
        # Agent의 can_handle 메서드 활용 (우선순위: PandasAgent > SQLAgent > RAGAgent > MCPAgent)
        priority_order = ['pandas', 'sql', 'rag', 'mcp']
        
        # 우선순위별로 체크
        for priority_name in priority_order:
            for agent in self.agents:
                if priority_name in agent.get_name().lower() and agent.can_handle(query, context or {}):
                    logger.info(f"Fallback selected agent: {agent.get_name()}")
                    return agent
        
        # 우선순위 없는 Agent 체크
        for agent in self.agents:
            if agent.can_handle(query, context or {}):
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
    
    def execute_parallel(self, query: str, agent_names: List[str], timeout: int = 30) -> List[AgentResult]:
        """
        Execute agents in parallel with timeout and error handling
        
        Args:
            query: User query
            agent_names: List of agent names to execute
            timeout: Timeout per agent in seconds
            
        Returns:
            List of results
        """
        from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
        
        agents = [self._get_agent_by_name(name) for name in agent_names]
        agents = [a for a in agents if a]
        
        if not agents:
            return []
        
        results = []
        with ThreadPoolExecutor(max_workers=min(len(agents), 5)) as executor:
            future_to_agent = {executor.submit(agent.execute, query): agent for agent in agents}
            
            for future in as_completed(future_to_agent, timeout=timeout):
                agent = future_to_agent[future]
                try:
                    result = future.result(timeout=timeout)
                    results.append(result)
                    logger.info(f"Agent {agent.get_name()} completed")
                except TimeoutError:
                    logger.warning(f"Agent {agent.get_name()} timed out")
                    results.append(AgentResult(
                        output=f"Timeout: {agent.get_name()}",
                        metadata={"error": True, "timeout": True}
                    ))
                except Exception as e:
                    logger.error(f"Agent {agent.get_name()} failed: {e}")
                    results.append(AgentResult(
                        output=f"Error: {str(e)}",
                        metadata={"error": True}
                    ))
        
        return results
    
    def execute_parallel_optimized(self, query: str, context: Optional[Dict] = None) -> str:
        """
        Optimized parallel execution with intelligent agent selection
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Merged result
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # LLM으로 적합한 Agent들 선택 (최대 3개)
        suitable_agents = self._select_multiple_agents(query, context, max_agents=3)
        
        if not suitable_agents:
            return self.run(query, context)
        
        if len(suitable_agents) == 1:
            return suitable_agents[0].execute(query, context).output
        
        # 병렬 실행
        results = []
        with ThreadPoolExecutor(max_workers=len(suitable_agents)) as executor:
            future_to_agent = {executor.submit(agent.execute, query, context): agent for agent in suitable_agents}
            
            for future in as_completed(future_to_agent, timeout=30):
                agent = future_to_agent[future]
                try:
                    result = future.result(timeout=10)
                    if not result.metadata.get("error"):
                        results.append((agent.get_name(), result.output))
                except Exception as e:
                    logger.error(f"Agent {agent.get_name()} failed: {e}")
        
        # 결과 병합
        return self._merge_results(results)
    
    def _select_multiple_agents(self, query: str, context: Optional[Dict], max_agents: int = 3) -> List[BaseAgent]:
        """
        Select multiple suitable agents using can_handle method
        
        Args:
            query: User query
            context: Additional context
            max_agents: Maximum number of agents
            
        Returns:
            List of selected agents
        """
        selected = []
        
        # 모든 Agent의 can_handle 체크
        for agent in self.agents:
            try:
                if agent.can_handle(query, context or {}):
                    selected.append(agent)
                    logger.info(f"Agent {agent.get_name()} can handle query")
                    
                    if len(selected) >= max_agents:
                        break
            except Exception as e:
                logger.error(f"Agent {agent.get_name()} can_handle check failed: {e}")
        
        # 선택된 Agent가 없으면 모두 사용 (최대 max_agents개)
        if not selected:
            logger.warning("No agents selected by can_handle, using all agents")
            selected = self.agents[:max_agents]
        
        logger.info(f"Selected {len(selected)} agents: {[a.get_name() for a in selected]}")
        return selected
    
    def _merge_results(self, results: List[tuple]) -> str:
        """
        Merge results from multiple agents
        
        Args:
            results: List of (agent_name, output) tuples
            
        Returns:
            Merged output
        """
        if not results:
            return "No results available"
        
        if len(results) == 1:
            return results[0][1]
        
        # LLM으로 결과 통합
        merged_text = "\n\n".join([f"**{name}:**\n{output}" for name, output in results])
        
        prompt = f"""Synthesize these agent results into a coherent answer:

{merged_text}

Provide a unified, comprehensive response:"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.error(f"Result merging failed: {e}")
            return merged_text
    
    def _get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        for agent in self.agents:
            if agent.get_name() == name:
                return agent
        return None
