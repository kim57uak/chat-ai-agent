"""
Migration runner for token tracking database schema.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from core.logging import get_logger

logger = get_logger(__name__)


class MigrationRunner:
    """Runs database migrations for token tracking system."""
    
    def __init__(self, db_path: str):
        """
        Initialize migration runner.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent
    
    def run_migrations(self) -> bool:
        """
        Run all pending migrations.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                
                # Get applied migrations
                applied = self._get_applied_migrations(conn)
                logger.info(f"Applied migrations: {applied}")
                
                # Get available migrations
                available = self._get_available_migrations()
                logger.info(f"Available migrations: {available}")
                
                # Run pending migrations
                for version in available:
                    if version not in applied:
                        logger.info(f"Running migration {version}...")
                        self._run_migration(conn, version)
                        logger.info(f"Migration {version} completed")
                
                return True
                
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return False
    
    def _get_applied_migrations(self, conn: sqlite3.Connection) -> set:
        """Get list of applied migration versions."""
        try:
            cursor = conn.execute(
                "SELECT version FROM migration_history ORDER BY applied_at"
            )
            return {row[0] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            # migration_history table doesn't exist yet
            return set()
    
    def _get_available_migrations(self) -> list:
        """Get list of available migration files."""
        migrations = []
        for file in sorted(self.migrations_dir.glob("*.sql")):
            version = file.stem  # e.g., "001_add_token_tables"
            migrations.append(version)
        return migrations
    
    def _run_migration(self, conn: sqlite3.Connection, version: str):
        """Run a single migration."""
        sql_file = self.migrations_dir / f"{version}.sql"
        
        if not sql_file.exists():
            raise FileNotFoundError(f"Migration file not found: {sql_file}")
        
        # Read and execute SQL
        sql = sql_file.read_text()
        conn.executescript(sql)
        conn.commit()
        
        logger.info(f"Migration {version} applied successfully")
    
    def rollback_migration(self, version: str) -> bool:
        """
        Rollback a specific migration (if rollback script exists).
        
        Args:
            version: Migration version to rollback
            
        Returns:
            True if successful, False otherwise
        """
        try:
            rollback_file = self.migrations_dir / f"{version}_rollback.sql"
            
            if not rollback_file.exists():
                logger.warning(f"No rollback script for {version}")
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                sql = rollback_file.read_text()
                conn.executescript(sql)
                conn.commit()
                
                # Remove from migration history
                conn.execute(
                    "DELETE FROM migration_history WHERE version = ?",
                    (version,)
                )
                conn.commit()
                
                logger.info(f"Migration {version} rolled back successfully")
                return True
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
            return False


def run_token_tracking_migrations(db_path: str) -> bool:
    """
    Convenience function to run token tracking migrations.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        True if successful, False otherwise
    """
    runner = MigrationRunner(db_path)
    return runner.run_migrations()
