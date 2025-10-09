"""Chat client following SRP."""

from typing import List, Dict, Any, Tuple, Optional, Callable
from core.ai_agent import AIAgent
from core.logging import get_logger

logger = get_logger("chat_client")


class ChatClient:
    """Simple chat client with single responsibility."""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model_name = model_name
        self.agent = AIAgent(api_key, model_name)
    
    def chat(self, user_input: str) -> str:
        """Simple chat without tools."""
        return self.agent.simple_chat(user_input)
    
    def agent_chat(self, user_input: str) -> Tuple[str, List]:
        """Chat with tools enabled."""
        return self.agent.process_message(user_input)
    
    def chat_with_history(self, user_input: str, history: List[Dict]) -> str:
        """Chat with conversation history."""
        return self.agent.simple_chat_with_history(user_input, history)
    
    def agent_chat_with_history(self, user_input: str, history: List[Dict], force_agent: bool = True) -> Tuple[str, List]:
        """Agent chat with conversation history."""
        return self.agent.process_message_with_history(user_input, history, force_agent)