#!/usr/bin/env python3
"""
간단한 데이터 마이그레이션 스크립트
"""

import sys
import sqlite3
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.auth.auth_manager import AuthManager
from core.security.encrypted_database import EncryptedDatabase

def main():
    # 경로 설정
    old_db = "/Users/dolpaks/Downloads/ai_file_folder/config/db/chat_sessions.db"
    new_db = "/Users/dolpaks/Downloads/ai_file_folder/config/db/chat_sessions_encrypted.db"
    
    print(f"기존 DB: {old_db}")
    print(f"새 DB: {new_db}")
    
    # 인증 관리자 초기화
    auth_manager = AuthManager()
    if not auth_manager.login("Gjwns74103!"):
        print("인증 실패")
        return 1
    
    print("인증 성공")
    
    # 암호화된 DB 초기화
    encrypted_db = EncryptedDatabase(new_db, auth_manager)
    
    # 기존 DB에서 데이터 읽기
    with sqlite3.connect(old_db) as old_conn:
        old_conn.row_factory = sqlite3.Row
        
        # 세션 마이그레이션
        print("세션 마이그레이션 시작...")
        cursor = old_conn.execute("SELECT * FROM sessions WHERE is_active = 1 ORDER BY id")
        session_mapping = {}
        
        for row in cursor.fetchall():
            try:
                new_session_id = encrypted_db.create_session(
                    title=row['title'] or '',
                    topic_category=row['topic_category'],
                    model_used=row['model_used']
                )
                session_mapping[row['id']] = new_session_id
                print(f"세션 {row['id']} -> {new_session_id}: {row['title']}")
                
                # 메타데이터 업데이트
                with sqlite3.connect(new_db) as new_conn:
                    new_conn.execute("""
                        UPDATE sessions 
                        SET created_at = ?, last_used_at = ?, message_count = ?
                        WHERE id = ?
                    """, (row['created_at'], row['last_used_at'], 
                          row['message_count'], new_session_id))
                    new_conn.commit()
                    
            except Exception as e:
                print(f"세션 {row['id']} 마이그레이션 실패: {e}")
        
        print(f"세션 마이그레이션 완료: {len(session_mapping)}개")
        
        # 메시지 마이그레이션
        print("메시지 마이그레이션 시작...")
        cursor = old_conn.execute("SELECT * FROM messages ORDER BY session_id, timestamp")
        message_count = 0
        
        for row in cursor.fetchall():
            try:
                old_session_id = row['session_id']
                if old_session_id not in session_mapping:
                    continue
                
                new_session_id = session_mapping[old_session_id]
                
                message_id = encrypted_db.add_message(
                    session_id=new_session_id,
                    role=row['role'],
                    content=row['content'] or '',
                    content_html=row['content_html'],
                    token_count=row['token_count'] or 0,
                    tool_calls=row['tool_calls']
                )
                
                # 타임스탬프 업데이트
                with sqlite3.connect(new_db) as new_conn:
                    new_conn.execute("""
                        UPDATE messages SET timestamp = ? WHERE id = ?
                    """, (row['timestamp'], message_id))
                    new_conn.commit()
                
                message_count += 1
                if message_count % 50 == 0:
                    print(f"메시지 {message_count}개 마이그레이션 완료...")
                    
            except Exception as e:
                print(f"메시지 {row['id']} 마이그레이션 실패: {e}")
        
        print(f"메시지 마이그레이션 완료: {message_count}개")
    
    # 검증
    print("\n=== 마이그레이션 검증 ===")
    sessions = encrypted_db.get_sessions(100)
    print(f"암호화된 DB 세션 수: {len(sessions)}")
    
    if sessions:
        sample_session = sessions[0]
        print(f"샘플 세션: {sample_session['title']}")
        
        messages = encrypted_db.get_messages(sample_session['id'], 5)
        print(f"샘플 메시지 수: {len(messages)}")
        
        if messages:
            print(f"첫 메시지: {messages[0]['content'][:50]}...")
    
    print("✅ 마이그레이션 완료!")
    return 0

if __name__ == "__main__":
    sys.exit(main())