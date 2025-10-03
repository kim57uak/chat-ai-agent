#!/usr/bin/env python3
"""
마이그레이션 검증 스크립트
암호화된 데이터베이스의 무결성 및 버전 호환성 검증
"""

import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.auth.auth_manager import AuthManager
from core.security.version_manager import VersionManager, BackwardCompatibility
from core.security.encrypted_database import EncryptedDatabase
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='마이그레이션 검증 도구')
    parser.add_argument('--db', required=True, help='검증할 데이터베이스 경로')
    parser.add_argument('--password', help='암호화 비밀번호')
    parser.add_argument('--detailed', action='store_true', help='상세 검증 수행')
    
    args = parser.parse_args()
    
    db_path = Path(args.db)
    
    if not db_path.exists():
        logger.error(f"데이터베이스가 존재하지 않습니다: {db_path}")
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
        
        # 버전 관리자 초기화
        version_manager = VersionManager(str(db_path), auth_manager)
        compatibility_manager = BackwardCompatibility(version_manager)
        
        # 기본 검증
        logger.info("=== 기본 검증 ===")
        
        # 버전 호환성 확인
        compatibility = version_manager.get_version_compatibility()
        logger.info(f"데이터베이스 버전: {compatibility['database_version']}")
        logger.info(f"현재 지원 버전: {compatibility['current_version']}")
        logger.info(f"호환성: {'✅ 호환' if compatibility['is_compatible'] else '❌ 비호환'}")
        
        if compatibility['needs_upgrade']:
            logger.warning("⚠️ 업그레이드가 필요합니다")
        
        # 버전별 통계
        stats = version_manager.get_version_statistics()
        logger.info(f"총 세션: {stats['total_sessions']}개")
        logger.info(f"총 메시지: {stats['total_messages']}개")
        
        for version, count in stats['sessions'].items():
            logger.info(f"  세션 {version}: {count}개")
        
        # 데이터 무결성 검증
        logger.info("=== 데이터 무결성 검증 ===")
        integrity = version_manager.validate_data_integrity()
        logger.info(f"전체 건강도: {integrity['overall_health']:.1f}%")
        logger.info(f"세션 유효성: {integrity['sessions']['valid']}/{integrity['sessions']['total']}")
        logger.info(f"메시지 유효성: {integrity['messages']['valid']}/{integrity['messages']['total']}")
        
        # 상세 검증
        if args.detailed:
            logger.info("=== 상세 검증 ===")
            
            # 암호화된 DB로 실제 데이터 접근 테스트
            encrypted_db = EncryptedDatabase(str(db_path), auth_manager)
            
            # 세션 샘플 테스트
            sessions = encrypted_db.get_sessions(limit=5)
            logger.info(f"세션 샘플 조회: {len(sessions)}개")
            
            for session in sessions[:3]:
                logger.info(f"  세션 {session['id']}: '{session['title'][:30]}...'")
                
                # 메시지 샘플 테스트
                messages = encrypted_db.get_messages(session['id'], limit=3)
                logger.info(f"    메시지: {len(messages)}개")
                
                for msg in messages[:2]:
                    content_preview = msg['content'][:50].replace('\n', ' ')
                    logger.info(f"      {msg['role']}: {content_preview}...")
            
            # 레거시 데이터 호환성 테스트
            if compatibility_manager.can_read_legacy_data():
                logger.info("✅ 레거시 데이터 읽기 가능")
                
                legacy_sessions = compatibility_manager.get_legacy_sessions(limit=3)
                logger.info(f"레거시 세션 조회: {len(legacy_sessions)}개")
            else:
                logger.warning("⚠️ 레거시 데이터 읽기 불가")
        
        # 검증 결과 요약
        logger.info("=== 검증 결과 요약 ===")
        
        issues = []
        if not compatibility['is_compatible']:
            issues.append("버전 비호환")
        if integrity['overall_health'] < 100:
            issues.append(f"데이터 무결성 {integrity['overall_health']:.1f}%")
        
        if not issues:
            logger.info("✅ 모든 검증 통과")
            return 0
        else:
            logger.warning(f"⚠️ 발견된 문제: {', '.join(issues)}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        return 1
    except Exception as e:
        logger.error(f"검증 중 오류 발생: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())