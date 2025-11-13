"""
Vector DB Repair Tool
손상된 벡터 DB 복구 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging import get_logger
import lancedb

logger = get_logger("repair_vector_db")


def repair_vector_db(db_path: str):
    """
    벡터 DB 복구
    
    Args:
        db_path: 벡터 DB 경로
    """
    db_path = Path(db_path)
    
    if not db_path.exists():
        logger.error(f"DB path not found: {db_path}")
        return False
    
    try:
        logger.info(f"Connecting to DB: {db_path}")
        db = lancedb.connect(str(db_path))
        
        # 테이블 목록 확인
        tables = db.table_names()
        logger.info(f"Found {len(tables)} tables: {tables}")
        
        for table_name in tables:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Repairing table: {table_name}")
                logger.info(f"{'='*60}")
                
                table = db.open_table(table_name)
                
                # 1. 통계 확인
                try:
                    count = table.count_rows()
                    logger.info(f"✓ Row count: {count}")
                except Exception as e:
                    logger.error(f"✗ Failed to count rows: {e}")
                    continue
                
                # 2. Compact files (손상된 파일 정리)
                try:
                    logger.info("Running compact_files()...")
                    table.compact_files()
                    logger.info("✓ Compact completed")
                except Exception as e:
                    logger.warning(f"✗ Compact failed: {e}")
                
                # 3. Cleanup old versions
                try:
                    logger.info("Running cleanup_old_versions()...")
                    from datetime import timedelta
                    table.cleanup_old_versions(
                        older_than=timedelta(seconds=0),
                        delete_unverified=True
                    )
                    logger.info("✓ Cleanup completed")
                except Exception as e:
                    logger.warning(f"✗ Cleanup failed: {e}")
                
                # 4. Optimize
                try:
                    logger.info("Running optimize()...")
                    table.optimize()
                    logger.info("✓ Optimize completed")
                except Exception as e:
                    logger.warning(f"✗ Optimize failed: {e}")
                
                # 5. 최종 확인
                try:
                    final_count = table.count_rows()
                    logger.info(f"✓ Final row count: {final_count}")
                except Exception as e:
                    logger.error(f"✗ Final count failed: {e}")
                
                logger.info(f"✅ Table '{table_name}' repaired successfully\n")
                
            except Exception as e:
                logger.error(f"❌ Failed to repair table '{table_name}': {e}\n")
                continue
        
        logger.info("="*60)
        logger.info("✅ Repair completed")
        logger.info("="*60)
        return True
        
    except Exception as e:
        logger.error(f"❌ Repair failed: {e}")
        return False


def repair_all_models():
    """모든 모델의 벡터 DB 복구"""
    try:
        from utils.config_path import config_path_manager
        user_config_path = config_path_manager.get_user_config_path()
        
        if user_config_path and user_config_path.exists():
            base_path = user_config_path / "vectordb"
        else:
            import os
            if os.name == "nt":
                base_path = Path.home() / "AppData" / "Local" / "ChatAIAgent" / "vectordb"
            else:
                base_path = Path.home() / ".chat-ai-agent" / "vectordb"
        
        logger.info(f"Base vector DB path: {base_path}")
        
        if not base_path.exists():
            logger.error(f"Vector DB base path not found: {base_path}")
            return
        
        # 모든 모델 폴더 찾기
        model_folders = [f for f in base_path.iterdir() if f.is_dir()]
        logger.info(f"Found {len(model_folders)} model folders")
        
        for model_folder in model_folders:
            logger.info(f"\n{'#'*60}")
            logger.info(f"# Model: {model_folder.name}")
            logger.info(f"{'#'*60}")
            repair_vector_db(str(model_folder))
        
    except Exception as e:
        logger.error(f"Failed to repair all models: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Repair vector database")
    parser.add_argument("--path", help="Specific DB path to repair")
    parser.add_argument("--all", action="store_true", help="Repair all model DBs")
    
    args = parser.parse_args()
    
    if args.all:
        repair_all_models()
    elif args.path:
        repair_vector_db(args.path)
    else:
        # 기본: 모든 모델 복구
        repair_all_models()
