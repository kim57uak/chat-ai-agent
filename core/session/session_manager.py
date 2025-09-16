"""
Chat Session Manager
주제별 AI 대화 세션을 관리하는 메인 클래스
"""

from typing import List, Dict, Optional
import logging
import re
from .session_database import SessionDatabase

logger = logging.getLogger(__name__)


class SessionManager:
    """채팅 세션 관리 클래스"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db = SessionDatabase(db_path)
    
    def create_session(self, title: str, topic_category: str = None, model_used: str = None) -> int:
        """새 세션 생성"""
        print(f"[SESSION_MANAGER] create_session - title: {title}")
        session_id = self.db.execute_insert('''
            INSERT INTO sessions (title, topic_category, model_used)
            VALUES (?, ?, ?)
        ''', (title, topic_category, model_used))
        
        print(f"[SESSION_MANAGER] 세션 생성 성공 - session_id: {session_id}")
        logger.info(f"새 세션 생성: {session_id} - {title}")
        return session_id
    
    def get_sessions(self, limit: int = 50) -> List[Dict]:
        """세션 목록 조회 (최근 사용 순)"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT id, title, topic_category, created_at, last_used_at, 
                       message_count, model_used, is_active
                FROM sessions 
                WHERE is_active = 1
                ORDER BY last_used_at DESC
                LIMIT ?
            ''', (limit,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row['id'],
                    'title': row['title'],
                    'topic_category': row['topic_category'],
                    'created_at': row['created_at'],
                    'last_used_at': row['last_used_at'],
                    'message_count': row['message_count'],
                    'model_used': row['model_used'],
                    'is_active': row['is_active']
                })
            
            return sessions
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """특정 세션 조회"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT id, title, topic_category, created_at, last_used_at,
                       message_count, model_used, is_active
                FROM sessions 
                WHERE id = ? AND is_active = 1
            ''', (session_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'title': row['title'],
                    'topic_category': row['topic_category'],
                    'created_at': row['created_at'],
                    'last_used_at': row['last_used_at'],
                    'message_count': row['message_count'],
                    'model_used': row['model_used'],
                    'is_active': row['is_active']
                }
            return None
    
    def update_session(self, session_id: int, title: str = None, topic_category: str = None) -> bool:
        """세션 정보 업데이트"""
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if topic_category is not None:
            updates.append("topic_category = ?")
            params.append(topic_category)
        
        if not updates:
            return False
        
        updates.append("last_used_at = CURRENT_TIMESTAMP")
        params.append(session_id)
        
        rowcount = self.db.execute_update(f'''
            UPDATE sessions 
            SET {", ".join(updates)}
            WHERE id = ? AND is_active = 1
        ''', params)
        
        success = rowcount > 0
        if success:
            logger.info(f"세션 업데이트: {session_id}")
        
        return success
    
    def delete_session(self, session_id: int) -> bool:
        """세션 삭제 (소프트 삭제)"""
        rowcount = self.db.execute_update('''
            UPDATE sessions 
            SET is_active = 0 
            WHERE id = ?
        ''', (session_id,))
        
        success = rowcount > 0
        if success:
            logger.info(f"세션 삭제: {session_id}")
        
        return success
    
    def _remove_html_tags(self, text: str) -> str:
        """HTML 태그 제거"""
        if not text:
            return text
        # HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        # HTML 엔티티 디코딩
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return clean_text.strip()
    
    def add_message(self, session_id: int, role: str, content: str, 
                   content_html: str = None, token_count: int = 0, tool_calls: str = None) -> int:
        """메시지 추가"""
        print(f"[SESSION_MANAGER] add_message - session_id: {session_id}, role: {role}, content 길이: {len(content) if content else 0}")
        
        # content 필드에는 HTML 태그 제거된 텍스트 저장
        clean_content = self._remove_html_tags(content)
        
        with self.db.get_connection() as conn:
            # 메시지 추가
            cursor = conn.execute('''
                INSERT INTO messages (session_id, role, content, content_html, token_count, tool_calls)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, role, clean_content, content_html, token_count, tool_calls))
            
            message_id = cursor.lastrowid
            print(f"[SESSION_MANAGER] 메시지 삽입 성공 - message_id: {message_id}")
            
            # 세션의 메시지 카운트 및 마지막 사용 시간 업데이트
            conn.execute('''
                UPDATE sessions 
                SET message_count = message_count + 1,
                    last_used_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (session_id,))
            
            conn.commit()
            return message_id
    
    def get_session_messages(self, session_id: int, limit: int = 100, include_html: bool = False) -> List[Dict]:
        """세션의 메시지 목록 조회 (시간순 정렬)"""
        print(f"[GET_MESSAGES] session_id: {session_id}, limit: {limit}, include_html: {include_html}")
        with self.db.get_connection() as conn:
            if include_html:
                cursor = conn.execute('''
                    SELECT id, role, content, content_html, timestamp, token_count, tool_calls
                    FROM messages 
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                ''', (session_id, limit))
            else:
                cursor = conn.execute('''
                    SELECT id, role, content, timestamp, token_count, tool_calls
                    FROM messages 
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                ''', (session_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                message = {
                    'id': row['id'],
                    'role': row['role'],
                    'content': row['content'],
                    'timestamp': row['timestamp'],
                    'token_count': row['token_count'],
                    'tool_calls': row['tool_calls']
                }
                if include_html and 'content_html' in row.keys():
                    message['content_html'] = row['content_html']
                messages.append(message)
            
            print(f"[GET_MESSAGES] 반환할 메시지 수: {len(messages)}")
            # 메시지 내용 디버깅
            for i, msg in enumerate(messages[:3]):  # 처음 3개만 로그
                print(f"[GET_MESSAGES] 메시지 {i+1}: role={msg['role']}, content={msg['content'][:50]}...")
            return messages
    
    def get_session_context(self, session_id: int, max_tokens: int = 4000) -> List[Dict]:
        """세션 컨텍스트 조회 (토큰 제한 고려)"""
        messages = self.get_session_messages(session_id)
        
        # 토큰 수가 제한을 넘지 않도록 최근 메시지부터 선택
        context_messages = []
        total_tokens = 0
        
        for message in reversed(messages):
            message_tokens = message.get('token_count', len(message['content']) // 4)
            if total_tokens + message_tokens > max_tokens and context_messages:
                break
            
            context_messages.insert(0, {
                'role': message['role'],
                'content': message['content']
            })
            total_tokens += message_tokens
        
        return context_messages
    
    def search_sessions(self, query: str, limit: int = 20) -> List[Dict]:
        """세션 검색"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT DISTINCT s.id, s.title, s.topic_category, s.created_at, 
                       s.last_used_at, s.message_count, s.model_used
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                WHERE s.is_active = 1 AND (
                    s.title LIKE ? OR 
                    s.topic_category LIKE ? OR 
                    m.content LIKE ?
                )
                ORDER BY s.last_used_at DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row['id'],
                    'title': row['title'],
                    'topic_category': row['topic_category'],
                    'created_at': row['created_at'],
                    'last_used_at': row['last_used_at'],
                    'message_count': row['message_count'],
                    'model_used': row['model_used']
                })
            
            return sessions
    
    def get_message_count(self, session_id: int) -> int:
        """세션의 실제 메시지 수 조회"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM messages WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            return row[0] if row else 0
    
    def get_session_stats(self) -> Dict:
        """세션 통계 조회"""
        with self.db.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(message_count) as total_messages,
                    AVG(message_count) as avg_messages_per_session
                FROM sessions 
                WHERE is_active = 1
            ''')
            
            row = cursor.fetchone()
            return {
                'total_sessions': row[0] or 0,
                'total_messages': row[1] or 0,
                'avg_messages_per_session': round(row[2] or 0, 1)
            }


# 전역 세션 매니저 인스턴스
session_manager = SessionManager()