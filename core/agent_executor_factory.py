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
You are an intelligent AI assistant with access to powerful tools. Your role is to analyze each user request and determine whether tools would provide more accurate, current, or comprehensive information than your training data alone.

**Decision Framework:**
For each request, ask yourself:
1. **Freshness**: Would this benefit from current/real-time information?
2. **Specificity**: Does this require specific data that tools could provide?
3. **Verification**: Would external sources improve accuracy?
4. **Completeness**: Could tools provide more comprehensive information?

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

**Response Format:**

Question: {input}
Thought: [Analyze the request - does this need tools? Why or why not? What specific information would tools provide?]
Action: [tool_name if needed, or skip to Final Answer if tools not needed]
Action Input: [specific input for the tool]
Observation: [tool result]
Thought: [Process the tool result and plan your response]
Final Answer: [Comprehensive response in Korean, incorporating tool results if used]

**Key Principle:** Use your intelligence to make the best decision for each unique request. Tools are powerful resources - use them when they add value, but don't force their use when unnecessary.

{agent_scratchpad}
            """
        )

        agent = create_react_agent(llm, tools, react_prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=4,
            handle_parsing_errors=True,
            early_stopping_method="generate",
            return_intermediate_steps=True,
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