"""
SQLite Database Repair Tool
"""
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def repair_database(db_path: str):
    """Repair corrupted SQLite database"""
    db_path = Path(db_path)
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return False
    
    # Backup
    backup_path = db_path.parent / f"{db_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"✅ Backup created: {backup_path}")
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return False
    
    # Repair
    temp_path = db_path.parent / f"{db_path.stem}_temp.db"
    
    try:
        logger.info(f"🔧 Repairing: {db_path}")
        
        # Dump to SQL
        with sqlite3.connect(str(db_path)) as old_conn:
            with open(temp_path.with_suffix('.sql'), 'w') as f:
                for line in old_conn.iterdump():
                    f.write(f'{line}\n')
        
        logger.info("✓ Dumped to SQL")
        
        # Create new DB
        if temp_path.exists():
            temp_path.unlink()
        
        with sqlite3.connect(str(temp_path)) as new_conn:
            with open(temp_path.with_suffix('.sql'), 'r') as f:
                new_conn.executescript(f.read())
        
        logger.info("✓ Created new DB")
        
        # Replace
        db_path.unlink()
        temp_path.rename(db_path)
        temp_path.with_suffix('.sql').unlink()
        
        logger.info(f"✅ Repaired: {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Repair failed: {e}")
        
        # Restore backup
        if backup_path.exists():
            shutil.copy2(backup_path, db_path)
            logger.info("↩️  Restored from backup")
        
        return False


def find_and_repair_all():
    """Find and repair all SQLite databases"""
    try:
        from utils.config_path import config_path_manager
        user_config_path = config_path_manager.get_user_config_path()
        
        if user_config_path and user_config_path.exists():
            base_path = user_config_path
        else:
            import os
            if os.name == "nt":
                base_path = Path.home() / "AppData" / "Local" / "ChatAIAgent"
            else:
                base_path = Path.home() / ".chat-ai-agent"
        
        logger.info(f"📁 Searching in: {base_path}")
        
        # Find all .db files
        db_files = list(base_path.rglob("*.db"))
        logger.info(f"Found {len(db_files)} database files")
        
        for db_file in db_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Checking: {db_file.name}")
            
            try:
                # Test connection
                with sqlite3.connect(str(db_file)) as conn:
                    conn.execute("PRAGMA integrity_check").fetchone()
                logger.info("✅ OK")
            except Exception as e:
                logger.warning(f"⚠️  Corrupted: {e}")
                repair_database(str(db_file))
        
    except Exception as e:
        logger.error(f"Failed: {e}")


if __name__ == "__main__":
    print("\n🔧 SQLite Database Repair Tool\n")
    find_and_repair_all()
    print("\n✨ Complete!")
