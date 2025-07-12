"""실제 MCP 서버 제어 함수들"""
import subprocess
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from .mcp_client import mcp_manager
    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False
    logger.warning("MCP 클라이언트를 사용할 수 없습니다. 기본 모드로 실행합니다.")

def start_mcp_server(server_name):
    """MCP 서버 시작"""
    try:
        if MCP_CLIENT_AVAILABLE:
            success = mcp_manager.start_server(server_name)
            logger.info(f"MCP 서버 '{server_name}' 시작: {'성공' if success else '실패'}")
            return success
        else:
            logger.warning("MCP 클라이언트를 사용할 수 없어 시뮬레이션 모드로 실행")
            return True
                
    except Exception as e:
        logger.error(f"MCP 서버 '{server_name}' 시작 중 오류: {e}")
        return False

def stop_mcp_server(server_name):
    """MCP 서버 중지"""
    try:
        if MCP_CLIENT_AVAILABLE:
            success = mcp_manager.stop_server(server_name)
            logger.info(f"MCP 서버 '{server_name}' 중지: {'성공' if success else '실패'}")
            return success
        else:
            logger.warning("MCP 클라이언트를 사용할 수 없어 시뮬레이션 모드로 실행")
            return True
                
    except Exception as e:
        logger.error(f"MCP 서버 '{server_name}' 중지 중 오류: {e}")
        return False

def restart_mcp_server(server_name):
    """MCP 서버 재시작"""
    try:
        if MCP_CLIENT_AVAILABLE:
            success = mcp_manager.restart_server(server_name)
            logger.info(f"MCP 서버 '{server_name}' 재시작: {'성공' if success else '실패'}")
            return success
        else:
            logger.warning("MCP 클라이언트를 사용할 수 없어 시뮬레이션 모드로 실행")
            return True
            
    except Exception as e:
        logger.error(f"MCP 서버 '{server_name}' 재시작 중 오류: {e}")
        return False

def get_mcp_servers():
    """MCP 서버 목록 및 상태 반환"""
    try:
        if MCP_CLIENT_AVAILABLE:
            # 실제 MCP 매니저에서 서버 상태 가져오기
            server_status = mcp_manager.get_server_status()
            
            # UI에서 사용하기 쉬운 형태로 변환
            result = {}
            for server_name, info in server_status.items():
                result[server_name] = {
                    'status': info.get('status', 'unknown'),
                    'tools': [tool.get('name', 'Unknown Tool') for tool in info.get('tools', [])],
                    'config': {
                        'command': info.get('command', ''),
                        'args': info.get('args', []),
                        'env': info.get('env', {})
                    }
                }
            
            return result
        else:
            # 시뮬레이션 모드
            logger.warning("MCP 클라이언트를 사용할 수 없어 시뮬레이션 데이터 반환")
            return {
                'excel-stdio': {
                    'status': 'running',
                    'tools': ['read_data_from_excel', 'write_data_to_excel', 'create_workbook'],
                    'config': {'command': 'uvx', 'args': ['mcp-server-excel'], 'env': {}}
                }
            }
            
    except Exception as e:
        logger.error(f"MCP 서버 목록 조회 중 오류: {e}")
        return {}