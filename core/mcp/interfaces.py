"""MCP interfaces following ISP."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ToolCaller(ABC):
    """Interface for tool calling operations."""
    
    @abstractmethod
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a specific tool."""
        pass


class ToolProvider(ABC):
    """Interface for tool provision."""
    
    @abstractmethod
    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available tools."""
        pass


class ServerManager(ABC):
    """Interface for server management."""
    
    @abstractmethod
    def start_servers(self, config_path: str = "mcp.json") -> bool:
        """Start MCP servers."""
        pass
    
    @abstractmethod
    def stop_servers(self) -> None:
        """Stop all MCP servers."""
        pass


class MCPService(ToolCaller, ToolProvider, ServerManager):
    """Complete MCP service interface."""
    pass