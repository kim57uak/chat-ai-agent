import json
import os
from typing import Dict

class MCPServerState:
    """MCP 서버 상태 관리"""
    
    def __init__(self, state_file: str = "mcp_server_state.json"):
        self.state_file = state_file
        self.server_states = {}
        self.load_state()
    
    def save_state(self):
        """서버 상태를 파일에 저장"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.server_states, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"MCP 서버 상태 저장 실패: {e}")
    
    def load_state(self):
        """파일에서 서버 상태 로드"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.server_states = json.load(f)
        except Exception as e:
            print(f"MCP 서버 상태 로드 실패: {e}")
            self.server_states = {}
    
    def set_server_enabled(self, server_name: str, enabled: bool):
        """서버 활성화 상태 설정"""
        self.server_states[server_name] = enabled
        self.save_state()
    
    def is_server_enabled(self, server_name: str) -> bool:
        """서버 활성화 상태 확인 (기본값: True)"""
        return self.server_states.get(server_name, True)
    
    def get_all_states(self) -> Dict[str, bool]:
        """모든 서버 상태 반환"""
        return self.server_states.copy()

# 전역 인스턴스
mcp_state = MCPServerState()