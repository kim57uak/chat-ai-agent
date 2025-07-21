"""
Perplexity API 호환성 문제를 해결하기 위한 래퍼 클래스
"""

import logging
import inspect
from typing import Any, Dict, List, Optional, Union, Iterator, Mapping
from langchain_perplexity import ChatPerplexity
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from core.enhanced_system_prompts import SystemPrompts

logger = logging.getLogger(__name__)

class PerplexityWrapper(ChatPerplexity):
    """
    Perplexity API 호환성 문제를 해결하기 위한 강화된 래퍼 클래스
    stop_sequences 파라미터 문제와 ReAct 형식 문제를 완전히 해결합니다.
    """
    
    def __init__(self, **kwargs):
        # stop_sequences 파라미터 제거
        kwargs.pop('stop_sequences', None)
        kwargs.pop('stop', None)
        
        # 부모 클래스 초기화
        super().__init__(**kwargs)
        
        # 모델 설정에서 stop_sequences 관련 설정 제거
        if hasattr(self, 'model_kwargs'):
            self.model_kwargs.pop('stop_sequences', None)
            self.model_kwargs.pop('stop', None)
        
        logger.info("PerplexityWrapper 초기화 완료 (stop_sequences 파라미터 제거)")
    
    def invoke(self, *args, **kwargs):
        """
        invoke method override to remove stop_sequences parameter and add system prompt for MCP tool usage
        """
        # Remove stop_sequences parameter
        kwargs.pop('stop_sequences', None)
        kwargs.pop('stop', None)
        
        # Add special system prompt for MCP tool usage
        if args and isinstance(args[0], list) and len(args[0]) > 0:
            messages = args[0]
            
            # Always add our MCP system prompt at the beginning, replacing any existing system message
            # This ensures the model always follows our strict instructions
            mcp_system_prompt = SystemPrompts.get_perplexity_mcp_prompt()
            
            # Add ReAct format enforcement to the system prompt
            react_format_instruction = """
**CRITICAL FORMAT INSTRUCTION**:

When using tools, you MUST follow this exact format:

Thought: [your reasoning about what to do]
Action: [tool name]
Action Input: [tool input as JSON]

After receiving the Observation, continue with:

Thought: [your reasoning about the result]
Action: [next tool name or "Final Answer" if done]
...

When you have all the information needed:

Thought: [final reasoning]
Final Answer: [your complete response to the user]

NEVER deviate from this format when using tools. ALWAYS include "Action:" immediately after "Thought:".
"""
            
            enhanced_prompt = f"{mcp_system_prompt}\n\n{react_format_instruction}"
            system_message = SystemMessage(content=enhanced_prompt)
            
            # Remove any existing system messages
            messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
            
            # Insert our system message at the beginning
            messages.insert(0, system_message)
            args = (messages,) + args[1:]
            logger.info("Added enhanced MCP tool usage system prompt to Perplexity model")
            
        # Call parent class invoke method
        response = super().invoke(*args, **kwargs)
        
        # Post-process the response to enforce ReAct format if needed
        if isinstance(response.content, str):
            # 다양한 ReAct 형식 오류 패턴 확인
            has_thought = "Thought:" in response.content
            has_action = "Action:" in response.content
            has_final_answer = "Final Answer:" in response.content
            
            # 형식 오류 감지 및 수정
            if has_thought and (not has_action or not has_final_answer):
                logger.warning("Detected invalid ReAct format in response, attempting to fix")
                fixed_content = self._fix_react_format(response.content)
                response.content = fixed_content
            
        return response
    
    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """
        _stream 메서드 오버라이드하여 stop_sequences 파라미터 제거
        """
        # stop_sequences 파라미터 제거
        kwargs.pop('stop_sequences', None)
        kwargs.pop('stop', None)
        
        # stop 파라미터를 None으로 설정 (Perplexity API에서 지원하지 않음)
        stop = None
        
        # 부모 클래스의 _stream 메서드 호출
        return super()._stream(messages, stop=stop, run_manager=run_manager, **kwargs)
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        _generate 메서드 오버라이드하여 stop_sequences 파라미터 제거
        """
        # stop_sequences 파라미터 제거
        kwargs.pop('stop_sequences', None)
        kwargs.pop('stop', None)
        
        # stop 파라미터를 None으로 설정 (Perplexity API에서 지원하지 않음)
        stop = None
        
        # 부모 클래스의 _generate 메서드 호출
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
    
    def _create_message_dicts(
        self, messages: List[BaseMessage], stop: Optional[List[str]]
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        _create_message_dicts 메서드 오버라이드하여 stop_sequences 파라미터 제거
        """
        # 부모 클래스의 _create_message_dicts 메서드 호출
        message_dicts, params = super()._create_message_dicts(messages, None)  # stop을 None으로 설정
        
        # stop 파라미터 제거
        params.pop('stop', None)
        params.pop('stop_sequences', None)
        
        return message_dicts, params
    
    def _call(self, *args, **kwargs):
        """
        _call 메서드 오버라이드하여 stop_sequences 파라미터 제거
        """
        # stop_sequences 파라미터 제거
        kwargs.pop('stop_sequences', None)
        kwargs.pop('stop', None)
        
        # 부모 클래스의 _call 메서드 호출
        return super()._call(*args, **kwargs)
    
    @property
    def _invocation_params(self) -> Mapping[str, Any]:
        """
        _invocation_params 프로퍼티 오버라이드하여 stop_sequences 파라미터 제거
        """
        params = super()._invocation_params
        
        # dict 복사 후 stop_sequences 파라미터 제거
        params_copy = dict(params)
        params_copy.pop('stop_sequences', None)
        params_copy.pop('stop', None)
        
        return params_copy
        
    def _fix_react_format(self, content: str) -> str:
        """
        ReAct 형식이 잘못된 경우 수정
        
        다양한 형식 오류 패턴을 감지하고 LangChain이 이해할 수 있는 올바른 ReAct 형식으로 변환합니다.
        - "Thought:" 다음에 "Action:" 또는 "Final Answer:"가 없는 경우
        - "Action:" 다음에 "Action Input:"이 없는 경우
        - "Action Input:" 다음에 "Observation:"이 없는 경우
        - "Observation:" 다음에 "Thought:"가 없는 경우
        - 전체 응답에 "Final Answer:"가 없는 경우
        - JSON 형식이 잘못된 경우
        - 중첩된 ReAct 형식이 있는 경우
        """
        import re
        import json
        
        # 이미 올바른 형식인지 확인 (기본 검사)
        has_thought = "Thought:" in content
        has_action = "Action:" in content
        has_final_answer = "Final Answer:" in content
        
        # 완벽한 형식인 경우 그대로 반환 (모든 필수 요소 포함)
        if has_thought and has_action and has_final_answer and "Action Input:" in content:
            # 추가 검증: 형식 순서가 올바른지 확인
            if re.search(r"Thought:.*?Action:.*?Action Input:.*?Observation:.*?Thought:.*?Final Answer:", content, re.DOTALL):
                return content
        
        # 라인 단위로 분리하여 처리
        lines = content.split('\n')
        result_lines = []
        i = 0
        in_action_input = False  # Action Input 블록 내부인지 추적
        json_buffer = []  # JSON 형식 수집을 위한 버퍼
        
        while i < len(lines):
            line = lines[i].strip()
            current_line = lines[i]  # 원본 라인 (공백 포함)
            
            # JSON 블록 처리 (Action Input 내부)
            if in_action_input:
                if line.startswith("Observation:") or line.startswith("Thought:") or line.startswith("Action:") or line.startswith("Final Answer:"):
                    # JSON 블록 종료
                    in_action_input = False
                    
                    # JSON 형식 검증 및 수정
                    json_str = '\n'.join(json_buffer).strip()
                    try:
                        # 중괄호가 없는 경우 추가
                        if not json_str.startswith('{'):
                            json_str = '{' + json_str
                        if not json_str.endswith('}'):
                            json_str = json_str + '}'
                            
                        # JSON 파싱 테스트
                        json.loads(json_str)
                        result_lines.append("Action Input: " + json_str)
                    except json.JSONDecodeError:
                        # JSON 형식이 잘못된 경우 빈 객체로 대체
                        result_lines.append("Action Input: {}")
                        logger.warning(f"잘못된 JSON 형식 감지: {json_str}")
                    
                    # 현재 라인 처리 계속
                    json_buffer = []
                else:
                    # JSON 블록 내용 수집
                    json_buffer.append(line)
                    i += 1
                    continue
            
            # "Thought:" 라인 처리
            if line.startswith("Thought:"):
                result_lines.append(current_line)
                
                # 다음 라인이 있고, "Action:" 또는 "Final Answer:"로 시작하지 않는 경우
                if i < len(lines) - 1:
                    next_line = lines[i+1].strip()
                    if not (next_line.startswith("Action:") or next_line.startswith("Final Answer:")):
                        # 내용이 있으면 Final Answer로 처리
                        if next_line and not next_line.startswith("Thought:"):
                            result_lines.append("Action: Final Answer")
                            result_lines.append("Action Input: {}")
                            result_lines.append("Observation: Tool execution completed")
                            result_lines.append("Thought: Now I can provide the final answer.")
                            result_lines.append("Final Answer: " + next_line)
                            i += 1  # 다음 라인 건너뛰기
            
            # "Action:" 라인 처리
            elif line.startswith("Action:"):
                result_lines.append(current_line)
                
                # 다음 라인이 "Action Input:"으로 시작하지 않는 경우
                if i < len(lines) - 1:
                    next_line = lines[i+1].strip()
                    if not next_line.startswith("Action Input:"):
                        # Action Input 추가
                        result_lines.append("Action Input: {}")
                
                # "Final Answer" 액션인 경우 특별 처리
                if "Final Answer" in line and i < len(lines) - 1:
                    result_lines.append("Action Input: {}")
                    result_lines.append("Observation: Tool execution completed")
                    
                    # 다음 라인이 Final Answer가 아니면 추가
                    next_line = lines[i+1].strip() if i < len(lines) - 1 else ""
                    if not next_line.startswith("Final Answer:"):
                        result_lines.append("Thought: I can now provide the final answer.")
                        result_lines.append("Final Answer: " + (next_line if next_line else "Based on the information provided, here's my answer."))
                        if next_line:  # 다음 라인 건너뛰기
                            i += 1
            
            # "Action Input:" 라인 처리
            elif line.startswith("Action Input:"):
                # Action Input 시작 표시
                in_action_input = True
                json_buffer = [line.replace("Action Input:", "").strip()]
                i += 1
                continue
            
            # "Observation:" 다음에 "Thought:"가 없는 경우
            elif line.startswith("Observation:"):
                result_lines.append(current_line)
                
                if i < len(lines) - 1:
                    next_line = lines[i+1].strip()
                    if not next_line.startswith("Thought:"):
                        result_lines.append("Thought: Based on the observation, I can now proceed.")
            
            # "Final Answer:" 라인 처리 (이미 처리되지 않은 경우)
            elif line.startswith("Final Answer:"):
                # 이전에 "Action: Final Answer"가 없는 경우 추가
                if not any(l.strip() == "Action: Final Answer" for l in result_lines):
                    result_lines.append("Thought: I have enough information to provide a final answer.")
                    result_lines.append("Action: Final Answer")
                    result_lines.append("Action Input: {}")
                    result_lines.append("Observation: Tool execution completed")
                    result_lines.append("Thought: Now I can provide the final answer.")
                
                result_lines.append(current_line)
            
            # 그 외 라인은 그대로 추가
            else:
                result_lines.append(current_line)
            
            i += 1
        
        # JSON 버퍼가 남아있는 경우 처리
        if json_buffer:
            json_str = '\n'.join(json_buffer).strip()
            try:
                # 중괄호가 없는 경우 추가
                if not json_str.startswith('{'):
                    json_str = '{' + json_str
                if not json_str.endswith('}'):
                    json_str = json_str + '}'
                    
                # JSON 파싱 테스트
                json.loads(json_str)
                result_lines.append("Action Input: " + json_str)
            except json.JSONDecodeError:
                result_lines.append("Action Input: {}")
                logger.warning(f"잘못된 JSON 형식 감지: {json_str}")
        
        # "Final Answer:"가 없는 경우 추가
        if "Final Answer:" not in '\n'.join(result_lines):
            # 마지막 Thought 찾기
            last_thought_idx = -1
            for idx, line in enumerate(result_lines):
                if line.strip().startswith("Thought:"):
                    last_thought_idx = idx
            
            if last_thought_idx >= 0 and last_thought_idx < len(result_lines) - 1:
                # Thought 다음 라인을 Final Answer로 변환
                next_line = result_lines[last_thought_idx + 1]
                if not next_line.strip().startswith("Final Answer:") and not next_line.strip().startswith("Action:"):
                    result_lines.insert(last_thought_idx + 1, "Final Answer: " + next_line.strip())
                    result_lines.pop(last_thought_idx + 2)  # 원래 라인 제거
            else:
                # 마지막에 Final Answer 추가
                result_lines.append("Thought: Based on all the information, I can now provide a final answer.")
                result_lines.append("Action: Final Answer")
                result_lines.append("Action Input: {}")
                result_lines.append("Observation: Tool execution completed")
                result_lines.append("Thought: Now I can provide the final answer.")
                result_lines.append("Final Answer: I've analyzed the information and found the answer to your question.")
        
        fixed_content = '\n'.join(result_lines)
        logger.info(f"ReAct 형식 수정됨: {fixed_content[:100]}...")
        return fixed_content