"""Conversation management following SRP."""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation history and optimization."""
    
    def __init__(self, max_history_pairs: int = 5, max_tokens_estimate: int = 2000):
        self.conversation_history: List[Dict] = []
        self.max_history_pairs = max_history_pairs
        self.max_tokens_estimate = max_tokens_estimate
    
    def add_message(self, role: str, content: str) -> None:
        """Add message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
    
    def get_optimized_history(self) -> List[Dict]:
        """Get optimized conversation history."""
        if not self.conversation_history:
            return []
        
        # Keep recent N pairs
        if len(self.conversation_history) > self.max_history_pairs * 2:
            recent_history = self.conversation_history[-(self.max_history_pairs * 2):]
        else:
            recent_history = self.conversation_history.copy()
        
        # Limit by tokens
        return self._limit_by_tokens(recent_history)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        if not text:
            return 0
        
        korean_chars = sum(1 for c in text if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3)
        english_words = len([w for w in text.split() if w.isascii()])
        other_chars = len(text) - korean_chars
        
        estimated_tokens = int(korean_chars * 1.5 + english_words * 1.3 + other_chars * 0.8)
        return max(estimated_tokens, len(text) // 4)
    
    def _limit_by_tokens(self, history: List[Dict]) -> List[Dict]:
        """Limit history by token count."""
        if not history:
            return []
        
        total_tokens = 0
        limited_history = []
        
        for msg in reversed(history):
            content = msg.get("content", "")
            msg_tokens = self._estimate_tokens(content)
            
            if total_tokens + msg_tokens > self.max_tokens_estimate:
                break
            
            limited_history.insert(0, msg)
            total_tokens += msg_tokens
        
        logger.info(f"대화 기록 최적화: {len(history)}개 -> {len(limited_history)}개")
        return limited_history