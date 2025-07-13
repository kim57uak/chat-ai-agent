from typing import Dict, Any, List
from core.mcp_interface import MCPToolCaller, MCPServerManager
from mcp.client.mcp_client import mcp_manager
import logging

logger = logging.getLogger(__name__)


class MCPToolCallerImpl(MCPToolCaller):
    """MCP 도구 호출 구현체"""
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """MCP 도구 호출"""
        return mcp_manager.call_tool(server_name, tool_name, arguments)
    
    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """모든 MCP 도구 목록 반환"""
        return mcp_manager.get_all_tools()


class MCPServerManagerImpl(MCPServerManager):
    """MCP 서버 관리 구현체"""
    
    def start_servers(self, config_path: str = "mcp.json") -> bool:
        """MCP 서버들 시작"""
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
        """모든 MCP 서버 종료"""
        mcp_manager.close_all()


# 싱글톤 인스턴스
mcp_tool_caller = MCPToolCallerImpl()
mcp_server_manager = MCPServerManagerImpl()