"""
Hybrid Analyzer
질의 분석 및 Agent 조합 전략
"""

from typing import List, Dict, Any, Optional
from langchain.schema import HumanMessage
from core.logging import get_logger
from .base_agent import BaseAgent, AgentResult

logger = get_logger("hybrid_analyzer")


class HybridAnalyzer:
    """하이브리드 분석 시스템"""
    
    def __init__(self, llm, agents: List[BaseAgent]):
        """
        Initialize hybrid analyzer
        
        Args:
            llm: LangChain LLM
            agents: List of available agents
        """
        self.llm = llm
        self.agents = agents
        
        logger.info(f"Hybrid analyzer initialized with {len(agents)} agents")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze user query
        
        Args:
            query: User query
            
        Returns:
            Analysis result
        """
        analysis = {
            "query": query,
            "intent": self._detect_intent(query),
            "entities": self._extract_entities(query),
            "complexity": self._assess_complexity(query),
            "required_agents": []
        }
        
        # 필요한 Agent 결정
        analysis["required_agents"] = self._determine_agents(analysis)
        
        logger.info(f"Query analysis: {analysis['intent']}, agents: {len(analysis['required_agents'])}")
        return analysis
    
    def execute_hybrid(self, query: str) -> str:
        """
        Execute hybrid analysis and agent combination
        
        Args:
            query: User query
            
        Returns:
            Final response
        """
        # 질의 분석
        analysis = self.analyze_query(query)
        
        # Agent 실행
        results = []
        for agent_name in analysis["required_agents"]:
            agent = self._get_agent_by_name(agent_name)
            if agent:
                result = agent.execute(query)
                results.append(result)
        
        # 결과 통합
        final_response = self._integrate_results(results, query)
        
        return final_response
    
    def _detect_intent(self, query: str) -> str:
        """
        Detect query intent using LLM
        
        Args:
            query: User query
            
        Returns:
            Intent type
        """
        prompt = f"""Analyze the user's intent from the query and return ONLY ONE of these categories:
- search: Finding or retrieving information
- analyze: Analyzing, summarizing, or processing data
- create: Creating, generating, or building something
- general: General conversation or unclear intent

Query: {query}

Return only the category name (search/analyze/create/general):"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            intent = response.content.strip().lower()
            
            if intent in ["search", "analyze", "create", "general"]:
                logger.info(f"LLM detected intent: {intent}")
                return intent
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
        
        return "general"
    
    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract entities from query using LLM
        
        Args:
            query: User query
            
        Returns:
            List of entities
        """
        prompt = f"""Extract key entities from the query. Return a comma-separated list.
Focus on: file types, data types, tools, services, locations, dates, etc.

Query: {query}

Return entities as comma-separated values (e.g., "pdf, excel, database"):"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            entities_text = response.content.strip()
            
            if entities_text and entities_text.lower() not in ["none", "n/a", ""]:
                entities = [e.strip() for e in entities_text.split(",") if e.strip()]
                logger.info(f"LLM extracted entities: {entities}")
                return entities
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
        
        return []
    
    def _assess_complexity(self, query: str) -> str:
        """
        Assess query complexity
        
        Args:
            query: User query
            
        Returns:
            Complexity level (low, medium, high)
        """
        # 단어 수 기반 복잡도
        word_count = len(query.split())
        
        if word_count < 5:
            return "low"
        elif word_count < 15:
            return "medium"
        else:
            return "high"
    
    def _determine_agents(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Determine required agents using LLM based on analysis
        
        Args:
            analysis: Query analysis result
            
        Returns:
            List of agent names
        """
        # Agent 정보 수집
        agent_descriptions = []
        for agent in self.agents:
            agent_descriptions.append(f"- {agent.get_name()}: {agent.get_description()}")
        
        agents_info = "\n".join(agent_descriptions)
        
        prompt = f"""Based on the query analysis, select the most appropriate agents.

Query: {analysis['query']}
Intent: {analysis['intent']}
Entities: {', '.join(analysis['entities']) if analysis['entities'] else 'None'}
Complexity: {analysis['complexity']}

Available Agents:
{agents_info}

Return ONLY the agent names as comma-separated values (e.g., "RAGAgent, MCPAgent"):"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            agents_text = response.content.strip()
            
            # Agent 이름 파싱
            selected_names = [name.strip() for name in agents_text.split(",") if name.strip()]
            
            # 유효한 Agent만 필터링
            valid_agents = []
            for name in selected_names:
                for agent in self.agents:
                    if name in agent.get_name() or agent.get_name() in name:
                        valid_agents.append(agent.get_name())
                        break
            
            if valid_agents:
                logger.info(f"LLM selected agents: {valid_agents}")
                return valid_agents
        
        except Exception as e:
            logger.error(f"Agent determination failed: {e}")
        
        # Fallback: 첫 번째 Agent
        if self.agents:
            return [self.agents[0].get_name()]
        return []
    
    def _integrate_results(self, results: List[AgentResult], query: str) -> str:
        """
        Integrate multiple agent results
        
        Args:
            results: List of agent results
            query: Original query
            
        Returns:
            Integrated response
        """
        if not results:
            return "No results available."
        
        if len(results) == 1:
            return results[0].output
        
        # 여러 결과 통합
        integrated = "## Combined Results\n\n"
        
        for i, result in enumerate(results, 1):
            agent_name = result.metadata.get("agent", f"Agent {i}")
            integrated += f"### {agent_name}\n{result.output}\n\n"
        
        return integrated
    
    def _get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        for agent in self.agents:
            if agent.get_name() == name or name in agent.get_name():
                return agent
        return None
