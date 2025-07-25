"""MCP components following SOLID principles."""

from .interfaces import ToolCaller, ToolProvider, ServerManager, MCPService
from .service_impl import MCPServiceImpl

# Singleton instance for backward compatibility
mcp_service = MCPServiceImpl()

__all__ = ['ToolCaller', 'ToolProvider', 'ServerManager', 'MCPService', 'MCPServiceImpl', 'mcp_service']