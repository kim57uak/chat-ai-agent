from abc import ABC, abstractmethod
from typing import List, Any, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent, create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
import logging

logger = logging.getLogger(__name__)


class AgentExecutorFactory(ABC):
    """에이전트 실행기 생성을 위한 추상 팩토리"""
    
    @abstractmethod
    def create_agent_executor(self, llm: Any, tools: List[Any]) -> Optional[AgentExecutor]:
        pass


class OpenAIAgentExecutorFactory(AgentExecutorFactory):
    """OpenAI 에이전트 실행기 팩토리"""
    
    def create_agent_executor(self, llm: Any, tools: List[Any]) -> Optional[AgentExecutor]:
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
            max_iterations=2,
            handle_parsing_errors=True,
        )


class GeminiAgentExecutorFactory(AgentExecutorFactory):
    """Gemini 에이전트 실행기 팩토리"""
    
    def create_agent_executor(self, llm: Any, tools: List[Any]) -> Optional[AgentExecutor]:
        """ReAct 에이전트 생성 (Gemini 등 다른 모델용)"""
        if not tools:
            return None

        react_prompt = PromptTemplate.from_template(
            """
You are a helpful AI assistant that can use various tools to provide accurate information.

**Instructions:**
- Analyze user requests carefully to select the most appropriate tools
- Use tools to gather current, accurate information when needed
- Organize information in a clear, logical structure
- Respond in natural, conversational Korean
- Be friendly and helpful while maintaining accuracy
- If multiple tools are needed, use them systematically
- Focus on providing exactly what the user asked for

Available tools:
{tools}

Tool names: {tool_names}

Follow this format exactly:

Question: {input}
Thought: I need to analyze this request and determine which tool(s) would be most helpful.
Action: tool_name
Action Input: input_for_tool
Observation: tool_execution_result
Thought: Based on the result, I will provide a comprehensive answer in Korean with clear formatting.
Final Answer: [Provide a well-organized response in Korean with clear headings, bullet points, and highlighted important information]

{agent_scratchpad}
            """
        )

        agent = create_react_agent(llm, tools, react_prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            max_iterations=2,
            handle_parsing_errors=True,
            early_stopping_method="force",
            return_intermediate_steps=False,
        )


class AgentExecutorFactoryProvider:
    """에이전트 실행기 팩토리 제공자"""
    
    _factories = {
        'openai': OpenAIAgentExecutorFactory(),
        'gemini': GeminiAgentExecutorFactory()
    }
    
    @classmethod
    def get_factory(cls, model_name: str) -> AgentExecutorFactory:
        """모델명에 따라 적절한 팩토리 반환"""
        if 'gemini' in model_name.lower():
            return cls._factories['gemini']
        return cls._factories['openai']
    
    @classmethod
    def create_agent_executor(cls, llm: Any, tools: List[Any]) -> Optional[AgentExecutor]:
        """에이전트 실행기 생성"""
        model_name = getattr(llm, 'model_name', str(llm))
        factory = cls.get_factory(model_name)
        return factory.create_agent_executor(llm, tools)