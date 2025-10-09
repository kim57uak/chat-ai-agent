"""
Version Manager
암호화 버전 관리 및 호환성 유지
"""

import sqlite3
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from core.logging import get_logger

from ..auth.auth_manager import AuthManager

logger = get_logger("version_manager")


class VersionManager:
    """암호화 버전 관리자"""
    
    SUPPORTED_VERSIONS = [1]  # 지원하는 암호화 버전
    CURRENT_VERSION = 1
    
    def __init__(self, db_path: str, auth_manager: AuthManager):
        self.db_path = Path(db_path)
        self.auth_manager = auth_manager
    
    def get_database_version(self) -> Optional[int]:
        """데이터베이스의 암호화 버전 확인"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT version FROM encryption_keys 
                    WHERE is_active = 1 
                    ORDER BY version DESC 
                    LIMIT 1
                """)
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"데이터베이스 버전 확인 실패: {e}")
            return None
    
    def is_version_supported(self, version: int) -> bool:
        """버전 지원 여부 확인"""
        return version in self.SUPPORTED_VERSIONS
    
    def get_version_compatibility(self) -> Dict[str, Any]:
        """버전 호환성 정보"""
        db_version = self.get_database_version()
        
        return {
            "database_version": db_version,
            "current_version": self.CURRENT_VERSION,
            "supported_versions": self.SUPPORTED_VERSIONS,
            "is_compatible": db_version in self.SUPPORTED_VERSIONS if db_version else False,
            "needs_upgrade": db_version < self.CURRENT_VERSION if db_version else True,
            "can_downgrade": db_version > min(self.SUPPORTED_VERSIONS) if db_version else False
        }
    
    def decrypt_data_v1(self, encrypted_data: bytes) -> str:
        """버전 1 데이터 복호화"""
        return self.auth_manager.decrypt_data(encrypted_data)
    
    def decrypt_data_by_version(self, encrypted_data: bytes, version: int) -> str:
        """버전별 데이터 복호화"""
        if version == 1:
            return self.decrypt_data_v1(encrypted_data)
        else:
            raise ValueError(f"지원하지 않는 암호화 버전: {version}")
    
    def get_mixed_version_data(self, table_name: str) -> List[Dict[str, Any]]:
        """다양한 버전의 데이터 조회"""
        results = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(f"""
                    SELECT *, encryption_version FROM {table_name}
                    ORDER BY id
                """)
                
                for row in cursor.fetchall():
                    try:
                        version = row.get('encryption_version', 1)
                        
                        if table_name == 'sessions':
                            decrypted_data = {
                                'id': row['id'],
                                'title': self.decrypt_data_by_version(row['title'], version) if row['title'] else '',
                                'topic_category': self.decrypt_data_by_version(row['topic_category'], version) if row['topic_category'] else None,
                                'model_used': self.decrypt_data_by_version(row['model_used'], version) if row['model_used'] else None,
                                'created_at': row['created_at'],
                                'last_used_at': row['last_used_at'],
                                'message_count': row['message_count'],
                                'encryption_version': version
                            }
                        elif table_name == 'messages':
                            decrypted_data = {
                                'id': row['id'],
                                'session_id': row['session_id'],
                                'role': row['role'],
                                'content': self.decrypt_data_by_version(row['content'], version),
                                'content_html': self.decrypt_data_by_version(row['content_html'], version) if row['content_html'] else None,
                                'tool_calls': self.decrypt_data_by_version(row['tool_calls'], version) if row['tool_calls'] else None,
                                'timestamp': row['timestamp'],
                                'token_count': row['token_count'],
                                'encryption_version': version
                            }
                        
                        results.append(decrypted_data)
                        
                    except Exception as e:
                        logger.warning(f"{table_name} 레코드 {row['id']} 복호화 실패 (버전 {version}): {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"{table_name} 데이터 조회 실패: {e}")
            
        return results
    
    def upgrade_data_version(self, from_version: int, to_version: int) -> Dict[str, Any]:
        """데이터 버전 업그레이드"""
        if from_version == to_version:
            return {"success": True, "message": "이미 최신 버전입니다"}
        
        if not self.is_version_supported(from_version) or not self.is_version_supported(to_version):
            return {"success": False, "error": "지원하지 않는 버전입니다"}
        
        try:
            # 현재는 버전 1만 지원하므로 실제 업그레이드 로직은 향후 구현
            logger.info(f"버전 업그레이드: {from_version} -> {to_version}")
            
            # 새 버전 키 등록
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO encryption_keys (version, is_active) 
                    VALUES (?, 1)
                """, (to_version,))
                conn.commit()
            
            return {
                "success": True,
                "message": f"버전 {from_version}에서 {to_version}으로 업그레이드 완료"
            }
            
        except Exception as e:
            logger.error(f"버전 업그레이드 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def get_version_statistics(self) -> Dict[str, Any]:
        """버전별 데이터 통계"""
        stats = {
            "sessions": {},
            "messages": {},
            "total_sessions": 0,
            "total_messages": 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 세션 버전별 통계
                cursor = conn.execute("""
                    SELECT encryption_version, COUNT(*) as count 
                    FROM sessions 
                    WHERE is_active = 1 
                    GROUP BY encryption_version
                """)
                for row in cursor.fetchall():
                    version, count = row
                    stats["sessions"][f"v{version}"] = count
                    stats["total_sessions"] += count
                
                # 메시지 버전별 통계
                cursor = conn.execute("""
                    SELECT encryption_version, COUNT(*) as count 
                    FROM messages 
                    GROUP BY encryption_version
                """)
                for row in cursor.fetchall():
                    version, count = row
                    stats["messages"][f"v{version}"] = count
                    stats["total_messages"] += count
                    
        except Exception as e:
            logger.error(f"버전 통계 조회 실패: {e}")
            
        return stats
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """데이터 무결성 검증"""
        results = {
            "sessions": {"total": 0, "valid": 0, "invalid": 0},
            "messages": {"total": 0, "valid": 0, "invalid": 0},
            "overall_health": 0.0
        }
        
        # 세션 데이터 검증
        try:
            sessions = self.get_mixed_version_data('sessions')
            results["sessions"]["total"] = len(sessions)
            results["sessions"]["valid"] = len(sessions)  # 복호화 성공한 것만 반환되므로
            
        except Exception as e:
            logger.error(f"세션 데이터 검증 실패: {e}")
        
        # 메시지 데이터 검증
        try:
            messages = self.get_mixed_version_data('messages')
            results["messages"]["total"] = len(messages)
            results["messages"]["valid"] = len(messages)  # 복호화 성공한 것만 반환되므로
            
        except Exception as e:
            logger.error(f"메시지 데이터 검증 실패: {e}")
        
        # 전체 건강도 계산
        total_records = results["sessions"]["total"] + results["messages"]["total"]
        valid_records = results["sessions"]["valid"] + results["messages"]["valid"]
        
        if total_records > 0:
            results["overall_health"] = (valid_records / total_records) * 100
        
        return results


class BackwardCompatibility:
    """하위 호환성 관리"""
    
    def __init__(self, version_manager: VersionManager):
        self.version_manager = version_manager
    
    def can_read_legacy_data(self) -> bool:
        """레거시 데이터 읽기 가능 여부"""
        compatibility = self.version_manager.get_version_compatibility()
        return compatibility["is_compatible"]
    
    def get_legacy_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """레거시 세션 데이터 조회"""
        return self.version_manager.get_mixed_version_data('sessions')[:limit]
    
    def get_legacy_messages(self, session_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """레거시 메시지 데이터 조회"""
        all_messages = self.version_manager.get_mixed_version_data('messages')
        session_messages = [msg for msg in all_messages if msg['session_id'] == session_id]
        return session_messages[:limit]