"""Claude 모델 전략 - 새로운 AI 모델 추가 예시"""
from typing import List, Any, Tuple
from core.strategies.model_strategy import ModelStrategy
import logging

logger = logging.getLogger(__name__)


class ClaudeModelStrategy(ModelStrategy):
    """Claude 모델 전략 - 확장성 예시"""
    
    def get_model_type(self) -> str:
        return "claude"
    
    def supports_model(self, model_name: str) -> bool:
        return 'claude' in model_name.lower() or 'anthropic' in model_name.lower()
    
    def process_tool_chat(self, user_input: str, llm: Any, tools: List, agent_executor_factory, agent_executor=None) -> Tuple[str, List]:
        """Claude 모델용 도구 채팅 처리"""
        # Claude 특화 처리 로직 구현
        if not agent_executor:
            agent_executor = agent_executor_factory.create_agent_executor(llm, tools)
        
        if not agent_executor:
            return "사용 가능한 도구가 없습니다.", []
        
        # Claude 모델의 특별한 처리가 필요한 경우 여기에 구현
        result = agent_executor.invoke({"input": user_input})
        output = result.get("output", "")
        
        used_tools = []
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if len(step) >= 2 and hasattr(step[0], "tool"):
                    used_tools.append(step[0].tool)
        
        if "Agent stopped" in output or not output.strip():
            from core.processors.simple_chat_processor import SimpleChatProcessor
            simple_processor = SimpleChatProcessor()
            return simple_processor.process_chat(user_input, llm), []
        
        logger.info(f"✅ Claude 도구 채팅 성공: {len(used_tools)}개 도구 사용")
        return output, used_tools


# 새로운 모델 전략을 자동으로 등록
def register_claude_strategy():
    """Claude 전략을 팩토리에 등록"""
    from core.strategies.model_strategy import ModelStrategyFactory
    ModelStrategyFactory.register_strategy(ClaudeModelStrategy())

# 모듈 로드 시 자동 등록
register_claude_strategy()