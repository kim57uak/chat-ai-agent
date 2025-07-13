from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class MCPToolCaller(ABC):
    """MCP 도구 호출을 위한 추상 인터페이스"""
    
    @abstractmethod
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """MCP 도구 호출"""
        pass
    
    @abstractmethod
    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """모든 MCP 도구 목록 반환"""
        pass


class MCPServerManager(ABC):
    """MCP 서버 관리를 위한 추상 인터페이스"""
    
    @abstractmethod
    def start_servers(self, config_path: str = "mcp.json") -> bool:
        """MCP 서버들 시작"""
        pass
    
    @abstractmethod
    def stop_servers(self) -> None:
        """모든 MCP 서버 종료"""
        pass