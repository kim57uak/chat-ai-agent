# MCP Tools Package
"""
MCP(Model Context Protocol) 및 도구 관련 모듈들을 관리하는 패키지

주요 모듈:
- mcp: MCP 서버 관리 및 도구 조회
- mcp_client: MCP 클라이언트 구현
- langchain_tools: LangChain 도구 래퍼
- tool_manager: 도구 관리자
- tool_decision_strategy: 도구 사용 결정 전략
"""

# 주요 클래스들을 패키지 레벨에서 import 가능하도록 설정
from .servers.mcp import get_all_mcp_tools, start_mcp_servers

# 순환 import를 피하기 위해 필요시에만 import
def get_tool_registry():
    from tools.langchain.langchain_tools import tool_registry
    return tool_registry

def get_mcp_tool():
    from tools.langchain.langchain_tools import MCPTool
    return MCPTool

__all__ = [
    'get_all_mcp_tools',
    'start_mcp_servers',
    'get_tool_registry',
    'get_mcp_tool'
]