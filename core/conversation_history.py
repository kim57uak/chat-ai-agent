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
        
        # 과도한 구분선 정리
        content = self._clean_excessive_separators(content)
        
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
        """Get recent messages for display - 시간순으로 정렬하여 반환"""
        if count <= 0:
            return []
        # 최근 N개 메시지를 가져와서 시간순으로 정렬 (오래된 것부터)
        recent = self.current_session[-count:] if self.current_session else []
        return recent

    def get_context_messages(self) -> List[Dict]:
        """Get messages for AI context - 최근 5개 대화 기준"""
        messages = self.get_recent_messages(10)  # 5개 대화 = 10개 메시지 (user + assistant)
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
    
    def _clean_excessive_separators(self, content: str) -> str:
        """과도한 구분선 정리"""
        import re
        
        # 10개 이상의 대시, 등호, 별표를 3개로 정리
        content = re.sub(r'^-{10,}$', '---', content, flags=re.MULTILINE)
        content = re.sub(r'^={10,}$', '---', content, flags=re.MULTILINE)
        content = re.sub(r'^\*{10,}$', '---', content, flags=re.MULTILINE)
        
        # 연속된 과도한 구분선 제거
        lines = content.split('\n')
        cleaned_lines = []
        prev_was_separator = False
        
        for line in lines:
            line_stripped = line.strip()
            is_separator = line_stripped in ['---', '===', '***'] or len(line_stripped) > 50 and all(c in '-=*' for c in line_stripped)
            
            if is_separator:
                if not prev_was_separator:
                    cleaned_lines.append('---')
                prev_was_separator = True
            else:
                cleaned_lines.append(line)
                prev_was_separator = False
        
        return '\n'.join(cleaned_lines)