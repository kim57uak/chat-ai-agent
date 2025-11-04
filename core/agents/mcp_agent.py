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
        """Create OpenAI functions agent with MCP tools"""
        if not self.tools:
            logger.warning("No MCP tools available")
            return None
        
        # 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant with access to various tools."),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Agent 생성
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        
        # AgentExecutor 생성
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            max_execution_time=30,
            return_intermediate_steps=True
        )
        
        logger.info(f"MCP agent executor created with {len(self.tools)} tools")
        return executor
    
    def can_handle(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Check if query requires MCP tools using LLM
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if MCP tools needed
        """
        from langchain.schema import HumanMessage
        
        if not self.tools:
            return False
        
        try:
            # 사용 가능한 도구 목록
            tool_list = "\n".join([f"- {t.name}: {t.description}" for t in self.tools[:10]])
            
            prompt = f"""Does this query require using any of these tools?

Query: {query}

Available tools:
{tool_list}

Answer only 'YES' or 'NO'."""
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().upper()
            
            return "YES" in decision
            
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return False
