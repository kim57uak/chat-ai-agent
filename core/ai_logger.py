"""AI 프롬프트 및 응답 로깅 시스템"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class AILogger:
    """AI와의 모든 상호작용을 로깅하는 클래스"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 로그 파일 설정
        self.setup_logger()
    
    def setup_logger(self):
        """로거 설정"""
        self.logger = logging.getLogger('ai_interaction')
        self.logger.setLevel(logging.INFO)
        
        # 기존 핸들러 제거
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 파일 핸들러 추가
        log_file = self.log_dir / f"ai_interactions_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # JSON 형태로 로깅
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_request(self, 
                   model: str,
                   system_prompt: str,
                   user_input: str,
                   conversation_history: List[Dict] = None,
                   tools_available: List[str] = None,
                   agent_mode: bool = False) -> str:
        """AI 요청 로깅"""
        
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        log_data = {
            "type": "REQUEST",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "agent_mode": agent_mode,
            "system_prompt": system_prompt,
            "user_input": user_input,
            "conversation_history_length": len(conversation_history) if conversation_history else 0,
            "tools_available": tools_available or [],
            "conversation_history": conversation_history[-5:] if conversation_history else []  # 최근 5개만
        }
        
        log_message = json.dumps(log_data, ensure_ascii=False, indent=2)
        self.logger.info(log_message)
        print(f"\n=== AI REQUEST LOG ===\n{log_message}\n")
        return request_id
    
    def log_response(self,
                    request_id: str,
                    model: str,
                    response: str,
                    used_tools: List[str] = None,
                    token_usage: Dict[str, int] = None,
                    response_time: float = None,
                    error: str = None):
        """AI 응답 로깅"""
        
        log_data = {
            "type": "RESPONSE",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "response": response,
            "used_tools": used_tools or [],
            "token_usage": token_usage or {},
            "response_time_seconds": response_time,
            "error": error
        }
        
        log_message = json.dumps(log_data, ensure_ascii=False, indent=2)
        self.logger.info(log_message)
        print(f"\n=== AI RESPONSE LOG ===\n{log_message}\n")
    
    def log_tool_call(self,
                     request_id: str,
                     tool_name: str,
                     tool_input: Dict[str, Any],
                     tool_output: str,
                     execution_time: float = None):
        """도구 호출 로깅"""
        
        log_data = {
            "type": "TOOL_CALL",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output[:1000] + "..." if len(str(tool_output)) > 1000 else tool_output,
            "execution_time_seconds": execution_time
        }
        
        self.logger.info(json.dumps(log_data, ensure_ascii=False, indent=2))
    
    def get_recent_logs(self, hours: int = 24) -> List[Dict]:
        """최근 로그 조회"""
        try:
            log_file = self.log_dir / f"ai_interactions_{datetime.now().strftime('%Y%m%d')}.log"
            if not log_file.exists():
                return []
            
            logs = []
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # 타임스탬프와 JSON 분리
                        parts = line.strip().split(' - ', 1)
                        if len(parts) == 2:
                            log_data = json.loads(parts[1])
                            logs.append(log_data)
                    except json.JSONDecodeError:
                        continue
            
            return logs[-100:]  # 최근 100개
        except Exception as e:
            print(f"로그 조회 오류: {e}")
            return []


# 전역 로거 인스턴스
ai_logger = AILogger()