"""Prompt management following SRP."""

from typing import Dict
from core.config import ConfigManager
import logging

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages user prompts for different models."""
    
    def __init__(self, config_manager: ConfigManager):
        self._config = config_manager
        self._prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load user prompts from config."""
        default_prompts = {
            "gpt": "Korean responses. For tables: |Header1|Header2|\\n|---|---|\\n|Data1|Data2|. Separator MUST be |---|---| (3 dashes only).",
            "gemini": "Korean responses. For tables: |Header1|Header2|\\n|---|---|\\n|Data1|Data2|. Separator MUST be |---|---| (3 dashes only).",
            "perplexity": "Korean responses. For tables: |Header1|Header2|\\n|---|---|\\n|Data1|Data2|. Separator MUST be |---|---| (3 dashes only). Use your real-time search capabilities when needed."
        }
        
        return self._config.get("user_prompt", default_prompts)
    
    def get_prompt_for_model(self, model_name: str) -> str:
        """Get prompt for specific model."""
        model_lower = model_name.lower()
        
        if "gemini" in model_lower:
            return self._prompts.get("gemini", "")
        elif "sonar" in model_lower or "r1-" in model_lower:
            return self._prompts.get("perplexity", "")
        else:
            return self._prompts.get("gpt", "")
    
    def update_prompt(self, model_type: str, prompt_text: str) -> None:
        """Update prompt for model type."""
        if model_type in self._prompts:
            self._prompts[model_type] = prompt_text
            self._save_prompts()
    
    def _save_prompts(self) -> None:
        """Save prompts to config."""
        self._config.set("user_prompt", self._prompts)