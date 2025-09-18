import json
import os
import uuid
from datetime import datetime
from typing import List, Dict
from core.file_utils import load_config
from utils.config_path import config_path_manager


class ConversationHistory:
    """Hybrid conversation history management"""

    def __init__(self, history_file: str = "conversation_history.json"):
        self.history_file = history_file
        self._resolved_path = None
        self.current_session = []
        self.config = load_config()
        self.settings = self.config.get("conversation_settings", {})
        
        # 설정값 로드
        self.hybrid_mode = self.settings.get("hybrid_mode", True)
        self.user_message_limit = self.settings.get("user_message_limit", 10)
        self.ai_response_limit = self.settings.get("ai_response_limit", 10)
        self.ai_response_token_limit = self.settings.get("ai_response_token_limit", 15000)
        self.max_history_length = 100  # 전체 세션 최대 길이

    def add_message(self, role: str, content: str, model_name: str = None, input_tokens: int = None, output_tokens: int = None, total_tokens: int = None):
        """Add message with duplicate prevention, model info and accurate token data"""
        if not content or not content.strip():
            return
            
        content = content.strip()
        content = self._clean_excessive_separators(content)
        
        # Prevent duplicate consecutive messages
        if (self.current_session and 
            self.current_session[-1]["role"] == role and 
            self.current_session[-1]["content"] == content):
            return
            
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "token_count": self._estimate_tokens(content)
        }
        
        # AI 응답인 경우 모델 정보와 정확한 토큰 정보 추가
        if role in ["assistant", "agent"] and model_name:
            message["model"] = model_name
            
            # 정확한 토큰 정보가 제공된 경우 저장
            if input_tokens is not None:
                message["input_tokens"] = input_tokens
            if output_tokens is not None:
                message["output_tokens"] = output_tokens
            if total_tokens is not None:
                message["total_tokens"] = total_tokens
                # 정확한 토큰 수가 있으면 추정값 대신 사용
                message["token_count"] = output_tokens if output_tokens is not None else total_tokens
        
        self.current_session.append(message)
        
        # Keep only recent messages
        if len(self.current_session) > self.max_history_length:
            self.current_session = self.current_session[-self.max_history_length:]
        
        return message["id"]

    def get_context_messages(self) -> List[Dict]:
        """Get messages for AI context using hybrid approach"""
        if not self.hybrid_mode:
            return self._get_legacy_context()
        
        # 하이브리드 방식: 사용자 메시지와 AI 응답을 별도로 처리
        user_messages = []
        ai_messages = []
        
        # 역순으로 순회하여 최근 메시지부터 수집
        for msg in reversed(self.current_session):
            if msg["role"] == "user":
                if len(user_messages) < self.user_message_limit:
                    user_messages.insert(0, msg)
            elif msg["role"] in ["assistant", "agent"]:
                if len(ai_messages) < self.ai_response_limit:
                    ai_messages.insert(0, msg)
        
        # AI 응답에 토큰 제한 적용
        ai_messages = self._apply_token_limit(ai_messages)
        
        # 시간순으로 병합
        all_messages = user_messages + ai_messages
        all_messages.sort(key=lambda x: x["timestamp"])
        
        return [{"role": msg["role"], "content": self._clean_content_for_ai(msg["content"])} for msg in all_messages]

    def _apply_token_limit(self, ai_messages: List[Dict]) -> List[Dict]:
        """Apply token limit to AI responses"""
        if not ai_messages:
            return []
        
        total_tokens = 0
        filtered_messages = []
        
        # 최신 메시지부터 토큰 제한까지 추가
        for msg in reversed(ai_messages):
            # 정확한 토큰 수가 있으면 사용, 없으면 추정
            msg_tokens = msg.get("output_tokens") or msg.get("total_tokens") or msg.get("token_count", self._estimate_tokens(msg["content"]))
            if total_tokens + msg_tokens <= self.ai_response_token_limit:
                filtered_messages.insert(0, msg)
                total_tokens += msg_tokens
            else:
                break
        
        return filtered_messages

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        from core.token_logger import TokenLogger
        return TokenLogger.estimate_tokens(text)

    def _get_legacy_context(self) -> List[Dict]:
        """Legacy context method for backward compatibility"""
        messages = self.get_recent_messages(10)
        
        if messages:
            if messages[-1]["role"] == "user":
                messages = messages[:-1]
            
            if len(messages) > 10:
                messages = messages[-10:]
        
        return [{"role": msg["role"], "content": self._clean_content_for_ai(msg["content"])} for msg in messages]

    def get_recent_messages(self, count: int = 5) -> List[Dict]:
        """Get recent messages for display"""
        if count <= 0:
            return []
        recent = self.current_session[-count:] if self.current_session else []
        return recent

    def clear_session(self):
        """Clear current session"""
        self.current_session = []

    def save_to_file(self):
        """JSON 저장 기능 비활성화 - 세션 관리 시스템으로 대체됨"""
        # JSON 저장 기능 비활성화
        # 나중에 다시 필요할 수도 있으므로 코드는 주석 처리
        pass
        
        # 기존 코드 (비활성화)
        # try:
        #     if self._resolved_path is None:
        #         self._resolved_path = config_path_manager.get_config_path(self.history_file)
        #     
        #     data = {
        #         "messages": self.current_session,
        #         "last_updated": datetime.now().isoformat()
        #     }
        #     
        #     with open(self._resolved_path, "w", encoding="utf-8") as f:
        #         json.dump(data, f, ensure_ascii=False, indent=2)
        #         
        # except Exception as e:
        #     print(f"History save failed: {e}")

    def load_from_file(self):
        """Load from file with validation"""
        try:
            if self._resolved_path is None:
                self._resolved_path = config_path_manager.get_config_path(self.history_file)
            
            if not self._resolved_path.exists():
                self.current_session = []
                return
                
            with open(self._resolved_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            messages = data.get("messages", [])
            
            # Validate and clean messages
            valid_messages = []
            for msg in messages:
                if (isinstance(msg, dict) and 
                    "role" in msg and 
                    "content" in msg and 
                    msg["content"].strip()):
                    
                    # 토큰 수가 없으면 추가
                    if "token_count" not in msg:
                        msg["token_count"] = self._estimate_tokens(msg["content"])
                    
                    # 모델 정보가 없는 AI 메시지에 기본값 추가
                    if msg["role"] in ["assistant", "agent"] and "model" not in msg:
                        msg["model"] = "unknown"
                    
                    # ID가 없는 메시지에 ID 추가
                    if "id" not in msg:
                        msg["id"] = str(uuid.uuid4())
                    
                    valid_messages.append(msg)
            
            self.current_session = valid_messages[-self.max_history_length:]
            
        except Exception as e:
            print(f"History load failed: {e}")
            self.current_session = []
    
    def _clean_excessive_separators(self, content: str) -> str:
        """Clean excessive separators"""
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

    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        user_count = len([m for m in self.current_session if m["role"] == "user"])
        ai_count = len([m for m in self.current_session if m["role"] in ["assistant", "agent"]])
        
        # 정확한 토큰 수 사용
        total_tokens = 0
        for m in self.current_session:
            if m["role"] in ["assistant", "agent"]:
                # 정확한 토큰 수가 있으면 사용
                tokens = m.get("total_tokens") or m.get("output_tokens") or m.get("token_count", 0)
            else:
                tokens = m.get("token_count", 0)
            total_tokens += tokens
        
        # 모델별 통계
        model_stats = {}
        for msg in self.current_session:
            if msg["role"] in ["assistant", "agent"] and "model" in msg:
                model = msg["model"]
                if model not in model_stats:
                    model_stats[model] = {"count": 0, "tokens": 0}
                model_stats[model]["count"] += 1
                # 정확한 토큰 수 사용
                tokens = msg.get("total_tokens") or msg.get("output_tokens") or msg.get("token_count", 0)
                model_stats[model]["tokens"] += tokens
        
        return {
            "total_messages": len(self.current_session),
            "user_messages": user_count,
            "ai_messages": ai_count,
            "total_tokens": total_tokens,
            "hybrid_mode": self.hybrid_mode,
            "model_stats": model_stats
        }
    
    def delete_message(self, message_id: str) -> bool:
        """Delete message by ID"""
        try:
            original_length = len(self.current_session)
            self.current_session = [msg for msg in self.current_session if msg.get("id") != message_id]
            
            if len(self.current_session) < original_length:
                # self.save_to_file()  # JSON 저장 비활성화
                return True
            return False
        except Exception as e:
            print(f"Message deletion failed: {e}")
            return False
    
    def _clean_content_for_ai(self, content: str) -> str:
        """Clean HTML tags and emojis from content for AI context"""
        import re
        
        if not content:
            return content
        
        # HTML 태그 제거
        content = re.sub(r'<[^>]+>', '', content)
        
        # HTML 엔티티 디코딩
        content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        content = content.replace('&quot;', '"').replace('&#39;', "'")
        
        # 이모지 제거 (유니코드 이모지 범위)
        content = re.sub(r'[\U0001F600-\U0001F64F]', '', content)  # 얼굴 이모지
        content = re.sub(r'[\U0001F300-\U0001F5FF]', '', content)  # 기호 및 그림 문자
        content = re.sub(r'[\U0001F680-\U0001F6FF]', '', content)  # 교통 및 지도 기호
        content = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', content)  # 국기
        content = re.sub(r'[\U00002600-\U000026FF]', '', content)  # 기타 기호
        content = re.sub(r'[\U00002700-\U000027BF]', '', content)  # 딩배트
        
        # 모든 이스케이프 문자 제거
        content = re.sub(r'\\[nrtbfav\\]', ' ', content)  # \n, \r, \t, \b, \f, \a, \v, \\
        content = re.sub(r'[\n\r\t\f\v]', ' ', content)  # 실제 제어문자
        content = content.replace('\\', '')  # 남은 백슬래시
        
        # 여러 공백을 하나로 정리
        content = re.sub(r'\s+', ' ', content)
        
        # 앞뒤 공백 제거
        content = content.strip()
        
        return content