"""
MCP Tool Wrapper
MCP 도구를 LangChain BaseTool로 래핑
"""

from typing import Optional, Type, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from core.logging import get_logger

logger = get_logger("mcp_tool_wrapper")


class MCPToolInput(BaseModel):
    """MCP Tool 입력 스키마"""
    query: str = Field(description="Query or parameters for the tool")


class MCPToolWrapper(BaseTool):
    """MCP 도구를 LangChain Tool로 래핑"""
    
    name: str
    description: str
    args_schema: Type[BaseModel] = MCPToolInput
    mcp_client: Any
    tool_name: str
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, query: str) -> str:
        """
        Execute MCP tool
        
        Args:
            query: Tool query/parameters
            
        Returns:
            Tool result as string
        """
        try:
            result = self.mcp_client.call_tool(self.tool_name, {"query": query})
            logger.debug(f"MCP tool {self.tool_name} executed")
            return str(result)
        except Exception as e:
            logger.error(f"MCP tool execution failed: {e}")
            return f"Error: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """
        Async execution (fallback to sync)
        
        Args:
            query: Tool query/parameters
            
        Returns:
            Tool result as string
        """
        return self._run(query)
