"""
Model pricing database for accurate cost calculation.

Pricing data based on official API documentation (pay-as-you-go rates).
"""

from typing import Dict, Optional, Tuple
from core.logging import get_logger

logger = get_logger(__name__)

# Pricing per 1K tokens (USD)
MODEL_PRICING = {
    # OpenAI
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
    
    # Google Gemini 2.0 Flash Series
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-2.0-flash-exp": {"input": 0.0001, "output": 0.0004},
    "gemini-2.0-flash-001": {"input": 0.0001, "output": 0.0004},
    "gemini-2.0-flash-lite": {"input": 0.00005, "output": 0.0002},
    "gemini-2.0-flash-lite-001": {"input": 0.00005, "output": 0.0002},
    "gemini-2.0-flash-thinking-exp": {"input": 0.0001, "output": 0.0004},
    "gemini-flash-latest": {"input": 0.0001, "output": 0.0004},
    "gemini-flash-lite-latest": {"input": 0.00005, "output": 0.0002},
    
    # Google Gemini 2.0 Pro Series
    "gemini-2.0-pro-exp": {"input": 0.00125, "output": 0.005},
    "gemini-2.0-pro-exp-02-05": {"input": 0.00125, "output": 0.005},
    
    # Google Gemini 2.5 Flash Series
    "gemini-2.5-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-2.5-flash-lite": {"input": 0.00005, "output": 0.0002},
    "gemini-2.5-flash-preview-05-20": {"input": 0.0001, "output": 0.0004},
    "gemini-2.5-flash-lite-preview-06-17": {"input": 0.00005, "output": 0.0002},
    
    # Google Gemini 2.5 Pro Series
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-2.5-pro-preview-03-25": {"input": 0.00125, "output": 0.005},
    "gemini-2.5-pro-preview-05-06": {"input": 0.00125, "output": 0.005},
    "gemini-2.5-pro-preview-06-05": {"input": 0.00125, "output": 0.005},
    
    # Google Gemini Legacy
    "gemini-pro": {"input": 0.000125, "output": 0.000375},
    "gemini-pro-latest": {"input": 0.000125, "output": 0.000375},
    "gemini-exp-1206": {"input": 0.000125, "output": 0.000375},
    
    # Perplexity - Sonar Series (Online with web search)
    "sonar": {"input": 0.001, "output": 0.001},
    "sonar-pro": {"input": 0.003, "output": 0.015},
    "sonar-reasoning": {"input": 0.001, "output": 0.005},
    
    # Perplexity - Chat Series (Offline without web search)
    "llama-3.1-sonar-small-128k-chat": {"input": 0.0002, "output": 0.0002},
    "llama-3.1-sonar-large-128k-chat": {"input": 0.001, "output": 0.001},
    "llama-3.1-sonar-huge-128k-chat": {"input": 0.005, "output": 0.005},
    
    # Pollinations (Free)
    "pollinations": {"input": 0.0, "output": 0.0},
    "pollinations-mistral": {"input": 0.0, "output": 0.0},
}


class ModelPricing:
    """Handles model pricing and cost calculations."""
    
    @staticmethod
    def get_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for given token usage.
        
        Args:
            model: Model name (e.g., 'gemini-2.0-flash')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        pricing = ModelPricing.get_pricing_info(model)
        
        if not pricing:
            logger.warning(f"No pricing info for model: {model}, using $0")
            return 0.0
        
        # Calculate cost (pricing is per 1K tokens)
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)
    
    @staticmethod
    def get_pricing_info(model: str) -> Optional[Dict[str, float]]:
        """
        Get pricing information for a model.
        
        Args:
            model: Model name
            
        Returns:
            Dict with 'input' and 'output' prices per 1K tokens, or None
        """
        # Exact match
        if model in MODEL_PRICING:
            return MODEL_PRICING[model]
        
        # Fuzzy match (e.g., "gemini-2.0-flash-exp-1234" -> "gemini-2.0-flash-exp")
        for known_model in MODEL_PRICING:
            if model.startswith(known_model):
                logger.info(f"Using pricing for {known_model} (matched {model})")
                return MODEL_PRICING[known_model]
        
        logger.warning(f"No pricing found for model: {model}")
        return None
    
    @staticmethod
    def update_pricing(model: str, input_price: float, output_price: float):
        """
        Update pricing for a model (runtime only, not persisted).
        
        Args:
            model: Model name
            input_price: Input price per 1K tokens
            output_price: Output price per 1K tokens
        """
        MODEL_PRICING[model] = {"input": input_price, "output": output_price}
        logger.info(f"Updated pricing for {model}: in=${input_price}, out=${output_price}")
    
    @staticmethod
    def get_all_models() -> list:
        """Get list of all models with pricing."""
        return sorted(MODEL_PRICING.keys())
    
    @staticmethod
    def get_cost_comparison(input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """
        Compare costs across all models for given token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dict mapping model name to cost
        """
        return {
            model: ModelPricing.get_cost(model, input_tokens, output_tokens)
            for model in MODEL_PRICING
        }
    
    @staticmethod
    def get_cheapest_model(input_tokens: int, output_tokens: int) -> Tuple[str, float]:
        """
        Find cheapest model for given token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Tuple of (model_name, cost)
        """
        costs = ModelPricing.get_cost_comparison(input_tokens, output_tokens)
        # Exclude free models
        paid_costs = {k: v for k, v in costs.items() if v > 0}
        
        if not paid_costs:
            return ("pollinations", 0.0)
        
        cheapest = min(paid_costs.items(), key=lambda x: x[1])
        return cheapest
    
    @staticmethod
    def get_most_expensive_model(input_tokens: int, output_tokens: int) -> Tuple[str, float]:
        """
        Find most expensive model for given token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Tuple of (model_name, cost)
        """
        costs = ModelPricing.get_cost_comparison(input_tokens, output_tokens)
        most_expensive = max(costs.items(), key=lambda x: x[1])
        return most_expensive
