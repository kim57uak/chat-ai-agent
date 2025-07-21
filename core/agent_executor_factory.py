from abc import ABC, abstractmethod
from typing import List, Any, Optional
from langchain.agents import (
    AgentExecutor,
    create_openai_tools_agent,
    create_react_agent,
)
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from core.perplexity_agent_helper import create_perplexity_agent
import logging

logger = logging.getLogger(__name__)


class AgentExecutorFactory(ABC):
    """에이전트 실행기 생성을 위한 추상 팩토리"""

    @abstractmethod
    def create_agent_executor(
        self, llm: Any, tools: List[Any]
    ) -> Optional[AgentExecutor]:
        pass


class OpenAIAgentExecutorFactory(AgentExecutorFactory):
    """OpenAI 에이전트 실행기 팩토리"""

    def create_agent_executor(
        self, llm: Any, tools: List[Any]
    ) -> Optional[AgentExecutor]:
        """OpenAI 도구 에이전트 생성"""
        if not tools:
            return None

        system_message = """You are a helpful AI assistant that can use various tools to provide accurate information.

**Instructions:**
- Analyze user requests carefully to select the most appropriate tools
- Use tools to gather current, accurate information when needed
- Organize information in a clear, logical structure
- Respond in natural, conversational Korean
- Be friendly and helpful while maintaining accuracy
- If multiple tools are needed, use them systematically
- Focus on providing exactly what the user asked for

**Response Format:**
- Use clear headings and bullet points when appropriate
- Highlight important information
- Keep responses well-organized and easy to read"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_openai_tools_agent(llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True,
        )


class GeminiAgentExecutorFactory(AgentExecutorFactory):
    """Gemini 에이전트 실행기 팩토리"""

    def create_agent_executor(
        self, llm: Any, tools: List[Any]
    ) -> Optional[AgentExecutor]:
        """ReAct 에이전트 생성 (Gemini 등 다른 모델용)"""
        if not tools:
            return None

        react_prompt = PromptTemplate.from_template(
            """
You are an intelligent AI assistant with access to powerful tools. Your role is to analyze each user request and determine whether tools would provide more accurate, current, or comprehensive information than your training data alone.

**CRITICAL FORMAT INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:**
1. ALWAYS use the exact format shown below
2. ALWAYS include "Thought:", "Action:", "Action Input:", "Observation:", and "Final Answer:" in your responses
3. NEVER skip steps in the process
4. NEVER create your own format
5. ALWAYS provide valid JSON for Action Input - DO NOT NEST JSON OBJECTS
6. NEVER include explanations outside of the specified format
7. For Action Input, use FLAT JSON with simple key-value pairs only
8. NEVER use double curly braces for JSON - use single curly braces only

**When to Use Tools:**
- Information that changes frequently or requires current data
- Specific factual queries about places, organizations, people, events
- Requests that explicitly or implicitly ask for external information
- Complex queries where multiple sources would improve the answer
- When your training data might be incomplete or outdated

**When NOT to Use Tools:**
- General knowledge questions you can answer confidently
- Creative tasks, opinions, or subjective discussions
- Theoretical concepts or explanations
- Simple calculations or logical reasoning
Available tools:
{tools}

Tool names: {tool_names}

**RESPONSE FORMAT - FOLLOW THIS EXACTLY:**

Question: You must end with "Action" or "Final Answer.". {input}.
Thought: [Analyze the request - does this need tools? Why or why not? What specific information would tools provide?]
Action: [tool_name]
Action Input: {{"param1": "value1", "param2": "value2"}}
Observation: [tool result]
Thought: [Process the tool result and plan your response]
Action: [another_tool_name or proceed to Final Answer]
Action Input: {{"param1": "value1"}}
Observation: [another tool result]
Thought: [Final analysis of all tool results]
Final Answer: [Comprehensive response in Korean, incorporating tool results]


{agent_scratchpad}
            """
        )

        agent = create_react_agent(llm, tools, react_prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True,
            early_stopping_method="force",  # Gemini는 "generate" 옵션을 지원하지 않음
            return_intermediate_steps=True,
        )


class PerplexityAgentExecutorFactory(AgentExecutorFactory):
    """Perplexity 에이전트 실행기 팩토리"""

    def create_agent_executor(
        self, llm: Any, tools: List[Any]
    ) -> Optional[AgentExecutor]:
        """Perplexity 모델용 ReAct 에이전트 생성"""
        if not tools:
            return None

        # Perplexity 모델에 최적화된 프롬프트
        react_prompt = PromptTemplate.from_template(
            """
You are an intelligent AI assistant with access to powerful tools and real-time search capabilities. Your role is to analyze each user request and determine whether tools would provide more accurate, current, or comprehensive information.

