#!/usr/bin/env python3
"""
기존 DB에 새 인덱스 추가 스크립트
"""

import sqlite3
from pathlib import Path

def get_db_path():
    """DB 경로 찾기"""
    possible_paths = [
        Path.home() / ".chat-ai-agent" / "chat_sessions.db",
        Path.home() / "AppData" / "Local" / "ChatAIAgent" / "chat_sessions.db",
        Path.cwd() / "chat_sessions.db",
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    return None

def add_indexes():
    """새 인덱스 추가"""
    db_path = get_db_path()
    if not db_path:
        print("DB 파일을 찾을 수 없습니다.")
        return
    
    print(f"DB 경로: {db_path}")
    
    with sqlite3.connect(db_path) as conn:
        # 새 인덱스들 추가
        new_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_title ON sessions(title)",
            "CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role)",
            "CREATE INDEX IF NOT EXISTS idx_messages_content ON messages(content)"
        ]
        
        print("새 인덱스 추가 중...")
        for sql in new_indexes:
            conn.execute(sql)
            print(f"✓ {sql.split('ON')[1].strip()}")
        
        conn.commit()
        
        # 전체 인덱스 확인
        cursor = conn.execute("""
            SELECT COUNT(*) FROM sqlite_master 
            WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
        """)
        total_indexes = cursor.fetchone()[0]
        
        print(f"\n인덱스 추가 완료! 총 {total_indexes}개 인덱스")

if __name__ == "__main__":
    add_indexes()