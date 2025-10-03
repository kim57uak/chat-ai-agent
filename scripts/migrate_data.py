#!/usr/bin/env python3
"""
데이터 마이그레이션 실행 스크립트
기존 평문 데이터를 암호화된 형태로 마이그레이션
"""

import sys
import os
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.auth.auth_manager import AuthManager
from core.security.data_migration import DataMigrator, create_rollback_script
from core.security.version_manager import VersionManager
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='데이터 마이그레이션 도구')
    parser.add_argument('--old-db', required=True, help='기존 데이터베이스 경로')
    parser.add_argument('--new-db', required=True, help='새 암호화 데이터베이스 경로')
    parser.add_argument('--password', help='암호화 비밀번호 (입력하지 않으면 프롬프트)')
    parser.add_argument('--dry-run', action='store_true', help='실제 마이그레이션 없이 검증만 수행')
    parser.add_argument('--force', action='store_true', help='기존 새 DB가 있어도 덮어쓰기')
    
    args = parser.parse_args()
    
    old_db_path = Path(args.old_db)
    new_db_path = Path(args.new_db)
    
    # 기존 DB 존재 확인
    if not old_db_path.exists():
        logger.error(f"기존 데이터베이스가 존재하지 않습니다: {old_db_path}")
        return 1
    
    # 새 DB 덮어쓰기 확인
    if new_db_path.exists() and not args.force:
        logger.error(f"새 데이터베이스가 이미 존재합니다: {new_db_path}")
        logger.error("--force 옵션을 사용하여 덮어쓰기하거나 다른 경로를 지정하세요")
        return 1
    
    try:
        # 인증 관리자 초기화
        auth_manager = AuthManager()
        
        # 비밀번호 입력
        if args.password:
            password = args.password
        else:
            import getpass
            password = getpass.getpass("암호화 비밀번호를 입력하세요: ")
        
        # 로그인
        if not auth_manager.login(password):
            logger.error("비밀번호가 올바르지 않습니다")
            return 1
        
        logger.info("인증 성공")
        
        # 마이그레이션 도구 초기화
        migrator = DataMigrator(str(old_db_path), str(new_db_path), auth_manager)
        
        # Dry run 모드
        if args.dry_run:
            logger.info("=== DRY RUN 모드 ===")
            
            # 기존 DB 검증
            if not migrator.verify_old_database():
                logger.error("기존 데이터베이스 구조가 올바르지 않습니다")
                return 1
            
            # 통계 출력
            stats = migrator.get_migration_stats()
            logger.info(f"마이그레이션 대상:")
            logger.info(f"  - 세션: {stats['sessions']}개")
            logger.info(f"  - 메시지: {stats['messages']}개")
            
            logger.info("DRY RUN 완료 - 실제 마이그레이션을 수행하려면 --dry-run 옵션을 제거하세요")
            return 0
        
        # 실제 마이그레이션 수행
        logger.info("=== 데이터 마이그레이션 시작 ===")
        
        result = migrator.run_migration()
        
        if result["success"]:
            logger.info("✅ 마이그레이션 성공!")
            logger.info(f"백업 파일: {result['backup_path']}")
            logger.info(f"마이그레이션된 데이터:")
            logger.info(f"  - 세션: {result['migrated']['sessions']}개")
            logger.info(f"  - 메시지: {result['migrated']['messages']}개")
            
            # 롤백 스크립트 생성
            if result['backup_path']:
                rollback_script = create_rollback_script(
                    result['backup_path'], 
                    str(new_db_path)
                )
                logger.info(f"롤백 스크립트: {rollback_script}")
            
            # 버전 정보 출력
            version_manager = VersionManager(str(new_db_path), auth_manager)
            compatibility = version_manager.get_version_compatibility()
            logger.info(f"암호화 버전: {compatibility['current_version']}")
            
            return 0
        else:
            logger.error("❌ 마이그레이션 실패!")
            logger.error(f"오류: {result.get('error', '알 수 없는 오류')}")
            if result.get('backup_path'):
                logger.info(f"백업 파일: {result['backup_path']}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        return 1
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())