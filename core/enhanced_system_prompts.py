"""
DEPRECATED: Enhanced system prompts for AI agent

이 파일은 더 이상 사용되지 않습니다.
대신 ui/prompts.py의 중앙관리 시스템을 사용하세요.

Migration Guide:
- SystemPrompts.get_general_chat_prompt() -> prompt_manager.get_system_prompt(model_type)
- SystemPrompts.get_image_analysis_prompt() -> prompt_manager.get_ocr_prompt()
- SystemPrompts.get_tool_decision_prompt() -> prompt_manager.get_tool_decision_prompt()
- SystemPrompts.get_perplexity_mcp_prompt() -> prompt_manager.get_agent_system_prompt(ModelType.PERPLEXITY.value)
"""

import warnings
from ui.prompts import prompt_manager, ModelType

warnings.warn(
    "enhanced_system_prompts.py is deprecated. Use ui.prompts.prompt_manager instead.",
    DeprecationWarning,
    stacklevel=2
)


class SystemPrompts:
    """Deprecated: Use ui.prompts.prompt_manager instead"""
    
    @staticmethod
    def get_general_chat_prompt() -> str:
        warnings.warn("Use prompt_manager.get_system_prompt() instead", DeprecationWarning)
        return prompt_manager.get_system_prompt(ModelType.COMMON.value)
    
    @staticmethod
    def get_image_analysis_prompt() -> str:
        warnings.warn("Use prompt_manager.get_ocr_prompt() instead", DeprecationWarning)
        return prompt_manager.get_ocr_prompt()
    
    @staticmethod
    def get_tool_decision_prompt() -> str:
        warnings.warn("Use prompt_manager.get_tool_decision_prompt() instead", DeprecationWarning)
        return "Use prompt_manager.get_tool_decision_prompt(model_type, user_input, available_tools)"
    
    @staticmethod
    def get_mcp_tool_usage_prompt() -> str:
        warnings.warn("Use prompt_manager.get_tool_prompt() instead", DeprecationWarning)
        return prompt_manager.get_tool_prompt(ModelType.COMMON.value)
    
    @staticmethod
    def get_content_formatting_prompt() -> str:
        warnings.warn("Use prompt_manager.get_response_format_prompt() instead", DeprecationWarning)
        return prompt_manager.get_response_format_prompt()
    
    @staticmethod
    def get_perplexity_mcp_prompt() -> str:
        warnings.warn("Use prompt_manager.get_agent_system_prompt(ModelType.PERPLEXITY.value) instead", DeprecationWarning)
        return prompt_manager.get_agent_system_prompt(ModelType.PERPLEXITY.value)