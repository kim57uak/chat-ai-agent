"""
Session Database Handler
SQLite 데이터베이스 관리 클래스
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SessionDatabase:
    """SQLite 데이터베이스 핸들러"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = self._get_default_db_path()
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _get_default_db_path(self) -> str:
        """기본 데이터베이스 경로 반환"""
        import os
        if os.name == 'nt':  # Windows
            data_dir = Path.home() / "AppData" / "Local" / "ChatAIAgent"
        else:  # macOS, Linux
            data_dir = Path.home() / ".chat-ai-agent"
        
        data_dir.mkdir(parents=True, exist_ok=True)
        return str(data_dir / "chat_sessions.db")
    
    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            # WAL 모드로 성능 향상
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            
            # 세션 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    topic_category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    model_used TEXT,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # 메시지 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_html TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    token_count INTEGER DEFAULT 0,
                    tool_calls TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            ''')
            
            # 인덱스 생성
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_last_used ON sessions(last_used_at DESC)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp)')
            
            conn.commit()
            logger.info(f"세션 데이터베이스 초기화 완료: {self.db_path}")
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """쿼리 실행"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn.execute(query, params)
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """업데이트 쿼리 실행"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """삽입 쿼리 실행"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn