"""
MCP Agent
기존 MCP 도구를 LangChain Tool로 래핑
"""

from typing import List, Dict, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from core.logging import get_logger
from .base_agent import BaseAgent

logger = get_logger("mcp_agent")


class MCPAgent(BaseAgent):
    """MCP (Model Context Protocol) Agent"""
    
    def __init__(self, llm, mcp_client, tools: Optional[List[BaseTool]] = None):
        """
        Initialize MCP agent
        
        Args:
            llm: LangChain LLM
            mcp_client: MCP client instance
            tools: Pre-wrapped MCP tools
        """
        super().__init__(llm, tools)
        self.mcp_client = mcp_client
        
        # MCP 도구를 LangChain Tool로 변환
        if not self.tools and mcp_client:
            self.tools = self._wrap_mcp_tools()
    
    def _wrap_mcp_tools(self) -> List[BaseTool]:
        """
        Wrap MCP tools as LangChain tools
        
        Returns:
            List of LangChain BaseTool
        """
        from tools.langchain.mcp_tool_wrapper import MCPToolWrapper
        
        wrapped_tools = []
        
        try:
            # MCP 클라이언트에서 도구 목록 가져오기
            if hasattr(self.mcp_client, 'list_tools'):
                mcp_tools = self.mcp_client.list_tools()
                
                for tool in mcp_tools:
                    wrapped = MCPToolWrapper(
                        name=tool.name,
                        description=tool.description,
                        mcp_client=self.mcp_client,
                        tool_name=tool.name
                    )
                    wrapped_tools.append(wrapped)
                
                logger.info(f"Wrapped {len(wrapped_tools)} MCP tools")
        
        except Exception as e:
            logger.error(f"Failed to wrap MCP tools: {e}")
        
        return wrapped_tools
    
    def _create_executor(self) -> AgentExecutor:
        """Create agent with MCP tools (model-specific)"""
        if not self.tools:
            logger.warning("No MCP tools available")
            return None
        
        try:
            # Gemini 모델 체크
            model_name = str(getattr(self.llm, 'model_name', '') or getattr(self.llm, 'model', '')).lower()
            is_gemini = 'gemini' in model_name
            logger.info(f"Model detection: {model_name}, is_gemini: {is_gemini}")
            
            if is_gemini:
                # Gemini: ReAct Agent 사용
                from langchain.agents import create_react_agent
                from langchain.prompts import PromptTemplate
                
                template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
                
                prompt = PromptTemplate.from_template(template)
                agent = create_react_agent(self.llm, self.tools, prompt)
            else:
                # OpenAI: Functions Agent 사용
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a helpful assistant with access to various tools."),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ])
                agent = create_openai_functions_agent(self.llm, self.tools, prompt)
            
            # AgentExecutor 생성
            executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=5,
                max_execution_time=30,
                return_intermediate_steps=True,
                handle_parsing_errors=True
            )
            
            logger.info(f"MCP agent executor created with {len(self.tools)} tools (Gemini: {is_gemini})")
            return executor
            
        except Exception as e:
            logger.error(f"Failed to create agent executor: {e}")
            return None
    
    def can_handle(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Check if query requires MCP tools using LLM context understanding
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if MCP tools needed
        """
        if not self.tools:
            return False
        
        from langchain.schema import HumanMessage
        
        # 도구 목록 생성 (최대 10개)
        tool_descriptions = "\n".join([
            f"- {t.name}: {t.description}" 
            for t in self.tools[:10]
        ])
        
        # Context 정보 추가
        context_info = ""
        if context:
            context_info = f"\n\nContext: {str(context)[:200]}"
        
        prompt = f"""Analyze if this query requires using any of the available tools.

Query: {query}{context_info}

Available Tools:
{tool_descriptions}

Consider:
1. Does the query mention files, databases, APIs, or external services?
2. Can the tools help answer this query?
3. Is this a simple conversation or does it need tool execution?

Answer ONLY 'YES' or 'NO':"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().upper()
            result = "YES" in decision
            logger.info(f"MCP Agent can_handle: {result} for query: {query[:50]}...")
            return result
        except Exception as e:
            logger.error(f"MCP Agent can_handle failed: {e}")
            return False
