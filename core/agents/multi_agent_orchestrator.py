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
            selected_name = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
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
        
        # 병렬 실행 (각 Agent 독립 실행)
        results = []
        with ThreadPoolExecutor(max_workers=len(suitable_agents)) as executor:
            # 각 Agent를 별도 함수로 래핑하여 독립성 보장
            def execute_agent(agent, q, ctx):
                # 각 Agent에 독립적인 context 전달 (RAG 문서 정보 제외)
                clean_ctx = {k: v for k, v in (ctx or {}).items() if k not in ['documents', 'rag_mode_active']}
                return agent.execute(q, clean_ctx)
            
            future_to_agent = {executor.submit(execute_agent, agent, query, context): agent for agent in suitable_agents}
            
            for future in as_completed(future_to_agent, timeout=90):  # 전체 타임아웃 증가
                agent = future_to_agent[future]
                try:
                    result = future.result(timeout=60)  # 개별 Agent 타임아웃 증가
                    if not result.metadata.get("error"):
                        results.append((agent.get_name(), result.output))
                        logger.info(f"Agent {agent.get_name()} completed successfully")
                except TimeoutError:
                    logger.warning(f"Agent {agent.get_name()} timed out, skipping")
                except Exception as e:
                    logger.error(f"Agent {agent.get_name()} failed: {e}")
        
        # 결과 병합
        return self._merge_results(results)
    
    def _select_multiple_agents(self, query: str, context: Optional[Dict], max_agents: int = 3) -> List[BaseAgent]:
        """
        Select multiple suitable agents using SINGLE LLM call
        
        Args:
            query: User query
            context: Additional context
            max_agents: Maximum number of agents
            
        Returns:
            List of selected agents
        """
        # Agent 정보 수집
        agent_info = []
        for agent in self.agents:
            agent_info.append(f"- {agent.get_name()}: {agent.get_description()}")
        
        agents_text = "\n".join(agent_info)
        
        # 단일 LLM 호출로 모든 Agent 판단
        prompt = f"""Analyze which agents can handle this query. You can select MULTIPLE agents if the query requires multiple capabilities.

Query: {query}

Available Agents:
{agents_text}

Analysis Guidelines:
- Does the query need internal documents? Consider RAGAgent
- Does the query need external/web information? Consider MCPAgent
- Does the query need data analysis? Consider PandasAgent
- Does the query need calculations/code? Consider PythonREPLAgent

IMPORTANT:
- If query requires BOTH internal knowledge AND external information, select BOTH agents
- Think about what information sources are needed to fully answer the query
- Select ALL relevant agents that can contribute (up to {max_agents})

Return ONLY agent names (comma-separated, max {max_agents}):"""
        
        try:
            logger.info(f"[AI REQ] Orchestrator selecting agents for: {query[:50]}...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            logger.info(f"[AI RES] Orchestrator agent selection completed")
            
            selected_names = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
            # Agent 매칭
            selected = []
            for agent in self.agents:
                if agent.get_name() in selected_names:
                    selected.append(agent)
                    if len(selected) >= max_agents:
                        break
            
            if selected:
                logger.info(f"Selected {len(selected)} agents: {[a.get_name() for a in selected]}")
                return selected
        
        except Exception as e:
            logger.error(f"LLM agent selection failed: {e}")
        
        # Fallback: 첫 번째 Agent만 사용
        logger.warning("Using fallback: first agent only")
        return [self.agents[0]] if self.agents else []
    
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
        
        # 긍정적 결과 우선 선택
        positive_results = []
        negative_results = []
        
        for name, output in results:
            output_stripped = output.strip()
            
            # 너무 짧은 응답 제외
            if len(output_stripped) < 30:
                logger.debug(f"Filtered short response from {name}")
                continue
            
            # 부정적 키워드 체크 (문서/정보 없음)
            negative_keywords = [
                "문서에", "제공된 문서", "주어진 문서",
                "없습니다", "없어요", "모릅니다",
                "no information", "cannot provide", "not available"
            ]
            
            is_negative = any(keyword in output_stripped[:100] for keyword in negative_keywords)
            
            if is_negative:
                logger.debug(f"Negative response from {name}")
                negative_results.append((name, output))
            else:
                logger.info(f"Positive response from {name}")
                positive_results.append((name, output))
        
        # 긍정적 결과가 있으면 우선 사용
        if positive_results:
            if len(positive_results) == 1:
                return positive_results[0][1]
            
            # 여러 긍정적 결과 병합
            merged_text = "\n\n".join([f"**{name}:**\n{output}" for name, output in positive_results])
            return merged_text
        
        # 긍정적 결과 없으면 부정적 결과라도 반환
        if negative_results:
            logger.warning("Only negative results available")
            return negative_results[0][1]
        
        return "No valid results available"
    
    def _get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        for agent in self.agents:
            if agent.get_name() == name:
                return agent
        return None
