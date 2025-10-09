"""
Unified logger combining AI, Security, and Token logging functionality
Based on loguru for simplicity and power
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger


class UnifiedLogger:
    """Unified logger for all application logging needs"""
    
    def __init__(self):
        self.logger = logger
    
    # AI Interaction Logging
    def log_ai_request(self, 
                       model: str,
                       user_input: str,
                       system_prompt: str = None,
                       conversation_history: List[Dict] = None,
                       tools_available: List[str] = None,
                       agent_mode: bool = False) -> str:
        """Log AI request"""
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        log_data = {
            "type": "REQUEST",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "agent_mode": agent_mode,
            "user_input": user_input[:500] if user_input else "",
            "system_prompt": system_prompt[:200] if system_prompt else "",
            "conversation_history_length": len(conversation_history) if conversation_history else 0,
            "tools_available": tools_available or []
        }
        
        self.logger.bind(category="ai").info(json.dumps(log_data, ensure_ascii=False))
        return request_id
    
    def log_ai_response(self,
                        request_id: str,
                        model: str,
                        response: str,
                        used_tools: List[str] = None,
                        token_usage: Dict[str, int] = None,
                        response_time: float = None,
                        error: str = None):
        """Log AI response"""
        log_data = {
            "type": "RESPONSE",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "response_length": len(response) if response else 0,
            "used_tools": used_tools or [],
            "token_usage": token_usage or {},
            "response_time_seconds": response_time,
            "error": error
        }
        
        self.logger.bind(category="ai").info(json.dumps(log_data, ensure_ascii=False))
    
    def log_tool_call(self,
                      request_id: str,
                      tool_name: str,
                      tool_input: Dict[str, Any],
                      tool_output: str,
                      execution_time: float = None):
        """Log tool call"""
        log_data = {
            "type": "TOOL_CALL",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "tool_input": str(tool_input)[:200],
            "tool_output_length": len(str(tool_output)),
            "execution_time_seconds": execution_time
        }
        
        self.logger.bind(category="ai").info(json.dumps(log_data, ensure_ascii=False))
    
    # Token Logging
    def log_token_usage(self,
                        model_name: str,
                        input_tokens: int,
                        output_tokens: int,
                        operation: str = "chat"):
        """Log token usage"""
        total_tokens = input_tokens + output_tokens
        self.logger.bind(category="token").info(
            f"Token Usage [{model_name}] {operation}: "
            f"Input: {input_tokens:,}, Output: {output_tokens:,}, Total: {total_tokens:,}"
        )
    
    # Security Logging
    def log_login_attempt(self, success: bool, details: Dict[str, Any] = None):
        """Log login attempt"""
        status = "SUCCESS" if success else "FAILED"
        safe_details = self._sanitize_dict(details) if details else {}
        
        level = "info" if success else "warning"
        getattr(self.logger.bind(category="security"), level)(
            f"Login attempt: {status} - {json.dumps(safe_details, ensure_ascii=False)}"
        )
    
    def log_logout(self, reason: str = "user_initiated"):
        """Log logout"""
        self.logger.bind(category="security").info(f"Logout: {reason}")
    
    def log_encryption_event(self, event_type: str, success: bool, details: str = ""):
        """Log encryption event"""
        status = "SUCCESS" if success else "FAILED"
        level = "info" if success else "error"
        getattr(self.logger.bind(category="security"), level)(
            f"Encryption {event_type}: {status} - {details}"
        )
    
    def log_security_violation(self, violation_type: str, details: str = ""):
        """Log security violation"""
        self.logger.bind(category="security").critical(f"Security violation: {violation_type} - {details}")
    
    # General Application Logging
    def debug(self, message: str, **kwargs):
        """Debug level logging"""
        self.logger.debug(message)
    
    def info(self, message: str, **kwargs):
        """Info level logging"""
        self.logger.info(message)
    
    def warning(self, message: str, **kwargs):
        """Warning level logging"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Error level logging"""
        if exc_info:
            self.logger.exception(message)
        else:
            self.logger.error(message)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Critical level logging"""
        if exc_info:
            self.logger.opt(exception=True).critical(message)
        else:
            self.logger.critical(message)
    
    # Helper methods
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from dict"""
        sensitive_keys = {'password', 'key', 'token', 'secret', 'api_key'}
        return {k: '[REDACTED]' if k.lower() in sensitive_keys else v 
                for k, v in data.items()}


# Global unified logger instance
unified_logger = UnifiedLogger()
