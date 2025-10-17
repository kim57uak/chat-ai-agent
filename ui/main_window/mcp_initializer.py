"""
MCP Initializer
MCP 서버 초기화 전담 클래스
"""

import json
import threading
from core.logging import get_logger
from core.safe_timer import safe_timer_manager

logger = get_logger("mcp_initializer")


class MCPInitializer:
    """MCP 서버 초기화 전담 클래스"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self._mcp_init_timer = None
    
    def initialize(self):
        """MCP 서버 초기화"""
        if self._mcp_init_timer is None:
            self._mcp_init_timer = safe_timer_manager.create_timer(
                200, self._init_mcp_servers, single_shot=True, parent=self.main_window
            )
        if self._mcp_init_timer:
            self._mcp_init_timer.start()
    
    def _init_mcp_servers(self):
        """MCP 서버 상태 파일을 읽어서 활성화된 서버만 시작"""
        def start_servers():
            try:
                from utils.config_path import config_path_manager
                from mcp.servers.mcp import start_mcp_servers
                
                config_path = config_path_manager.get_config_path('mcp_server_state.json')
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        server_states = json.load(f)
                    
                    enabled_servers = [name for name, enabled in server_states.items() if enabled]
                    if enabled_servers:
                        logger.debug(f"활성화된 MCP 서버 시작: {enabled_servers}")
                        start_mcp_servers()
                    else:
                        logger.debug("활성화된 MCP 서버가 없습니다")
                else:
                    logger.debug("MCP 서버 상태 파일이 없습니다")
            except Exception as e:
                logger.debug(f"MCP 서버 시작 오류: {e}")
        
        threading.Thread(target=start_servers, daemon=True).start()
