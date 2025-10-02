#!/usr/bin/env python3
"""
DB 클린징 스크립트 - is_active = 0인 세션과 메시지 완전 삭제
"""

import sqlite3
from pathlib import Path
import os

def get_db_path():
    """DB 경로 찾기"""
    # 기본 경로들 확인
    possible_paths = [
        Path.home() / ".chat-ai-agent" / "chat_sessions.db",  # macOS/Linux
        Path.home() / "AppData" / "Local" / "ChatAIAgent" / "chat_sessions.db",  # Windows
        Path.cwd() / "chat_sessions.db",  # 현재 디렉토리
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    print("DB 파일을 찾을 수 없습니다.")
    return None

def cleanup_inactive_sessions():
    """is_active = 0인 세션과 관련 메시지 완전 삭제"""
    db_path = get_db_path()
    if not db_path:
        return
    
    print(f"DB 경로: {db_path}")
    
    with sqlite3.connect(db_path) as conn:
        # 삭제 전 통계
        cursor = conn.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 0")
        inactive_sessions = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT COUNT(*) FROM messages 
            WHERE session_id IN (SELECT id FROM sessions WHERE is_active = 0)
        """)
        orphaned_messages = cursor.fetchone()[0]
        
        print(f"삭제 대상: 비활성 세션 {inactive_sessions}개, 관련 메시지 {orphaned_messages}개")
        
        if inactive_sessions == 0:
            print("삭제할 비활성 세션이 없습니다.")
            return
        
        # 확인
        response = input("정말 삭제하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("취소되었습니다.")
            return
        
        # 메시지 먼저 삭제
        cursor = conn.execute("""
            DELETE FROM messages 
            WHERE session_id IN (SELECT id FROM sessions WHERE is_active = 0)
        """)
        deleted_messages = cursor.rowcount
        
        # 세션 삭제
        cursor = conn.execute("DELETE FROM sessions WHERE is_active = 0")
        deleted_sessions = cursor.rowcount
        
        conn.commit()
        
        print(f"삭제 완료: 세션 {deleted_sessions}개, 메시지 {deleted_messages}개")
        
        # VACUUM으로 DB 최적화
        print("DB 최적화 중...")
        conn.execute("VACUUM")
        print("DB 최적화 완료")

if __name__ == "__main__":
    cleanup_inactive_sessions()