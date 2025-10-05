#!/usr/bin/env python3
"""
DB 인덱스 확인 스크립트
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

def check_indexes():
    """현재 DB의 인덱스 확인"""
    db_path = get_db_path()
    if not db_path:
        print("DB 파일을 찾을 수 없습니다.")
        return
    
    print(f"DB 경로: {db_path}")
    
    with sqlite3.connect(db_path) as conn:
        # 모든 인덱스 조회
        cursor = conn.execute("""
            SELECT name, tbl_name, sql 
            FROM sqlite_master 
            WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
            ORDER BY tbl_name, name
        """)
        
        indexes = cursor.fetchall()
        
        print(f"\n현재 설정된 인덱스: {len(indexes)}개")
        print("-" * 60)
        
        for name, table, sql in indexes:
            print(f"테이블: {table}")
            print(f"인덱스: {name}")
            print(f"SQL: {sql}")
            print("-" * 60)

if __name__ == "__main__":
    check_indexes()