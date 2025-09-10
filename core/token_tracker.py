"""
Token usage tracking system for precise measurement across all AI interactions
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
from core.token_logger import TokenLogger

logger = logging.getLogger(__name__)


class StepType(Enum):
    """토큰 사용 단계 타입"""
    INITIAL_PROMPT = "initial_prompt"
    TOOL_DECISION = "tool_decision"
    TOOL_EXECUTION = "tool_execution"
    TOOL_RESULT_PROCESSING = "tool_result_processing"
    FINAL_RESPONSE = "final_response"
    CONVERSATION_HISTORY = "conversation_history"


@dataclass
class TokenUsageStep:
    """단계별 토큰 사용량 정보"""
    step_type: StepType
    step_name: str
    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0
    input_text_length: int = 0
    output_text_length: int = 0
    tool_name: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
    
    @property
    def total_estimated_tokens(self) -> int:
        return self.estimated_input_tokens + self.estimated_output_tokens


@dataclass
class ConversationTokenUsage:
    """대화 전체의 토큰 사용량 정보"""
    conversation_id: str
    user_input: str
    final_response: str
    model_name: str
    steps: List[TokenUsageStep] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_duration_ms: float = 0
    
    @property
    def total_input_tokens(self) -> int:
        return sum(step.input_tokens for step in self.steps)
    
    @property
    def total_output_tokens(self) -> int:
        return sum(step.output_tokens for step in self.steps)
    
    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens
    
    @property
    def total_estimated_input_tokens(self) -> int:
        return sum(step.estimated_input_tokens for step in self.steps)
    
    @property
    def total_estimated_output_tokens(self) -> int:
        return sum(step.estimated_output_tokens for step in self.steps)
    
    @property
    def total_estimated_tokens(self) -> int:
        return self.total_estimated_input_tokens + self.total_estimated_output_tokens


class TokenTracker:
    """정확한 토큰 사용량 추적 시스템"""
    
    def __init__(self):
        self.current_conversation: Optional[ConversationTokenUsage] = None
        self.conversation_history: List[ConversationTokenUsage] = []
        self.step_start_time: Optional[float] = None
    
    def start_conversation(self, user_input: str, model_name: str) -> str:
        """새로운 대화 추적 시작"""
        # 이전 대화가 있고 아직 히스토리에 추가되지 않았다면 추가
        if self.current_conversation and self.current_conversation not in self.conversation_history:
            self.conversation_history.append(self.current_conversation)
            logger.info(f"📝 Previous conversation {self.current_conversation.conversation_id} moved to history")
        
        conversation_id = f"conv_{int(time.time() * 1000)}"
        self.current_conversation = ConversationTokenUsage(
            conversation_id=conversation_id,
            user_input=user_input,
            final_response="",
            model_name=model_name
        )
        logger.info(f"🎯 Started tracking conversation: {conversation_id}")
        return conversation_id
    
    def start_step(self, step_type: StepType, step_name: str, tool_name: Optional[str] = None):
        """단계 시작"""
        self.step_start_time = time.time()
        logger.debug(f"📊 Starting step: {step_name} ({step_type.value})")
    
    def end_step(self, 
                 step_type: StepType, 
                 step_name: str,
                 input_text: str = "",
                 output_text: str = "",
                 response_obj: Any = None,
                 tool_name: Optional[str] = None,
                 additional_info: Dict[str, Any] = None) -> TokenUsageStep:
        """단계 종료 및 토큰 사용량 기록"""
        if not self.current_conversation:
            logger.warning("No active conversation to track")
            return None
        
        # 실제 토큰 사용량 추출
        actual_input_tokens, actual_output_tokens = TokenLogger.extract_actual_tokens(response_obj)
        
        # 추정 토큰 사용량 계산
        estimated_input_tokens = TokenLogger.estimate_tokens(input_text, self.current_conversation.model_name)
        estimated_output_tokens = TokenLogger.estimate_tokens(output_text, self.current_conversation.model_name)
        
        # 단계 정보 생성
        duration_ms = (time.time() - self.step_start_time) * 1000 if self.step_start_time else 0
        
        # additional_info에 실제 토큰 정보 추가 (UI에서 사용)
        enhanced_additional_info = additional_info or {}
        enhanced_additional_info.update({
            'input_tokens': actual_input_tokens,
            'output_tokens': actual_output_tokens,
            'estimated_input_tokens': estimated_input_tokens,
            'estimated_output_tokens': estimated_output_tokens
        })
        
        step = TokenUsageStep(
            step_type=step_type,
            step_name=step_name,
            model_name=self.current_conversation.model_name,
            input_tokens=actual_input_tokens,
            output_tokens=actual_output_tokens,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            duration_ms=duration_ms,
            input_text_length=len(input_text),
            output_text_length=len(output_text),
            tool_name=tool_name,
            additional_info=enhanced_additional_info
        )
        
        self.current_conversation.steps.append(step)
        
        # 로깅
        self._log_step_usage(step)
        
        return step
    
    def end_conversation(self, final_response: str = ""):
        """대화 종료 및 전체 토큰 사용량 요약"""
        if not self.current_conversation:
            return
        
        self.current_conversation.final_response = final_response
        self.current_conversation.end_time = time.time()
        self.current_conversation.total_duration_ms = (
            self.current_conversation.end_time - self.current_conversation.start_time
        ) * 1000
        
        # 전체 요약 로깅
        self._log_conversation_summary(self.current_conversation)
        
        # 히스토리에 추가 (중복 방지)
        if self.current_conversation not in self.conversation_history:
            self.conversation_history.append(self.current_conversation)
            logger.info(f"📚 Conversation {self.current_conversation.conversation_id} added to history")
        
        # 현재 대화를 None으로 설정하지 않고 유지 (UI에서 계속 참조할 수 있도록)
        # self.current_conversation = None  # 주석 처리
    
    def _log_step_usage(self, step: TokenUsageStep):
        """단계별 토큰 사용량 로깅"""
        actual_str = f"Input: {step.input_tokens:,}, Output: {step.output_tokens:,}, Total: {step.total_tokens:,}"
        estimated_str = f"Input: {step.estimated_input_tokens:,}, Output: {step.estimated_output_tokens:,}, Total: {step.total_estimated_tokens:,}"
        
        tool_info = f" [Tool: {step.tool_name}]" if step.tool_name else ""
        
        logger.info(
            f"📊 Step [{step.step_type.value}] {step.step_name}{tool_info} "
            f"({step.duration_ms:.1f}ms)\n"
            f"   🔢 Actual Tokens: {actual_str}\n"
            f"   📏 Estimated Tokens: {estimated_str}\n"
            f"   📝 Text Length: Input {step.input_text_length:,}, Output {step.output_text_length:,}"
        )
    
    def _log_conversation_summary(self, conversation: ConversationTokenUsage):
        """대화 전체 토큰 사용량 요약 로깅"""
        logger.info(
            f"\n🎯 Conversation Summary [{conversation.conversation_id}] "
            f"({conversation.total_duration_ms:.1f}ms)\n"
            f"   Model: {conversation.model_name}\n"
            f"   Steps: {len(conversation.steps)}\n"
            f"   🔢 Total Actual Tokens: Input {conversation.total_input_tokens:,}, "
            f"Output {conversation.total_output_tokens:,}, Total {conversation.total_tokens:,}\n"
            f"   📏 Total Estimated Tokens: Input {conversation.total_estimated_input_tokens:,}, "
            f"Output {conversation.total_estimated_output_tokens:,}, Total {conversation.total_estimated_tokens:,}\n"
            f"   💰 Accuracy: Input {self._calculate_accuracy(conversation.total_input_tokens, conversation.total_estimated_input_tokens):.1f}%, "
            f"Output {self._calculate_accuracy(conversation.total_output_tokens, conversation.total_estimated_output_tokens):.1f}%"
        )
        
        # 단계별 상세 정보
        for i, step in enumerate(conversation.steps, 1):
            tool_info = f" [{step.tool_name}]" if step.tool_name else ""
            logger.info(
                f"   Step {i}: {step.step_name}{tool_info} - "
                f"Actual: {step.total_tokens:,} tokens, "
                f"Estimated: {step.total_estimated_tokens:,} tokens "
                f"({step.duration_ms:.1f}ms)"
            )
    
    def _calculate_accuracy(self, actual: int, estimated: int) -> float:
        """토큰 추정 정확도 계산"""
        if actual == 0:
            return 100.0 if estimated == 0 else 0.0
        return min(100.0, (1 - abs(actual - estimated) / actual) * 100)
    
    def get_session_total_tokens(self) -> Tuple[int, int, int]:
        """세션 전체 토큰 사용량 반환 (input, output, total)"""
        total_input = 0
        total_output = 0
        
        # 히스토리 대화 토큰 포함 (실제 토큰 우선, 없으면 추정)
        for conv in self.conversation_history:
            if conv.total_tokens > 0:  # 실제 토큰이 있으면
                total_input += conv.total_input_tokens
                total_output += conv.total_output_tokens
            else:  # 실제 토큰이 없으면 추정 토큰 사용
                total_input += conv.total_estimated_input_tokens
                total_output += conv.total_estimated_output_tokens
        
        # 현재 대화 토큰 포함 (실제 토큰 우선, 없으면 추정)
        if self.current_conversation:
            if self.current_conversation.total_tokens > 0:  # 실제 토큰이 있으면
                total_input += self.current_conversation.total_input_tokens
                total_output += self.current_conversation.total_output_tokens
            else:  # 실제 토큰이 없으면 추정 토큰 사용
                total_input += self.current_conversation.total_estimated_input_tokens
                total_output += self.current_conversation.total_estimated_output_tokens
        
        return total_input, total_output, total_input + total_output
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """대화 통계 정보 반환"""
        # 현재 진행 중인 대화가 있으면 우선 반환
        if self.current_conversation:
            return {
                "conversation_id": self.current_conversation.conversation_id,
                "model_name": self.current_conversation.model_name,
                "steps_count": len(self.current_conversation.steps),
                "total_actual_tokens": self.current_conversation.total_tokens,
                "total_estimated_tokens": self.current_conversation.total_estimated_tokens,
                "duration_ms": self.current_conversation.total_duration_ms,
                "steps": [
                    {
                        "step_name": step.step_name,
                        "step_type": step.step_type.value,
                        "actual_tokens": step.total_tokens,
                        "estimated_tokens": step.total_estimated_tokens,
                        "duration_ms": step.duration_ms,
                        "tool_name": step.tool_name,
                        "additional_info": step.additional_info
                    }
                    for step in self.current_conversation.steps
                ]
            }
        
        # 현재 대화가 없으면 최근 대화 확인
        if self.conversation_history:
            last_conv = self.conversation_history[-1]
            return {
                "conversation_id": last_conv.conversation_id,
                "model_name": last_conv.model_name,
                "steps_count": len(last_conv.steps),
                "total_actual_tokens": last_conv.total_tokens,
                "total_estimated_tokens": last_conv.total_estimated_tokens,
                "duration_ms": last_conv.total_duration_ms,
                "steps": [
                    {
                        "step_name": step.step_name,
                        "step_type": step.step_type.value,
                        "actual_tokens": step.total_tokens,
                        "estimated_tokens": step.total_estimated_tokens,
                        "duration_ms": step.duration_ms,
                        "tool_name": step.tool_name,
                        "additional_info": step.additional_info
                    }
                    for step in last_conv.steps
                ]
            }
        
        return {}
    
    def export_conversation_data(self, filepath: str):
        """대화 데이터를 JSON 파일로 내보내기"""
        data = {
            "export_time": datetime.now().isoformat(),
            "conversations": []
        }
        
        for conv in self.conversation_history:
            conv_data = {
                "conversation_id": conv.conversation_id,
                "model_name": conv.model_name,
                "user_input": conv.user_input[:200] + "..." if len(conv.user_input) > 200 else conv.user_input,
                "start_time": datetime.fromtimestamp(conv.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(conv.end_time).isoformat() if conv.end_time else None,
                "total_duration_ms": conv.total_duration_ms,
                "total_actual_tokens": conv.total_tokens,
                "total_estimated_tokens": conv.total_estimated_tokens,
                "steps": [
                    {
                        "step_name": step.step_name,
                        "step_type": step.step_type.value,
                        "actual_input_tokens": step.input_tokens,
                        "actual_output_tokens": step.output_tokens,
                        "estimated_input_tokens": step.estimated_input_tokens,
                        "estimated_output_tokens": step.estimated_output_tokens,
                        "duration_ms": step.duration_ms,
                        "tool_name": step.tool_name,
                        "timestamp": datetime.fromtimestamp(step.timestamp).isoformat()
                    }
                    for step in conv.steps
                ]
            }
            data["conversations"].append(conv_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 Exported {len(self.conversation_history)} conversations to {filepath}")


# 전역 토큰 트래커 인스턴스
token_tracker = TokenTracker()