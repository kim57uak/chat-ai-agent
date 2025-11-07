"""
Unified token tracker with 4-dimensional analysis.

Tracks tokens across:
- Chat Mode (SIMPLE/TOOL/RAG)
- Model (GPT-4, Gemini, etc.)
- Agent (RAGAgent, MCPAgent, etc.)
- Time (session, 7d, 30d, all)
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from threading import Lock
from PyQt6.QtCore import QObject, pyqtSignal

from .model_pricing import ModelPricing
from .token_storage import TokenStorage
from core.logging import get_logger

logger = get_logger(__name__)


class ChatModeType(Enum):
    """Chat mode types."""
    SIMPLE = "simple"
    TOOL = "tool"
    RAG = "rag"


@dataclass
class AgentExecutionToken:
    """Token usage for single agent execution."""
    agent_name: str
    model_name: str
    input_tokens: int
    output_tokens: int
    cost: float
    tool_calls: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ConversationToken:
    """Token usage for entire conversation."""
    conversation_id: str
    mode: ChatModeType
    model_name: str
    agents: List[AgentExecutionToken] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    session_id: Optional[int] = None
    
    @property
    def total_input(self) -> int:
        return sum(a.input_tokens for a in self.agents)
    
    @property
    def total_output(self) -> int:
        return sum(a.output_tokens for a in self.agents)
    
    @property
    def total_tokens(self) -> int:
        return self.total_input + self.total_output
    
    @property
    def total_cost(self) -> float:
        return sum(a.cost for a in self.agents)
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class UnifiedTokenTracker(QObject):
    """
    Unified token tracking system.
    
    Provides comprehensive tracking with DB persistence and real-time updates.
    """
    
    # Signals for UI updates
    token_updated = pyqtSignal(dict)  # Emits current conversation stats
    
    def __init__(self, db_path: str):
        """
        Initialize unified token tracker.
        
        Args:
            db_path: Path to SQLite database
        """
        super().__init__()
        
        # Create tables if not exist
        self._create_tables(db_path)
        
        self.storage = TokenStorage(db_path)
        self._lock = Lock()
        
        # Current conversation tracking
        self._current_conversation: Optional[ConversationToken] = None
        self._conversation_counter = 0
        
        # Session cache
        self._session_cache: Dict[int, ConversationToken] = {}
        
        logger.info("UnifiedTokenTracker initialized")
    
    def _create_tables(self, db_path: str):
        """Create token tracking tables if not exist."""
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Token usage table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    message_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    chat_mode TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    agent_name TEXT,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    duration_ms REAL,
                    tool_calls TEXT,
                    additional_info TEXT
                )
            """)
            
            # Session summary table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_token_summary (
                    session_id INTEGER PRIMARY KEY,
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    total_cost_usd REAL DEFAULT 0.0,
                    mode_breakdown TEXT,
                    model_breakdown TEXT,
                    agent_breakdown TEXT,
                    first_message_at DATETIME,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            

            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_token_usage_session ON token_usage(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp ON token_usage(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_token_usage_mode ON token_usage(chat_mode)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_token_usage_model ON token_usage(model_name)")
            
            conn.commit()
            conn.close()
            
            logger.info("Token tracking tables created/verified")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
    
    # ========== Conversation Lifecycle ==========
    
    def start_conversation(
        self,
        mode: ChatModeType,
        model: str,
        session_id: Optional[int] = None
    ) -> str:
        """
        Start tracking a new conversation.
        
        Args:
            mode: Chat mode (SIMPLE/TOOL/RAG)
            model: Model name
            session_id: Optional session ID for DB persistence
            
        Returns:
            Conversation ID
        """
        with self._lock:
            self._conversation_counter += 1
            conversation_id = f"conv_{self._conversation_counter}_{datetime.now().timestamp()}"
            
            self._current_conversation = ConversationToken(
                conversation_id=conversation_id,
                mode=mode,
                model_name=model,
                session_id=session_id
            )
            
            logger.info(f"Started conversation {conversation_id} (mode={mode.value}, model={model}, session_id={session_id})")
            return conversation_id
    
    def track_agent(
        self,
        agent_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        tool_calls: Optional[List[str]] = None,
        duration_ms: float = 0.0
    ):
        """
        Track agent execution within current conversation.
        
        Args:
            agent_name: Name of agent (e.g., 'RAGAgent')
            model: Model used by agent
            input_tokens: Input token count
            output_tokens: Output token count
            tool_calls: List of tool names called
            duration_ms: Execution duration in milliseconds
        """
        if not self._current_conversation:
            logger.warning("No active conversation, cannot track agent")
            return
        
        with self._lock:
            # Calculate cost
            cost = ModelPricing.get_cost(model, input_tokens, output_tokens)
            
            # Create agent execution record
            agent_exec = AgentExecutionToken(
                agent_name=agent_name,
                model_name=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                tool_calls=tool_calls or [],
                duration_ms=duration_ms
            )
            
            self._current_conversation.agents.append(agent_exec)
            
            logger.info(
                f"Tracked {agent_name}: {input_tokens}+{output_tokens} tokens, "
                f"${cost:.6f}, {len(tool_calls or [])} tools"
            )
            
            # Emit signal for UI update
            self._emit_update()
    
    def end_conversation(self) -> Optional[ConversationToken]:
        """
        End current conversation and persist to DB.
        
        Returns:
            Completed conversation token data
        """
        if not self._current_conversation:
            logger.warning("No active conversation to end")
            return None
        
        with self._lock:
            self._current_conversation.end_time = datetime.now()
            
            # Save to database
            if self._current_conversation.session_id:
                self._save_to_db(self._current_conversation)
            
            # Cache for session
            if self._current_conversation.session_id:
                self._session_cache[self._current_conversation.session_id] = self._current_conversation
            
            logger.info(
                f"Ended conversation {self._current_conversation.conversation_id}: "
                f"{self._current_conversation.total_tokens} tokens, "
                f"${self._current_conversation.total_cost:.6f}, "
                f"session_id={self._current_conversation.session_id}"
            )
            
            result = self._current_conversation
            self._current_conversation = None
            
            return result
    
    # ========== Persistence ==========
    
    def _save_to_db(self, conversation: ConversationToken):
        """Save conversation to database."""
        try:
            session_id = conversation.session_id
            if not session_id:
                return
            
            # Insert each agent execution
            for agent in conversation.agents:
                self.storage.insert_token_usage(
                    session_id=session_id,
                    chat_mode=conversation.mode.value,
                    model_name=agent.model_name,
                    input_tokens=agent.input_tokens,
                    output_tokens=agent.output_tokens,
                    cost_usd=agent.cost,
                    agent_name=agent.agent_name,
                    duration_ms=agent.duration_ms,
                    tool_calls=agent.tool_calls
                )
            
            # Update session summary
            mode_breakdown = self._calculate_mode_breakdown(session_id)
            model_breakdown = self._calculate_model_breakdown(session_id)
            agent_breakdown = self._calculate_agent_breakdown(session_id)
            
            self.storage.update_session_summary(
                session_id=session_id,
                total_input=conversation.total_input,
                total_output=conversation.total_output,
                total_cost=conversation.total_cost,
                mode_breakdown=mode_breakdown,
                model_breakdown=model_breakdown,
                agent_breakdown=agent_breakdown
            )
            
            logger.info(f"Saved conversation to DB (session_id={session_id})")
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}", exc_info=True)
    
    def _load_from_db(self, session_id: int) -> Optional[ConversationToken]:
        """Load conversation from database."""
        try:
            tokens = self.storage.get_session_tokens(session_id)
            if not tokens:
                return None
            
            # Reconstruct conversation
            first_token = tokens[0]
            conversation = ConversationToken(
                conversation_id=f"session_{session_id}",
                mode=ChatModeType(first_token['chat_mode']),
                model_name=first_token['model_name'],
                session_id=session_id
            )
            
            # Add agent executions
            for token in tokens:
                agent = AgentExecutionToken(
                    agent_name=token['agent_name'] or 'Unknown',
                    model_name=token['model_name'],
                    input_tokens=token['input_tokens'],
                    output_tokens=token['output_tokens'],
                    cost=token['cost_usd'],
                    tool_calls=token['tool_calls'] or [],
                    duration_ms=token['duration_ms'] or 0.0,
                    timestamp=datetime.fromisoformat(token['timestamp'])
                )
                conversation.agents.append(agent)
            
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}", exc_info=True)
            return None
    
    # ========== Statistics ==========
    
    def get_session_stats(self, session_id: Optional[int] = None) -> Dict:
        """
        Get statistics for current or specific session.
        
        Args:
            session_id: Session ID (None for current conversation)
            
        Returns:
            Dict with comprehensive statistics
        """
        if session_id:
            conversation = self._session_cache.get(session_id) or self._load_from_db(session_id)
        else:
            conversation = self._current_conversation
        
        if not conversation:
            return self._empty_stats()
        
        return {
            'conversation_id': conversation.conversation_id,
            'mode': conversation.mode.value,
            'model': conversation.model_name,
            'total_input': conversation.total_input,
            'total_output': conversation.total_output,
            'total_tokens': conversation.total_tokens,
            'total_cost': conversation.total_cost,
            'agent_count': len(conversation.agents),
            'agents': [
                {
                    'name': a.agent_name,
                    'tokens': a.total_tokens,
                    'cost': a.cost,
                    'tools': len(a.tool_calls)
                }
                for a in conversation.agents
            ]
        }
    
    def get_mode_breakdown(self, session_id: Optional[int] = None) -> Dict[str, Dict]:
        """Get token breakdown by chat mode."""
        return self.storage.aggregate_by_mode(session_id)
    
    def get_model_breakdown(self, session_id: Optional[int] = None) -> Dict[str, Dict]:
        """Get token breakdown by model."""
        return self.storage.aggregate_by_model(session_id)
    
    def get_agent_breakdown(self, session_id: Optional[int] = None) -> Dict[str, Dict]:
        """Get token breakdown by agent (RAG mode only)."""
        return self.storage.aggregate_by_agent(session_id)
    
    def get_historical_stats(self, days: int = 30) -> Dict:
        """
        Get historical statistics for past N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with mode/model/agent breakdown
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query token_usage table directly
        mode_breakdown = self.storage.aggregate_by_mode_period(start_date, end_date)
        model_breakdown = self.storage.aggregate_by_model_period(start_date, end_date)
        agent_breakdown = self.storage.aggregate_by_agent_period(start_date, end_date)
        
        return {
            'mode_breakdown': mode_breakdown,
            'model_breakdown': model_breakdown,
            'agent_breakdown': agent_breakdown
        }
    
    # ========== Cost Analysis ==========
    
    def get_total_cost(self, session_id: Optional[int] = None) -> float:
        """Get total cost for session or all time."""
        if session_id:
            summary = self.storage.get_session_summary(session_id)
            return summary['total_cost_usd'] if summary else 0.0
        
        # Current conversation
        if self._current_conversation:
            return self._current_conversation.total_cost
        
        return 0.0
    
    def get_cost_by_model(self, session_id: Optional[int] = None) -> Dict[str, float]:
        """Get cost breakdown by model."""
        breakdown = self.get_model_breakdown(session_id)
        return {model: data['total_cost'] for model, data in breakdown.items()}
    
    def get_most_expensive_model(self, session_id: Optional[int] = None) -> tuple:
        """Get most expensive model and its cost."""
        costs = self.get_cost_by_model(session_id)
        if not costs:
            return ("N/A", 0.0)
        
        most_expensive = max(costs.items(), key=lambda x: x[1])
        return most_expensive
    
    # ========== Helper Methods ==========
    
    def _calculate_mode_breakdown(self, session_id: int) -> Dict[str, int]:
        """Calculate mode breakdown for session."""
        breakdown = self.storage.aggregate_by_mode(session_id)
        return {mode: data['total_tokens'] for mode, data in breakdown.items()}
    
    def _calculate_model_breakdown(self, session_id: int) -> Dict[str, int]:
        """Calculate model breakdown for session."""
        breakdown = self.storage.aggregate_by_model(session_id)
        return {model: data['total_tokens'] for model, data in breakdown.items()}
    
    def _calculate_agent_breakdown(self, session_id: int) -> Dict[str, int]:
        """Calculate agent breakdown for session."""
        breakdown = self.storage.aggregate_by_agent(session_id)
        return {agent: data['total_tokens'] for agent, data in breakdown.items()}
    
    def _emit_update(self):
        """Emit signal with current stats for UI update."""
        try:
            stats = self.get_session_stats()
            self.token_updated.emit(stats)
        except Exception as e:
            logger.error(f"Failed to emit update: {e}", exc_info=True)
    
    def _empty_stats(self) -> Dict:
        """Return empty statistics dict."""
        return {
            'conversation_id': None,
            'mode': None,
            'model': None,
            'total_input': 0,
            'total_output': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'agent_count': 0,
            'agents': []
        }


# Global instance (singleton pattern)
_unified_tracker_instance: Optional[UnifiedTokenTracker] = None


def get_unified_tracker(db_path: Optional[str] = None) -> UnifiedTokenTracker:
    """
    Get global unified token tracker instance.
    
    Args:
        db_path: Database path (required for first call)
        
    Returns:
        UnifiedTokenTracker instance
    """
    global _unified_tracker_instance
    
    if _unified_tracker_instance is None:
        if db_path is None:
            raise ValueError("db_path required for first initialization")
        _unified_tracker_instance = UnifiedTokenTracker(db_path)
    
    return _unified_tracker_instance
