import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PerplexityLLM:
    """Perplexity API 래퍼"""
    
    def __init__(self, api_key: str, model_name: str = "llama-3.1-sonar-small-128k-online"):
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = "https://api.perplexity.ai/chat/completions"
        
    @property
    def _llm_type(self) -> str:
        return "perplexity"
    
    def _call(self, prompt: str, stop: Optional[list] = None, **kwargs) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 4000)
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Perplexity API 오류: {e}")
            raise e