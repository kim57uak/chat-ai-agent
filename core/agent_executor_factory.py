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
            max_iterations=10,
            max_execution_time=60,
            handle_parsing_errors=True,
        )


class GeminiAgentExecutorFactory(AgentExecutorFactory):
    """Gemini 에이전트 실행기 팩토리"""

    def create_agent_executor(
        self, llm: Any, tools: List[Any]
    ) -> Optional[AgentExecutor]:
        """Gemini용 간단한 ReAct 에이전트 생성"""
        if not tools:
            return None

        # Gemini에 최적화된 간단한 프롬프트
        react_prompt = PromptTemplate.from_template(
            """
You are a helpful AI assistant with access to tools. Use tools when you need current information or to perform specific tasks.

Available tools:
{tools}

Tool names: {tool_names}

Use this format:

Question: {input}
Thought: I need to use a tool to help with this request.
Action: [tool_name]
Action Input: {{"parameter": "value"}}
Observation: [tool result will appear here]
Thought: Now I can provide a helpful response.
Final Answer: [Your response in Korean based on the tool result]

{agent_scratchpad}
            """
        )

        agent = create_react_agent(llm, tools, react_prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            max_execution_time=60,
            handle_parsing_errors=True,
            early_stopping_method="force",
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

        # Perplexity 모델에 최적화된 간단한 ReAct 프롬프트
        react_prompt = PromptTemplate.from_template(
            """
You are a helpful AI assistant with access to tools. Use tools when you need current information or to perform specific tasks.

Available tools:
{tools}

Tool names: {tool_names}

Use this format:

Question: {input}
Thought: I need to analyze this request and decide if I need tools.
Action: [tool_name]
Action Input: {{"parameter": "value"}}
Observation: [tool result will appear here]
Thought: Now I can provide a helpful response.
Final Answer: [Your response in Korean based on the tool result]

{agent_scratchpad}
            """
        )

        try:
            logger.info("Perplexity ReAct 에이전트 생성 시작")
            agent = create_react_agent(llm, tools, react_prompt)
            executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=10,
                max_execution_time=60,
                handle_parsing_errors=True,
                early_stopping_method="force",
                return_intermediate_steps=True,
            )
            logger.info("Perplexity ReAct 에이전트 생성 완료")
            return executor
        except Exception as e:
            logger.error(f"Perplexity ReAct 에이전트 생성 실패: {e}")
            return None


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