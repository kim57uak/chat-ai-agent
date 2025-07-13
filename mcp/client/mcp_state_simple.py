"""간단한 MCP 상태 관리"""

class MCPState:
    def __init__(self):
        self.enabled_servers = set()
    
    def is_server_enabled(self, server_name):
        return server_name in self.enabled_servers or True  # 기본적으로 모든 서버 활성화
    
    def enable_server(self, server_name):
        self.enabled_servers.add(server_name)
    
    def disable_server(self, server_name):
        self.enabled_servers.discard(server_name)

# 전역 인스턴스
mcp_state = MCPState()