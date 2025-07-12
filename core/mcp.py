from .mcp_client import mcp_manager
from .mcp_state import mcp_state
import logging

logger = logging.getLogger(__name__)

def start_mcp_servers(config_path: str = 'mcp.json') -> bool:
    """MCP 서버들을 시작하고 초기화 (상태 파일 기반)"""
    # 전체 서버 로드
    success = mcp_manager.load_from_config(config_path)
    
    if success:
        # 상태 파일에서 비활성화된 서버들 중지
        server_names = list(mcp_manager.clients.keys())
        for server_name in server_names:
            if not mcp_state.is_server_enabled(server_name):
                logger.info(f"상태 파일에 따라 {server_name} 서버 중지")
                mcp_manager.stop_server(server_name)
            else:
                logger.info(f"상태 파일에 따라 {server_name} 서버 활성화")
    
    return success

def get_all_mcp_tools():
    """모든 MCP 서버의 도구 목록 반환"""
    return mcp_manager.get_all_tools()

def call_mcp_tool(server_name: str, tool_name: str, arguments: dict = None):
    """MCP 도구 호출"""
    return mcp_manager.call_tool(server_name, tool_name, arguments)

def stop_mcp_servers():
    """모든 MCP 서버 종료"""
    mcp_manager.close_all()

def get_mcp_servers():
    """모든 MCP 서버 상태 정보 반환"""
    return mcp_manager.get_server_status()

def start_mcp_server(server_name: str) -> bool:
    """특정 MCP 서버 시작"""
    success = mcp_manager.start_server(server_name)
    if success:
        mcp_state.set_server_enabled(server_name, True)
    return success

def stop_mcp_server(server_name: str) -> bool:
    """특정 MCP 서버 중지"""
    success = mcp_manager.stop_server(server_name)
    if success:
        mcp_state.set_server_enabled(server_name, False)
    return success

def restart_mcp_server(server_name: str) -> bool:
    """특정 MCP 서버 재시작"""
    return mcp_manager.restart_server(server_name)