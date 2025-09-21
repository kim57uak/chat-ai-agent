"""
Message Management Utilities
세션 내 메시지 관리 기능
"""

from typing import List, Dict, Optional
import logging
import re
from .session_manager import session_manager

logger = logging.getLogger(__name__)


class MessageManager:
    """메시지 관리 클래스"""
    
    @staticmethod
    def delete_message(session_id: int, message_id: int) -> bool:
        """특정 메시지 삭제"""
        try:
            with session_manager.db.get_connection() as conn:
                cursor = conn.execute('''
                    DELETE FROM messages 
                    WHERE id = ? AND session_id = ?
                ''', (message_id, session_id))
                
                success = cursor.rowcount > 0
                
                if success:
                    # 세션의 메시지 카운트 업데이트
                    conn.execute('''
                        UPDATE sessions 
                        SET message_count = (
                            SELECT COUNT(*) FROM messages WHERE session_id = ?
                        ),
                        last_used_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (session_id, session_id))
                
                conn.commit()
                
                if success:
                    logger.info(f"메시지 삭제 성공: {message_id}")
                
                return success
                
        except Exception as e:
            logger.error(f"메시지 삭제 오류: {e}")
            return False
    
    @staticmethod
    def get_message(session_id: int, message_id: int) -> Optional[Dict]:
        """특정 메시지 조회"""
        try:
            with session_manager.db.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT id, role, content, content_html, timestamp, token_count, tool_calls
                    FROM messages 
                    WHERE id = ? AND session_id = ?
                ''', (message_id, session_id))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row['id'],
                        'role': row['role'],
                        'content': row['content'],
                        'content_html': row['content_html'],
                        'timestamp': row['timestamp'],
                        'token_count': row['token_count'],
                        'tool_calls': row['tool_calls']
                    }
                return None
                
        except Exception as e:
            logger.error(f"메시지 조회 오류: {e}")
            return None
    
    @staticmethod
    def _remove_html_tags(text: str) -> str:
        """메시지에서 HTML 태그 제거"""
        if not text:
            return text
        # HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        # HTML 엔티티 디코딩
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return clean_text.strip()
    
    @staticmethod
    def get_messages(session_id: int) -> List[Dict]:
        """세션의 모든 메시지 조회"""
        try:
            with session_manager.db.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT id, role, content, content_html, timestamp, token_count, tool_calls
                    FROM messages 
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                ''', (session_id,))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'id': row['id'],
                        'role': row['role'],
                        'content': row['content'],
                        'content_html': row['content_html'],
                        'timestamp': row['timestamp'],
                        'created_at': row['timestamp'],  # PDF 내보내기 호환성
                        'token_count': row['token_count'],
                        'tool_calls': row['tool_calls']
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"메시지 목록 조회 오류: {e}")
            return []
    
    @staticmethod
    def update_message(session_id: int, message_id: int, content: str, content_html: str = None) -> bool:
        """메시지 내용 수정"""
        try:
            # content 필드에는 HTML 태그 제거된 텍스트 저장
            clean_content = MessageManager._remove_html_tags(content)
            
            with session_manager.db.get_connection() as conn:
                cursor = conn.execute('''
                    UPDATE messages 
                    SET content = ?, content_html = ?
                    WHERE id = ? AND session_id = ?
                ''', (clean_content, content_html, message_id, session_id))
                
                success = cursor.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"메시지 수정 성공: {message_id}")
                
                return success
                
        except Exception as e:
            logger.error(f"메시지 수정 오류: {e}")
            return False
    
    @staticmethod
    def find_session_by_message_id(message_id: int) -> Optional[int]:
        """메시지 ID로부터 세션 ID 찾기"""
        try:
            with session_manager.db.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT session_id FROM messages WHERE id = ?
                ''', (message_id,))
                
                row = cursor.fetchone()
                if row:
                    return row['session_id']
                return None
                
        except Exception as e:
            logger.error(f"메시지 ID로 세션 찾기 오류: {e}")
            return None


# 전역 메시지 매니저 인스턴스
message_manager = MessageManager()