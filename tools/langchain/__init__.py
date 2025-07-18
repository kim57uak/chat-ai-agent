"""LangChain 도구 래퍼 모듈"""

from core.mcp_interface import MCPToolCaller
from .langchain_tools import MCPTool, MCPToolRegistry

# 도구 레지스트리 인스턴스 생성을 위한 팩토리 함수
def create_tool_registry(mcp_caller):
    """도구 레지스트리 생성"""
    return MCPToolRegistry(mcp_caller)

# 임시 MCPToolCaller 구현 (실제 구현체는 나중에 주입됨)
class DummyMCPToolCaller(MCPToolCaller):
    def call_tool(self, server_name, tool_name, arguments=None):
        return None
    
    def get_all_tools(self):
        return {}

# 도구 레지스트리 인스턴스 생성
tool_registry = MCPToolRegistry(DummyMCPToolCaller())