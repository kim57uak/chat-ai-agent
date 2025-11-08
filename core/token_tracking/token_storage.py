"""
Token storage layer for database operations.

Handles all CRUD operations for token tracking tables.
"""

import sqlite3
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from core.logging import get_logger

logger = get_logger(__name__)


class TokenStorage:
    """Manages token tracking data persistence."""
    
    def __init__(self, db_path: str):
        """
        Initialize token storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_connection()
    
    def _ensure_connection(self):
        """Ensure database file exists and is accessible."""
        db_file = Path(self.db_path)
        if not db_file.exists():
            logger.warning(f"Database file not found: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with WAL mode."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========== Insert Operations ==========
    
    def insert_token_usage(
        self,
        session_id: int,
        chat_mode: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        agent_name: Optional[str] = None,
        message_id: Optional[int] = None,
        duration_ms: Optional[float] = None,
        tool_calls: Optional[List[str]] = None,
        additional_info: Optional[Dict] = None
    ) -> int:
        """
        Insert token usage record.
        
        Returns:
            ID of inserted record
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO token_usage (
                        session_id, message_id, chat_mode, model_name, agent_name,
                        input_tokens, output_tokens, total_tokens, cost_usd,
                        duration_ms, tool_calls, additional_info
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        message_id,
                        chat_mode,
                        model_name,
                        agent_name,
                        input_tokens,
                        output_tokens,
                        input_tokens + output_tokens,
                        cost_usd,
                        duration_ms,
                        json.dumps(tool_calls) if tool_calls else None,
                        json.dumps(additional_info) if additional_info else None
                    )
                )
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Failed to insert token usage: {e}", exc_info=True)
            return -1
    
    def update_session_summary(
        self,
        session_id: int,
        total_input: int,
        total_output: int,
        total_cost: float,
        mode_breakdown: Dict[str, int],
        model_breakdown: Dict[str, int],
        agent_breakdown: Dict[str, int]
    ):
        """Update session token summary."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO session_token_summary (
                        session_id, total_input_tokens, total_output_tokens,
                        total_tokens, total_cost_usd, mode_breakdown,
                        model_breakdown, agent_breakdown, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        total_input,
                        total_output,
                        total_input + total_output,
                        total_cost,
                        json.dumps(mode_breakdown),
                        json.dumps(model_breakdown),
                        json.dumps(agent_breakdown),
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to update session summary: {e}", exc_info=True)
    

    
    # ========== Query Operations ==========
    
    def get_session_tokens(self, session_id: int) -> List[Dict]:
        """Get all token usage records for a session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM token_usage
                    WHERE session_id = ?
                    ORDER BY timestamp
                    """,
                    (session_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get session tokens: {e}", exc_info=True)
            return []
    
    def get_session_summary(self, session_id: int) -> Optional[Dict]:
        """Get session token summary."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM session_token_summary WHERE session_id = ?",
                    (session_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get session summary: {e}", exc_info=True)
            return None
    

    
    def get_model_usage_history(self, model: str, days: int = 30) -> List[Dict]:
        """Get usage history for specific model."""
        try:
            start_date = date.today() - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT 
                        DATE(timestamp) as date,
                        SUM(total_tokens) as total_tokens,
                        SUM(cost_usd) as total_cost,
                        COUNT(*) as usage_count
                    FROM token_usage
                    WHERE model_name = ? AND DATE(timestamp) >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                    """,
                    (model, start_date.isoformat())
                )
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get model usage history: {e}", exc_info=True)
            return []
    
    # ========== Aggregation Operations ==========
    
    def aggregate_by_mode(self, session_id: Optional[int] = None) -> Dict[str, Dict]:
        """Aggregate token usage by chat mode."""
        try:
            with self._get_connection() as conn:
                if session_id:
                    cursor = conn.execute(
                        """
                        SELECT 
                            chat_mode,
                            SUM(input_tokens) as input_tokens,
                            SUM(output_tokens) as output_tokens,
                            SUM(total_tokens) as total_tokens,
                            SUM(cost_usd) as total_cost,
                            COUNT(*) as count
                        FROM token_usage
                        WHERE session_id = ?
                        GROUP BY chat_mode
                        """,
                        (session_id,)
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT 
                            chat_mode,
                            SUM(input_tokens) as input_tokens,
                            SUM(output_tokens) as output_tokens,
                            SUM(total_tokens) as total_tokens,
                            SUM(cost_usd) as total_cost,
                            COUNT(*) as count
                        FROM token_usage
                        GROUP BY chat_mode
                        """
                    )
                
                return {row['chat_mode']: dict(row) for row in cursor.fetchall()}
                
        except Exception as e:
            logger.error(f"Failed to aggregate by mode: {e}", exc_info=True)
            return {}
    
    def aggregate_by_model(self, session_id: Optional[int] = None) -> Dict[str, Dict]:
        """Aggregate token usage by model."""
        try:
            with self._get_connection() as conn:
                if session_id:
                    cursor = conn.execute(
                        """
                        SELECT 
                            model_name,
                            SUM(input_tokens) as input_tokens,
                            SUM(output_tokens) as output_tokens,
                            SUM(total_tokens) as total_tokens,
                            SUM(cost_usd) as total_cost,
                            COUNT(*) as count
                        FROM token_usage
                        WHERE session_id = ?
                        GROUP BY model_name
                        """,
                        (session_id,)
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT 
                            model_name,
                            SUM(input_tokens) as input_tokens,
                            SUM(output_tokens) as output_tokens,
                            SUM(total_tokens) as total_tokens,
                            SUM(cost_usd) as total_cost,
                            COUNT(*) as count
                        FROM token_usage
                        GROUP BY model_name
                        """
                    )
                
                return {row['model_name']: dict(row) for row in cursor.fetchall()}
                
        except Exception as e:
            logger.error(f"Failed to aggregate by model: {e}", exc_info=True)
            return {}
    
    def aggregate_by_agent(self, session_id: Optional[int] = None) -> Dict[str, Dict]:
        """Aggregate token usage by agent (RAG mode only)."""
        try:
            with self._get_connection() as conn:
                if session_id:
                    cursor = conn.execute(
                        """
                        SELECT 
                            agent_name,
                            SUM(input_tokens) as input_tokens,
                            SUM(output_tokens) as output_tokens,
                            SUM(total_tokens) as total_tokens,
                            SUM(cost_usd) as total_cost,
                            COUNT(*) as count
                        FROM token_usage
                        WHERE session_id = ? AND agent_name IS NOT NULL
                        GROUP BY agent_name
                        """,
                        (session_id,)
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT 
                            agent_name,
                            SUM(input_tokens) as input_tokens,
                            SUM(output_tokens) as output_tokens,
                            SUM(total_tokens) as total_tokens,
                            SUM(cost_usd) as total_cost,
                            COUNT(*) as count
                        FROM token_usage
                        WHERE agent_name IS NOT NULL
                        GROUP BY agent_name
                        """
                    )
                
                return {row['agent_name']: dict(row) for row in cursor.fetchall()}
                
        except Exception as e:
            logger.error(f"Failed to aggregate by agent: {e}", exc_info=True)
            return {}
    
    def aggregate_by_mode_period(self, start_date: datetime, end_date: datetime) -> Dict[str, Dict]:
        """Aggregate by mode for date range."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT 
                        chat_mode,
                        SUM(input_tokens) as input_tokens,
                        SUM(output_tokens) as output_tokens,
                        SUM(total_tokens) as total_tokens,
                        SUM(cost_usd) as total_cost,
                        COUNT(*) as count
                    FROM token_usage
                    WHERE timestamp BETWEEN ? AND ?
                    GROUP BY chat_mode
                    """,
                    (start_date.isoformat(), end_date.isoformat())
                )
                return {row['chat_mode']: dict(row) for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to aggregate by mode period: {e}")
            return {}
    
    def aggregate_by_model_period(self, start_date: datetime, end_date: datetime) -> Dict[str, Dict]:
        """Aggregate by model for date range."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT 
                        model_name,
                        SUM(input_tokens) as input_tokens,
                        SUM(output_tokens) as output_tokens,
                        SUM(total_tokens) as total_tokens,
                        SUM(cost_usd) as total_cost,
                        COUNT(*) as count
                    FROM token_usage
                    WHERE timestamp BETWEEN ? AND ?
                    GROUP BY model_name
                    """,
                    (start_date.isoformat(), end_date.isoformat())
                )
                return {row['model_name']: dict(row) for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to aggregate by model period: {e}")
            return {}
    
    def aggregate_by_agent_period(self, start_date: datetime, end_date: datetime) -> Dict[str, Dict]:
        """Aggregate by agent for date range."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT 
                        agent_name,
                        SUM(input_tokens) as input_tokens,
                        SUM(output_tokens) as output_tokens,
                        SUM(total_tokens) as total_tokens,
                        SUM(cost_usd) as total_cost,
                        COUNT(*) as count
                    FROM token_usage
                    WHERE timestamp BETWEEN ? AND ? AND agent_name IS NOT NULL
                    GROUP BY agent_name
                    """,
                    (start_date.isoformat(), end_date.isoformat())
                )
                return {row['agent_name']: dict(row) for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to aggregate by agent period: {e}")
            return {}
