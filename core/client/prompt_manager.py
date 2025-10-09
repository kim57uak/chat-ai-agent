"""Prompt management following SRP."""

from typing import Dict
from core.config import ConfigManager
from ui.prompts import prompt_manager as central_prompt_manager, ModelType
from core.logging import get_logger

logger = get_logger("prompt_manager")


class PromptManager:
    """Manages user prompts for different models."""
    
    def __init__(self, config_manager: ConfigManager):
        self._config = config_manager
        self._prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load user prompts from config."""
        return self._config.get("user_prompt", {})
    
    def get_prompt_for_model(self, model_name: str) -> str:
        """Get prompt for specific model."""
        model_lower = model_name.lower()
        
        if "gemini" in model_lower:
            return self._prompts.get("gemini") or central_prompt_manager.get_system_prompt(ModelType.GOOGLE.value)
        elif "sonar" in model_lower or "r1-" in model_lower:
            return self._prompts.get("perplexity") or central_prompt_manager.get_system_prompt(ModelType.PERPLEXITY.value)
        else:
            return self._prompts.get("gpt") or central_prompt_manager.get_system_prompt(ModelType.OPENAI.value)
    
    def update_prompt(self, model_type: str, prompt_text: str) -> None:
        """Update prompt for model type."""
        if model_type in self._prompts:
            self._prompts[model_type] = prompt_text
            self._save_prompts()
    
    def _save_prompts(self) -> None:
        """Save prompts to config."""
        self._config.set("user_prompt", self._prompts)