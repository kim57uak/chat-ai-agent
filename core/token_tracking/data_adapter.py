"""
Data adapter for backward compatibility with existing UI.

Converts new unified tracker format to legacy token_tracker format.
"""

from typing import Dict, List, Optional
from core.logging import get_logger

logger = get_logger(__name__)


class DataAdapter:
    """Converts unified tracker data to legacy format for UI compatibility."""
    
    @staticmethod
    def convert_to_legacy_format(conversation_token) -> Dict:
        """
        Convert ConversationToken to legacy format.
        
        Args:
            conversation_token: ConversationToken instance
            
        Returns:
            Dict in legacy format for token_usage_display.py
        """
        if not conversation_token:
            return {
                'conversation_id': None,
                'model_name': None,
                'steps_count': 0,
                'duration_ms': 0,
                'total_actual_tokens': 0,
                'total_estimated_tokens': 0,
                'steps': []
            }
        
        # Convert agents to steps
        steps = []
        for i, agent in enumerate(conversation_token.agents, 1):
            step = {
                'step_name': agent.agent_name,
                'step_type': DataAdapter._agent_to_step_type(agent.agent_name),
                'duration_ms': agent.duration_ms,
                'actual_tokens': agent.total_tokens,
                'estimated_tokens': agent.total_tokens,  # Same as actual
                'tool_name': ', '.join(agent.tool_calls) if agent.tool_calls else None,
                'additional_info': {
                    'input_tokens': agent.input_tokens,
                    'output_tokens': agent.output_tokens,
                    'total_tokens': agent.total_tokens,
                    'estimated_input_tokens': agent.input_tokens,
                    'estimated_output_tokens': agent.output_tokens
                }
            }
            steps.append(step)
        
        # Calculate totals
        total_duration = sum(a.duration_ms for a in conversation_token.agents)
        
        return {
            'conversation_id': conversation_token.conversation_id,
            'model_name': conversation_token.model_name,
            'steps_count': len(conversation_token.agents),
            'duration_ms': total_duration,
            'total_actual_tokens': conversation_token.total_tokens,
            'total_estimated_tokens': conversation_token.total_tokens,
            'steps': steps
        }
    
    @staticmethod
    def _agent_to_step_type(agent_name: str) -> str:
        """
        Convert agent name to legacy StepType.
        
        Args:
            agent_name: Agent name (e.g., 'RAGAgent')
            
        Returns:
            Legacy step type string
        """
        mapping = {
            'SimpleLLM': 'FINAL_RESPONSE',
            'MCPAgent': 'TOOL_EXECUTION',
            'RAGAgent': 'RAG_RETRIEVAL',
            'PythonREPLAgent': 'TOOL_EXECUTION',
            'FileSystemAgent': 'TOOL_EXECUTION',
            'Orchestrator': 'TOOL_DECISION'
        }
        
        return mapping.get(agent_name, 'TOOL_EXECUTION')
    
    @staticmethod
    def get_session_total_tokens(unified_tracker, session_id: Optional[int] = None) -> tuple:
        """
        Get session total tokens in legacy format.
        
        Args:
            unified_tracker: UnifiedTokenTracker instance
            session_id: Session ID (None for current)
            
        Returns:
            (input_tokens, output_tokens, total_tokens)
        """
        try:
            stats = unified_tracker.get_session_stats(session_id)
            
            if not stats or stats['total_tokens'] == 0:
                return (0, 0, 0)
            
            return (
                stats['total_input'],
                stats['total_output'],
                stats['total_tokens']
            )
            
        except Exception as e:
            logger.warning(f"Failed to get session total: {e}")
            return (0, 0, 0)
    
    @staticmethod
    def get_conversation_stats(unified_tracker) -> Optional[Dict]:
        """
        Get current conversation stats in legacy format.
        
        Args:
            unified_tracker: UnifiedTokenTracker instance
            
        Returns:
            Dict in legacy format or None
        """
        try:
            stats = unified_tracker.get_session_stats()
            
            if not stats or stats['conversation_id'] is None:
                return None
            
            # Convert to legacy format
            legacy_stats = {
                'conversation_id': stats['conversation_id'],
                'model_name': stats['model'],
                'steps_count': stats['agent_count'],
                'duration_ms': sum(a['tokens'] for a in stats['agents']),  # Approximate
                'total_actual_tokens': stats['total_tokens'],
                'total_estimated_tokens': stats['total_tokens'],
                'steps': []
            }
            
            # Convert agents to steps
            for agent in stats['agents']:
                step = {
                    'step_name': agent['name'],
                    'step_type': DataAdapter._agent_to_step_type(agent['name']),
                    'duration_ms': 0,  # Not available in summary
                    'actual_tokens': agent['tokens'],
                    'estimated_tokens': agent['tokens'],
                    'tool_name': ', '.join(agent.get('tools', [])) if agent.get('tools') else None,
                    'additional_info': {
                        'input_tokens': agent['tokens'] // 2,  # Approximate
                        'output_tokens': agent['tokens'] // 2,
                        'total_tokens': agent['tokens']
                    }
                }
                legacy_stats['steps'].append(step)
            
            return legacy_stats
            
        except Exception as e:
            logger.warning(f"Failed to get conversation stats: {e}")
            return None
