"""AI 모델별 처리 전략을 정의하는 모듈"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ModelStrategy(ABC):
    """AI 모델별 처리 전략을 위한 추상 클래스"""
    
    @abstractmethod
    def get_model_type(self) -> str:
        """모델 타입 반환"""
        pass
    
    @abstractmethod
    def supports_model(self, model_name: str) -> bool:
        """해당 모델을 지원하는지 확인"""
        pass
    
    @abstractmethod
    def process_tool_chat(self, user_input: str, llm: Any, tools: List, agent_executor_factory, agent_executor=None) -> Tuple[str, List]:
        """도구 채팅 처리"""
        pass


class GPTModelStrategy(ModelStrategy):
    """GPT 모델 전략"""
    
    def get_model_type(self) -> str:
        return "gpt"
    
    def supports_model(self, model_name: str) -> bool:
        return 'gpt' in model_name.lower() or 'openai' in model_name.lower()
    
    def process_tool_chat(self, user_input: str, llm: Any, tools: List, agent_executor_factory, agent_executor=None) -> Tuple[str, List]:
        """GPT 모델용 도구 채팅 처리"""
        try:
            if not agent_executor:
                agent_executor = agent_executor_factory.create_agent_executor(llm, tools)
            
            if not agent_executor:
                return "사용 가능한 도구가 없습니다.", []
            
            result = agent_executor.invoke({"input": user_input})
            output = result.get("output", "")
            
            used_tools = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) >= 2 and hasattr(step[0], "tool"):
                        used_tools.append(step[0].tool)
            
            # 에이전트 중단 또는 빈 결과 처리
            if ("Agent stopped" in output or 
                "iteration limit" in output or
                "time limit" in output or
                not output.strip()):
                logger.warning("GPT 에이전트 중단 감지, 단순 채팅으로 대체")
                from core.processors.simple_chat_processor import SimpleChatProcessor
                simple_processor = SimpleChatProcessor()
                return simple_processor.process_chat(user_input, llm), []
            
            return output, used_tools
            
        except Exception as e:
            logger.error(f"GPT 도구 채팅 오류: {e}")
            from core.processors.simple_chat_processor import SimpleChatProcessor
            simple_processor = SimpleChatProcessor()
            return simple_processor.process_chat(user_input, llm), []


class GeminiModelStrategy(ModelStrategy):
    """Gemini 모델 전략"""
    
    def get_model_type(self) -> str:
        return "gemini"
    
    def supports_model(self, model_name: str) -> bool:
        return 'gemini' in model_name.lower()
    
    def process_tool_chat(self, user_input: str, llm: Any, tools: List, agent_executor_factory, agent_executor=None) -> Tuple[str, List]:
        """Gemini 모델용 도구 채팅 처리"""
        try:
            if not agent_executor:
                agent_executor = agent_executor_factory.create_agent_executor(llm, tools)
            
            if not agent_executor:
                return "사용 가능한 도구가 없습니다.", []
            
            logger.info(f"Gemini 에이전트 실행: {user_input[:50]}...")
            result = agent_executor.invoke({"input": user_input})
            output = result.get("output", "")
            
            used_tools = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) >= 2 and hasattr(step[0], "tool"):
                        used_tools.append(step[0].tool)
            
            # 에이전트가 중단되거나 빈 결과인 경우 단순 채팅으로 대체
            if (not output.strip() or 
                "Agent stopped" in output or 
                "iteration limit" in output or
                "time limit" in output or
                "에이전트 중단 감지" in output):
                logger.warning("Gemini 에이전트 중단 감지, 단순 채팅으로 대체")
                from core.processors.simple_chat_processor import SimpleChatProcessor
                simple_processor = SimpleChatProcessor()
                return simple_processor.process_chat(user_input, llm), []
            
            return output, used_tools
            
        except Exception as e:
            logger.error(f"Gemini 도구 채팅 오류: {e}")
            from core.processors.simple_chat_processor import SimpleChatProcessor
            simple_processor = SimpleChatProcessor()
            return simple_processor.process_chat(user_input, llm), []


class PerplexityModelStrategy(ModelStrategy):
    """Perplexity 모델 전략"""
    
    def get_model_type(self) -> str:
        return "perplexity"
    
    def supports_model(self, model_name: str) -> bool:
        return 'sonar' in model_name.lower() or 'r1-' in model_name.lower() or 'perplexity' in model_name.lower()
    
    def process_tool_chat(self, user_input: str, llm: Any, tools: List, agent_executor_factory, agent_executor=None) -> Tuple[str, List]:
        """Perplexity 모델용 도구 채팅 처리"""
        # Perplexity는 기본적으로 GPT와 유사하게 처리
        gpt_strategy = GPTModelStrategy()
        return gpt_strategy.process_tool_chat(user_input, llm, tools, agent_executor_factory, agent_executor)


class ModelStrategyFactory:
    """모델 전략 팩토리"""
    
    _strategies = [
        GPTModelStrategy(),
        GeminiModelStrategy(),
        PerplexityModelStrategy()
    ]
    
    @classmethod
    def get_strategy(cls, model_name: str) -> ModelStrategy:
        """모델명에 따른 전략 반환"""
        for strategy in cls._strategies:
            if strategy.supports_model(model_name):
                return strategy
        
        # 기본값으로 GPT 전략 사용
        return GPTModelStrategy()
    
    @classmethod
    def register_strategy(cls, strategy: ModelStrategy):
        """새로운 전략 등록"""
        cls._strategies.append(strategy)