**CRITICAL FORMAT INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:**
1. ALWAYS use the exact format shown below
2. ALWAYS include "Thought:", "Action:", "Action Input:", "Observation:", and "Final Answer:" in your responses
3. NEVER skip steps in the process
4. NEVER create your own format
5. ALWAYS provide valid JSON for Action Input - DO NOT NEST JSON OBJECTS
6. NEVER include explanations outside of the specified format
7. NEVER generate fake "Observation:" results - WAIT for the actual tool execution results
8. NEVER continue with "Thought:" after "Action:" until you see the "Observation:" from the system
9. For Action Input, use FLAT JSON with simple key-value pairs only
10. NEVER use double curly braces for JSON - use single curly braces only

**When to Use Tools:**
- Information that changes frequently or requires current data
- Specific factual queries about places, organizations, people, events
- Requests that explicitly or implicitly ask for external information
- Complex queries where multiple sources would improve the answer
- When your training data might be incomplete or outdated

Available tools:
{tools}

Tool names: {tool_names}

**RESPONSE FORMAT - FOLLOW THIS EXACTLY:**

Question: You must end with "Action" or "Final Answer.". {input}
Thought: [Analyze the request - does this need tools? Why or why not? What specific information would tools provide?]
Action: [tool_name]
Action Input: {{"param1": "value1", "param2": "value2"}}
Observation: [WAIT FOR ACTUAL TOOL RESULT - DO NOT GENERATE THIS]
Thought: [AFTER SEEING THE OBSERVATION, YOU MUST INCLUDE THIS LINE - Process the tool result and plan your response]
Action: [another_tool_name or proceed to Final Answer]
Action Input: {{"param1": "value1"}}
Observation: [WAIT FOR ACTUAL TOOL RESULT - DO NOT GENERATE THIS]
Thought: [AFTER SEEING THE OBSERVATION, YOU MUST INCLUDE THIS LINE - Final analysis of all tool results]
Final Answer: [Comprehensive response in Korean, incorporating tool results]


{agent_scratchpad}
            """
        )

        # 커스텀 Perplexity 에이전트 생성 함수 사용
        try:
            logger.info("커스텀 Perplexity 에이전트 생성 시작")
            agent = create_perplexity_agent(llm, tools, react_prompt)
            logger.info("커스텀 Perplexity 에이전트 생성 완료")
        except Exception as e:
            logger.warning(
                f"커스텀 Perplexity 에이전트 생성 실패: {e}, 기본 방식으로 시도"
            )
            # 실패 시 기본 방식으로 시도
            agent = create_react_agent(llm, tools, react_prompt)

        # Perplexity API 호환성을 위해 추가 파라미터 제한
        executor_kwargs = {
            "agent": agent,
            "tools": tools,
            "verbose": True,
            "max_iterations": 3,
            "handle_parsing_errors": True,
            "early_stopping_method": "force",  # Perplexity는 "generate" 옵션을 지원하지 않음
            "return_intermediate_steps": True,
            "max_execution_time": 120,  # 최대 실행 시간 증가 (2분)
        }

        # stop 파라미터 사용 안함
        if hasattr(llm, "model_name") and (
            "sonar" in llm.model_name.lower() or "r1-" in llm.model_name.lower()
        ):
            logger.info("Perplexity 모델용 AgentExecutor 생성 - stop 파라미터 제외")
            # stop 파라미터 제거
            executor_kwargs.pop("stop", None)

        return AgentExecutor(**executor_kwargs)


class AgentExecutorFactoryProvider:
    """에이전트 실행기 팩토리 제공자"""

    _factories = {
        "openai": OpenAIAgentExecutorFactory(),
        "gemini": GeminiAgentExecutorFactory(),
        "perplexity": PerplexityAgentExecutorFactory(),
    }

    @classmethod
    def get_factory(cls, model_name: str) -> AgentExecutorFactory:
        """모델명에 따라 적절한 팩토리 반환"""
        model_name_lower = model_name.lower()
        if "gemini" in model_name_lower:
            return cls._factories["gemini"]
        elif (
            "sonar" in model_name_lower
            or "r1-" in model_name_lower
            or "perplexity" in model_name_lower
        ):
            logger.info(f"Perplexity 모델 감지: {model_name}, Perplexity 팩토리 사용")
            return cls._factories["perplexity"]
        return cls._factories["openai"]

    @classmethod
    def create_agent_executor(
        cls, llm: Any, tools: List[Any]
    ) -> Optional[AgentExecutor]:
        """에이전트 실행기 생성"""
        model_name = getattr(llm, "model_name", str(llm))
        factory = cls.get_factory(model_name)
        return factory.create_agent_executor(llm, tools)