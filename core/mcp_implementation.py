"""MCP implementation - refactored to follow SOLID principles."""

from typing import Dict, Any, List
from core.mcp_interface import MCPToolCaller, MCPServerManager
from core.mcp import mcp_service

class MCPToolCallerImpl(MCPToolCaller):
    """Legacy wrapper for MCP tool calling."""
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        return mcp_service.call_tool(server_name, tool_name, arguments)
    
    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        return mcp_service.get_all_tools()


class MCPServerManagerImpl(MCPServerManager):
    """Legacy wrapper for MCP server management."""
    
    def start_servers(self, config_path: str = "mcp.json") -> bool:
        return mcp_service.start_servers(config_path)
    
    def stop_servers(self) -> None:
        return mcp_service.stop_servers()


# Legacy singleton instances for backward compatibility
mcp_tool_caller = MCPToolCallerImpl()
mcp_server_manager = MCPServerManagerImpl()