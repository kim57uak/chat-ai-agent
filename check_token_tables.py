#!/usr/bin/env python3
"""
토큰 추적 테이블 확인 및 생성 스크립트
"""

import sqlite3
import sys
from pathlib import Path

def check_and_create_tables(db_path: str):
    """토큰 추적 테이블 확인 및 생성"""
    
    print(f"📊 데이터베이스 확인: {db_path}")
    
    if not Path(db_path).exists():
        print(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 기존 테이블 확인
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"\n✅ 기존 테이블 ({len(existing_tables)}개):")
        for table in existing_tables:
            print(f"   - {table}")
        
        # 토큰 추적 테이블 확인
        required_tables = [
            'token_usage',
            'session_token_summary',
            'global_token_stats',
            'migration_history'
        ]
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"\n⚠️  누락된 토큰 추적 테이블 ({len(missing_tables)}개):")
            for table in missing_tables:
                print(f"   - {table}")
            
            # 마이그레이션 실행
            print("\n🔧 마이그레이션 실행 중...")
            from core.token_tracking.migrations.migration_runner import run_token_tracking_migrations
            
            success = run_token_tracking_migrations(db_path)
            
            if success:
                print("✅ 마이그레이션 완료!")
                
                # 다시 확인
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN (?, ?, ?, ?)
                """, required_tables)
                
                created_tables = [row[0] for row in cursor.fetchall()]
                print(f"\n✅ 생성된 테이블 ({len(created_tables)}개):")
                for table in created_tables:
                    # 테이블 구조 확인
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    print(f"\n   📋 {table} ({len(columns)} 컬럼):")
                    for col in columns:
                        col_id, name, col_type, not_null, default, pk = col
                        pk_str = " [PK]" if pk else ""
                        not_null_str = " NOT NULL" if not_null else ""
                        print(f"      - {name}: {col_type}{not_null_str}{pk_str}")
                
                return True
            else:
                print("❌ 마이그레이션 실패!")
                return False
        else:
            print("\n✅ 모든 토큰 추적 테이블이 존재합니다!")
            
            # 각 테이블의 레코드 수 확인
            print("\n📊 테이블별 레코드 수:")
            for table in required_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   - {table}: {count:,}개")
            
            return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()


if __name__ == "__main__":
    # 데이터베이스 경로 확인
    try:
        from core.security.secure_path_manager import secure_path_manager
        db_path = secure_path_manager.get_database_path()
    except Exception as e:
        print(f"❌ 데이터베이스 경로를 가져올 수 없습니다: {e}")
        print("\n💡 수동으로 경로를 지정하세요:")
        print("   python check_token_tables.py /path/to/database.db")
        
        if len(sys.argv) > 1:
            db_path = sys.argv[1]
        else:
            sys.exit(1)
    
    print("=" * 60)
    print("🔍 토큰 추적 테이블 확인 및 생성")
    print("=" * 60)
    
    success = check_and_create_tables(db_path)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 완료!")
    else:
        print("❌ 실패!")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
