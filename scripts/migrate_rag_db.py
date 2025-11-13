#!/usr/bin/env python3
"""
RAG Database Migration Script
기존 데이터베이스에 embedding_model 컬럼 추가
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path: str):
    """데이터베이스 마이그레이션"""
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 현재 컬럼 확인
        cursor.execute("PRAGMA table_info(documents)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "embedding_model" not in columns:
            print("Adding embedding_model column...")
            cursor.execute("ALTER TABLE documents ADD COLUMN embedding_model TEXT")
            
            # 기존 문서에 기본 모델 설정
            cursor.execute("UPDATE documents SET embedding_model = 'dragonkue-KoEn-E5-Tiny' WHERE embedding_model IS NULL")
            
            # 인덱스 생성
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_model ON documents(embedding_model)")
            
            conn.commit()
            print("✅ Migration completed successfully!")
        else:
            print("✅ Database already up to date!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

def find_rag_databases():
    """RAG 데이터베이스 파일 찾기"""
    possible_paths = []
    
    # 사용자 설정 경로
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utils.config_path import config_path_manager
        config_dir = config_path_manager.get_user_config_path()
        if config_dir and config_dir.exists():
            db_path = config_dir / "db" / "rag_topics.db"
            if db_path.exists():
                possible_paths.append(str(db_path))
    except Exception:
        pass
    
    # 기본 경로들
    import os
    if os.name == "nt":
        default_path = Path.home() / "AppData" / "Local" / "ChatAIAgent" / "db" / "rag_topics.db"
    else:
        default_path = Path.home() / ".chat-ai-agent" / "db" / "rag_topics.db"
    
    if default_path.exists():
        possible_paths.append(str(default_path))
    
    return possible_paths

if __name__ == "__main__":
    print("🔧 RAG Database Migration Tool")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        # 직접 경로 지정
        db_path = sys.argv[1]
        if Path(db_path).exists():
            migrate_database(db_path)
        else:
            print(f"❌ Database not found: {db_path}")
    else:
        # 자동 탐지
        databases = find_rag_databases()
        
        if not databases:
            print("❌ No RAG databases found!")
            print("Usage: python migrate_rag_db.py [database_path]")
            sys.exit(1)
        
        print(f"Found {len(databases)} database(s):")
        for db_path in databases:
            print(f"  📁 {db_path}")
            migrate_database(db_path)
            print()
    
    print("🎉 Migration process completed!")