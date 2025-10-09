"""AI 프롬프트 및 응답 로깅 시스템 (Backward Compatibility Wrapper)"""
from typing import Dict, Any, List, Optional

from core.logging import unified_logger


class AILogger:
    """AI와의 모든 상호작용을 로깅하는 클래스 (하위 호환성 유지)"""
    
    def __init__(self, log_dir: str = None):
        self._unified = unified_logger
    

    
    def log_request(self, 
                   model: str,
                   system_prompt: str,
                   user_input: str,
                   conversation_history: List[Dict] = None,
                   tools_available: List[str] = None,
                   agent_mode: bool = False) -> str:
        """AI 요청 로깅"""
        return self._unified.log_ai_request(
            model=model,
            user_input=user_input,
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            tools_available=tools_available,
            agent_mode=agent_mode
        )
    
    def log_response(self,
                    request_id: str,
                    model: str,
                    response: str,
                    used_tools: List[str] = None,
                    token_usage: Dict[str, int] = None,
                    response_time: float = None,
                    error: str = None):
        """AI 응답 로깅"""
        self._unified.log_ai_response(
            request_id=request_id,
            model=model,
            response=response,
            used_tools=used_tools,
            token_usage=token_usage,
            response_time=response_time,
            error=error
        )
    
    def log_tool_call(self,
                     request_id: str,
                     tool_name: str,
                     tool_input: Dict[str, Any],
                     tool_output: str,
                     execution_time: float = None):
        """도구 호출 로깅"""
        self._unified.log_tool_call(
            request_id=request_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            execution_time=execution_time
        )
    
    def get_recent_logs(self, hours: int = 24) -> List[Dict]:
        """최근 로그 조회 (deprecated)"""
        self._unified.warning("get_recent_logs is deprecated")
        return []


# 전역 로거 인스턴스
ai_logger = AILogger()