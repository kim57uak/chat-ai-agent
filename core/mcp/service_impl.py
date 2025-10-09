"""MCP service implementation following DIP."""

from typing import Dict, Any, List
from .interfaces import MCPService
from mcp.client.mcp_client import mcp_manager
from core.logging import get_logger

logger = get_logger("service_impl")


class MCPServiceImpl(MCPService):
    """MCP service implementation."""
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a specific tool."""
        return mcp_manager.call_tool(server_name, tool_name, arguments)
    
    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available tools."""
        return mcp_manager.get_all_tools()
    
    def start_servers(self, config_path: str = "mcp.json") -> bool:
        """Start MCP servers."""
        from mcp.client.mcp_state import mcp_state
        
        success = mcp_manager.load_from_config(config_path)
        
        if success:
            server_names = list(mcp_manager.clients.keys())
            for server_name in server_names:
                if not mcp_state.is_server_enabled(server_name):
                    logger.info(f"상태 파일에 따라 {server_name} 서버 중지")
                    mcp_manager.stop_server(server_name)
                else:
                    logger.info(f"상태 파일에 따라 {server_name} 서버 활성화")
        
        return success
    
    def stop_servers(self) -> None:
        """Stop all MCP servers."""
        mcp_manager.close_all()