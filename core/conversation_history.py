import json
import os
from datetime import datetime
from typing import List, Dict


class ConversationHistory:
    """Simple conversation history management"""

    def __init__(self, history_file: str = "conversation_history.json"):
        self.history_file = history_file
        self.current_session = []
        self.max_history_length = 50

    def add_message(self, role: str, content: str):
        """Add message with duplicate prevention"""
        if not content or not content.strip():
            return
            
        content = content.strip()
        
        # Prevent duplicate consecutive messages
        if (self.current_session and 
            self.current_session[-1]["role"] == role and 
            self.current_session[-1]["content"] == content):
            return
            
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.current_session.append(message)
        
        # Keep only recent messages
        if len(self.current_session) > self.max_history_length:
            self.current_session = self.current_session[-self.max_history_length:]

    def get_recent_messages(self, count: int = 5) -> List[Dict]:
        """Get recent messages for display"""
        if count <= 0:
            return []
        return self.current_session[-count:] if self.current_session else []

    def get_context_messages(self) -> List[Dict]:
        """Get messages for AI context"""
        messages = self.get_recent_messages(8)
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    def clear_session(self):
        """Clear current session"""
        self.current_session = []

    def save_to_file(self):
        """Save to file"""
        try:
            data = {
                "messages": self.current_session,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"History save failed: {e}")

    def load_from_file(self):
        """Load from file with validation"""
        try:
            if not os.path.exists(self.history_file):
                self.current_session = []
                return
                
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            messages = data.get("messages", [])
            
            # Validate and clean messages
            valid_messages = []
            for msg in messages:
                if (isinstance(msg, dict) and 
                    "role" in msg and 
                    "content" in msg and 
                    msg["content"].strip()):
                    valid_messages.append(msg)
            
            # 로딩 시에는 모든 히스토리를 로드하되, 최대 50개까지만 유지
            self.current_session = valid_messages[-self.max_history_length:]
            
        except Exception as e:
            print(f"History load failed: {e}")
            self.current_session = []