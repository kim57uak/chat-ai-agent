"""
LangChain Memory Adapter
기존 EncryptedDatabase를 LangChain Memory로 래핑
"""

from typing import List
from langchain.schema import BaseChatMessageHistory, BaseMessage
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from core.logging import get_logger

logger = get_logger("langchain_memory_adapter")


class EncryptedChatMessageHistory(BaseChatMessageHistory):
    """기존 EncryptedDatabase를 LangChain Memory로 래핑"""
    
    def __init__(self, session_id: int, encrypted_db):
        """
        Initialize with existing encrypted database
        
        Args:
            session_id: Session ID
            encrypted_db: EncryptedDatabase instance
        """
        self.session_id = session_id
        self.db = encrypted_db
        
        # 인증 확인
        if not self.db.auth_manager or not self.db.auth_manager.is_logged_in():
            raise RuntimeError("Authentication required for encrypted chat history")
        
        logger.info(f"Initialized LangChain memory adapter for session {session_id}")
    
    def add_message(self, message: BaseMessage) -> None:
        """
        Add a message to the database
        
        Args:
            message: LangChain BaseMessage
        """
        # LangChain Message → Dict 변환
        role = self._get_role(message)
        content = message.content
        
        # 기존 DB에 저장
        self.db.add_message(
            session_id=self.session_id,
            role=role,
            content=content
        )
        
        logger.debug(f"Added {role} message to session {self.session_id}")
    
    @property
    def messages(self) -> List[BaseMessage]:
        """
        Get all messages from the database
        
        Returns:
            List of LangChain BaseMessage objects
        """
        # 기존 DB에서 메시지 로드
        msgs = self.db.get_messages(self.session_id)
        
        # Dict → LangChain Message 변환
        langchain_messages = []
        for msg in msgs:
            try:
                langchain_msg = self._to_langchain_message(msg)
                langchain_messages.append(langchain_msg)
            except Exception as e:
                logger.warning(f"Failed to convert message {msg.get('id')}: {e}")
                continue
        
        logger.debug(f"Loaded {len(langchain_messages)} messages from session {self.session_id}")
        return langchain_messages
    
    def clear(self) -> None:
        """Clear all messages (optional implementation)"""
        logger.warning(f"Clear operation not implemented for session {self.session_id}")
        pass
    
    def _get_role(self, message: BaseMessage) -> str:
        """
        Convert LangChain message type to role string
        
        Args:
            message: LangChain BaseMessage
            
        Returns:
            Role string ("user", "assistant", "system")
        """
        if isinstance(message, HumanMessage):
            return "user"
        elif isinstance(message, SystemMessage):
            return "system"
        else:
            return "assistant"
    
    def _to_langchain_message(self, msg_dict: dict) -> BaseMessage:
        """
        Convert dict message to LangChain message
        
        Args:
            msg_dict: Message dictionary from database
            
        Returns:
            LangChain BaseMessage
        """
        role = msg_dict.get("role", "assistant")
        content = msg_dict.get("content", "")
        
        if role == "user":
            return HumanMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        else:
            return AIMessage(content=content)
