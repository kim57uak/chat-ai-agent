#!/usr/bin/env python3
"""
기존 데이터를 암호화된 데이터베이스로 마이그레이션
"""

import sys
import os
import sqlite3
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.auth.auth_manager import AuthManager
from core.security.encrypted_database import EncryptedDatabase
from core.session.session_database import SessionDatabase


def migrate_data():
    """데이터 마이그레이션 실행"""
    print("🔄 데이터 마이그레이션 시작")
    
    # 인증 매니저 초기화
    auth = AuthManager()
    
    # 로그인 확인
    if not auth.is_logged_in():
        password = input("암호화를 위한 비밀번호를 입력하세요: ")
        if not auth.login(password):
            print("❌ 로그인 실패")
            return False
    
    # 기존 데이터베이스 경로
    old_db_path = Path.home() / ".chat-ai-agent" / "chat_sessions.db"
    if not old_db_path.exists():
        print("ℹ️ 기존 데이터베이스가 없습니다. 새로운 암호화 데이터베이스를 생성합니다.")
        return True
    
    print(f"📂 기존 데이터베이스: {old_db_path}")
    
    # 기존 데이터베이스 연결
    old_db = SessionDatabase(str(old_db_path))
    
    # 새로운 암호화 데이터베이스 생성
    encrypted_db = EncryptedDatabase(auth_manager=auth)
    
    try:
        # 세션 마이그레이션
        print("📋 세션 데이터 마이그레이션...")
        with old_db.get_connection() as old_conn:
            cursor = old_conn.execute('''
                SELECT id, title, topic_category, created_at, last_used_at, 
                       message_count, model_used, is_active 
                FROM sessions 
                WHERE is_active = 1
            ''')
            
            sessions = cursor.fetchall()
            session_map = {}  # old_id -> new_id 매핑
            
            for session in sessions:
                try:
                    new_session_id = encrypted_db.create_session(
                        title=session['title'] or 'Untitled',
                        topic_category=session['topic_category'],
                        model_used=session['model_used']
                    )
                    session_map[session['id']] = new_session_id
                    print(f"  ✅ 세션 {session['id']} -> {new_session_id}: {session['title']}")
                except Exception as e:
                    print(f"  ❌ 세션 {session['id']} 마이그레이션 실패: {e}")
        
        # 메시지 마이그레이션
        print("💬 메시지 데이터 마이그레이션...")
        with old_db.get_connection() as old_conn:
            for old_session_id, new_session_id in session_map.items():
                cursor = old_conn.execute('''
                    SELECT role, content, content_html, timestamp, token_count, tool_calls
                    FROM messages 
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                ''', (old_session_id,))
                
                messages = cursor.fetchall()
                for message in messages:
                    try:
                        encrypted_db.add_message(
                            session_id=new_session_id,
                            role=message['role'],
                            content=message['content'] or '',
                            content_html=message['content_html'],
                            token_count=message['token_count'] or 0,
                            tool_calls=message['tool_calls']
                        )
                    except Exception as e:
                        print(f"  ❌ 메시지 마이그레이션 실패: {e}")
                
                print(f"  ✅ 세션 {new_session_id}: {len(messages)}개 메시지 마이그레이션")
        
        # 통계 출력
        stats = encrypted_db.get_encryption_stats()
        print(f"\n📊 마이그레이션 완료:")
        print(f"  - 세션: {sum(stats['session_stats'].values())}개")
        print(f"  - 메시지: {sum(stats['message_stats'].values())}개")
        print(f"  - 암호화 버전: {stats['current_version']}")
        
        # 기존 데이터베이스 백업
        backup_path = old_db_path.with_suffix('.db.backup')
        import shutil
        shutil.copy2(old_db_path, backup_path)
        print(f"💾 기존 데이터베이스 백업: {backup_path}")
        
        print("🎉 마이그레이션 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        return False


def test_encrypted_database():
    """암호화된 데이터베이스 테스트"""
    print("\n🧪 암호화된 데이터베이스 테스트")
    
    # 인증 매니저 초기화
    auth = AuthManager()
    
    if not auth.is_logged_in():
        password = input("테스트를 위한 비밀번호를 입력하세요: ")
        if not auth.login(password):
            print("❌ 로그인 실패")
            return False
    
    # 암호화된 데이터베이스 생성
    db = EncryptedDatabase(auth_manager=auth)
    
    try:
        # 테스트 세션 생성
        session_id = db.create_session(
            title="테스트 세션",
            topic_category="테스트",
            model_used="gpt-4"
        )
        print(f"✅ 테스트 세션 생성: {session_id}")
        
        # 테스트 메시지 추가
        message_id = db.add_message(
            session_id=session_id,
            role="user",
            content="안녕하세요! 이것은 암호화된 메시지입니다.",
            token_count=10
        )
        print(f"✅ 테스트 메시지 추가: {message_id}")
        
        # 데이터 조회
        session = db.get_session(session_id)
        print(f"✅ 세션 조회: {session['title']}")
        
        messages = db.get_messages(session_id)
        print(f"✅ 메시지 조회: {messages[0]['content']}")
        
        # 통계 조회
        stats = db.get_encryption_stats()
        print(f"✅ 암호화 통계: {stats}")
        
        print("🎉 암호화된 데이터베이스 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔐 Chat AI Agent 데이터 마이그레이션")
    print("=" * 60)
    
    # 테스트 실행
    if test_encrypted_database():
        print("\n" + "=" * 60)
        
        # 마이그레이션 실행 여부 확인
        response = input("기존 데이터를 마이그레이션하시겠습니까? (y/N): ")
        if response.lower() == 'y':
            migrate_data()
        else:
            print("마이그레이션을 건너뜁니다.")
    else:
        print("❌ 테스트 실패로 마이그레이션을 중단합니다.")
        sys.exit(1)