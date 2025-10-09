"""
from core.logging import get_logger

logger = get_logger("encrypted_database")
Encrypted Database Handler
암호화된 데이터베이스 관리 클래스
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from core.logging import get_logger

from ..auth.auth_manager import AuthManager
from .memory_security import memory_security
from .security_logger import security_logger

logger = get_logger("encrypted_database")


class EncryptedDatabase:
    """암호화된 데이터베이스 핸들러"""

    CURRENT_ENCRYPTION_VERSION = 1

    def __init__(
        self, db_path: Optional[str] = None, auth_manager: Optional[AuthManager] = None
    ):
        if db_path is None:
            db_path = self._get_default_db_path()

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.auth_manager = auth_manager
        self._init_database()

    def _get_default_db_path(self) -> str:
        """기본 데이터베이스 경로 반환"""
        try:
            # 기존 ConfigPathManager와 연동
            from utils.config_path import config_path_manager

            # 사용자 설정 경로가 있으면 사용 (db 서브폴더에 저장)
            user_config_path = config_path_manager.get_user_config_path()
            if user_config_path and user_config_path.exists():
                db_path = user_config_path / "db" / "chat_sessions_encrypted.db"
                db_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Using user-configured DB path: {db_path}")
                return str(db_path)
            else:
                logger.info("No user config path set, using default")
        except Exception as e:
            logger.warning(f"Failed to get user config path: {e}")

        # 폴백: 기본 외부 경로 (db 서브폴더 사용)
        import os

        if os.name == "nt":  # Windows
            data_dir = Path.home() / "AppData" / "Local" / "ChatAIAgent" / "db"
        else:  # macOS, Linux
            data_dir = Path.home() / ".chat-ai-agent" / "db"

        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using default DB path: {data_dir / 'chat_sessions_encrypted.db'}")
        return str(data_dir / "chat_sessions_encrypted.db")

    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            # WAL 모드로 성능 향상
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")

            # 암호화 키 버전 관리 테이블
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS encryption_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            """
            )

            # 세션 테이블 (title은 평문, 나머지는 암호화)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    topic_category BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    model_used BLOB,
                    is_active INTEGER DEFAULT 1,
                    encryption_version INTEGER DEFAULT 1
                )
            """
            )

            # 메시지 테이블 (암호화 버전 추가)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content BLOB NOT NULL,
                    content_html BLOB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    token_count INTEGER DEFAULT 0,
                    tool_calls BLOB,
                    encryption_version INTEGER DEFAULT 1,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """
            )

            # 인덱스 생성
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_last_used ON sessions(last_used_at DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_encryption_version ON encryption_keys(version)"
            )

            # 현재 암호화 버전 등록
            conn.execute(
                """
                INSERT OR IGNORE INTO encryption_keys (version, is_active) 
                VALUES (?, 1)
            """,
                (self.CURRENT_ENCRYPTION_VERSION,),
            )

            conn.commit()
            logger.info(f"암호화된 데이터베이스 초기화 완료: {self.db_path}")

    def _encrypt_data(self, data: str) -> bytes:
        """데이터 암호화"""
        if not self.auth_manager or not self.auth_manager.is_logged_in():
            security_logger.log_security_violation(
                "encryption_without_auth", "Encryption attempted without authentication"
            )
            raise RuntimeError("Authentication required for encryption")

        try:
            result = self.auth_manager.encrypt_data(data)
            security_logger.log_encryption_event("encrypt", True)
            return result
        except Exception as e:
            security_logger.log_encryption_event("encrypt", False, str(e))
            raise

    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """데이터 복호화"""
        if not self.auth_manager or not self.auth_manager.is_logged_in():
            security_logger.log_security_violation(
                "decryption_without_auth", "Decryption attempted without authentication"
            )
            raise RuntimeError("Authentication required for decryption")

        try:
            result = self.auth_manager.decrypt_data(encrypted_data)
            security_logger.log_encryption_event("decrypt", True)
            return result
        except Exception as e:
            security_logger.log_encryption_event("decrypt", False, str(e))
            # 민감한 데이터 메모리에서 제거
            memory_security.clear_sensitive_data("encrypted_data", "result")
            raise

    def create_session(
        self, title: str, topic_category: str = None, model_used: str = None
    ) -> int:
        """새 세션 생성 (title은 평문 저장)"""
        with sqlite3.connect(self.db_path) as conn:
            # title은 평문, 나머지는 암호화
            topic_category_encrypted = (
                self._encrypt_data(topic_category) if topic_category else None
            )
            model_used_encrypted = (
                self._encrypt_data(model_used) if model_used else None
            )

            cursor = conn.execute(
                """
                INSERT INTO sessions (
                    title, topic_category, model_used, 
                    encryption_version
                ) VALUES (?, ?, ?, ?)
            """,
                (
                    title,
                    topic_category_encrypted,
                    model_used_encrypted,
                    self.CURRENT_ENCRYPTION_VERSION,
                ),
            )

            conn.commit()
            return cursor.lastrowid

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """세션 조회 (실제 메시지 수 조회)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT s.*, 
                       (SELECT COUNT(*) FROM messages WHERE session_id = s.id) as actual_message_count
                FROM sessions s
                WHERE s.id = ? AND s.is_active = 1
            """,
                (session_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # 데이터 복호화 (title은 평문)
            try:
                return {
                    "id": row["id"],
                    "title": row["title"] if row["title"] else "",
                    "topic_category": (
                        self._decrypt_data(row["topic_category"])
                        if row["topic_category"]
                        else None
                    ),
                    "created_at": row["created_at"],
                    "last_used_at": row["last_used_at"],
                    "message_count": row["actual_message_count"],
                    "model_used": (
                        self._decrypt_data(row["model_used"])
                        if row["model_used"]
                        else None
                    ),
                    "encryption_version": row["encryption_version"],
                }
            except Exception as e:
                logger.warning(f"Failed to decrypt session {session_id}: {e}")
                return None

    def get_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """세션 목록 조회 (실제 메시지 수 조회)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT s.*,
                       (SELECT COUNT(*) FROM messages WHERE session_id = s.id) as actual_message_count
                FROM sessions s
                WHERE s.is_active = 1
                ORDER BY s.last_used_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            sessions = []
            for row in cursor.fetchall():
                try:
                    session = {
                        "id": row["id"],
                        "title": row["title"] if row["title"] else "",
                        "topic_category": (
                            self._decrypt_data(row["topic_category"])
                            if row["topic_category"]
                            else None
                        ),
                        "created_at": row["created_at"],
                        "last_used_at": row["last_used_at"],
                        "message_count": row["actual_message_count"],
                        "model_used": (
                            self._decrypt_data(row["model_used"])
                            if row["model_used"]
                            else None
                        ),
                        "encryption_version": row["encryption_version"],
                    }
                    sessions.append(session)
                except Exception as e:
                    logger.warning(f"Failed to decrypt session {row['id']}: {e}")
                    continue

            return sessions

    def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        content_html: str = None,
        token_count: int = 0,
        tool_calls: str = None,
    ) -> int:
        """메시지 추가"""
        with sqlite3.connect(self.db_path) as conn:
            # 데이터 암호화
            content_encrypted = self._encrypt_data(content)
            content_html_encrypted = (
                self._encrypt_data(content_html) if content_html else None
            )
            tool_calls_encrypted = (
                self._encrypt_data(tool_calls) if tool_calls else None
            )

            cursor = conn.execute(
                """
                INSERT INTO messages (
                    session_id, role, content, content_html,
                    token_count, tool_calls, encryption_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    role,
                    content_encrypted,
                    content_html_encrypted,
                    token_count,
                    tool_calls_encrypted,
                    self.CURRENT_ENCRYPTION_VERSION,
                ),
            )

            # 세션의 메시지 카운트 업데이트
            conn.execute(
                """
                UPDATE sessions 
                SET message_count = message_count + 1, last_used_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (session_id,),
            )

            conn.commit()
            return cursor.lastrowid

    def get_messages(self, session_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """메시지 목록 조회 (최근 N개를 가져와서 user -> ai 순서로 정렬)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # 최근 메시지 N개를 가져온 후 역순 정렬
            cursor = conn.execute(
                """
                SELECT * FROM (
                    SELECT * FROM messages 
                    WHERE session_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                ) ORDER BY timestamp ASC
            """,
                (session_id, limit, offset),
            )

            messages = []
            for row in cursor.fetchall():
                try:
                    message = {
                        "id": row["id"],
                        "session_id": row["session_id"],
                        "role": row["role"],
                        "content": self._decrypt_data(row["content"]),
                        "content_html": (
                            self._decrypt_data(row["content_html"])
                            if row["content_html"]
                            else None
                        ),
                        "timestamp": row["timestamp"],
                        "token_count": row["token_count"],
                        "tool_calls": (
                            self._decrypt_data(row["tool_calls"])
                            if row["tool_calls"]
                            else None
                        ),
                        "encryption_version": row["encryption_version"],
                    }
                    messages.append(message)
                    logger.debug(f"DB] Message {row['id']}: role={row['role']}, timestamp={row['timestamp'][:19]}")
                except Exception as e:
                    logger.warning(f"Failed to decrypt message {row['id']}: {e}")
                    continue
            
            logger.debug(f"DB] Total {len(messages)} messages loaded for session {session_id}")
            return messages

    def delete_session(self, session_id: int) -> bool:
        """세션 삭제 (소프트 삭제)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE sessions SET is_active = 0 WHERE id = ?
            """,
                (session_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_encryption_stats(self) -> Dict[str, Any]:
        """암호화 통계 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # 세션 통계
            cursor = conn.execute(
                """
                SELECT encryption_version, COUNT(*) as count 
                FROM sessions 
                WHERE is_active = 1 
                GROUP BY encryption_version
            """
            )
            session_stats = {
                row["encryption_version"]: row["count"] for row in cursor.fetchall()
            }

            # 메시지 통계
            cursor = conn.execute(
                """
                SELECT encryption_version, COUNT(*) as count 
                FROM messages 
                GROUP BY encryption_version
            """
            )
            message_stats = {
                row["encryption_version"]: row["count"] for row in cursor.fetchall()
            }

            return {
                "current_version": self.CURRENT_ENCRYPTION_VERSION,
                "session_stats": session_stats,
                "message_stats": message_stats,
            }

    def get_connection(self):
        """데이터베이스 연결 반환 (컨텍스트 매니저)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """UPDATE/DELETE 쿼리 실행 후 영향받은 행 수 반환"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
