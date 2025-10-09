"""MCP server management service."""
from core.logging import get_logger

logger = get_logger("mcp_service")

import os
import json
import threading
from PyQt6.QtCore import QTimer
from mcp.servers.mcp import start_mcp_servers, stop_mcp_servers


class MCPService:
    """Service for managing MCP servers."""
    
    def __init__(self, tools_update_callback=None):
        self._tools_update_callback = tools_update_callback
    
    def initialize_servers(self) -> None:
        """Initialize MCP servers based on state file."""
        def start_servers():
            try:
                state_file = 'mcp_server_state.json'
                if os.path.exists(state_file):
                    with open(state_file, 'r', encoding='utf-8') as f:
                        server_states = json.load(f)
                    
                    enabled_servers = [name for name, enabled in server_states.items() if enabled]
                    if enabled_servers:
                        logger.debug(f"활성화된 MCP 서버 시작: {enabled_servers}")
                        start_mcp_servers()
                        if self._tools_update_callback:
                            QTimer.singleShot(1000, self._tools_update_callback)
                    else:
                        logger.debug("활성화된 MCP 서버가 없습니다")
                else:
                    logger.debug("MCP 서버 상태 파일이 없습니다")
            except Exception as e:
                logger.debug(f"MCP 서버 시작 오류: {e}")
        
        threading.Thread(target=start_servers, daemon=True).start()
    
    def shutdown_servers(self) -> None:
        """Shutdown all MCP servers."""
        try:
            stop_mcp_servers()
        except Exception as e:
            logger.debug(f"MCP 서버 종료 오류: {e}")