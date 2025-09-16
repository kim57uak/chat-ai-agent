from abc import ABC, abstractmethod
from typing import List, Any, Optional
from langchain.agents import (
    AgentExecutor,
    create_openai_tools_agent,
    create_react_agent,
)
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from core.perplexity_agent_helper import create_perplexity_agent
from ui.prompts import prompt_manager, ModelType
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

        system_message = prompt_manager.get_full_prompt(ModelType.OPENAI.value)

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
            max_iterations=15,
            max_execution_time=240,
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
        base_prompt = prompt_manager.get_system_prompt(ModelType.GOOGLE.value)
        react_pattern = prompt_manager.get_tool_prompt(ModelType.GOOGLE.value)
        
        react_prompt = PromptTemplate.from_template(
            f"""{base_prompt}

{react_pattern}

Available tools:
{{tools}}

Tool names: {{tool_names}}

Question: {{input}}
{{agent_scratchpad}}
            """
        )

        agent = create_react_agent(llm, tools, react_prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=15,
            max_execution_time=240,
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
        base_prompt = prompt_manager.get_system_prompt(ModelType.PERPLEXITY.value)
        research_approach = prompt_manager.get_tool_prompt(ModelType.PERPLEXITY.value)
        
        react_prompt = PromptTemplate.from_template(
            f"""{base_prompt}

{research_approach}

Available tools:
{{tools}}

Tool names: {{tool_names}}

Question: {{input}}
{{agent_scratchpad}}
            """
        )

        try:
            logger.info("Perplexity ReAct 에이전트 생성 시작")
            agent = create_react_agent(llm, tools, react_prompt)
            executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=15,
                max_execution_time=180,
                handle_parsing_errors=True,
                early_stopping_method="force",
                return_intermediate_steps=True,
            )
            logger.info("Perplexity ReAct 에이전트 생성 완료")
            return executor
        except Exception as e:
            logger.error(f"Perplexity ReAct 에이전트 생성 실패: {e}")
            return None


class ClaudeAgentExecutorFactory(AgentExecutorFactory):
    """Claude 에이전트 실행기 팩토리"""

    def create_agent_executor(
        self, llm: Any, tools: List[Any]
    ) -> Optional[AgentExecutor]:
        """Claude용 ReAct 에이전트 생성"""
        if not tools:
            return None

        base_prompt = prompt_manager.get_system_prompt(ModelType.CLAUDE.value)
        tool_prompt = prompt_manager.get_tool_prompt(ModelType.CLAUDE.value)
        
        react_prompt = PromptTemplate.from_template(
            f"""{base_prompt}

{tool_prompt}

Available tools:
{{tools}}

Tool names: {{tool_names}}

Question: {{input}}
{{agent_scratchpad}}
            """
        )

        agent = create_react_agent(llm, tools, react_prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=20,  # Claude는 더 많은 반복 허용
            max_execution_time=300,  # Claude는 더 긴 시간 허용
            handle_parsing_errors=True,
            early_stopping_method="force",
            return_intermediate_steps=True,
        )


class AgentExecutorFactoryProvider:
    """에이전트 실행기 팩토리 제공자"""

    _factories = {
        "openai": OpenAIAgentExecutorFactory(),
        "gemini": GeminiAgentExecutorFactory(),
        "perplexity": PerplexityAgentExecutorFactory(),
        "claude": ClaudeAgentExecutorFactory(),
    }

    @classmethod
    def get_factory(cls, model_name: str) -> AgentExecutorFactory:
        """모델명에 따라 적절한 팩토리 반환"""
        model_name_lower = model_name.lower()
        if "gemini" in model_name_lower:
            return cls._factories["gemini"]
        elif "claude" in model_name_lower:
            return cls._factories["claude"]
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