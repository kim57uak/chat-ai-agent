"""MCP 서비스 관리 모듈"""
from core.mcp_implementation import mcp_server_manager


def start_mcp_servers(config_path: str = "mcp.json") -> bool:
    """MCP 서버들을 시작"""
    return mcp_server_manager.start_servers(config_path)


def stop_mcp_servers() -> None:
    """모든 MCP 서버 종료"""
    mcp_server_manager.stop_servers()