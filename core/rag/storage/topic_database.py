"""
Topic Database
SQLite 기반 토픽 및 문서 메타데이터 관리
"""

import sqlite3
import hashlib
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from core.logging import get_logger

logger = get_logger("topic_database")


class TopicDatabase:
    """토픽 및 문서 메타데이터 관리 데이터베이스"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize topic database
        
        Args:
            db_path: Database path (None for auto-detection)
        """
        if db_path is None:
            db_path = self._get_default_db_path()
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=30.0)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.row_factory = sqlite3.Row
        self._init_database()
        
        logger.info(f"Topic database initialized: {self.db_path}")
    
    def _get_default_db_path(self) -> str:
        """기본 데이터베이스 경로 반환"""
        try:
            from utils.config_path import config_path_manager
            config_dir = config_path_manager.get_user_config_path()
            if config_dir and config_dir.exists():
                db_path = config_dir / "db" / "rag_topics.db"
                db_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Using user-configured path: {db_path}")
                return str(db_path)
        except Exception as e:
            logger.warning(f"Failed to get user config path: {e}")
        
        # 폴백: 홈 디렉토리
        import os
        if os.name == "nt":  # Windows
            data_dir = Path.home() / "AppData" / "Local" / "ChatAIAgent" / "db"
        else:  # macOS, Linux
            data_dir = Path.home() / ".chat-ai-agent" / "db"
        
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = data_dir / "rag_topics.db"
        logger.info(f"Using default path: {db_path}")
        return str(db_path)
    
    def _init_database(self):
        """데이터베이스 테이블 초기화"""
        # Topics 테이블
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                parent_id TEXT,
                description TEXT,
                document_count INTEGER DEFAULT 0,
                is_selected INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        """)
        
        # Documents 테이블
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                topic_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT,
                file_type TEXT,
                file_size INTEGER,
                chunk_count INTEGER DEFAULT 0,
                chunking_strategy TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        """)
        
        # 인덱스 생성
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_topics_parent 
            ON topics(parent_id)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_topic 
            ON documents(topic_id)
        """)
        
        self.conn.commit()
        
        # is_selected 컬럼 추가 (기존 DB 호환)
        try:
            self.conn.execute("ALTER TABLE topics ADD COLUMN is_selected INTEGER DEFAULT 0")
            self.conn.commit()
            logger.info("Added is_selected column to topics table")
        except sqlite3.OperationalError:
            pass
        
        logger.info("Database tables initialized")
    
    # ========== Topic CRUD ==========
    
    def create_topic(self, name: str, parent_id: Optional[str] = None, 
                    description: str = "") -> str:
        """
        토픽 생성
        
        Args:
            name: 토픽 이름
            parent_id: 부모 토픽 ID
            description: 설명
            
        Returns:
            생성된 토픽 ID
        """
        topic_id = self._generate_id(name)
        
        self.conn.execute("""
            INSERT INTO topics (id, name, parent_id, description)
            VALUES (?, ?, ?, ?)
        """, (topic_id, name, parent_id, description))
        
        self.conn.commit()
        logger.info(f"Created topic: {name} ({topic_id})")
        return topic_id
    
    def get_topic(self, topic_id: str) -> Optional[Dict]:
        """토픽 조회"""
        cursor = self.conn.execute("""
            SELECT * FROM topics WHERE id = ?
        """, (topic_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_topics(self) -> List[Dict]:
        """모든 토픽 조회"""
        cursor = self.conn.execute("""
            SELECT * FROM topics ORDER BY name
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_selected_topic(self) -> Optional[Dict]:
        """선택된 토픽 조회"""
        cursor = self.conn.execute("""
            SELECT * FROM topics WHERE is_selected = 1 LIMIT 1
        """)
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def set_selected_topic(self, topic_id: str) -> bool:
        """토픽 선택"""
        try:
            # 모든 토픽 선택 해제
            self.conn.execute("UPDATE topics SET is_selected = 0")
            
            # 해당 토픽 선택
            self.conn.execute("""
                UPDATE topics SET is_selected = 1 WHERE id = ?
            """, (topic_id,))
            
            self.conn.commit()
            logger.info(f"Selected topic: {topic_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to select topic: {e}")
            return False
    
    def clear_selected_topic(self) -> bool:
        """토픽 선택 해제"""
        try:
            self.conn.execute("UPDATE topics SET is_selected = 0")
            self.conn.commit()
            logger.info("Cleared topic selection")
            return True
        except Exception as e:
            logger.error(f"Failed to clear topic selection: {e}")
            return False
    
    def update_topic(self, topic_id: str, name: Optional[str] = None,
                    description: Optional[str] = None) -> bool:
        """토픽 수정"""
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if not updates:
            return False
        
        params.append(topic_id)
        query = f"UPDATE topics SET {', '.join(updates)} WHERE id = ?"
        
        self.conn.execute(query, params)
        self.conn.commit()
        logger.info(f"Updated topic: {topic_id}")
        return True
    
    def delete_topic(self, topic_id: str) -> List[str]:
        """
        토픽 삭제 (계층적 삭제)
        
        Returns:
            삭제된 문서 ID 리스트
        """
        # 1. 해당 토픽의 모든 문서 조회
        documents = self.get_documents_by_topic(topic_id)
        doc_ids = [doc["id"] for doc in documents]
        
        # 2. 토픽 삭제 (CASCADE로 문서도 자동 삭제)
        self.conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
        self.conn.commit()
        
        logger.info(f"Deleted topic: {topic_id} ({len(doc_ids)} documents)")
        return doc_ids
    
    def increment_document_count(self, topic_id: str):
        """토픽 문서 수 증가"""
        self.conn.execute("""
            UPDATE topics SET document_count = document_count + 1
            WHERE id = ?
        """, (topic_id,))
        self.conn.commit()
    
    def decrement_document_count(self, topic_id: str):
        """토픽 문서 수 감소"""
        self.conn.execute("""
            UPDATE topics SET document_count = document_count - 1
            WHERE id = ?
        """, (topic_id,))
        self.conn.commit()
    
    # ========== Document CRUD ==========
    
    def create_document(self, topic_id: str, filename: str, file_path: str,
                       file_type: str, file_size: int = 0,
                       chunking_strategy: str = "sliding_window") -> str:
        """
        문서 생성
        
        Returns:
            생성된 문서 ID
        """
        doc_id = self._generate_id(f"{filename}_{topic_id}")
        
        self.conn.execute("""
            INSERT INTO documents 
            (id, topic_id, filename, file_path, file_type, file_size, chunking_strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, topic_id, filename, file_path, file_type, file_size, chunking_strategy))
        
        # 토픽 문서 수 증가
        self.increment_document_count(topic_id)
        
        self.conn.commit()
        logger.info(f"Created document: {filename} ({doc_id})")
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """문서 조회"""
        cursor = self.conn.execute("""
            SELECT * FROM documents WHERE id = ?
        """, (doc_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_documents_by_topic(self, topic_id: str) -> List[Dict]:
        """토픽별 문서 목록"""
        cursor = self.conn.execute("""
            SELECT * FROM documents 
            WHERE topic_id = ?
            ORDER BY upload_date DESC
        """, (topic_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_document_chunks(self, doc_id: str, chunk_count: int):
        """문서 청크 수 업데이트"""
        self.conn.execute("""
            UPDATE documents SET chunk_count = ? WHERE id = ?
        """, (chunk_count, doc_id))
        self.conn.commit()
    
    def delete_document(self, doc_id: str) -> Optional[str]:
        """
        문서 삭제
        
        Returns:
            토픽 ID (문서 수 감소용)
        """
        # 토픽 ID 조회
        doc = self.get_document(doc_id)
        if not doc:
            return None
        
        topic_id = doc["topic_id"]
        
        # 문서 삭제
        self.conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        
        # 토픽 문서 수 감소
        self.decrement_document_count(topic_id)
        
        self.conn.commit()
        logger.info(f"Deleted document: {doc_id}")
        return topic_id
    
    # ========== Utility ==========
    
    def _generate_id(self, text: str) -> str:
        """ID 생성"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{text}_{timestamp}".encode()).hexdigest()[:16]
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
