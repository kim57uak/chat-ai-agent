#!/usr/bin/env python3
"""
Session Title Migration Script
암호화된 세션 제목을 평문으로 마이그레이션
"""

import sqlite3
import sys
from pathlib import Path
from core.security.encrypted_database import EncryptedDatabase
from core.auth.auth_manager import AuthManager

def migrate_session_titles(custom_db_path=None):
    """암호화된 세션 제목을 평문으로 마이그레이션 (in-place)"""
    print("🔄 세션 제목 마이그레이션 시작...")
    
    try:
        auth_manager = AuthManager()
        
        if not auth_manager.is_logged_in():
            print("⚠️  인증이 필요합니다. 비밀번호를 입력하세요:")
            password = input("비밀번호: ")
            if not auth_manager.login(password):
                print("❌ 인증 실패")
                return False
        
        # 사용자 지정 경로 또는 기본 경로 사용
        if custom_db_path:
            db_path = Path(custom_db_path) / "chat_sessions_encrypted.db"
            print(f"\n📂 사용자 지정 DB 경로: {db_path}")
            db = EncryptedDatabase(db_path=str(db_path), auth_manager=auth_manager)
        else:
            db = EncryptedDatabase(auth_manager=auth_manager)
        
        print(f"\n📂 DB 경로: {db.db_path}")
        print(f"   DB 파일 존재: {'✅' if db.db_path.exists() else '❌'}")
        
        if db.db_path.exists():
            import os
            file_size = os.path.getsize(db.db_path)
            print(f"   DB 파일 크기: {file_size:,} bytes")
        
        with db.get_connection() as conn:
            print("\n📋 테이블 구조 확인 중...")
            cursor = conn.execute("PRAGMA table_info(sessions)")
            columns = {row['name']: row['type'] for row in cursor.fetchall()}
            
            title_type = columns.get('title', 'UNKNOWN')
            print(f"   현재 title 컬럼 타입: {title_type}")
            
            if title_type == 'BLOB':
                print("\n📦 세션 데이터 조회 중...")
                
                # 전체 세션 수 확인
                cursor = conn.execute("SELECT COUNT(*) as total FROM sessions")
                total_count = cursor.fetchone()['total']
                print(f"   전체 세션 수: {total_count}개")
                
                if total_count == 0:
                    print("\n⚠️  세션이 없습니다. 마이그레이션할 데이터가 없습니다.")
                    print("\n💡 힌트: 다른 DB 파일을 사용 중일 수 있습니다.")
                    print("   앱 설정에서 'user_config_path.json'을 확인하세요.")
                    return True
                
                cursor = conn.execute("SELECT id, title FROM sessions")
                sessions = cursor.fetchall()
                
                print(f"\n📦 BLOB 데이터 복호화 중... ({len(sessions)}개 세션)\n")
                
                migrated_count = 0
                skipped_count = 0
                error_count = 0
                
                for session in sessions:
                    try:
                        title_data = session['title']
                        
                        # 데이터 타입 확인
                        if title_data is None:
                            print(f"   ⏭️  세션 {session['id']}: title이 NULL")
                            skipped_count += 1
                            continue
                        
                        if isinstance(title_data, bytes):
                            decrypted_title = db._decrypt_data(title_data)
                            
                            # 동일 행 업데이트
                            conn.execute(
                                "UPDATE sessions SET title = ? WHERE id = ?",
                                (decrypted_title, session['id'])
                            )
                            
                            print(f"   ✅ 세션 {session['id']}: '{decrypted_title[:30]}...'")
                            migrated_count += 1
                        else:
                            print(f"   ⏭️  세션 {session['id']}: 이미 평문 - '{str(title_data)[:30]}...'")
                            skipped_count += 1
                        
                    except Exception as e:
                        print(f"   ⚠️  세션 {session['id']}: 오류 - {e}")
                        error_count += 1
                
                conn.commit()
                
                print(f"\n🎉 마이그레이션 완료!")
                print(f"   ✅ 성공: {migrated_count}개")
                print(f"   ⏭️  건너뜀: {skipped_count}개")
                print(f"   ❌ 실패: {error_count}개")
                
                if migrated_count > 0:
                    print(f"\n💡 팁: 앱을 재시작하면 세션 검색이 정상 작동합니다.")
                else:
                    print(f"\n💡 모든 세션이 이미 평문 상태입니다.")
                
            else:
                print("\n✅ 테이블 구조는 이미 최신 상태입니다.")
                
                # 전체 세션 수 확인
                cursor = conn.execute("SELECT COUNT(*) as total FROM sessions")
                total_count = cursor.fetchone()['total']
                print(f"\n📦 전체 세션 수: {total_count}개")
                
                if total_count > 0:
                    print("\n📦 최근 세션 확인 중...\n")
                    cursor = conn.execute("SELECT id, title FROM sessions WHERE is_active = 1 ORDER BY last_used_at DESC LIMIT 5")
                    sessions = cursor.fetchall()
                    
                    for session in sessions:
                        title = session['title'] or "Untitled"
                        print(f"   세션 {session['id']}: '{title[:50]}...'")
                else:
                    print("\n⚠️  세션이 없습니다.")
            
            return True
            
    except Exception as e:
        print(f"❌ 마이그레이션 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 사용자 지정 경로 확인
    custom_path = None
    if len(sys.argv) > 1:
        custom_path = sys.argv[1]
    else:
        # user_config_path.json에서 경로 확인
        try:
            from utils.config_path import config_path_manager
            user_config = config_path_manager.get_user_config_path()
            if user_config:
                custom_path = str(user_config / "db")
                print(f"📂 설정된 경로 발견: {custom_path}")
        except Exception as e:
            print(f"⚠️  설정 경로 로드 실패: {e}")
    
    success = migrate_session_titles(custom_path)
    sys.exit(0 if success else 1)
