import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class ConversationHistory:
    """대화 히스토리 관리 클래스"""
    
    def __init__(self, history_file: str = "conversation_history.json"):
        self.history_file = history_file
        self.current_session = []
        self.max_history_length = 50  # 최대 대화 기록 수
        
    def add_message(self, role: str, content: str):
        """메시지 추가"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.current_session.append(message)
        
        # 길이 제한
        if len(self.current_session) > self.max_history_length:
            self.current_session = self.current_session[-self.max_history_length:]
    
    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """최근 메시지 가져오기"""
        return self.current_session[-count:] if count > 0 else self.current_session
    
    def clear_session(self):
        """현재 세션 초기화"""
        self.current_session = []
    
    def save_to_file(self):
        """파일에 저장"""
        try:
            history_data = {
                "last_updated": datetime.now().isoformat(),
                "messages": self.current_session
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"히스토리 저장 실패: {e}")
    
    def load_from_file(self):
        """파일에서 로드"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_session = data.get("messages", [])
        except Exception as e:
            print(f"히스토리 로드 실패: {e}")
            self.current_session = []