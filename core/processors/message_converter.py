"""메시지 변환 처리를 담당하는 모듈"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain.schema import HumanMessage, SystemMessage, AIMessage, BaseMessage
from core.logging import get_logger

logger = get_logger("message_converter")


class MessageConverter(ABC):
    """메시지 변환을 위한 추상 클래스"""
    
    @abstractmethod
    def convert_history_to_messages(self, conversation_history: List[Dict], model_name: str) -> List:
        """대화 기록을 LangChain 메시지로 변환"""
        pass
    
    @abstractmethod
    def create_system_message(self, content: str, model_name: str):
        """시스템 메시지 생성"""
        pass


class StandardMessageConverter(MessageConverter):
    """표준 메시지 변환기"""
    
    def convert_history_to_messages(self, conversation_history: List[Dict], model_name: str) -> List:
        """대화 기록을 LangChain 메시지로 변환"""
        messages = []
        
        if not conversation_history:
            return messages
        
        recent_history = (
            conversation_history[-10:]
            if len(conversation_history) > 10
            else conversation_history
        )

        for msg in recent_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if not content or not content.strip():
                continue
                
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        logger.info(f"대화 기록 변환 완료: {len(recent_history)}개 -> {len(messages)}개 메시지")
        return messages
    
    def create_system_message(self, content: str, model_name: str):
        """시스템 메시지 생성"""
        if 'gemini' in model_name.lower():
            return HumanMessage(content=content)
        else:
            return SystemMessage(content=content)
    
    @staticmethod
    def dict_to_langchain(msg_dict: Dict) -> BaseMessage:
        """Dict → LangChain Message 변환"""
        role = msg_dict.get("role", "assistant")
        content = msg_dict.get("content", "")
        
        if role == "user":
            return HumanMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        else:
            return AIMessage(content=content)
    
    @staticmethod
    def langchain_to_dict(message: BaseMessage) -> Dict:
        """LangChain Message → Dict 변환"""
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, SystemMessage):
            role = "system"
        else:
            role = "assistant"
        
        return {
            "role": role,
            "content": message.content
        }