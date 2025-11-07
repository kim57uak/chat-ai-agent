"""
Apply token tracking migration to existing database.
"""

import sys
from pathlib import Path
from core.token_tracking.migrations.migration_runner import run_token_tracking_migrations
from core.security.secure_path_manager import SecurePathManager
from core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Apply token tracking migration."""
    print("🔄 Token Tracking Migration\n")
    
    try:
        # Get database path
        path_manager = SecurePathManager()
        db_path = path_manager.get_database_path()
        
        print(f"Database: {db_path}")
        
        if not Path(db_path).exists():
            print("❌ Database file not found!")
            return 1
        
        # Backup database
        backup_path = f"{db_path}.backup"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        
        # Run migrations
        print("\n🚀 Running migrations...")
        success = run_token_tracking_migrations(db_path)
        
        if success:
            print("\n✅ Migration completed successfully!")
            print("\nNew tables created:")
            print("  - token_usage")
            print("  - session_token_summary")
            print("  - global_token_stats")
            print("  - migration_history")
            return 0
        else:
            print("\n❌ Migration failed!")
            print(f"Restore from backup: {backup_path}")
            return 1
            
    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
