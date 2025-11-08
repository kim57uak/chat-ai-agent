"""
Auto-migration for token tracking on app startup.
"""

from core.logging import get_logger
from .migrations.migration_runner import run_token_tracking_migrations

logger = get_logger(__name__)


def auto_migrate_token_tracking():
    """
    Automatically run token tracking migrations on app startup.
    
    Returns:
        bool: True if successful or already migrated, False on error
    """
    try:
        from core.security.secure_path_manager import secure_path_manager
        db_path = secure_path_manager.get_database_path()
        
        logger.info("Running token tracking auto-migration...")
        success = run_token_tracking_migrations(db_path)
        
        if success:
            logger.info("Token tracking migration completed successfully")
        else:
            logger.warning("Token tracking migration failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Auto-migration error: {e}")
        return False
