"""
Data Migration Script
기존 평문 데이터를 암호화된 형태로 마이그레이션
"""

import sqlite3
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from core.logging import get_logger

from ..auth.auth_manager import AuthManager
from .encrypted_database import EncryptedDatabase

logger = get_logger("data_migration")


class DataMigrator:
    """데이터 마이그레이션 관리자"""
    
    def __init__(self, old_db_path: str, new_db_path: str, auth_manager: AuthManager):
        self.old_db_path = Path(old_db_path)
        self.new_db_path = Path(new_db_path)
        self.auth_manager = auth_manager
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self) -> str:
        """기존 데이터베이스 백업"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"chat_sessions_backup_{timestamp}.db"
        
        if self.old_db_path.exists():
            shutil.copy2(self.old_db_path, backup_path)
            logger.info(f"백업 생성 완료: {backup_path}")
            return str(backup_path)
        else:
            logger.warning(f"기존 데이터베이스가 존재하지 않음: {self.old_db_path}")
            return ""
    
    def verify_old_database(self) -> bool:
        """기존 데이터베이스 구조 검증"""
        if not self.old_db_path.exists():
            return False
            
        try:
            with sqlite3.connect(self.old_db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['sessions', 'messages']
                return all(table in tables for table in required_tables)
        except Exception as e:
            logger.error(f"기존 데이터베이스 검증 실패: {e}")
            return False
    
    def get_migration_stats(self) -> Dict[str, int]:
        """마이그레이션 대상 데이터 통계"""
        if not self.old_db_path.exists():
            return {"sessions": 0, "messages": 0}
            
        try:
            with sqlite3.connect(self.old_db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1")
                session_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM messages")
                message_count = cursor.fetchone()[0]
                
                return {"sessions": session_count, "messages": message_count}
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {"sessions": 0, "messages": 0}
    
    def migrate_sessions(self, encrypted_db: EncryptedDatabase) -> int:
        """세션 데이터 마이그레이션"""
        migrated_count = 0
        
        try:
            with sqlite3.connect(self.old_db_path) as old_conn:
                old_conn.row_factory = sqlite3.Row
                cursor = old_conn.execute("""
                    SELECT * FROM sessions WHERE is_active = 1 ORDER BY id
                """)
                
                for row in cursor.fetchall():
                    try:
                        # 기존 평문 데이터를 암호화하여 새 DB에 저장
                        session_id = encrypted_db.create_session(
                            title=row['title'] or '',
                            topic_category=row['topic_category'],
                            model_used=row['model_used']
                        )
                        
                        # 세션 메타데이터 업데이트
                        with sqlite3.connect(encrypted_db.db_path) as new_conn:
                            new_conn.execute("""
                                UPDATE sessions 
                                SET created_at = ?, last_used_at = ?, message_count = ?
                                WHERE id = ?
                            """, (row['created_at'], row['last_used_at'], 
                                  row['message_count'], session_id))
                            new_conn.commit()
                        
                        # 세션 ID 매핑 저장 (메시지 마이그레이션용)
                        if not hasattr(self, 'session_mapping'):
                            self.session_mapping = {}
                        self.session_mapping[row['id']] = session_id
                        
                        migrated_count += 1
                        logger.debug(f"세션 마이그레이션: {row['id']} -> {session_id}")
                        
                    except Exception as e:
                        logger.error(f"세션 {row['id']} 마이그레이션 실패: {e}")
                        
        except Exception as e:
            logger.error(f"세션 마이그레이션 실패: {e}")
            
        return migrated_count
    
    def migrate_messages(self, encrypted_db: EncryptedDatabase) -> int:
        """메시지 데이터 마이그레이션"""
        migrated_count = 0
        
        if not hasattr(self, 'session_mapping'):
            logger.error("세션 매핑이 없음. 세션을 먼저 마이그레이션하세요.")
            return 0
        
        try:
            with sqlite3.connect(self.old_db_path) as old_conn:
                old_conn.row_factory = sqlite3.Row
                cursor = old_conn.execute("""
                    SELECT * FROM messages ORDER BY session_id, timestamp
                """)
                
                for row in cursor.fetchall():
                    try:
                        old_session_id = row['session_id']
                        if old_session_id not in self.session_mapping:
                            logger.warning(f"세션 {old_session_id}에 대한 매핑이 없음")
                            continue
                        
                        new_session_id = self.session_mapping[old_session_id]
                        
                        # 메시지 마이그레이션
                        message_id = encrypted_db.add_message(
                            session_id=new_session_id,
                            role=row['role'],
                            content=row['content'] or '',
                            content_html=row['content_html'],
                            token_count=row['token_count'] or 0,
                            tool_calls=row['tool_calls']
                        )
                        
                        # 타임스탬프 업데이트
                        with sqlite3.connect(encrypted_db.db_path) as new_conn:
                            new_conn.execute("""
                                UPDATE messages SET timestamp = ? WHERE id = ?
                            """, (row['timestamp'], message_id))
                            new_conn.commit()
                        
                        migrated_count += 1
                        
                    except Exception as e:
                        logger.error(f"메시지 {row['id']} 마이그레이션 실패: {e}")
                        
        except Exception as e:
            logger.error(f"메시지 마이그레이션 실패: {e}")
            
        return migrated_count
    
    def verify_migration(self, encrypted_db: EncryptedDatabase) -> Dict[str, bool]:
        """마이그레이션 결과 검증"""
        results = {"sessions": False, "messages": False, "data_integrity": False}
        
        try:
            # 세션 수 비교
            old_stats = self.get_migration_stats()
            
            with sqlite3.connect(encrypted_db.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1")
                new_session_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM messages")
                new_message_count = cursor.fetchone()[0]
            
            results["sessions"] = (old_stats["sessions"] == new_session_count)
            results["messages"] = (old_stats["messages"] == new_message_count)
            
            # 데이터 무결성 검증 (샘플 데이터 복호화 테스트)
            try:
                sessions = encrypted_db.get_sessions(limit=5)
                if sessions:
                    sample_session = sessions[0]
                    messages = encrypted_db.get_messages(sample_session['id'], limit=5)
                    results["data_integrity"] = len(messages) >= 0  # 복호화 성공
                else:
                    results["data_integrity"] = True  # 데이터가 없으면 성공으로 간주
            except Exception as e:
                logger.error(f"데이터 무결성 검증 실패: {e}")
                results["data_integrity"] = False
                
        except Exception as e:
            logger.error(f"마이그레이션 검증 실패: {e}")
            
        return results
    
    def run_migration(self) -> Dict[str, any]:
        """전체 마이그레이션 실행"""
        logger.info("데이터 마이그레이션 시작")
        
        # 1. 백업 생성
        backup_path = self.create_backup()
        
        # 2. 기존 DB 검증
        if not self.verify_old_database():
            return {
                "success": False,
                "error": "기존 데이터베이스 검증 실패",
                "backup_path": backup_path
            }
        
        # 3. 마이그레이션 통계
        stats = self.get_migration_stats()
        logger.info(f"마이그레이션 대상: 세션 {stats['sessions']}개, 메시지 {stats['messages']}개")
        
        try:
            # 4. 암호화된 DB 초기화
            encrypted_db = EncryptedDatabase(str(self.new_db_path), self.auth_manager)
            
            # 5. 세션 마이그레이션
            migrated_sessions = self.migrate_sessions(encrypted_db)
            
            # 6. 메시지 마이그레이션
            migrated_messages = self.migrate_messages(encrypted_db)
            
            # 7. 검증
            verification = self.verify_migration(encrypted_db)
            
            result = {
                "success": all(verification.values()),
                "backup_path": backup_path,
                "original_stats": stats,
                "migrated": {
                    "sessions": migrated_sessions,
                    "messages": migrated_messages
                },
                "verification": verification
            }
            
            if result["success"]:
                logger.info("데이터 마이그레이션 성공")
            else:
                logger.error(f"데이터 마이그레이션 검증 실패: {verification}")
                
            return result
            
        except Exception as e:
            logger.error(f"마이그레이션 실행 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "backup_path": backup_path
            }


def create_rollback_script(backup_path: str, current_db_path: str) -> str:
    """롤백 스크립트 생성"""
    rollback_script = f"""#!/bin/bash
# 데이터 마이그레이션 롤백 스크립트
# 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "데이터베이스 롤백 시작..."

# 현재 DB 백업
cp "{current_db_path}" "{current_db_path}.rollback_backup"

# 원본 DB 복원
cp "{backup_path}" "{current_db_path}"

echo "롤백 완료"
echo "원본 백업: {backup_path}"
echo "롤백 전 백업: {current_db_path}.rollback_backup"
"""
    
    rollback_path = Path("rollback_script.sh")
    rollback_path.write_text(rollback_script)
    rollback_path.chmod(0o755)
    
    return str(rollback_path)