"""AI Model configuration manager."""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class AIModelManager:
    """Manages AI model configurations."""
    
    def __init__(self, model_config_path: str = "ai_model.json"):
        self.model_config_path = Path(model_config_path)
        self._models = self._load_models()
    
    def _load_models(self) -> Dict:
        """Load model configurations from JSON file."""
        if not self.model_config_path.exists():
            return {"models": {}}
        
        try:
            with open(self.model_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"models": {}}
    
    def get_available_models(self) -> List[str]:
        """Get list of available model IDs."""
        return list(self._models.get("models", {}).keys())
    
    def get_models_by_category(self) -> Dict[str, List[Dict]]:
        """Get models grouped by category."""
        models_by_category = {}
        
        for model_id, model_info in self._models.get("models", {}).items():
            category = model_info.get("category", "Other")
            if category not in models_by_category:
                models_by_category[category] = []
            
            models_by_category[category].append({
                "id": model_id,
                "name": model_info.get("name", model_id),
                "provider": model_info.get("provider", "unknown")
            })
        
        return models_by_category
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """Get information for a specific model."""
        return self._models.get("models", {}).get(model_id)
    
    def get_model_display_name(self, model_id: str) -> str:
        """Get display name for a model."""
        model_info = self.get_model_info(model_id)
        if model_info:
            return model_info.get("name", model_id)
        return model_id
    
    def get_model_provider(self, model_id: str) -> str:
        """Get provider for a model."""
        model_info = self.get_model_info(model_id)
        if model_info:
            return model_info.get("provider", "unknown")
        return "unknown"