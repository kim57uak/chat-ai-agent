from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain.schema import HumanMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)


class ToolDecisionStrategy(ABC):
    """도구 사용 결정을 위한 전략 인터페이스"""
    
    @abstractmethod
    def should_use_tools(self, user_input: str, tools: List[Any], llm: Any, force_agent: bool = False) -> bool:
        pass


class AIBasedToolDecisionStrategy(ToolDecisionStrategy):
    """AI 기반 도구 사용 결정 전략"""
    
    def should_use_tools(self, user_input: str, tools: List[Any], llm: Any, force_agent: bool = False) -> bool:
        """AI가 자연어를 이해하여 도구 사용 여부를 지능적으로 결정"""
        import time
        start_time = time.time()
        logger.info(f"🤔 도구 사용 판단 시작: {user_input[:30]}...")
        
        try:
            # 도구 설명 수집
            tool_descriptions = []
            for tool in tools[:8]:  # 주요 도구들만
                desc = getattr(tool, "description", tool.name)
                tool_descriptions.append(f"- {tool.name}: {desc[:100]}")

            tools_info = (
                "\n".join(tool_descriptions)
                if tool_descriptions
                else "사용 가능한 도구 없음"
            )

            # Agent 모드 선택 시 더 적극적인 판단 기준 적용
            agent_context = ""
            if force_agent:
                agent_context = "\n\nIMPORTANT: The user has specifically selected Agent mode, indicating they want to use available tools when possible. Be more inclined to use tools for information gathering, searches, or data processing tasks."

            decision_prompt = f"""User request: "{user_input}"

Available tools:
{tools_info}

Determine if this request requires using tools to provide accurate information.

Requires tools:
- Real-time information search (web search, news, weather, etc.)
- Database queries (travel products, flights, etc.)
- External API calls (maps, translation, etc.)
- File processing or calculations
- Current time or date-related information
- Specific data lookups or searches
- Location-based queries
- If you request something You don't know, utilize appropriate tools.

Does not require tools:
- General conversation or questions
- Explanations or opinions
- Creative writing or idea suggestions
- General knowledge already known{agent_context}

Answer: YES or NO only."""

            messages = [
                SystemMessage(
                    content="You are an expert at analyzing user requests to determine if tools are needed."
                ),
                HumanMessage(content=decision_prompt),
            ]

            llm_start = time.time()
            response = llm.invoke(messages)
            llm_elapsed = time.time() - llm_start
            decision = response.content.strip().upper()

            result = "YES" in decision
            mode_info = " (Agent 모드)" if force_agent else " (Ask 모드)"
            total_elapsed = time.time() - start_time
            logger.info(
                f"🤔 도구 사용 판단{mode_info}: {decision} -> {result} (LLM: {llm_elapsed:.2f}초, 총: {total_elapsed:.2f}초)"
            )
            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ 도구 사용 판단 오류: {elapsed:.2f}초, 오류: {e}")
            return False


class KeywordBasedToolDecisionStrategy(ToolDecisionStrategy):
    """키워드 기반 도구 사용 결정 전략"""
    
    TOOL_KEYWORDS = [
        '검색', 'search', '찾아', '조회', '알려줘', '정보',
        '날씨', 'weather', '지도', 'map', '위치', 'location',
        '여행', 'travel', '호텔', 'hotel', '항공', 'flight'
    ]
    
    def should_use_tools(self, user_input: str, tools: List[Any], llm: Any, force_agent: bool = False) -> bool:
        """키워드 기반으로 도구 사용 여부 결정"""
        if force_agent:
            return True
            
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in self.TOOL_KEYWORDS)


class ToolDecisionContext:
    """도구 결정 전략 컨텍스트"""
    
    def __init__(self, strategy: ToolDecisionStrategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: ToolDecisionStrategy):
        self._strategy = strategy
    
    def should_use_tools(self, user_input: str, tools: List[Any], llm: Any, force_agent: bool = False) -> bool:
        return self._strategy.should_use_tools(user_input, tools, llm, force_agent)